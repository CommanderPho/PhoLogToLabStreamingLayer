# XDF Files

A comprehensive Dart package for working with XDF (Extensible Data Format) files used in Lab Streaming Layer (LSL) applications. This package supports the full XDF specification and is designed to be compatible with standard EEG analysis software.

## Features

- **Full XDF Specification Support**: All data types (int8, int16, int32, int64, float32, double64, string)
- **EEG Stream Support**: Complete EEG metadata including channel locations, filtering, and hardware info
- **Multi-Stream Files**: Support for synchronized multiple streams in a single XDF file
- **Standard Electrode Systems**: Built-in 10-20 electrode locations and configurations
- **Marker/Event Streams**: Support for event markers and annotations
- **Data Validation**: Built-in validation for EEG data quality
- **Helper Classes**: Convenient utilities for common use cases
- **Backward Compatibility**: Maintains compatibility with existing simple text logger implementations

## Supported Stream Types

- **EEG**: Electroencephalography with comprehensive metadata
- **Markers/Events**: Time-stamped event markers
- **Custom Streams**: Any LSL-compatible stream type

## Getting Started

Add this package to your `pubspec.yaml`:

```yaml
dependencies:
  xdf_files:
    path: ../xdf_files  # For local package
```

## Usage

### Basic EEG Stream

```dart
import 'package:xdf_files/xdf_files.dart';
import 'dart:math';

// Create EEG stream info
final streamInfo = XDFEEGHelper.createStandardEEGStream(
  name: 'My EEG Recording',
  channelLabels: ['Fp1', 'Fp2', 'C3', 'C4', 'O1', 'O2'],
  sampleRate: 250.0,
  sourceId: 'eeg_device_001',
  manufacturer: 'MyEEGCompany',
  amplifierModel: 'MyAmp-64',
);

// Generate sample data
final samples = <XDFSample>[];
for (int i = 0; i < 1000; i++) {
  final timestamp = i / 250.0; // 250 Hz sampling rate
  final channelData = List.generate(6, (ch) => 
    sin(2 * pi * 10 * timestamp) + (Random().nextDouble() - 0.5) * 5.0
  );
  samples.add(XDFSample(timestamp: timestamp, data: channelData));
}

// Write to XDF file
await XDFWriterGeneral.writeXDFSingleStream(
  filePath: 'my_eeg_recording.xdf',
  samples: samples,
  streamInfo: streamInfo,
);
```

### Marker/Event Stream

```dart
// Create marker stream
final markerStream = XDFMarkerHelper.createMarkerStream(
  name: 'Experiment Events',
  sourceId: 'experiment_markers',
);

// Create event samples
final events = [
  XDFSample(timestamp: 1.0, data: ['Experiment Start']),
  XDFSample(timestamp: 5.5, data: ['Stimulus A']),
  XDFSample(timestamp: 10.2, data: ['Response']),
  XDFSample(timestamp: 15.0, data: ['Experiment End']),
];

await XDFWriterGeneral.writeXDFSingleStream(
  filePath: 'experiment_events.xdf',
  samples: events,
  streamInfo: markerStream,
);
```

### Multi-Stream XDF File

```dart
// Write synchronized EEG and marker streams
await XDFWriterGeneral.writeXDF(
  filePath: 'synchronized_recording.xdf',
  streams: {
    1: eegSamples,
    2: markerSamples,
  },
  streamInfos: {
    1: eegStreamInfo,
    2: markerStreamInfo,
  },
);
```

### Advanced EEG Configuration

```dart
// Create EEG stream with detailed metadata
final locations = XDFEEGHelper.getStandard1020Locations();
final streamInfo = XDFStreamInfo(
  name: 'High-Density EEG',
  type: 'EEG',
  channelCount: channelLabels.length,
  nominalSampleRate: 1000.0,
  channelFormat: XDFDataType.float32,
  sourceId: 'hd_eeg_001',
  manufacturer: 'Research Systems Inc.',
  channels: channelLabels.map((label) => XDFChannelInfo(
    label: label,
    unit: 'microvolts',
    type: 'EEG',
    location: locations[label],
    filtering: XDFFilterHelper.createStandardEEGFilter(),
  )).toList(),
  reference: XDFReference(
    labels: ['Cz'],
    subtracted: true,
    commonAverage: false,
  ),
  fiducials: XDFEEGHelper.getStandardFiducials(),
  cap: XDFCap(
    name: 'Research Cap 128',
    size: '56',
    manufacturer: 'Research Systems Inc.',
    labelScheme: '10-20',
  ),
  amplifier: XDFAmplifier(
    manufacturer: 'Research Systems Inc.',
    model: 'RA-128',
    precision: 24,
    compensatedLag: 0.002,
  ),
);
```

## Data Validation

```dart
// Validate EEG data before writing
final validation = XDFDataHelper.validateEEGData(samples, streamInfo);
if (validation['issues'].isNotEmpty) {
  print('Data issues found: ${validation['issues']}');
}
print('Statistics: ${validation['stats']}');
```

## Compatibility

This package generates XDF files that are compatible with:

- **EEGLAB** (MATLAB/Octave)
- **MNE-Python** (Python)
- **FieldTrip** (MATLAB)
- **BrainVision Analyzer**
- **OpenViBE**
- **LSL-compatible software**

The generated files follow the official XDF specification and include all necessary metadata for proper interpretation by EEG analysis software.

## Data Types Supported

- `int8`, `int16`, `int32`, `int64`: Integer data types
- `float32`: Single-precision floating point (standard for EEG)
- `double64`: Double-precision floating point
- `string`: UTF-8 encoded strings (for markers/events)

## Examples

See the `example/example.dart` file for comprehensive usage examples including:

- Basic EEG recording
- Marker streams
- Multi-stream synchronized files
- Advanced metadata configuration

## Testing

Run the test suite with:

```bash
flutter test
```

## Contributing

This package is designed to be a complete implementation of the XDF specification for Dart/Flutter applications. Contributions are welcome, particularly for:

- Additional electrode location sets
- More filtering presets
- Hardware-specific configurations
- Additional validation rules

## License

See LICENSE file for details.
