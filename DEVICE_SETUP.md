# Kodi Utilities — Device Setup (0.1.10)

Manual CoreELEC 21 / 22 / Kodi configuration replication through the existing Kodi Utilities add-on repository.

## Settings policy

- The public profile `device-profiles/shared.json` contains **only explicitly approved operations**. The approved shared profile contains Screensaver mode = None, four Kodi cache settings (all filesystems, 512 MB, Adaptive, 256 KB), two File Manager sources (Jellyfin and Jurialmunkey), three Jellyfin for Kodi settings (cinema mode on, segment skipping on, recap skip button), two HDMI-CEC Stop Playback actions, preferred English audio and subtitle languages, the native Kodi Recently Added items limit of 25, Default select action = Show information, timezone country = Canada / timezone = America/Toronto, temperature unit = Celsius, speed unit = km/h, and installation/selection of Open-Meteo as the weather provider (shared profile revision 14). All are applied only after confirmation.
- Installing the add-on, opening it, and checking updates **never modify any Kodi settings**.
- Only operations intentionally placed in the profile can be applied.
- Apply first shows the exact differences and requires confirmation.
- Settings are backed up locally before writes; Restore Previous Settings can reverse the most recent reversible batch.
- If someone subsequently changes a setting by hand, restore skips that setting.
- Nothing syncs on startup. No arbitrary code execution, copying settings.xml wholesale, or background device settings changes.
- Public profiles reject credential-like setting IDs; do not put secrets, tokens or device identifiers in GitHub.
- `install_addon` may only install add-ons from repositories already known to Kodi; these installs cannot be automatically undone. First-time third-party repository bootstrap is not implemented yet.

## Install

1. Install the existing Kodi Utilities repository on a box.
2. Choose **Kodi Utilities - Device Setup** from that repository.
3. Open it from Kodi's **Program add-ons**.
4. Choose **Quick Settings** to edit this box’s advertised name or Recently Added item limit, or **Preview GitHub Changes** to inspect shared configuration changes.
5. When you have asked AI to modify the public profile, use **Apply My Setup** after reading the exact changes.

Repository profile URL: https://raw.githubusercontent.com/Roboatlas21/Kodi-Utilities/main/device-profiles/shared.json

## Supported explicit changes

The profile is a JSON object with `schema: 1`, `profile: "shared"`, integer `revision`, and a `changes` array.

Allowed operation objects (examples only; nothing below is active):

- `{"type":"kodi_setting","id":"some.setting.id","value":true}`
- `{"type":"skin_setting","skin":"skin.arctic.fuse.3","id":"SomeSkinSetting","value":"Value"}`
- `{"type":"addon_setting","addon_id":"some.addon","id":"some.setting","value":false}`
- `{"type":"advanced_setting","id":"videolibrary.recentlyaddeditems","value":25}` (the only shared advanced-setting operation allowed)
- `{"type":"timezone_setting","id":"timezone","value":{"country":"Canada","timezone":"America/Toronto"}}` (the only shared timezone pair allowed)
- `{"type":"install_addon","id":"some.installed.repository.addon"}`

**Do not add examples to the live profile.** Verify every exact setting ID and value before adding any operation. Other types, file-copying, bulk imports, and unknown fields are rejected.

### Limits

- Kodi 22's JSON-RPC `Settings.GetSkinSettingValue` and `Settings.SetSkinSettingValue` are used for the *active* skin only. Confirm these APIs on the installed CoreELEC 22 build.
- Full Arctic Fuse 3 hubs/widgets may require later targeted support. Copying a full skin settings directory is intentionally unsupported.
- Display resolution, audio passthrough, HDR-to-SDR and authentication remain device-local unless explicitly approved. The only shared HDMI-CEC operations allowed are the two Stop Playback actions listed below.
- Kodi repository add-on updates and GitHub configuration updates are independent.
- Developer tests ran locally with mocked Kodi APIs; **not yet tested on physical CoreELEC 22 hardware**.

## Quick Settings (v0.1.2)

- **Device name**: read the current `services.devicename` value from this Kodi box, then open the Kodi keyboard with that name prefilled. Confirming a new, nonblank name changes only the current Kodi box; Cancel, no-op, or blank input makes no change.
- Quick Settings is fully **local**: it does not fetch or modify the GitHub shared profile, and the shared-profile Restore Previous Settings does not roll back Quick Settings edits.
- This changes Kodi’s network-advertised name, not necessarily the CoreELEC operating-system hostname.
- Other editable shortcuts will be added only when specifically approved.

