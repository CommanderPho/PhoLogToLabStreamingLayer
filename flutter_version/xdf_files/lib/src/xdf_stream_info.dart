import 'dart:convert';

/// Supported data types for XDF streams
enum XDFDataType {
  int8,
  int16,
  int32,
  int64,
  float32,
  double64,
  string,
}

/// Channel information for XDF streams
class XDFChannelInfo {
  final String label;
  final String? unit;
  final String? type;
  final XDFChannelLocation? location;
  final XDFChannelHardware? hardware;
  final double? impedance;
  final XDFChannelFiltering? filtering;

  const XDFChannelInfo({
    required this.label,
    this.unit,
    this.type,
    this.location,
    this.hardware,
    this.impedance,
    this.filtering,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('    <channel>');
    buffer.writeln('      <label>$label</label>');
    if (unit != null) buffer.writeln('      <unit>$unit</unit>');
    if (type != null) buffer.writeln('      <type>$type</type>');
    if (location != null) buffer.write(location!.toXML());
    if (hardware != null) buffer.write(hardware!.toXML());
    if (impedance != null) buffer.writeln('      <impedance>$impedance</impedance>');
    if (filtering != null) buffer.write(filtering!.toXML());
    buffer.writeln('    </channel>');
    return buffer.toString();
  }
}

/// 3D location for channels and fiducials
class XDFChannelLocation {
  final double x; // mm, right from center
  final double y; // mm, front from center
  final double z; // mm, up from center

  const XDFChannelLocation({
    required this.x,
    required this.y,
    required this.z,
  });

  String toXML() {
    return '''      <location>
        <X>$x</X>
        <Y>$y</Y>
        <Z>$z</Z>
      </location>
''';
  }
}

/// Hardware information for channels
class XDFChannelHardware {
  final String? model;
  final String? manufacturer;
  final String? coupling; // Gel, Saline, Dry, Capacitive
  final String? material; // Ag-AgCl, Rubber, Foam, Plastic
  final String? surface; // Plate, Pins, Bristle, Pad

  const XDFChannelHardware({
    this.model,
    this.manufacturer,
    this.coupling,
    this.material,
    this.surface,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('      <hardware>');
    if (model != null) buffer.writeln('        <model>$model</model>');
    if (manufacturer != null) buffer.writeln('        <manufacturer>$manufacturer</manufacturer>');
    if (coupling != null) buffer.writeln('        <coupling>$coupling</coupling>');
    if (material != null) buffer.writeln('        <material>$material</material>');
    if (surface != null) buffer.writeln('        <surface>$surface</surface>');
    buffer.writeln('      </hardware>');
    return buffer.toString();
  }
}

/// Filtering information for channels
class XDFChannelFiltering {
  final XDFFilter? highpass;
  final XDFFilter? lowpass;
  final XDFNotchFilter? notch;

  const XDFChannelFiltering({
    this.highpass,
    this.lowpass,
    this.notch,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('      <filtering>');
    if (highpass != null) buffer.write(highpass!.toXML('highpass'));
    if (lowpass != null) buffer.write(lowpass!.toXML('lowpass'));
    if (notch != null) buffer.write(notch!.toXML());
    buffer.writeln('      </filtering>');
    return buffer.toString();
  }
}

/// Filter specification
class XDFFilter {
  final String? type; // FIR, IIR, Analog
  final String? design; // Butterworth, Elliptic
  final double? lower; // Hz
  final double? upper; // Hz
  final int? order;

  const XDFFilter({
    this.type,
    this.design,
    this.lower,
    this.upper,
    this.order,
  });

