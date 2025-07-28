import 'package:flutter_test/flutter_test.dart';
import 'package:xdf_files/xdf_files.dart';

void main() {
  group('XDF Stream Info Tests', () {
    test('creates basic stream info', () {
      final streamInfo = XDFStreamInfo(
        name: 'Test Stream',
        type: 'EEG',
        channelCount: 4,
        nominalSampleRate: 250.0,
        channelFormat: XDFDataType.float32,
        sourceId: 'test_001',
      );
      
      expect(streamInfo.name, 'Test Stream');
      expect(streamInfo.type, 'EEG');
      expect(streamInfo.channelCount, 4);
      expect(streamInfo.nominalSampleRate, 250.0);
      expect(streamInfo.channelFormat, XDFDataType.float32);
      expect(streamInfo.channelFormatString, 'float32');
    });

    test('generates stream header XML', () {
      final streamInfo = XDFStreamInfo(
        name: 'Test EEG',
        type: 'EEG',
        channelCount: 2,
        nominalSampleRate: 500.0,
        channelFormat: XDFDataType.float32,
        sourceId: 'test_eeg',
        channels: [
          const XDFChannelInfo(label: 'C3', unit: 'microvolts', type: 'EEG'),
          const XDFChannelInfo(label: 'C4', unit: 'microvolts', type: 'EEG'),
        ],
      );
      
      final xml = streamInfo.generateStreamHeaderXML();
      expect(xml, contains('<n>Test EEG</n>'));
      expect(xml, contains('<type>EEG</type>'));
      expect(xml, contains('<channel_count>2</channel_count>'));
      expect(xml, contains('<nominal_srate>500.0</nominal_srate>'));
      expect(xml, contains('<channel_format>float32</channel_format>'));
      expect(xml, contains('<label>C3</label>'));
      expect(xml, contains('<label>C4</label>'));
    });
  });

  group('XDF EEG Helper Tests', () {
    test('creates standard EEG stream', () {
      final streamInfo = XDFEEGHelper.createStandardEEGStream(
        name: 'Test EEG',
        channelLabels: ['Fp1', 'Fp2', 'C3', 'C4'],
        sampleRate: 250.0,
      );
      
      expect(streamInfo.type, 'EEG');
      expect(streamInfo.channelCount, 4);
      expect(streamInfo.nominalSampleRate, 250.0);
      expect(streamInfo.channelFormat, XDFDataType.float32);
      expect(streamInfo.channels.length, 4);
      expect(streamInfo.channels[0].label, 'Fp1');
      expect(streamInfo.channels[0].unit, 'microvolts');
      expect(streamInfo.channels[0].type, 'EEG');
    });

    test('provides standard 10-20 locations', () {
      final locations = XDFEEGHelper.getStandard1020Locations();
      expect(locations.containsKey('Cz'), true);
      expect(locations.containsKey('Fp1'), true);
      expect(locations.containsKey('O2'), true);
      
      final cz = locations['Cz']!;
      expect(cz.x, 0.0);
      expect(cz.y, 0.0);
      expect(cz.z, 100.0);
    });
  });

  group('XDF Marker Helper Tests', () {
    test('creates marker stream', () {
      final streamInfo = XDFMarkerHelper.createMarkerStream(
        name: 'Test Markers',
        sourceId: 'markers_test',
      );
      
      expect(streamInfo.type, 'Markers');
      expect(streamInfo.channelCount, 1);
      expect(streamInfo.nominalSampleRate, 0); // Irregular
      expect(streamInfo.channelFormat, XDFDataType.string);
      expect(streamInfo.channels.length, 1);
      expect(streamInfo.channels[0].label, 'Marker');
    });
  });

  group('XDF Data Helper Tests', () {
    test('converts matrix to samples', () {
      final data = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
      ];
      
      final samples = XDFDataHelper.matrixToSamples(
        data,
        sampleRate: 100.0,
        startTime: 1.0,
      );
      
      expect(samples.length, 3);
      expect(samples[0].timestamp, 1.0);
      expect(samples[1].timestamp, 1.01);
      expect(samples[2].timestamp, 1.02);
      expect(samples[0].data, [1.0, 2.0, 3.0]);
      expect(samples[2].data, [7.0, 8.0, 9.0]);
    });

    test('validates EEG data', () {
      final streamInfo = XDFStreamInfo(
        name: 'Test',
        type: 'EEG',
        channelCount: 2,
        nominalSampleRate: 100.0,
        channelFormat: XDFDataType.float32,
        sourceId: 'test',
      );
      
      final samples = [
        const XDFSample(timestamp: 0.0, data: [1.0, 2.0]),
        const XDFSample(timestamp: 0.01, data: [3.0, 4.0]),
        const XDFSample(timestamp: 0.02, data: [5.0]), // Wrong channel count
      ];
      
      final validation = XDFDataHelper.validateEEGData(samples, streamInfo);
      expect(validation['issues'], isA<List>());
      expect((validation['issues'] as List).isNotEmpty, true);
      expect(validation['stats']['sample_count'], 3);
    });
  });

  group('XDF Sample Tests', () {
    test('creates XDF sample', () {
      const sample = XDFSample(
        timestamp: 1.5,
        data: [10.0, 20.0, 30.0],
      );
      
      expect(sample.timestamp, 1.5);
      expect(sample.data.length, 3);
      expect(sample.data[1], 20.0);
    });
  });

  group('XDF Channel Info Tests', () {
    test('creates channel with location', () {
      const location = XDFChannelLocation(x: 10.0, y: 20.0, z: 30.0);
      const channel = XDFChannelInfo(
        label: 'Fp1',
        unit: 'microvolts',
        type: 'EEG',
        location: location,
      );
      
      expect(channel.label, 'Fp1');
      expect(channel.unit, 'microvolts');
      expect(channel.type, 'EEG');
      expect(channel.location!.x, 10.0);
      expect(channel.location!.y, 20.0);
      expect(channel.location!.z, 30.0);
      
      final xml = channel.toXML();
      expect(xml, contains('<label>Fp1</label>'));
      expect(xml, contains('<unit>microvolts</unit>'));
      expect(xml, contains('<X>10.0</X>'));
    });
  });
}
