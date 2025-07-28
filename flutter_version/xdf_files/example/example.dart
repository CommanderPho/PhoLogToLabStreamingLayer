// ignore_for_file: avoid_print

import 'dart:math';
import 'package:xdf_files/xdf_files.dart';

void main() async {
  // Example 1: Create a simple EEG stream
  await createEEGExample();
  
  // Example 2: Create a marker stream
  await createMarkerExample();
  
  // Example 3: Create a multi-stream file
  await createMultiStreamExample();
  
  print('All examples completed successfully!');
}

/// Example 1: Create a simple EEG recording
Future<void> createEEGExample() async {
  print('Creating EEG example...');
  
  // Define EEG channels (standard 10-20 subset)
  final channelLabels = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2'];
  final locations1020 = XDFEEGHelper.getStandard1020Locations();
  final channelLocations = channelLabels
      .map((label) => locations1020[label])
      .where((loc) => loc != null)
      .cast<XDFChannelLocation>()
      .toList();
  
  // Create EEG stream info
  final streamInfo = XDFEEGHelper.createStandardEEGStream(
    name: 'Example EEG',
    channelLabels: channelLabels,
    sampleRate: 250.0, // 250 Hz
    sourceId: 'example_eeg_001',
    manufacturer: 'ExampleManufacturer',
    amplifierModel: 'ExampleAmp-64',
    precision: 24,
    capName: 'ExampleCap',
    capSize: '56',
    channelLocations: channelLocations,
    reference: const XDFReference(
      labels: ['Cz'],
      subtracted: true,
      commonAverage: false,
    ),
    fiducials: XDFEEGHelper.getStandardFiducials(),
  );
  
  // Generate some example EEG data (10 seconds at 250 Hz)
  final sampleRate = 250.0;
  final duration = 10.0;
  final numSamples = (duration * sampleRate).round();
  final numChannels = channelLabels.length;
  
  final samples = <XDFSample>[];
  final random = Random(42); // Fixed seed for reproducibility
  
  for (int i = 0; i < numSamples; i++) {
    final timestamp = i / sampleRate;
    final channelData = <double>[];
    
    for (int ch = 0; ch < numChannels; ch++) {
      // Generate realistic EEG-like data
      // Alpha rhythm at 10 Hz + some noise
      final alpha = 10.0 * sin(2 * pi * 10 * timestamp);
      final noise = (random.nextDouble() - 0.5) * 5.0;
      final value = alpha + noise;
      channelData.add(value);
    }
    
    samples.add(XDFSample(timestamp: timestamp, data: channelData));
  }
  
  // Validate the data
  final validation = XDFDataHelper.validateEEGData(samples, streamInfo);
  print('EEG data validation: ${validation['issues'].length} issues found');
  if (validation['issues'].isNotEmpty) {
    print('Issues: ${validation['issues']}');
  }
  
  // Write to XDF file
  await XDFWriterGeneral.writeXDFSingleStream(
    filePath: 'example_eeg.xdf',
    samples: samples,
    streamInfo: streamInfo,
  );
  
  print('EEG example written to example_eeg.xdf');
}

/// Example 2: Create a marker/event stream
Future<void> createMarkerExample() async {
  print('Creating marker example...');
  
  // Create marker stream info
  final streamInfo = XDFMarkerHelper.createMarkerStream(
    name: 'Example Markers',
    sourceId: 'example_markers_001',
    manufacturer: 'ExampleSoftware',
  );
  
  // Generate some example markers
  final samples = <XDFSample>[
    const XDFSample(timestamp: 1.0, data: ['Experiment Start']),
    const XDFSample(timestamp: 5.5, data: ['Stimulus A']),
    const XDFSample(timestamp: 8.2, data: ['Stimulus B']),
    const XDFSample(timestamp: 12.1, data: ['Response']),
    const XDFSample(timestamp: 15.0, data: ['Experiment End']),
  ];
  
  // Write to XDF file
  await XDFWriterGeneral.writeXDFSingleStream(
    filePath: 'example_markers.xdf',
    samples: samples,
    streamInfo: streamInfo,
  );
  
  print('Marker example written to example_markers.xdf');
}

/// Example 3: Create a multi-stream file with synchronized EEG and markers
Future<void> createMultiStreamExample() async {
  print('Creating multi-stream example...');
  
  // Create EEG stream
  final eegChannels = ['C3', 'C4', 'Cz'];
  final eegStreamInfo = XDFEEGHelper.createStandardEEGStream(
    name: 'Multi-Stream EEG',
    channelLabels: eegChannels,
    sampleRate: 500.0,
    sourceId: 'multi_eeg_001',
  );
  
  // Create marker stream
  final markerStreamInfo = XDFMarkerHelper.createMarkerStream(
    name: 'Multi-Stream Markers',
    sourceId: 'multi_markers_001',
  );
  
  // Generate synchronized data
  final sampleRate = 500.0;
  final duration = 5.0;
  final numSamples = (duration * sampleRate).round();
  final random = Random(123);
  
  final eegSamples = <XDFSample>[];
  final markerSamples = <XDFSample>[];
  
  for (int i = 0; i < numSamples; i++) {
    final timestamp = i / sampleRate;
    
    // EEG data
    final channelData = List.generate(
      eegChannels.length,
      (ch) => sin(2 * pi * 8 * timestamp) + (random.nextDouble() - 0.5) * 2.0,
    );
    eegSamples.add(XDFSample(timestamp: timestamp, data: channelData));
    
    // Add occasional markers
    if (i % 1000 == 0) {
      markerSamples.add(XDFSample(
        timestamp: timestamp,
        data: ['Marker at ${timestamp.toStringAsFixed(1)}s'],
      ));
    }
  }
  
  // Write multi-stream XDF file
  await XDFWriterGeneral.writeXDF(
    filePath: 'example_multistream.xdf',
    streams: {
      1: eegSamples,
      2: markerSamples,
    },
    streamInfos: {
      1: eegStreamInfo,
      2: markerStreamInfo,
    },
  );
  
  print('Multi-stream example written to example_multistream.xdf');
}
