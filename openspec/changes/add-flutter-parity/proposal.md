> Status: SUPERSEDED by `add-flutter-eventboard-parity` and `add-flutter-real-lsl`.

## Why
The Flutter app is stale and currently uses a mock LSL service with JSON recording. We need feature parity with the Python app for Android/iOS clients to ensure consistent behavior across platforms.

## What Changes
- Implement real LSL via FFI (liblsl) for `TextLogger` and `EventBoard`
- Match EventBoard UI and behavior (instantaneous/toggleable, time offsets)
- Adopt Python-compatible message formats for events and notes
- Implement recording parity: XDF writer and CSV export, auto-start, split, backups/recovery
- Introduce configuration parity (schema aligned with `eventboard_config.json`)
- Add tests and validation for mobile platforms

## Impact
- Affected specs: `specs/logging/spec.md`
- Affected code: `flutter_version/logger_app/lib/**`


