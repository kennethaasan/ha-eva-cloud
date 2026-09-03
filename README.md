# Eva Cloud for Home Assistant

An experimental Home Assistant custom integration that lets an existing Eva
Smart Home account and Eva Hub coexist with Home Assistant. Devices remain
paired to Eva; Home Assistant reads and controls them through the Eva cloud.

The integration provides best-effort mappings for:

- sensors and binary sensors;
- lights and dimmers;
- switches;
- climate devices, including supported CTM Lyng thermostats; and
- existing Eva moods as Home Assistant scenes.

## Language support

The config flow and integration-owned entity names are available in English and
Norwegian Bokmål. Names supplied by Eva itself—such as rooms, devices, moods,
and automations—remain exactly as they are configured in the Eva app.

## Status and compatibility

This is community software, is not affiliated with Onics, Eva Smart Home, or
CTM Lyng, and uses the API used by the Eva mobile app. The API is undocumented
and may change without notice.

It has been tested with:

- Eva Hub / Onics Smart Home Gateway, software 5.0.16
- CTM Lyng mTouch dimmers and thermostats
- existing Eva moods
- Home Assistant OS

Device capabilities vary. Unsupported Eva devices are ignored rather than
guessed.

## API reference

The current app API route inventory is documented in
[`docs/eva-api.openapi.yaml`](docs/eva-api.openapi.yaml). It is an observed,
community-maintained reference for Eva Android app 2.4.5 (version code 499),
not an official API contract. Payload schemas are deliberately partial and
must be rechecked when Eva releases a new app or changes its API. The practical
sequence for editing and activating a mood is in
[`docs/eva-moods.md`](docs/eva-moods.md).

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Add `https://github.com/kennethaasan/ha-eva-cloud` as a custom integration
   repository.
3. Install **Eva** and restart Home Assistant.
4. Open **Settings → Devices & services → Add integration**, search for **Eva**,
   and sign in with your own Eva account.

### Manual installation

Copy `custom_components/eva_cloud` into Home Assistant's `custom_components`
directory, restart Home Assistant, and add the integration from the UI.

## Safety and coexistence

The Eva app, Eva automations, physical controls, and Home Assistant can all
change the same devices. Avoid competing automations and begin with conservative
setpoints. Heating and electrical equipment must retain its physical safety
controls.

The integration writes only known, mapped attributes and existing mood
activation routes. It does not pair or remove Zigbee devices, change hub
firmware, create Eva automations, or manage alarm access.

## Privacy

The integration has no analytics. Home Assistant stores the Eva username and
password in its private config-entry storage and sends them only to Eva's cloud
services for authentication. Use a dedicated Eva household member account when
possible.

Never include credentials, home IDs, device IDs, lock data, or unredacted Home
Assistant diagnostics in a GitHub issue.

## Support

Use GitHub issues for reproducible bugs and feature requests. Include the Eva
Hub software version and device model, but redact all household identifiers.

## License

Apache-2.0. See [LICENSE](LICENSE).
