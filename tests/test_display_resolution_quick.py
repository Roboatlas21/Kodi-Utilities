"""Packaged resolution-picker smoke tests, independent of Kodi itself."""
import types
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "script.kodi.utilities.setup/script.kodi.utilities.setup-0.1.17.zip"
MODULE = "script.kodi.utilities.setup/resources/lib/display_resolution.py"
with zipfile.ZipFile(PACKAGE) as archive:
    source = archive.read(MODULE)
display_resolution = types.ModuleType("display_resolution")
exec(compile(source, MODULE, "exec"), display_resolution.__dict__)


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.data = {"id":"videoscreen.resolution", "enabled":True, "value":21,
                     "options":[{"label":"1920x1080p","value":21},
                                {"label":"3840x2160p","value":45},
                                {"label":"1920x1080i","value":46},
                                {"label":"3840x2160p (HiDPI)","value":47}]}
        self.calls = []

    def rpc(self, method, params):
        self.calls.append((method, params))
        if method == "Settings.GetSettings":
            return {"settings":[self.data]}
        if method == "Settings.SetSettingValue":
            self.data["value"] = params["value"]
            return True
        raise AssertionError(method)

    def test_picks_actual_ids(self):
        info = display_resolution.details(self.rpc)
        self.assertEqual(info["current_size"],(1920,1080))
        self.assertEqual(info["choices"][(3840,2160)]["value"],45)
        self.assertTrue(display_resolution.set_size(self.rpc,info,(3840,2160)))
        self.assertEqual(self.data["value"],45)

    def test_current_is_noop(self):
        self.assertFalse(display_resolution.set_size(self.rpc,display_resolution.details(self.rpc),(1920,1080)))
        self.assertEqual(len(self.calls),1)

    def test_unavailable_never_writes(self):
        self.data["options"] = self.data["options"][:1]
        with self.assertRaises(ValueError):
            display_resolution.set_size(self.rpc,display_resolution.details(self.rpc),(3840,2160))
        self.assertEqual(len(self.calls),1)

    def test_disabled_setting(self):
        self.data["enabled"] = False
        with self.assertRaises(RuntimeError):
            display_resolution.details(self.rpc)

    def test_pending_modes(self):
        self.data["optionspending"] = True
        with self.assertRaises(RuntimeError):
            display_resolution.details(self.rpc)

    def test_bad_and_interlaced_options(self):
        self.data["options"].extend([{"label":"3840x2160p","value":True},{"label":"1920x1080p","value":"25"}])
        self.assertEqual(display_resolution.details(self.rpc)["choices"][(3840,2160)]["value"],45)


if __name__ == "__main__":
    unittest.main()
