# Flutter Version of LSL Logger

This is a Flutter implementation of the Python LSL Logger application. It provides equivalent functionality for logging text messages via Lab Streaming Layer (LSL) and recording them to files.

## Features

- **LSL Integration**: Send text messages over Lab Streaming Layer
- **XDF Recording**: Record LSL streams to native XDF binary format
- **Async File Writing**: Debounced writing with 3-second delay for data safety
- **Auto-start Recording**: Automatically begins recording when the app starts
- **Split Recording**: Split recordings into new files without losing data
- **Recovery Support**: Backup files for crash recovery
- **CSV Export**: Real-time CSV export alongside XDF for easy analysis
- **Cross-platform**: Runs on Windows, macOS, Linux, iOS, and Android

## Architecture

The Flutter app is structured with the following components:

### Main Components

- **`main.dart`**: Main application entry point and UI
- **`models/lsl_service.dart`**: LSL communication service (mock implementation)
- **`models/recording_service.dart`**: Recording and file management
- **`models/log_entry.dart`**: Data model for log entries

### Key Differences from Python Version

1. **LSL Implementation**: Currently uses a mock LSL service. Real implementation would require:
   - Native LSL library bindings via FFI
   - Platform channels for iOS/Android
   - Custom LSL Dart package

2. **File Format**: Saves recordings in native XDF binary format:
   - Full compatibility with Lab Streaming Layer ecosystem
   - Proper XDF chunk structure with headers, samples, and footers
   - Real-time CSV export for easy data analysis
   - Async writing with debouncing for data safety

3. **UI Framework**: Flutter Material Design instead of tkinter:
   - Responsive design for mobile and desktop
   - Modern UI components
   - Better cross-platform support

## Setup

1. **Install Dependencies**:
   ```bash
   cd flutter_version/logger_app
   flutter pub get
   ```

2. **Run the Application**:
   ```bash
   flutter run
   ```

## Dependencies

- `path_provider`: For accessing device directories
- `ffi`: For future native LSL library integration

## Usage

1. **Start the App**: The application will auto-initialize LSL connection
2. **Auto Recording**: Recording starts automatically in the default directory
3. **Send Messages**: Type messages and click "Log" or press Enter
4. **Manual Recording Control**: Start/stop/split recordings as needed
5. **File Output**: Recordings saved as XDF binary files with real-time CSV export
6. **Data Safety**: Files written asynchronously 3 seconds after messages for crash protection

## Future Enhancements

To make this a fully functional LSL application:

1. **Implement Real LSL Bindings**:
   - Create FFI bindings to LSL C library
   - Add platform-specific LSL library loading
   - Implement proper LSL inlet/outlet functionality

2. **Add Recovery Features**:
   - Scan for backup files on startup
   - Implement recovery dialog system
   - Auto-recovery options

3. **Enhanced File Formats**:
   - Add XDF format support via native libraries
   - Support for MNE-compatible formats
   - Data compression options

4. **Mobile Optimizations**:
   - Touch-friendly UI for mobile devices
   - Background recording capabilities
   - Cloud storage integration

## File Structure

```
flutter_version/logger_app/
├── lib/
│   ├── main.dart                 # Main app and UI
│   └── models/
│       ├── lsl_service.dart      # LSL communication
│       ├── recording_service.dart # File recording
│       └── log_entry.dart        # Data models
├── pubspec.yaml                  # Dependencies
└── README.md                     # This file
```

## Data Format

Recordings are saved in JSON format with the following structure:

```json
{
  "metadata": {
    "stream_name": "TextLogger",
    "stream_type": "Markers",
    "recording_start_time": "2024-01-01T12:00:00.000Z",
    "sample_count": 10
  },
  "data": [
    {
      "sample": ["message text"],
      "timestamp": 1704110400.123,
      "readable_timestamp": "2024-01-01T12:00:00.123Z"
    }
  ]
}
```

The CSV export provides the same data in a more readable format for analysis.
