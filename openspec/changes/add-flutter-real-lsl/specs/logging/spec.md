## MODIFIED Requirements
### Requirement: LSL Text Logging
#### Scenario: Flutter enqueues text (mock LSL)
- **WHEN** a user submits a message in the Flutter app
- **THEN** the app pushes a string sample to the real `TextLogger` outlet via FFI

### Requirement: EventBoard Stream
#### Scenario: Flutter emits EventBoard event (mock)
- **WHEN** a user presses an EventBoard button in Flutter
- **THEN** the app sends the formatted event string to the real `EventBoard` outlet via FFI


