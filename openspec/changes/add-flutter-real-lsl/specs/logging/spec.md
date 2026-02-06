## MODIFIED Requirements
### Requirement: LSL Text Logging
The system SHALL provide a Markers stream named `TextLogger` for freeform text messages.

#### Scenario: Python sends text over LSL
- **WHEN** a user submits a message via the main input or quick popover
- **THEN** the app pushes a single-channel string sample to the `TextLogger` outlet
- **AND** the GUI log history displays the message with a readable timestamp

#### Scenario: Flutter sends text over real LSL
- **WHEN** a user submits a message in the Flutter app
- **THEN** the app pushes a single-channel string sample to the `TextLogger` outlet using the `lsl_flutter` library
- **AND** the message is recorded identically to Python-originated samples

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

#### Scenario: Flutter emits EventBoard event over real LSL
- **WHEN** a user presses an EventBoard button in Flutter
- **THEN** the app sends the formatted event string to the `EventBoard` outlet using the `lsl_flutter` library

## ADDED Requirements
### Requirement: Flutter LSL Service uses lsl_flutter
Flutter SHALL integrate with LabStreamingLayer using the `lsl_flutter` package in `flutter_version/logger_app/lib/models/lsl_service.dart` for real-time stream outlets and inlets where applicable.

#### Scenario: Create and publish samples via Outlet (example)
- **WHEN** the Flutter app initializes an LSL outlet
- **THEN** it SHALL construct a `StreamInfo`, spawn an `OutletWorker`, add a stream, and push samples using `lsl_flutter`

```dart
// --- Outlet ---
// Create a stream information object for PPG data that will have integer samples, 4 channels,
// and a nominal sampling rate of 135 Hz
final streamInfo = StreamInfoFactory.createIntStreamInfo(
    "Test PPG", "PPG", Int64ChannelFormat(),
    channelCount: 4, nominalSRate: 135, sourceId: deviceId);

// Spawn an outlet isolate worker
final worker = await OutletWorker.spawn();

// Add a new stream outlet
final success = await worker.addStream(streamInfo);

// Push a sample to the newly created outlet
await worker.pushSample("Test PPG", sample);
```