## File Manager source — Jellyfin Repo (v0.1.3)

The user-approved shared profile includes the following Jellyfin operation:
```json
{"type":"file_source","name":"Jellyfin Repo","path":"https://kodi.jellyfin.org/"}
```

- **Apply My Setup** adds this source to the `<files>` section of Kodi's active/default profile `sources.xml`. Nothing installs automatically; Unknown Sources is not enabled.
- Kodi does not expose a standard JSON-RPC write method for File Manager sources. Kodi may need a **restart after applying** before the newly added source is available in Kodi → Add-ons → Install from zip file.
- Select **Jellyfin Repo → repository.jellyfin.kodi.zip** manually to install Jellyfin's official add-on repository.
- Existing source entries and other sections are preserved. An identical URL is not duplicated, even if installed under another name. A conflicting `Jellyfin Repo` source name with a different URL or malformed XML aborts before any changes.
- The add-on makes a local backup of the existing `sources.xml` before editing. **Restore Previous Settings** can remove its unchanged new entry, but will not delete a source later edited by the user.
- File Manager source entries must use safe public HTTPS URLs without embedded credentials; only explicitly approved entries added to the shared GitHub profile are applied.
- Source-file changes are scoped to the **default/master Kodi profile** on CoreELEC, not alternate multi-user Kodi profiles; multi-user installations should verify their File Manager sources manually.
- This functionality was covered by mocked Kodi/local filesystem tests, **not yet verified on the Ugoos AM6B+ running CoreELEC 22**.

## File Manager source — Jurialmunkey Repo (v0.1.4)

This release adds the explicitly requested File Manager source to the existing shared profile:

```json
{"type":"file_source","name":"Jurialmunkey Repo","path":"https://jurialmunkey.github.io/repository.jurialmunkey/"}
```

- The installer ZIP remains **manual**, as requested: Kodi → Add-ons → Install from zip file → Jurialmunkey Repo → `repository.jurialmunkey-3.4.zip` (or the available version).
- The source is a shortcut only; applying the profile does **not** install Jurialmunkey's repository, Arctic Fuse 3, Arctic Horizon 2, or enable Unknown Sources.
- The Jellyfin source and the five previously approved Kodi settings remain unchanged.
- Kodi may require a restart before File Manager displays the new source. No source is added if the URL already exists.
- Future public HTTPS File Manager sources can be added solely by updating the approved JSON profile; a separate add-on release is not required.

## Optional add-on settings (v0.1.5)

- **Apply My Setup** skips only settings belonging to add-ons that Kodi reports as **not installed**. It still previews and applies available approved Kodi, skin, File Manager source, and other add-on changes, after confirmation. It never installs a missing add-on automatically.
- The preview and completion dialog identify the missing add-on and the number of settings skipped (for example, `plugin.video.jellyfin not installed — 3 settings skipped`). If only missing add-on settings remain, no settings or prior rollback snapshots are changed.
- After installing the add-on, run **Apply My Setup** again to apply the previously skipped settings. The shared GitHub configuration remains unchanged.
- **Restore Previous Settings** skips add-on settings if their add-on has since been uninstalled, restores other eligible settings, and retains pending rollback entries for the missing add-on. It will still refuse to overwrite values independently modified since Apply.
- Errors unrelated to a missing add-on still stop the operation; they are not silently ignored.
- Verified by 20 Kodi-mocked regression tests, including missing add-ons, late uninstall, retry, File Manager source preservation, and restore. Physical CoreELEC 21/22 testing is still pending.

## HDMI-CEC Stop Playback support (v0.1.6)

The approved shared profile (revision 8) requests exactly two HDMI-CEC options:

- **When the TV is switched off** — Stop Playback (setting `standby_pc_on_tv_standby`, value `36044`)
- **Action when switching to another source** — Stop Playback (setting `pause_or_stop_playback_on_deactivate`, value `36044`)

These are peripheral CEC settings, not normal Kodi JSON-RPC settings. The add-on uses the read-only system CEC definition to check availability, and reads one uniquely identified saved CEC adapter configuration under the current Kodi profile. It skips settings that are absent or not yet saved, including installed builds that lack the source-switch setting. It never edits CoreELEC's read-only system file or installs the upstream CEC fix. When CoreELEC makes the setting available, the user must manually run **Apply My Setup** again; updates never automatically apply settings.

