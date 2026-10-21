"""Exercise the distributed ZIP, not a separate development source tree."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'script.kodi.utilities.setup/script.kodi.utilities.setup-0.1.10.zip'
SHARED = json.loads((ROOT / 'device-profiles/shared.json').read_text())
TARGET = {'country': 'Canada', 'timezone': 'America/Toronto'}
ORIGINAL = {'country': 'United States', 'timezone': 'America/New_York'}
OP = next(item for item in SHARED['changes'] if item['type'] == 'timezone_setting')
UNPACK = tempfile.TemporaryDirectory()
with zipfile.ZipFile(PACKAGE) as archive:
    archive.extractall(UNPACK.name)
SOURCE = Path(UNPACK.name) / 'script.kodi.utilities.setup'
sys.path.insert(0, str(SOURCE))


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.data.mkdir()
        self.dialog = Mock()
        self.dialog.yesno.return_value = True
        self.dialog.select.return_value = -1
        self.installed = set()
        self.install_commands = []
        self.fail_install = False
        xbmc = types.SimpleNamespace(getInfoLabel=lambda key: '21.3',
            getCondVisibility=lambda key: key == 'System.HasAddon(weather.openmeteo)' and 'weather.openmeteo' in self.installed,
            executebuiltin=self.install, Monitor=lambda: types.SimpleNamespace(waitForAbort=lambda seconds: False),
            LOGERROR=4, LOGWARNING=3, log=Mock())
        modules = {'xbmc': xbmc, 'xbmcgui': types.SimpleNamespace(Dialog=lambda: self.dialog),
                   'xbmcaddon': types.SimpleNamespace(Addon=Mock()),
                   'xbmcvfs': types.SimpleNamespace(translatePath=lambda path: str(self.data))}
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, modules).start()
        spec = importlib.util.spec_from_file_location('device_setup_under_test', SOURCE / 'default.py')
        self.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.app)
        self.tz = self.app.timezone_settings
        for key, value in {'OS_RELEASE': self.root/'os-release',
                           'TIMEZONE_FILE': self.root/'timezone',
                           'ZONEINFO': self.root/'zoneinfo',
                           'LOCALTIME': self.root/'localtime',
                           'UNIT': self.root/'tz-data.service'}.items():
            patch.object(self.tz, key, str(value)).start()
        Path(self.tz.UNIT).touch()
        zones = Path(self.tz.ZONEINFO)
        (zones/'America').mkdir(parents=True)
        (zones/'Europe').mkdir()
        for zone in ('UTC', 'America/New_York', 'America/Toronto', 'America/Atikokan', 'Europe/London'):
            (zones/zone).touch()
        (zones/'iso3166.tab').write_text('CA\tCanada\nUS\tUnited States\nGB\tUnited Kingdom\n')
        (zones/'zone.tab').write_text('CA\tcoords\tAmerica/Toronto\nUS\tcoords\tAmerica/New_York\nGB\tcoords\tEurope/London\n')
        Path(self.tz.TIMEZONE_FILE).write_text('TIMEZONE=America/New_York\n')
        self.version('21.3')
        self.native = False
        self.missing = set()
        self.values = {item['id']: 'old' for item in SHARED['changes'] if item['type']=='kodi_setting'}
        self.values['weather.addon'] = ''
        self.values.update({self.tz.COUNTRY_ID: ORIGINAL['country'], self.tz.ZONE_ID: ORIGINAL['timezone']})
        self.writes = []
        self.service_calls = []
        self.fail_setting = None
        self.fail_service = False
        self.fail_rpc = False
        self.app.rpc = self.rpc
        self.app.DATA_DIR = str(self.data)
        self.app.STATE_FILE = str(self.data/'state.json')
        self.app.ROLLBACK_FILE = str(self.data/'rollback.json')
        self.app.SOURCES_FILE = str(self.data/'sources.xml')
        self.app.ADVANCED_FILE = str(self.data/'advancedsettings.xml')
        self.app.CEC_RESTORE_PENDING = str(self.data/'cec_restore_pending.json')
        self.profile = copy.deepcopy(SHARED)
        self.app.fetch_profile = lambda: (self.profile, 'test-signature')
        patch.object(self.app.cec_settings, 'unavailable_reason', return_value='No test CEC device').start()
        patch.object(self.tz.shutil, 'which', return_value='/bin/systemctl').start()
        patch.object(self.tz.subprocess, 'run', side_effect=self.systemctl).start()
        patch.object(self.tz.time, 'tzset').start()
        patch.dict(os.environ).start()

    def version(self, version, distro='coreelec'):
        Path(self.tz.OS_RELEASE).write_text('ID="{}"\nVERSION_ID="{}"\nVERSION="{}"\n'.format(distro,version,version))

    def install(self, command):
        self.assertEqual(command, 'InstallAddon(weather.openmeteo)')
        self.install_commands.append(command)
        if not self.fail_install:
            self.installed.add('weather.openmeteo')

    def rpc(self, method, params):
        if self.fail_rpc:
            raise RuntimeError('RPC transport failure')
        if method == 'Settings.GetSettings':
            excluded = self.missing | ({self.tz.COUNTRY_ID, self.tz.ZONE_ID} if self.native else set())
            return {'settings': [{'id': key} for key in self.values if key not in excluded]}
        key = params['setting']
        if key in self.missing or (self.native and key in (self.tz.COUNTRY_ID,self.tz.ZONE_ID)):
            raise AssertionError('Unsupported setting was accessed')
        if method == 'Settings.GetSettingValue':
            return {'value': self.values[key]}
        if method == 'Settings.SetSettingValue':
            value = params['value']
            if key == 'weather.addon' and value == 'weather.openmeteo':
                self.assertIn(value, self.installed, 'Provider selected before installation finished')
            self.writes.append((key,value))
            if self.fail_setting == (key,value):
                self.fail_setting = None
                return False
            self.values[key] = value
            if key == self.tz.COUNTRY_ID:
                self.values[self.tz.ZONE_ID] = 'America/Atikokan' if value=='Canada' else 'America/New_York'
            return True
        raise AssertionError(method)

    def systemctl(self, args, **kwargs):
        self.assertEqual(args, ['systemctl','restart','tz-data.service'])
        self.service_calls.append(args)
        if self.fail_service:
            self.fail_service = False
            raise subprocess.CalledProcessError(1, args)
        zone = self.tz._configured_zone(self.tz._content())
        link = Path(self.tz.LOCALTIME)
        if link.is_symlink():
            link.unlink()
        link.symlink_to(Path(self.tz.ZONEINFO)/zone)
        return subprocess.CompletedProcess(args,0)

    def only_timezone(self):
        self.profile['changes'] = [copy.deepcopy(OP)]

    def native22(self):
        self.version('22.0-Piers_devel')
        self.native = True

    def pair(self):
        return self.tz.read_state(self.rpc)['value']

    def test_package_profile_and_index(self):
        from resources.lib.profile import parse
        parsed = parse((ROOT/'device-profiles/shared.json').read_bytes())
        self.assertEqual(parsed['revision'],14)
        self.assertEqual(len(parsed['changes']),21)
        self.assertEqual(next(item['value'] for item in parsed['changes'] if item.get('id') == 'videolibrary.recentlyaddeditems'),25)
        self.assertEqual(next(item['value'] for item in parsed['changes'] if item.get('id') == 'myvideos.selectaction'),3)
        index = (ROOT/'addons.xml').read_bytes()
        self.assertEqual(hashlib.md5(index).hexdigest(),(ROOT/'addons.xml.md5').read_text())
        self.assertEqual(ET.fromstring(index).find("addon[@id='script.kodi.utilities.setup']").get('version'),'0.1.10')
        with zipfile.ZipFile(PACKAGE) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()),9)
            self.assertEqual(ET.fromstring(archive.read('script.kodi.utilities.setup/addon.xml')).get('version'),'0.1.10')
            for name in archive.namelist():
                if name.endswith('.py'):
                    compile(archive.read(name),name,'exec')

    def test_full_profile_apply_and_restore_21(self):
        before = dict(self.values)
        self.app.apply()
        self.assertEqual(self.pair(), TARGET)
        self.assertEqual(self.values['myvideos.selectaction'],3)
        self.assertEqual(self.app.advanced_settings.get_limit_state(self.app.ADVANCED_FILE)['value'],25)
        self.assertTrue(Path(self.app.ROLLBACK_FILE).exists())
        self.assertFalse(self.service_calls)
        self.app.restore()
        self.assertEqual(self.values,before)
        self.assertFalse(Path(self.app.ROLLBACK_FILE).exists())

    def test_full_profile_apply_and_restore_22(self):
        self.native22()
        original_file = Path(self.tz.TIMEZONE_FILE).read_bytes()
        self.app.apply()
        self.assertEqual(self.pair(),TARGET)
        self.assertEqual(os.environ['TZ'],'America/Toronto')
        self.app.restore()
        self.assertEqual(Path(self.tz.TIMEZONE_FILE).read_bytes(),original_file)
        self.assertEqual(self.pair(),ORIGINAL)
        self.assertEqual(len(self.service_calls),2)

    def test_preview_is_read_only_and_shows_version(self):
        self.native22()
        before = Path(self.tz.TIMEZONE_FILE).read_bytes()
        self.app.preview()
        rendered = self.dialog.textviewer.call_args.args[1]
        self.assertIn('CoreELEC 22.0-Piers_devel',rendered)
        self.assertIn('Canada / America/Toronto',rendered)
        self.assertIn('CoreELEC timezone service',rendered)
        self.assertEqual(Path(self.tz.TIMEZONE_FILE).read_bytes(),before)
        self.assertFalse(self.writes or self.service_calls)
        self.assertFalse(Path(self.app.ROLLBACK_FILE).exists())

    def test_cancel_changes_nothing(self):
        self.dialog.yesno.return_value = False
        self.app.apply()
        self.assertFalse(self.writes or self.service_calls)
        self.assertFalse(self.install_commands)
        self.assertFalse(Path(self.app.ROLLBACK_FILE).exists())

    def test_already_set_is_noop(self):
        self.only_timezone()
        self.values.update({self.tz.COUNTRY_ID:TARGET['country'],self.tz.ZONE_ID:TARGET['timezone']})
        self.app.apply()
        self.assertFalse(self.writes or self.service_calls)
        self.dialog.yesno.assert_not_called()

    def test_missing_kodi_setting_is_skipped(self):
        self.missing.add('filecache.chunksize')
        self.app.apply()
        self.assertEqual(self.pair(),TARGET)
        self.assertNotIn('filecache.chunksize',[key for key,value in self.writes])
        self.assertIn('filecache.chunksize',self.dialog.textviewer.call_args.args[1])

    def test_21_never_falls_back_to_native(self):
        self.only_timezone()
        self.native=True
        self.app.apply()
        self.assertFalse(self.writes or self.service_calls)
        self.assertIn('does not expose both',self.dialog.ok.call_args.args[1])

    def test_22_uses_kodi_when_available(self):
        self.version('22.0')
        self.only_timezone()
        self.app.apply()
        self.assertEqual(self.pair(),TARGET)
        self.assertFalse(self.service_calls)

    def test_partial_kodi_pair_does_not_fall_back(self):
        self.version('22.0')
        self.missing.add(self.tz.ZONE_ID)
        self.only_timezone()
        self.app.apply()
        self.assertFalse(self.writes or self.service_calls)

    def test_unknown_versions_and_other_os_are_skipped(self):
        for version, distro in [('23.0','coreelec'),('20.5','coreelec'),('unknown','coreelec'),('22.0','libreelec')]:
            with self.subTest(version=version,distro=distro):
                self.version(version,distro)
                self.assertIsNotNone(self.tz.unavailable_reason(self.rpc))
        self.assertFalse(self.writes or self.service_calls)

    def test_version_suffixes_are_recognized(self):
        for version, major in [('21.3-Omega',21),('22.0-Piers_devel',22),('21',21)]:
            self.version(version)
            self.assertEqual(self.tz.device_info()['major'],major)

    def test_rpc_error_is_not_silently_skipped(self):
        self.fail_rpc=True
        with self.assertRaisesRegex(RuntimeError,'RPC transport failure'):
            self.app.apply()
        self.assertFalse(self.writes or self.service_calls)

    def test_missing_native_service_is_skipped(self):
        self.native22()
        Path(self.tz.UNIT).unlink()
        self.only_timezone()
        self.app.apply()
        self.assertFalse(self.service_calls)
        self.assertIn('tz-data service is unavailable',self.dialog.ok.call_args.args[1])

    def test_country_change_cannot_leave_first_city(self):
        self.only_timezone()
        self.values[self.tz.ZONE_ID]='America/Toronto'
        self.app.apply()
        self.assertEqual(self.pair(),TARGET)
        self.assertEqual(self.writes[-1],(self.tz.ZONE_ID,'America/Toronto'))

    def test_failed_kodi_timezone_rolls_back_entire_batch(self):
        before=dict(self.values)
        self.fail_setting=(self.tz.ZONE_ID,'America/Toronto')
        with self.assertRaisesRegex(RuntimeError,'Apply failed'):
            self.app.apply()
        self.assertEqual(self.values,before)
        self.assertFalse(Path(self.app.ROLLBACK_FILE).exists())
        for item in SHARED['changes']:
            if item['type'] == 'file_source':
                self.assertFalse(self.app.is_source_present(self.app.SOURCES_FILE,item['name'],item['path']))

    def test_failed_service_rolls_back_original_contents(self):
        self.native22()
        self.only_timezone()
        before=Path(self.tz.TIMEZONE_FILE).read_bytes()
        self.fail_service=True
        with self.assertRaisesRegex(RuntimeError,'Apply failed'):
            self.app.apply()
        self.assertEqual(Path(self.tz.TIMEZONE_FILE).read_bytes(),before)
        self.assertEqual(self.pair(),ORIGINAL)
        self.assertFalse(Path(self.app.ROLLBACK_FILE).exists())

    def test_absent_native_file_is_absent_after_restore(self):
        self.native22()
        self.only_timezone()
        Path(self.tz.TIMEZONE_FILE).unlink()
        self.app.apply()
        self.assertEqual(self.pair(),TARGET)
        self.app.restore()
        self.assertFalse(Path(self.tz.TIMEZONE_FILE).exists())
        self.assertEqual(self.pair(),{'country':'','timezone':'UTC'})

    def test_manual_timezone_edit_is_not_overwritten_by_restore(self):
        self.only_timezone()
        self.app.apply()
        self.values[self.tz.ZONE_ID]='America/Atikokan'
        before=list(self.writes)
        self.app.restore()
        self.assertEqual(self.writes,before)
        self.assertTrue(Path(self.app.ROLLBACK_FILE).exists())

    def test_changed_backend_is_not_restored(self):
        self.only_timezone()
        self.app.apply()
        self.native22()
        Path(self.tz.TIMEZONE_FILE).write_text('TIMEZONE=America/Toronto')
        self.app.restore()
        self.assertFalse(self.service_calls)
        self.assertTrue(Path(self.app.ROLLBACK_FILE).exists())
        self.assertIn('method changed',self.dialog.textviewer.call_args.args[1])

    def test_timezone_changed_during_confirmation_aborts(self):
        self.only_timezone()
        def confirm(*args,**kwargs):
            self.values[self.tz.ZONE_ID]='America/Atikokan'
            return True
        self.dialog.yesno.side_effect=confirm
        with self.assertRaisesRegex(RuntimeError,'changed since preview'):
            self.app.apply()
        self.assertFalse(self.writes)

    def test_invalid_native_configuration_is_not_overwritten(self):
        self.native22()
        self.only_timezone()
        for content in ('TIMEZONE=America/New_York\nOTHER=value\n','TIMEZONE=../../etc/passwd','bad'):
            with self.subTest(content=content):
                Path(self.tz.TIMEZONE_FILE).write_text(content)
                with self.assertRaises(RuntimeError):
                    self.app.apply()
                self.assertEqual(Path(self.tz.TIMEZONE_FILE).read_text(),content)
        self.assertFalse(self.writes or self.service_calls)

    def test_native_symlink_is_rejected(self):
        self.native22()
        self.only_timezone()
        destination=self.root/'other-file'
        destination.write_text('TIMEZONE=America/New_York')
        Path(self.tz.TIMEZONE_FILE).unlink()
        Path(self.tz.TIMEZONE_FILE).symlink_to(destination)
        with self.assertRaisesRegex(RuntimeError,'symbolic-link'):
            self.app.apply()
        self.assertEqual(destination.read_text(),'TIMEZONE=America/New_York')
        self.assertFalse(self.writes or self.service_calls)

    def test_unapproved_timezone_profiles_are_rejected(self):
        from resources.lib.profile import validate, ProfileError
        for value in ({'country':'Canada','timezone':'America/Vancouver'},
                      {'country':'Canada','timezone':'America/Toronto','extra':True},
                      'America/Toronto',True,None):
            invalid=copy.deepcopy(SHARED)
            next(item for item in invalid['changes'] if item['type'] == 'timezone_setting')['value']=value
            with self.assertRaises(ProfileError):
                validate(invalid)
        for limit in (25,50):
            valid=copy.deepcopy(SHARED)
            next(item for item in valid['changes'] if item['type'] == 'advanced_setting')['value']=limit
            validate(valid)

    def test_existing_recent_limit_and_unrelated_xml_survive(self):
        original = '<advancedsettings><!-- keep --><videolibrary><recentlyaddeditems>50</recentlyaddeditems></videolibrary><audio><foo>bar</foo></audio></advancedsettings>'
        Path(self.app.ADVANCED_FILE).write_text(original)
        self.app.apply()
        self.assertEqual(self.app.advanced_settings.get_limit_state(self.app.ADVANCED_FILE)['value'],25)
        self.assertIn('<!-- keep -->',Path(self.app.ADVANCED_FILE).read_text())
        self.app.restore()
        self.assertEqual(self.app.advanced_settings.get_limit_state(self.app.ADVANCED_FILE)['value'],50)
        self.assertEqual(ET.parse(self.app.ADVANCED_FILE).findtext('audio/foo'),'bar')

    def test_weather_install_select_and_restore(self):
        self.profile['changes'] = copy.deepcopy(SHARED['changes'][-2:])
        self.app.apply()
        self.assertEqual(self.install_commands, ['InstallAddon(weather.openmeteo)'])
        self.assertEqual(self.values['weather.addon'], 'weather.openmeteo')
        self.app.restore()
        self.assertEqual(self.values['weather.addon'], '')
        self.assertIn('weather.openmeteo', self.installed)
        self.assertEqual(len(self.install_commands), 1)

    def test_weather_install_failure_rolls_back_batch_without_selecting(self):
        before = dict(self.values)
        self.fail_install = True
        with self.assertRaisesRegex(RuntimeError, 'Installation not verified'):
            self.app.apply()
        self.assertEqual(self.values, before)
        self.assertNotIn(('weather.addon', 'weather.openmeteo'), self.writes)

    def test_weather_reuses_installed_addon(self):
        self.profile['changes'] = copy.deepcopy(SHARED['changes'][-2:])
        self.installed.add('weather.openmeteo')
        self.app.apply()
        self.assertFalse(self.install_commands)
        self.assertEqual(self.values['weather.addon'], 'weather.openmeteo')


if __name__ == '__main__':
    unittest.main(verbosity=2)