  String toXML(String filterType) {
    final buffer = StringBuffer();
    buffer.writeln('        <$filterType>');
    if (type != null) buffer.writeln('          <type>$type</type>');
    if (design != null) buffer.writeln('          <design>$design</design>');
    if (lower != null) buffer.writeln('          <lower>$lower</lower>');
    if (upper != null) buffer.writeln('          <upper>$upper</upper>');
    if (order != null) buffer.writeln('          <order>$order</order>');
    buffer.writeln('        </$filterType>');
    return buffer.toString();
  }
}

/// Notch filter specification
class XDFNotchFilter {
  final String? type; // FIR, IIR, Analog
  final String? design; // Butterworth, Elliptic
  final double? center; // Hz
  final double? bandwidth; // Hz
  final int? order;

  const XDFNotchFilter({
    this.type,
    this.design,
    this.center,
    this.bandwidth,
    this.order,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('        <notch>');
    if (type != null) buffer.writeln('          <type>$type</type>');
    if (design != null) buffer.writeln('          <design>$design</design>');
    if (center != null) buffer.writeln('          <center>$center</center>');
    if (bandwidth != null) buffer.writeln('          <bandwidth>$bandwidth</bandwidth>');
    if (order != null) buffer.writeln('          <order>$order</order>');
    buffer.writeln('        </notch>');
    return buffer.toString();
  }
}

/// Reference information
class XDFReference {
  final List<String> labels;
  final bool subtracted;
  final bool commonAverage;

  const XDFReference({
    this.labels = const [],
    this.subtracted = false,
    this.commonAverage = false,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('  <reference>');
    for (final label in labels) {
      buffer.writeln('    <label>$label</label>');
    }
    buffer.writeln('    <subtracted>${subtracted ? "Yes" : "No"}</subtracted>');
    buffer.writeln('    <common_average>${commonAverage ? "Yes" : "No"}</common_average>');
    buffer.writeln('  </reference>');
    return buffer.toString();
  }
}

/// Fiducial point information
class XDFFiducial {
  final String label; // e.g., Nasion, Inion, LPF, RPF
  final XDFChannelLocation location;

  const XDFFiducial({
    required this.label,
    required this.location,
  });

  String toXML() {
    return '''    <fiducial>
      <label>$label</label>
${location.toXML()}    </fiducial>
''';
  }
}

/// EEG cap information
class XDFCap {
  final String name;
  final String? size; // head circumference in cm
  final String? manufacturer;
  final String? labelScheme; // 10-20, BioSemi-128, etc.

  const XDFCap({
    required this.name,
    this.size,
    this.manufacturer,
    this.labelScheme,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('  <cap>');
    buffer.writeln('    <n>$name</n>');
    if (size != null) buffer.writeln('    <size>$size</size>');
    if (manufacturer != null) buffer.writeln('    <manufacturer>$manufacturer</manufacturer>');
    if (labelScheme != null) buffer.writeln('    <labelscheme>$labelScheme</labelscheme>');
    buffer.writeln('  </cap>');
    return buffer.toString();
  }
}

/// Amplifier information
class XDFAmplifier {
  final String? manufacturer;
  final String? model;
  final int? precision; // bits (8, 16, 24, 32)
  final double? compensatedLag; // seconds

  const XDFAmplifier({
    this.manufacturer,
    this.model,
    this.precision,
    this.compensatedLag,
  });

  String toXML() {
    final buffer = StringBuffer();
    buffer.writeln('  <amplifier>');
    buffer.writeln('    <settings/>');
    buffer.writeln('  </amplifier>');
    buffer.writeln('  <acquisition>');
    if (manufacturer != null) buffer.writeln('    <manufacturer>$manufacturer</manufacturer>');
    if (model != null) buffer.writeln('    <model>$model</model>');
    if (precision != null) buffer.writeln('    <precision>$precision</precision>');
    if (compensatedLag != null) buffer.writeln('    <compensated_lag>$compensatedLag</compensated_lag>');
    buffer.writeln('  </acquisition>');
    return buffer.toString();
  }
}

/// Complete stream information for XDF files
class XDFStreamInfo {
  final String name;
  final String type; // EEG, Markers, etc.
  final int channelCount;
  final double nominalSampleRate; // Hz, 0 for irregular
  final XDFDataType channelFormat;
  final String sourceId;
  final String? uid;
  final String? sessionId;
  final String? hostname;
  final String? manufacturer;
  final List<XDFChannelInfo> channels;
  final XDFReference? reference;
  final List<XDFFiducial> fiducials;
  final XDFCap? cap;
  final XDFAmplifier? amplifier;
  final Map<String, dynamic> customMetadata;

