import 'xdf_stream_info.dart';
import 'xdf_writer_general.dart';

/// Helper class for creating EEG stream configurations
class XDFEEGHelper {
  /// Create a standard EEG stream info with 10-20 electrode system
  static XDFStreamInfo createStandardEEGStream({
    required String name,
    required List<String> channelLabels,
    required double sampleRate,
    String sourceId = 'eeg_001',
    String? manufacturer,
    String? amplifierModel,
    int? precision,
    String? capName,
    String? capSize,
    String unit = 'microvolts',
    List<XDFChannelLocation>? channelLocations,
    XDFReference? reference,
    List<XDFFiducial>? fiducials,
  }) {
    // Create channel info
    final channels = <XDFChannelInfo>[];
    for (int i = 0; i < channelLabels.length; i++) {
      channels.add(XDFChannelInfo(
        label: channelLabels[i],
        unit: unit,
        type: 'EEG',
        location: channelLocations != null && i < channelLocations.length
            ? channelLocations[i]
            : null,
      ));
    }

    return XDFStreamInfo(
      name: name,
      type: 'EEG',
      channelCount: channelLabels.length,
      nominalSampleRate: sampleRate,
      channelFormat: XDFDataType.float32, // Standard for EEG
      sourceId: sourceId,
      manufacturer: manufacturer,
      channels: channels,
      reference: reference,
      fiducials: fiducials ?? [],
      cap: capName != null
          ? XDFCap(
              name: capName,
              size: capSize,
              manufacturer: manufacturer,
              labelScheme: '10-20',
            )
          : null,
      amplifier: amplifierModel != null
          ? XDFAmplifier(
              manufacturer: manufacturer,
              model: amplifierModel,
              precision: precision,
            )
          : null,
    );
  }

  /// Create standard 10-20 electrode locations (subset)
  static Map<String, XDFChannelLocation> getStandard1020Locations() {
    return {
      'Fp1': const XDFChannelLocation(x: -27.5, y: 85.0, z: 40.0),
      'Fp2': const XDFChannelLocation(x: 27.5, y: 85.0, z: 40.0),
      'F3': const XDFChannelLocation(x: -45.0, y: 45.0, z: 65.0),
      'F4': const XDFChannelLocation(x: 45.0, y: 45.0, z: 65.0),
      'C3': const XDFChannelLocation(x: -60.0, y: 0.0, z: 85.0),
      'C4': const XDFChannelLocation(x: 60.0, y: 0.0, z: 85.0),
      'P3': const XDFChannelLocation(x: -45.0, y: -45.0, z: 65.0),
      'P4': const XDFChannelLocation(x: 45.0, y: -45.0, z: 65.0),
      'O1': const XDFChannelLocation(x: -27.5, y: -85.0, z: 40.0),
      'O2': const XDFChannelLocation(x: 27.5, y: -85.0, z: 40.0),
      'F7': const XDFChannelLocation(x: -75.0, y: 30.0, z: 35.0),
      'F8': const XDFChannelLocation(x: 75.0, y: 30.0, z: 35.0),
      'T7': const XDFChannelLocation(x: -85.0, y: 0.0, z: 15.0),
      'T8': const XDFChannelLocation(x: 85.0, y: 0.0, z: 15.0),
      'P7': const XDFChannelLocation(x: -75.0, y: -30.0, z: 35.0),
      'P8': const XDFChannelLocation(x: 75.0, y: -30.0, z: 35.0),
      'Fz': const XDFChannelLocation(x: 0.0, y: 45.0, z: 85.0),
      'Cz': const XDFChannelLocation(x: 0.0, y: 0.0, z: 100.0),
      'Pz': const XDFChannelLocation(x: 0.0, y: -45.0, z: 85.0),
      'Oz': const XDFChannelLocation(x: 0.0, y: -85.0, z: 55.0),
    };
  }

  /// Create standard fiducials for head coordinate system
  static List<XDFFiducial> getStandardFiducials() {
    return [
      const XDFFiducial(
        label: 'Nasion',
        location: XDFChannelLocation(x: 0.0, y: 100.0, z: 0.0),
      ),
      const XDFFiducial(
        label: 'Inion',
        location: XDFChannelLocation(x: 0.0, y: -100.0, z: 0.0),
      ),
      const XDFFiducial(
        label: 'LPA',
        location: XDFChannelLocation(x: -100.0, y: 0.0, z: 0.0),
      ),
      const XDFFiducial(
        label: 'RPA',
        location: XDFChannelLocation(x: 100.0, y: 0.0, z: 0.0),
      ),
    ];
  }
}

/// Helper class for creating marker/event streams
class XDFMarkerHelper {
  /// Create a marker/event stream info
  static XDFStreamInfo createMarkerStream({
    required String name,
    String sourceId = 'markers_001',
    String? manufacturer,
  }) {
    return XDFStreamInfo(
      name: name,
      type: 'Markers',
      channelCount: 1,
      nominalSampleRate: 0, // Irregular sampling rate for events
      channelFormat: XDFDataType.string,
      sourceId: sourceId,
      manufacturer: manufacturer,
      channels: [
        const XDFChannelInfo(
          label: 'Marker',
          unit: 'string',
          type: 'Markers',
        ),
      ],
    );
  }
}

