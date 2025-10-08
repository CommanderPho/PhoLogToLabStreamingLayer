## Why
Flutter currently uses a mock LSL service. To interoperate in the LSL ecosystem, the app must use real LSL via FFI on Android/iOS.

## What Changes
- Add FFI bindings to liblsl and platform loader for Android/iOS
- Implement outlets for `TextLogger` and `EventBoard`
- Validate performance and stability on devices/emulators
- Minimal tests for send paths and error handling

## Impact
- Affected specs: `specs/logging/spec.md`
- Affected code: `flutter_version/logger_app/lib/**` and platform FFI setup


