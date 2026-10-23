"""Test the optional persistent GUI font workaround from the distributed add-on ZIP."""
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "script.kodi.utilities.setup/script.kodi.utilities.setup-0.1.18.zip"
ENTRY = "script.kodi.utilities.setup/resources/lib/native_gui_font.py"
with zipfile.ZipFile(PACKAGE) as archive:
    source = archive.read(ENTRY)
f = types.ModuleType("native_gui_font")
exec(compile(source, ENTRY, "exec"), f.__dict__)

VANILLA = b"#version 100\nprecision mediump float;\nvarying vec4 m_cord0;\nvoid main() {}\n"


class FontFixTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.shader = str(root / "usr/gles_shader_fonts.frag")
        self.autostart = str(root / "storage/.config/autostart.sh")
        self.data_dir = str(root / "storage/addon_data/native_gui_font")
        Path(self.shader).parent.mkdir(parents=True)
        Path(self.shader).write_bytes(VANILLA)
        self.storage_root = str(root / "storage")

    def install(self, apply_now=False):
        return f.install(shader=self.shader, autostart=self.autostart,
                         data_dir=self.data_dir, apply_now=apply_now,
                         storage_root=self.storage_root)

    def remove(self):
        return f.uninstall(shader=self.shader, autostart=self.autostart, data_dir=self.data_dir)

    def test_install_uninstall_without_existing_autostart(self):
        self.install()
        self.assertTrue(f.installed(autostart=self.autostart, data_dir=self.data_dir))
        self.assertIn(f.START, Path(self.autostart).read_bytes())
        self.remove()
        self.assertFalse(Path(self.autostart).exists())
        self.assertFalse(Path(self.data_dir).exists())

    def test_existing_autostart_is_preserved_exactly(self):
        original = b"#!/bin/sh\n# Existing customizations\n/bin/true &\n"
        Path(self.autostart).parent.mkdir(parents=True)
        Path(self.autostart).write_bytes(original)
        os.chmod(self.autostart, 0o750)
        self.install()
        self.install()
        self.assertEqual(Path(self.autostart).read_bytes().count(f.START), 1)
        self.remove()
        self.assertEqual(Path(self.autostart).read_bytes(), original)
        self.assertEqual(os.stat(self.autostart).st_mode & 0o777, 0o750)

    def test_preserves_autostart_without_shebang(self):
        original = b"echo custom startup\n"
        Path(self.autostart).parent.mkdir(parents=True)
        Path(self.autostart).write_bytes(original)
        self.install()
        self.remove()
        self.assertEqual(Path(self.autostart).read_bytes(), original)

    def test_refuses_modified_startup_hook(self):
        Path(self.autostart).parent.mkdir(parents=True)
        Path(self.autostart).write_bytes(f.START + b"echo unknown\n")
        with self.assertRaisesRegex(RuntimeError, "modified"):
            self.install()
        self.assertFalse(Path(self.data_dir).exists())

    def test_refuses_symlinked_autostart(self):
        Path(self.autostart).parent.mkdir(parents=True)
        foreign = Path(self.tmp.name, "foreign.sh")
        foreign.write_text("echo foreign\n")
        os.symlink(foreign, self.autostart)
        with self.assertRaisesRegex(RuntimeError, "non-regular"):
            self.install()
        self.assertEqual(foreign.read_text(), "echo foreign\n")

    def test_refuses_modified_helper_on_uninstall(self):
        self.install()
        Path(self.data_dir, "boot.sh").write_text("#!/bin/sh\necho foreign\n")
        previous = Path(self.autostart).read_bytes()
        with self.assertRaisesRegex(RuntimeError, "modified"):
            self.remove()
        self.assertEqual(Path(self.autostart).read_bytes(), previous)

    def test_boot_script_patches_original_without_overwriting_it(self):
        self.install()
        script = Path(self.data_dir, "boot.sh")
        subprocess.run(["/bin/sh", "-n", str(script)], check=True)
        bindir = Path(self.tmp.name, "bin")
        bindir.mkdir()
        logfile = Path(self.tmp.name, "mount.log")
        mount = bindir / "mount"
        mount.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$TEST_MOUNT_LOG\"\n")
        mount.chmod(0o755)
        env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ["PATH"],
                   TEST_MOUNT_LOG=str(logfile))
        subprocess.run(["/bin/sh", str(script)], check=True, env=env)
        patched = Path(self.data_dir, "patched.frag").read_text()
        self.assertIn("varying highp vec4 m_cord0;", patched)
        self.assertIn("varying mediump vec4 m_cord0;", patched)
        self.assertNotIn("\nvarying vec4 m_cord0;\n", patched)
        self.assertEqual(Path(self.shader).read_bytes(), VANILLA)
        self.assertIn(self.shader, logfile.read_text())

    def test_skips_shader_with_upstream_fix(self):
        Path(self.shader).write_bytes(
            VANILLA.replace(b"varying vec4 m_cord0;", b"varying highp vec4 m_cord0;"))
        self.install()
        subprocess.run(["/bin/sh", str(Path(self.data_dir, "boot.sh"))], check=True)
        self.assertFalse(Path(self.data_dir, "patched.frag").exists())
        self.remove()

    def test_missing_shader_does_not_change_startup(self):
        Path(self.shader).unlink()
        with self.assertRaisesRegex(RuntimeError, "not found"):
            self.install()
        self.assertFalse(Path(self.autostart).exists())

    def test_uninstall_unmounts_only_its_own_shader(self):
        self.install()
        Path(self.data_dir, "patched.frag").write_text("patched")
        with mock.patch.object(f, "active", return_value=True), mock.patch.object(f.subprocess, "run") as run:
            self.remove()
            run.assert_called_once_with(["umount", self.shader], check=True, timeout=10)


if __name__ == "__main__":
    unittest.main()
