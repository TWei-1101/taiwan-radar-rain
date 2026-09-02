# Changelog

## 0.4.0

- Support up to three independently named monitoring locations.
- Reuse one CWA radar download for all enabled locations.
- Create a separate Home Assistant MQTT device for each location.
- Preserve the first location's existing MQTT unique IDs.
- Remove MQTT entities when an optional location is disabled.

## 0.3.0

- Add estimated rain stopping time for the next 10–60 minutes.
- Clarify nearby reflectivity and approaching-rain entity names.