Applying available CEC changes requires explicit confirmation. A transient systemd timer stops Kodi, verifies the saved CEC values after Kodi has shut down, saves a copy, updates only the approved values, and requests a **full CoreELEC reboot** (v0.1.7). The helper accepts a value that already equals the requested target, but refuses unexpected values or ambiguous adapter files without committing the proposed edits. Once Kodi has been stopped, the helper requests a full reboot even if it encounters an error, to recover HDMI output; if the reboot request fails, it attempts to start Kodi and reports an error. If no CEC changes are available, no reboot is scheduled. Installing/updating the add-on never triggers the helper.

**Restore Previous Settings** can schedule another full CoreELEC reboot to restore the prior CEC values, provided the user has not independently changed those settings. The existing preview, missing-addon skipping, and non-CEC operations remain supported. Restart results are recorded under Kodi's `addon_data/script.kodi.utilities.setup` folder as `cec_job.status` and `cec_job.log`; use **Check for Updates** to see whether the CEC job is pending or failed. If `systemd-run` or the adapter's saved preferences are unavailable, no CEC change is applied.

Tested with **40 Kodi-mocked/unit and shell-worker regression tests**. Physical testing of the CEC restart helper on an actual CoreELEC device is still required. The CEC configuration definition itself was previously tested manually on Ugoos AM6B+ CoreELEC 22 with Stop Playback across a Kodi restart.

## Preferred playback languages (shared profile revision 8)

The approved shared profile sets these normal Kodi Player → Language settings:

- **Preferred audio language:** English (Kodi ID `locale.audiolanguage`, string value `English`)
- **Preferred subtitle language:** English (Kodi ID `locale.subtitlelanguage`, string value `English`)

Kodi's stream-language options store the displayed language name as the actual string value. Both are standard `kodi_setting` operations supported by Device Setup v0.1.6; no add-on release or restart helper is needed to apply these two settings. They are previewed, backed up, and restored through the existing normal Kodi settings flow. They influence which available tracks Kodi prefers, but the subtitle-language preference alone does not guarantee subtitles will be enabled for every video. No other Player or accessibility settings are changed.

## CoreELEC HDMI-CEC reboot recovery (v0.1.7)

- The v0.1.6 helper could fail if Kodi saved the requested Stop Playback value during shutdown after the setup preview still showed Pause Playback. v0.1.7 treats values already equal to the requested target as satisfied, changes only keys still at their expected old values, and rejects any third/unexpected value before replacing the live CEC XML.
- An explicit confirmation is shown before the one-time CEC helper runs. The helper now requests a **full CoreELEC reboot**, not a Kodi-only restart, whether the CEC operation succeeds or fails after Kodi was stopped. If systemd rejects the reboot, it attempts to restart Kodi and records an error in `cec_job.status`.
- Success remains `rebooting` until the add-on sees a different system boot and verifies that the saved values still match the requested options and that the installed CEC definitions expose those options. An unchanged boot ID or missing value is not reported as success. Use **Check for Updates** after the reboot to see the result.
- A `.changed` record lists the CEC values the helper actually modified. Any value Kodi itself had already saved to the target during shutdown is excluded from the add-on's Restore Previous Settings snapshot.
- CEC preferences and all other existing profile operations are unchanged; the v0.1.7 shared GitHub profile remained revision 8 with 14 entries. That release was an add-on-only update.
- **Tests:** 27 local isolated regression tests using mocked systemd/Kodi CEC files, plus Python compile and ZIP integrity checks. The full-reboot behavior still requires testing on one real CoreELEC 22 AM6B+ before deployment to additional boxes.

## Recently Added items limit (v0.1.8; shared profile revision 10)

**Apply My Setup** sets the native Kodi video-library Recently Added limit to its default **25**, with this explicitly approved shared-profile operation. Shared profile revision 9 requested 50; revision 10 restores 25 at the user's request because this setting does not override Jellyfin for Kodi's separate list limits:

```json
{"type":"advanced_setting","id":"videolibrary.recentlyaddeditems","value":25}
```

Kodi stores this setting at `/storage/.kodi/userdata/advancedsettings.xml` (Kodi path: `special://masterprofile/advancedsettings.xml`), as `<advancedsettings><videolibrary><recentlyaddeditems>25</recentlyaddeditems></videolibrary></advancedsettings>`. This setting also controls native Recently Added episodes and music videos. Arctic Fuse 3 widgets using Kodi's native Recently Added Movies library path should receive up to 25 items. Jellyfin-generated lists and smart playlists with explicit limits use their own limits; this setting does not override them.

