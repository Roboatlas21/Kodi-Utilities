# Kodi Utilities — Device Setup (0.1.6)

Manual CoreELEC 22 / Kodi configuration replication through the existing Kodi Utilities add-on repository.

## Settings policy

- The public profile `device-profiles/shared.json` contains **only explicitly approved operations**. The approved shared profile contains Screensaver mode = None, four Kodi cache settings (all filesystems, 512 MB, Adaptive, 256 KB), two File Manager sources (Jellyfin and Jurialmunkey), three Jellyfin for Kodi settings (cinema mode on, segment skipping on, recap skip button), two HDMI-CEC Stop Playback actions, and preferred English audio and subtitle languages. All are applied only after confirmation.
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
4. Choose **Quick Settings → Device name** to edit this box’s Kodi network-advertised name, or **Preview GitHub Changes** to inspect shared configuration changes.
5. When you have asked AI to modify the public profile, use **Apply My Setup** after reading the exact changes.

Repository profile URL: https://raw.githubusercontent.com/Roboatlas21/Kodi-Utilities/main/device-profiles/shared.json

## Supported explicit changes

The profile is a JSON object with `schema: 1`, `profile: "shared"`, integer `revision`, and a `changes` array.

Allowed operation objects (examples only; nothing below is active):

- `{"type":"kodi_setting","id":"some.setting.id","value":true}`
- `{"type":"skin_setting","skin":"skin.arctic.fuse.3","id":"SomeSkinSetting","value":"Value"}`
- `{"type":"addon_setting","addon_id":"some.addon","id":"some.setting","value":false}`
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

These are peripheral CEC settings, not normal Kodi JSON-RPC settings. The add-on uses the read-only system CEC definition to check availability, and reads one uniquely identified saved CEC adapter configuration under the current Kodi profile. It skips settings that are absent or not yet saved, including the source-switch setting omitted from stock CoreELEC 22. It never edits CoreELEC's read-only system file or installs the upstream CEC fix. When CoreELEC makes the setting available, the user must manually run **Apply My Setup** again; updates never automatically apply settings.

Applying available CEC changes requires explicit confirmation. Kodi then briefly restarts: an independent systemd timer stops Kodi, verifies that the saved CEC values still match the preview, saves a copy, updates only the approved values, and starts Kodi again. A changed value or ambiguous adapter file fails closed; the helper still attempts to restart Kodi. If no CEC changes are available, no restart is scheduled. A normal Kodi update/install never triggers the helper.

**Restore Previous Settings** can schedule another Kodi restart to restore the prior CEC values, provided the user has not independently changed those settings. The existing preview, missing-addon skipping, and non-CEC operations remain supported. Restart results are recorded under Kodi's `addon_data/script.kodi.utilities.setup` folder as `cec_job.status` and `cec_job.log`; use **Check for Updates** to see whether the CEC job is pending or failed. If `systemd-run` or the adapter's saved preferences are unavailable, no CEC change is applied.

Tested with **40 Kodi-mocked/unit and shell-worker regression tests**. Physical testing of the CEC restart helper on an actual CoreELEC device is still required. The CEC configuration definition itself was previously tested manually on Ugoos AM6B+ CoreELEC 22 with Stop Playback across a Kodi restart.

## Preferred playback languages (shared profile revision 8)

The approved shared profile sets these normal Kodi Player → Language settings:

- **Preferred audio language:** English (Kodi ID `locale.audiolanguage`, string value `English`)
- **Preferred subtitle language:** English (Kodi ID `locale.subtitlelanguage`, string value `English`)

Kodi's stream-language options store the displayed language name as the actual string value. Both are standard `kodi_setting` operations supported by Device Setup v0.1.6; no add-on release or restart helper is needed to apply these two settings. They are previewed, backed up, and restored through the existing normal Kodi settings flow. They influence which available tracks Kodi prefers, but the subtitle-language preference alone does not guarantee subtitles will be enabled for every video. No other Player or accessibility settings are changed.
