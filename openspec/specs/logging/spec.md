# Logging Capability

## Requirements

### Requirement: LSL Text Logging
The system SHALL provide a Markers stream named `TextLogger` for freeform text messages.

#### Scenario: Python sends text over LSL
- **WHEN** a user submits a message via the main input or quick popover
- **THEN** the app pushes a single-channel string sample to the `TextLogger` outlet
- **AND** the GUI log history displays the message with a readable timestamp

#### Scenario: Flutter enqueues text (mock LSL)
- **WHEN** a user submits a message in the Flutter app
- **THEN** the message is enqueued to the mock LSL service
- **AND** persisted to the active recording buffer for later file output
- **NOTE**: Real LSL integration SHALL be implemented via FFI in a future change

### Requirement: EventBoard Stream
The system SHALL provide structured button events via a `EventBoard` Markers stream with support for instantaneous and toggleable events.

#### Scenario: Python emits instantaneous event
- **WHEN** a user presses an instantaneous EventBoard button
- **THEN** the app sends `EVENT_NAME|BUTTON_TEXT|TIMESTAMP` over the `EventBoard` outlet
- **AND** shows the event in the GUI log with optional time offset annotation

#### Scenario: Python emits toggle start/end events
- **WHEN** a user toggles a toggleable EventBoard button ON
- **THEN** send `EVENT_NAME_START|BUTTON_TEXT|TIMESTAMP|TOGGLE:True`
- **AND** update the button state to active
- **WHEN** toggled OFF
- **THEN** send `EVENT_NAME_END|BUTTON_TEXT|TIMESTAMP|TOGGLE:False`
- **AND** restore the button state to inactive

#### Scenario: Flutter emits EventBoard event (mock)
- **WHEN** a user presses an EventBoard button in Flutter
- **THEN** the app records an equivalent event object in the active recording
- **NOTE**: Real LSL emission SHALL be added with FFI in a future change

### Requirement: Recording and Persistence
The system SHALL persist logged messages to durable files with a consistent, analyzable structure.

#### Scenario: Python records to FIF and CSV
- **WHEN** recording is active
- **THEN** collected LSL samples are saved as MNE `.fif`
- **AND** events are also exported to `CSV/*_events.csv`
- **AND** the app maintains a periodic JSON backup for crash recovery

#### Scenario: Flutter records to JSON (transition to XDF planned)
- **WHEN** recording is active in Flutter
- **THEN** messages/events are appended to a JSON recording format
- **NOTE**: Native XDF compatibility SHALL be implemented in a future change

### Requirement: Quick Entry UX (Desktop)
The system SHOULD provide desktop conveniences for rapid logging.

#### Scenario: System tray controls (Python)
- **WHEN** the app is minimized
- **THEN** a system tray icon provides Show, Quick Log, and Exit actions

#### Scenario: Global hotkey popover (Python)
- **WHEN** the user presses `Ctrl+Alt+L`
- **THEN** a focused popover appears for immediate text entry
- **AND** Enter logs the message; Escape cancels

### Requirement: Configuration
The system SHALL allow configuring EventBoard buttons.

#### Scenario: Python reads eventboard_config.json
- **WHEN** the app launches
- **THEN** it loads `eventboard_config.json` if present
- **AND** renders a 3x5 grid with defined buttons, colors, and types
- **AND** supports time offset entry per button

#### Scenario: Flutter configuration parity (planned)
- **THEN** Flutter SHALL support a compatible configuration model
- **NOTE**: Config file and schema alignment SHALL be proposed in a future change