Device Setup reads the existing XML safely and changes **only** the approved `videolibrary/recentlyaddeditems` field. It preserves unrelated settings, comments and processing instructions, makes a separate backup before each modification, and writes atomically. It refuses malformed XML, ambiguous duplicate entries, and symbolic links. Restore Previous Settings reverses the effective setting and removes an entry or entire file if Device Setup originally created it, without overwriting unrelated edits. The public profile cannot request arbitrary advanced settings.

**Quick Settings → Recently Added items limit** also offers **25 / 50 / 75 / 100** for the current box only. It is independent of shared-profile restore, just like Device name; the next **Apply My Setup** will bring it back to the shared value of 25.

**A full CoreELEC reboot is needed to activate any new limit.** This update does **not** automatically restart Kodi or reboot the box for the limit. Existing HDMI-CEC changes retain their previously approved full-reboot workflow when a CEC action is also pending. Installing or updating the add-on never applies settings by itself.

**Use Device Setup v0.1.9 or later for shared profile revisions 10 and 11; revision 12 requires v0.1.10.** v0.1.8 supports only the previous shared limit of 50 and rejects the entire profile when it requests 25. v0.1.9 accepts both approved shared values (25 and 50). Other advanced-setting IDs and values remain rejected. No other existing shared setting changes.

Offline tests: 47 tests (20 new XML/profile/apply/restore/Quick Settings cases plus the 27 existing CEC recovery regression tests), Python syntax compilation, shell syntax check, and ZIP archive integrity verification. Physical CoreELEC testing of this new XML workflow is still pending.

## Default select action (shared profile revision 11)

**Apply My Setup** sets **Settings → Media → Videos → Default select action** to **Show information**, using the normal Kodi setting `myvideos.selectaction` with integer value `3` (`ACTION_INFO`). This changes the default action when selecting a video to opening its information dialog. The separate **Default play action** setting is not changed.

This is a normal Kodi setting supported by the existing apply flow. **Use Device Setup v0.1.10 or later for the current shared profile**, because v0.1.8 rejects its Recently Added limit of 25 before applying any settings, including this one. The normal preview, confirmation, backup and restore flow applies; installing or updating the add-on does not apply the setting automatically. This setting takes effect without restarting Kodi.

## Shared-profile validation fix (v0.1.9)

- Fixes the `Only Recently Added limit 50 is approved for shared profiles` error when applying the requested reset to 25 in shared profile revisions 10 and 11.
- Keeps the shared profile at revision 11: Recently Added = 25 and Default select action = Show information. Update the add-on, then run **Apply My Setup** again. Reboot CoreELEC to activate a changed Recently Added limit; the select-action setting takes effect immediately.
- Corrects Quick Settings text to refer to the shared profile's value instead of promising a reset to 50.
- The CEC helper, XML backup/restore behavior, manual confirmation and no-auto-apply policy are unchanged.
- Verified against the actual v0.1.9 ZIP and published revision 11: profile validation, applying and restoring both requested changes with mocked Kodi APIs, cancellation, rollback after a simulated Kodi rejection, unrelated XML preservation, and package/index integrity. Physical CoreELEC testing remains pending.


## CoreELEC 21 / 22 and timezone setup (v0.1.10; shared profile revision 12)

**Update Device Setup to v0.1.10 before applying revision 12.** Older versions do not understand the new paired timezone operation and reject the profile before making changes. The profile retains Recently Added = 25 and Default select action = Show information, and adds the requested **Canada / America/Toronto** pair. The region format (for example USA 12h) is independent and is not part of this operation.

Device Setup reads `/etc/os-release` to identify CoreELEC and its version and displays that version with Kodi's build in the preview. It also queries Kodi's available settings: missing standard Kodi settings are explicitly skipped, while ordinary read/write errors still stop the operation. This avoids assuming that every build exposes the same options.

