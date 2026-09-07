# Changelog

## 0.3.2

- Add an observed OpenAPI reference for the current Eva Android API routes,
  headers, and partial payload schemas.
- Document that live device attributes such as `on` and `dimLevel` are exposed
  in the home response and can be persisted to a mood by the observed
  live-attribute, complete-mood-PATCH, and activation sequence.
- Clarify that mood objects expose membership and active state, but not a
  separate per-device value payload.

## 0.3.1

- Fix translated home-level sensor and automation names being hidden by an
  explicitly empty entity name.

## 0.3.0

- Add English and Norwegian Bokmål translations for every integration-owned
  config-flow and entity name.
- Preserve names supplied by Eva while localizing the surrounding Home
  Assistant labels.

## 0.2.1

- Improve compatibility with live Eva hubs and CTM Lyng devices.
## 0.4.0

- Add a verified service for enabling or disabling an existing Eva rule by name.
- Keep the rule schedule, mood target, and device membership unchanged.