/// Helper class for common EEG preprocessing configurations
class XDFFilterHelper {
  /// Create a standard EEG bandpass filter (0.5-50 Hz)
  static XDFChannelFiltering createStandardEEGFilter() {
    return XDFChannelFiltering(
      highpass: const XDFFilter(
        type: 'IIR',
        design: 'Butterworth',
        lower: 0.5,
        upper: 1.0,
        order: 4,
      ),
      lowpass: const XDFFilter(
        type: 'IIR',
        design: 'Butterworth',
        lower: 45.0,
        upper: 50.0,
        order: 4,
      ),
      notch: const XDFNotchFilter(
        type: 'IIR',
        design: 'Butterworth',
        center: 50.0, // For 50Hz line noise (use 60.0 for US)
        bandwidth: 2.0,
        order: 4,
      ),
    );
  }

  /// Create a wideband EEG filter (0.1-100 Hz)
  static XDFChannelFiltering createWidebandEEGFilter() {
    return XDFChannelFiltering(
      highpass: const XDFFilter(
        type: 'IIR',
        design: 'Butterworth',
        lower: 0.1,
        upper: 0.2,
        order: 4,
      ),
      lowpass: const XDFFilter(
        type: 'IIR',
        design: 'Butterworth',
        lower: 95.0,
        upper: 100.0,
        order: 4,
      ),
    );
  }
}

/// Utility class for data conversion and validation
class XDFDataHelper {
  /// Convert EEG data matrix to XDF samples
  /// [data] - 2D array where rows are samples and columns are channels
  /// [timestamps] - Timestamp for each sample
  /// [sampleRate] - If timestamps is null, generate timestamps at this rate
  static List<XDFSample> matrixToSamples(
    List<List<double>> data, {
    List<double>? timestamps,
    double? sampleRate,
    double? startTime,
  }) {
    final samples = <XDFSample>[];
    
    for (int i = 0; i < data.length; i++) {
      double timestamp;
      
      if (timestamps != null) {
        timestamp = timestamps[i];
      } else if (sampleRate != null) {
        final start = startTime ?? 0.0;
        timestamp = start + (i / sampleRate);
      } else {
        throw ArgumentError('Either timestamps or sampleRate must be provided');
      }
      
      samples.add(XDFSample(
        timestamp: timestamp,
        data: List<double>.from(data[i]),
      ));
    }
    
    return samples;
  }

  /// Validate EEG data for common issues
  static Map<String, dynamic> validateEEGData(
    List<XDFSample> samples,
    XDFStreamInfo streamInfo,
  ) {
    final issues = <String>[];
    final stats = <String, dynamic>{};
    
    if (samples.isEmpty) {
      issues.add('No samples provided');
      return {'issues': issues, 'stats': stats};
    }
    
    // Check channel count consistency
    final expectedChannels = streamInfo.channelCount;
    for (int i = 0; i < samples.length; i++) {
      if (samples[i].data.length != expectedChannels) {
        issues.add('Sample $i has ${samples[i].data.length} channels, expected $expectedChannels');
      }
    }
    
    // Check for NaN or infinite values
    int nanCount = 0;
    int infCount = 0;
    final channelStats = List<List<double>>.generate(expectedChannels, (_) => []);
    
    for (final sample in samples) {
      for (int ch = 0; ch < sample.data.length && ch < expectedChannels; ch++) {
        final value = sample.data[ch];
        if (value is double) {
          if (value.isNaN) nanCount++;
          if (value.isInfinite) infCount++;
          channelStats[ch].add(value);
        }
      }
    }
    
    if (nanCount > 0) issues.add('Found $nanCount NaN values');
    if (infCount > 0) issues.add('Found $infCount infinite values');
    
    // Calculate basic statistics
    stats['sample_count'] = samples.length;
    stats['duration'] = samples.last.timestamp - samples.first.timestamp;
    stats['nan_count'] = nanCount;
    stats['inf_count'] = infCount;
    
    // Channel statistics
    final channelStatsMap = <String, Map<String, double>>{};
    for (int ch = 0; ch < channelStats.length; ch++) {
      final values = channelStats[ch];
      if (values.isNotEmpty) {
        values.sort();
        final mean = values.reduce((a, b) => a + b) / values.length;
        final min = values.first;
        final max = values.last;
        final median = values[values.length ~/ 2];
        
        final channelLabel = ch < streamInfo.channels.length 
            ? streamInfo.channels[ch].label 
            : 'Ch$ch';
            
        channelStatsMap[channelLabel] = {
          'mean': mean,
          'min': min,
          'max': max,
          'median': median,
        };
      }
    }
    stats['channels'] = channelStatsMap;
    
    return {'issues': issues, 'stats': stats};
  }
}