- On CoreELEC 21, the add-on uses Kodi's `locale.timezonecountry` and `locale.timezone` settings. Country is applied first, then timezone, and both are verified. This order is also used when restoring because changing country can automatically choose a different city.
- On CoreELEC 22, the same Kodi settings are used if the installed build still exposes both. Otherwise, the add-on verifies CoreELEC's timezone data and `tz-data.service`, updates only `/storage/.cache/timezone`, restarts that service, verifies `/var/run/localtime`, and updates the running process timezone. This follows the mechanism in the CoreELEC settings add-on. The country is derived from the timezone database, so America/Toronto displays as Canada.
- Unknown CoreELEC versions, other operating systems, or missing timezone capabilities are shown as skipped. CoreELEC 21 never falls back to the CoreELEC 22 file method. A partially exposed Kodi timezone pair is also skipped.
- Preview and Cancel make no changes. Apply saves the original country/timezone pair and, for the CoreELEC service method, the original configuration contents or absence. Failed partial timezone changes attempt an immediate rollback. Normal batch rollback and Restore Previous Settings also support the pair. Restore skips a manually changed pair or a changed timezone backend after a firmware upgrade.
- No Kodi restart or box reboot is scheduled for timezone changes. Existing CEC changes retain their separately confirmed reboot flow. Reopen the CoreELEC settings screen if it was already open when applying a timezone change.

Implementation references: [Kodi 21 timezone handling](https://github.com/xbmc/xbmc/blob/Omega/xbmc/platform/posix/PosixTimezone.cpp), [CoreELEC settings timezone handling](https://github.com/CoreELEC/service.coreelec.settings/blob/coreelec-22/src/resources/lib/modules/system.py), and [CoreELEC tz-data service](https://github.com/CoreELEC/CoreELEC/blob/coreelec-22/packages/sysutils/tz/system.d/tz-data.service).

Validation: 25 passing regression tests against the actual v0.1.10 ZIP and shared profile, with mocked Kodi/systemd services, plus archive/index/checksum and Python/shell syntax checks. Run `python tests/test_device_setup_timezone.py` from the repository checkout. Physical CoreELEC 21 and 22 testing remains pending.


## Celsius and kilometres per hour (shared profile revision 13)

**Apply My Setup** now sets **Settings → Interface → Regional → Temperature unit** to **°C** and **Speed unit** to **km/h**. These are explicit unit choices, independent of the region's defaults:

- `locale.temperatureunit`: string `c` (Celsius).
- `locale.speedunit`: string `kmh` (kilometres per hour).

Both IDs and values were verified in Kodi 21 (Omega) and CoreELEC's Kodi 22 source. These ordinary Kodi settings are already supported by **Device Setup v0.1.10**; no new add-on release is required. Open the add-on and choose **Apply My Setup** to fetch revision 13. They take effect immediately, with no reboot required for these two changes. The existing preview, confirmation, backup, and restore flow applies. Region format, dates, clock format, and all previous shared-profile entries are unchanged.

The existing 25 packaged-add-on regression checks pass against revision 13. Physical testing of these unit settings remains pending.


## Open-Meteo weather provider (shared profile revision 14)

**Device Setup v0.1.10 already supports this; no add-on update is required.** Run **Apply My Setup** to fetch the new profile. It installs `weather.openmeteo` through Kodi's normal add-on installer if missing, waits for Kodi to report it installed, and then sets `weather.addon` to `weather.openmeteo`. Open-Meteo is available in the official Kodi repository; no third-party repository URL or API key is needed. Kodi may display its normal installation confirmation. The weather-provider setting was verified in Kodi 21 and CoreELEC's Kodi 22 source.

The two operations are deliberately ordered: installation must finish before selecting the provider. If installation is cancelled, unavailable, or not confirmed within the existing wait, Apply reports a failure and does not attempt provider selection. Previously applied reversible settings are rolled back. Installing the add-on is not automatically undone by rollback or **Restore Previous Settings**; restoring can return the previous weather-provider choice while leaving Open-Meteo installed.

Locations remain local to each box. Open-Meteo supports initial location detection, and you can correct its location in **Settings → Services → Weather → Settings** if needed. This profile does not write a shared city or coordinates. Open-Meteo defaults to using Kodi's temperature and speed units, so fresh installs follow the shared Celsius/km/h choices. Existing custom Open-Meteo unit overrides are preserved.

There is no reboot requirement for installing/selecting the weather provider. All prior profile settings remain unchanged. Validation: all 28 packaged-add-on regression checks pass, including installation before provider selection, cancelled/failed installation, reuse of an installed provider, and restoration without uninstalling it, with mocked Kodi APIs. Physical box testing is still pending.