  XDFStreamInfo({
    required this.name,
    required this.type,
    required this.channelCount,
    required this.nominalSampleRate,
    required this.channelFormat,
    required this.sourceId,
    this.uid,
    this.sessionId,
    this.hostname,
    this.manufacturer,
    this.channels = const [],
    this.reference,
    this.fiducials = const [],
    this.cap,
    this.amplifier,
    this.customMetadata = const {},
  });

  String get channelFormatString {
    switch (channelFormat) {
      case XDFDataType.int8:
        return 'int8';
      case XDFDataType.int16:
        return 'int16';
      case XDFDataType.int32:
        return 'int32';
      case XDFDataType.int64:
        return 'int64';
      case XDFDataType.float32:
        return 'float32';
      case XDFDataType.double64:
        return 'double64';
      case XDFDataType.string:
        return 'string';
    }
  }

  String generateStreamHeaderXML() {
    final buffer = StringBuffer();
    buffer.writeln('<?xml version="1.0"?>');
    buffer.writeln('<info>');
    buffer.writeln('  <n>$name</n>');
    buffer.writeln('  <type>$type</type>');
    buffer.writeln('  <channel_count>$channelCount</channel_count>');
    buffer.writeln('  <nominal_srate>$nominalSampleRate</nominal_srate>');
    buffer.writeln('  <channel_format>$channelFormatString</channel_format>');
    buffer.writeln('  <source_id>$sourceId</source_id>');
    buffer.writeln('  <version>1.0</version>');
    buffer.writeln('  <created_at>${DateTime.now().millisecondsSinceEpoch / 1000.0}</created_at>');
    buffer.writeln('  <uid>${uid ?? _generateUID()}</uid>');
    buffer.writeln('  <session_id>${sessionId ?? "default"}</session_id>');
    buffer.writeln('  <hostname>${hostname ?? "dart_app"}</hostname>');
    if (manufacturer != null) {
      buffer.writeln('  <manufacturer>$manufacturer</manufacturer>');
    }
    
    // Add metadata description
    if (channels.isNotEmpty || reference != null || fiducials.isNotEmpty || 
        cap != null || amplifier != null || customMetadata.isNotEmpty) {
      buffer.writeln('  <desc>');
      
      // Channels metadata
      if (channels.isNotEmpty) {
        buffer.writeln('    <channels>');
        for (final channel in channels) {
          buffer.write(channel.toXML());
        }
        buffer.writeln('    </channels>');
      }
      
      // Reference
      if (reference != null) {
        buffer.write(reference!.toXML());
      }
      
      // Fiducials
      if (fiducials.isNotEmpty) {
        buffer.writeln('    <fiducials>');
        for (final fiducial in fiducials) {
          buffer.write(fiducial.toXML());
        }
        buffer.writeln('    </fiducials>');
      }
      
      // Cap
      if (cap != null) {
        buffer.write(cap!.toXML());
      }
      
      // Amplifier
      if (amplifier != null) {
        buffer.write(amplifier!.toXML());
      }
      
      // Custom metadata
      for (final entry in customMetadata.entries) {
        if (entry.value is String) {
          buffer.writeln('    <${entry.key}>${entry.value}</${entry.key}>');
        }
      }
      
      buffer.writeln('  </desc>');
    } else {
      buffer.writeln('  <desc/>');
    }
    
    buffer.writeln('</info>');
    return buffer.toString();
  }

  String _generateUID() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final random = (timestamp % 0xFFFFFFFF).toRadixString(16);
    return '$timestamp-$random-dart-xdf';
  }
}
