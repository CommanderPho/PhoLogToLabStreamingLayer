## ADDED Requirements
### Requirement: Flutter LSL Integration via FFI
Flutter SHALL implement real LSL integration via FFI to support `TextLogger` and `EventBoard`.

#### Scenario: Send text over LSL (Flutter)
- **WHEN** a user submits a message
- **THEN** the app pushes a string sample to `TextLogger`

#### Scenario: Send EventBoard events over LSL (Flutter)
- **WHEN** a user presses an EventBoard button
- **THEN** the app sends an event message to `EventBoard`

### Requirement: Flutter Recording Parity
Flutter SHALL support XDF recording and CSV export with auto-start, split, and recovery.

#### Scenario: Record to XDF and CSV (Flutter)
- **WHEN** recording is active
- **THEN** the app writes XDF and mirrors events to CSV

#### Scenario: Backup and recovery (Flutter)
- **WHEN** the app is recording
- **THEN** periodic backups are written and restored on next startup if found

### Requirement: Flutter EventBoard UI Parity
Flutter SHALL provide a 3x5 EventBoard grid with instantaneous and toggleable buttons and time offsets.

#### Scenario: Toggle ON/OFF events (Flutter)
- **WHEN** a toggle button changes state
- **THEN** the UI updates and an appropriate START/END event is sent

#### Scenario: Time offsets (Flutter)
- **WHEN** a time offset is provided (e.g., `5s`, `2m`)
- **THEN** the event timestamp reflects the offset

### Requirement: Flutter Message Format Parity
Flutter SHALL emit messages using Python-compatible formats.

#### Scenario: Toggle event formatting (Flutter)
- **THEN** use `EVENT_NAME_START|BUTTON_TEXT|TIMESTAMP|TOGGLE:True` on start and `_END|...|TOGGLE:False` on end

### Requirement: Flutter Configuration Parity
Flutter SHALL support a configuration compatible with `eventboard_config.json`.

#### Scenario: Load and render config (Flutter)
- **WHEN** configuration is present
- **THEN** the grid is rendered with matching text, colors, types, and offsets


