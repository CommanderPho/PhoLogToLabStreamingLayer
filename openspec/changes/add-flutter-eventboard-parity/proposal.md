## Why
Flutter's EventBoard UI and behavior lag behind Python. We need parity in UI (3x5 grid), toggle behavior, time offsets, message formats, and configuration compatibility.

## What Changes
- Implement EventBoard UI: 3x5 grid, instantaneous/toggleable buttons
- Add time offset parsing on buttons (e.g., `5s`, `2m`, `1h`)
- Align event message format with Python (START/END + `|TOGGLE:<bool>`)
- Add configuration parity compatible with `eventboard_config.json`
- Tests for UI toggling, offsets, and formatting

## Impact
- Affected specs: `specs/logging/spec.md`
- Affected code: `flutter_version/logger_app/lib/**`


