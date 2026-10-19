# Kodi Utilities — Device Setup (0.1.0)

Manual CoreELEC 22 / Kodi configuration replication through the existing Kodi Utilities add-on repository.

## Settings policy

- The public profile `device-profiles/shared.json` **starts empty**, with `"changes": []`.
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
4. Choose **Preview GitHub Changes**. The initial shared profile shows **No changes**.
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
