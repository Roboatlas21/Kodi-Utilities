# Kodi Utilities — Device Setup (0.1.4)

Manual CoreELEC 22 / Kodi configuration replication through the existing Kodi Utilities add-on repository.

## Settings policy

- The public profile `device-profiles/shared.json` contains **only explicitly approved operations**. The approved shared profile contains Screensaver mode = None, four Kodi cache settings (all filesystems, 512 MB, 4x, 256 KB), and two File Manager sources (Jellyfin and Jurialmunkey). All are applied only after confirmation.
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
- Display resolution, audio passthrough, CEC, HDR-to-SDR and authentication should stay device-local unless you specifically approve each one.
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
