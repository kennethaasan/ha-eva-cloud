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
   device's live attribute. That is not automatically documented as editing
   the value saved inside a mood.

In particular, changing a thermostat setpoint or dimmer level while a mood is
active must not be assumed to update the mood permanently. The current public
reference has not confirmed a separate per-device mood-value schema.

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
confirm the mood's name, icon, room, and membership before using it.

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
step, and options). After changing a live value, activate the mood again and
verify whether Eva restores the old or new value. If it restores the old value,
the app is keeping a separate mood snapshot and its exact update payload must
be captured from a disposable/test mood before implementation.

## Safety and privacy

Mood edits can change heating and lighting for every included device. Do not
delete a mood or remove device membership until the updated home response has
been saved elsewhere. Never put real home IDs, device IDs, credentials, or
captured API responses in this repository.
