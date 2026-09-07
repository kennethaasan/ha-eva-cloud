# Editing Eva moods

This guide documents the observed Eva Android API flow. Eva does not publish
this API as a stable consumer contract, so use a test mood first and verify
every asynchronous write by reading the home again.

## What the operations mean

Eva exposes three different concepts:

1. `PATCH /homes/{homeId}/moods/{moodId}` edits the saved mood definition and
   its membership.
2. `POST /homes/{homeId}/moods/{moodId}/activate` applies the saved mood to its
   devices.
3. `POST /homes/{homeId}/devices/{deviceId}/{attribute}/{value}` changes a
   device's live attribute. The observed way to persist the current live
   values to a mood is to set the included devices first, then PATCH the
   complete mood object before activating it.

The home response exposes live values in `rooms[].devices[].attributes[]`.
Mood objects themselves expose membership and active state, but no separate
per-device value map. Eva does not expose a useful GET detail route for an
individual mood in the tested app/API combination; a GET to the mood resource
returned `405 Method Not Allowed`, so the home response is the read source.

The observed persistence behavior was verified with a CTM Lyng dimmer: setting
its live `on` value and then PATCHing the complete mood caused a later mood
activation to restore the new `on` value and its current `dimLevel`. Treat this
as compatibility behavior, not a guaranteed public contract.

## Safe edit sequence

Use the same JSON headers as other home-scoped Eva calls, including
`X-Partition-Key` set to the first character of the home ID. Keep IDs and
credentials in environment variables or a secret store.

```bash
export EVA_HOME_ID="<home-id>"
export EVA_MOOD_ID="<mood-id>"
export EVA_BASIC_AUTH="<base64-user-and-password>"
export EVA_PARTITION_KEY="${EVA_HOME_ID:0:1}"

# 1. Read the current home and locate EVA_MOOD_ID.
curl --fail-with-body \
  -H "Authorization: Basic ${EVA_BASIC_AUTH}" \
  -H "Accept: application/json" \
  -H "X-Client-ID: Android-2.4.5_499-evaSmartProd" \
  -H "X-Client-Brand: eva" \
  -H "X-Client-Language: nb" \
  -H "X-Schema-Version: 7" \
  -H "X-Partition-Key: ${EVA_PARTITION_KEY}" \
  "https://home.api.evasmart.no/homes/${EVA_HOME_ID}"
```

Before editing the mood, set the desired live values for every included device.
For example, a dimmer exposes `on` and `dimLevel` in its live attribute list:

```bash
# Use the attribute names and values returned by the home response.
curl --fail-with-body -X POST \
  -H "Authorization: Basic ${EVA_BASIC_AUTH}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: Android-2.4.5_499-evaSmartProd" \
  -H "X-Client-Brand: eva" \
  -H "X-Client-Language: nb" \
  -H "X-Schema-Version: 7" \
  -H "X-Partition-Key: ${EVA_PARTITION_KEY}" \
  "https://home.api.evasmart.no/homes/${EVA_HOME_ID}/devices/<dimmer-id>/on/true"

curl --fail-with-body -X POST \
  -H "Authorization: Basic ${EVA_BASIC_AUTH}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: Android-2.4.5_499-evaSmartProd" \
  -H "X-Client-Brand: eva" \
  -H "X-Client-Language: nb" \
  -H "X-Schema-Version: 7" \
  -H "X-Partition-Key: ${EVA_PARTITION_KEY}" \
  "https://home.api.evasmart.no/homes/${EVA_HOME_ID}/devices/<dimmer-id>/dimLevel/70"
```

Set all included devices deliberately before the mood PATCH. A complete mood
update may snapshot the current live values of every device in the mood, so a
device accidentally left in the wrong state can be saved as well.

Create a JSON body by copying the current mood and changing only what is
needed. The observed fields are `name`, `icon`, `roomId`, `deviceIds`, and
`groupIds`; preserve fields that the current response contains.

```json
{
  "name": "Hjemme",
  "icon": "home",
  "roomId": "<room-id>",
  "deviceIds": ["<device-id>"],
  "groupIds": []
}
```

Send the edited object:

```bash
curl --fail-with-body -X PATCH \
  -H "Authorization: Basic ${EVA_BASIC_AUTH}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: Android-2.4.5_499-evaSmartProd" \
  -H "X-Client-Brand: eva" \
  -H "X-Client-Language: nb" \
  -H "X-Schema-Version: 7" \
  -H "X-Partition-Key: ${EVA_PARTITION_KEY}" \
  --data @mood.json \
  "https://home.api.evasmart.no/homes/${EVA_HOME_ID}/moods/${EVA_MOOD_ID}"
```

Eva commonly answers with HTTP `202` and an `actionId`. That means the request
was accepted, not necessarily that it has finished. Repeat the home GET and
confirm the mood's name, icon, room, membership, and live device attributes
before using it.

## Activate the saved mood

Editing does not activate the mood. Once the GET response shows the intended
definition, activate it explicitly:

```bash
curl --fail-with-body -X POST \
  -H "Authorization: Basic ${EVA_BASIC_AUTH}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: Android-2.4.5_499-evaSmartProd" \
  -H "X-Client-Brand: eva" \
  -H "X-Client-Language: nb" \
  -H "X-Schema-Version: 7" \
  -H "X-Partition-Key: ${EVA_PARTITION_KEY}" \
  "https://home.api.evasmart.no/homes/${EVA_HOME_ID}/moods/${EVA_MOOD_ID}/activate"
```

The Home Assistant integration exposes existing Eva moods as scenes, so the
normal Home Assistant action is to call the scene. It intentionally does not
yet edit moods or create new Eva automations.

## Changing a mood's device values

The currently confirmed generic device-control route is separate from the
mood-edit route. It encodes the attribute and value in the URL, for example:

```text
POST /homes/{homeId}/devices/{deviceId}/{attribute}/{value}
```

The live attribute name is device-specific; discover it from the home response
and use the device's reported attribute metadata (`name`, `value`, limits,
step, and options). To save those values to a mood, set every included device,
PATCH the complete mood object, wait for completion, and then activate the
mood. Verify the live attributes after activation. If a device does not retain
the new value, treat that device/app combination as unsupported until its
write payload is captured from a disposable/test mood.

## Safety and privacy

Mood edits can change heating and lighting for every included device. Do not
delete a mood or remove device membership until the updated home response has
been saved elsewhere. Never put real home IDs, device IDs, credentials, or
captured API responses in this repository.
