## MODIFIED Requirements
### Requirement: EventBoard Stream
#### Scenario: Flutter emits EventBoard event (mock)
- **WHEN** a user presses an EventBoard button in Flutter
- **THEN** the app produces an event string formatted like Python: `EVENT_NAME|BUTTON_TEXT|TIMESTAMP` for instantaneous
- **AND** for toggles uses `EVENT_NAME_START|BUTTON_TEXT|TIMESTAMP|TOGGLE:True` and `_END|...|TOGGLE:False`
- **AND** the UI reflects ON/OFF states consistently

### Requirement: Flutter EventBoard UI Parity
#### Scenario: Toggle ON/OFF events (Flutter)
- **WHEN** a toggle button changes state
- **THEN** update the UI and emit the corresponding START/END message as above

#### Scenario: Time offsets (Flutter)
- **WHEN** a time offset is provided (e.g., `5s`, `2m`, `1h`)
- **THEN** the event timestamp reflects the offset

### Requirement: Flutter Configuration Parity
#### Scenario: Load and render config (Flutter)
- **WHEN** configuration is present
- **THEN** render the grid with matching text, colors, types, and offsets using a schema compatible with `eventboard_config.json`


