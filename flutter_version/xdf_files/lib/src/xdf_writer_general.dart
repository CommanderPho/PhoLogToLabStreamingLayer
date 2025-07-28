import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';
import 'xdf_stream_info.dart';

/// Sample data structure for XDF streams
class XDFSample {
  final double timestamp;
  final List<dynamic> data; // Can contain different data types based on stream format
  
  const XDFSample({
    required this.timestamp,
    required this.data,
  });
}

/// General XDF Writer supporting all LSL stream types and data formats
/// Based on XDF Specification 1.0: https://github.com/sccn/xdf/wiki/Specifications
class XDFWriterGeneral {
  static const String _magicCode = 'XDF:';
  
  // Chunk tags as defined in XDF specification
  static const int _tagFileHeader = 1;
  static const int _tagStreamHeader = 2;
  static const int _tagSamples = 3;
  static const int _tagClockOffset = 4;
  static const int _tagBoundary = 5;
  static const int _tagStreamFooter = 6;

  /// Write XDF file with general LSL stream data
  /// 
  /// [filePath] - Output file path
  /// [streams] - Map of stream ID to stream data
  /// [streamInfos] - Map of stream ID to stream information
  /// [chunkSize] - Number of samples per chunk (default 100)
  /// [boundaryInterval] - Write boundary chunks every N samples (default 1000)
  static Future<void> writeXDF({
    required String filePath,
    required Map<int, List<XDFSample>> streams,
    required Map<int, XDFStreamInfo> streamInfos,
    int chunkSize = 100,
    int boundaryInterval = 1000,
  }) async {
    final file = File(filePath);
    final buffer = BytesBuilder();
    
    // Write magic code
    buffer.add(utf8.encode(_magicCode));
    
    // Write file header
    _writeFileHeader(buffer);
    
    // Write stream headers for all streams
    for (final streamId in streamInfos.keys) {
      _writeStreamHeader(buffer, streamId, streamInfos[streamId]!);
    }
    
    // Write samples for all streams (interleaved by timestamp)
    _writeInterleavedSamples(buffer, streams, streamInfos, chunkSize, boundaryInterval);
    
    // Write stream footers for all streams
    for (final streamId in streams.keys) {
      if (streams[streamId]!.isNotEmpty) {
        _writeStreamFooter(buffer, streamId, streams[streamId]!);
      }
    }
    
    // Write to file
    await file.writeAsBytes(buffer.toBytes());
  }

  /// Write XDF file for a single stream (convenience method)
  static Future<void> writeXDFSingleStream({
    required String filePath,
    required List<XDFSample> samples,
    required XDFStreamInfo streamInfo,
    int streamId = 1,
    int chunkSize = 100,
    int boundaryInterval = 1000,
  }) async {
    await writeXDF(
      filePath: filePath,
      streams: {streamId: samples},
      streamInfos: {streamId: streamInfo},
      chunkSize: chunkSize,
      boundaryInterval: boundaryInterval,
    );
  }

  /// Write file header chunk
  static void _writeFileHeader(BytesBuilder buffer) {
    const xml = '''<?xml version="1.0"?>
<info>
    <version>1.0</version>
</info>''';
    
    _writeChunk(buffer, _tagFileHeader, utf8.encode(xml));
  }

  /// Write stream header chunk
  static void _writeStreamHeader(
    BytesBuilder buffer,
    int streamId,
    XDFStreamInfo streamInfo,
  ) {
    final xml = streamInfo.generateStreamHeaderXML();
    
    final content = BytesBuilder();
    content.add(_int32ToBytes(streamId)); // Stream ID
    content.add(utf8.encode(xml));
    
    _writeChunk(buffer, _tagStreamHeader, content.toBytes());
  }

  /// Write samples for multiple streams, interleaving by timestamp
  static void _writeInterleavedSamples(
    BytesBuilder buffer,
    Map<int, List<XDFSample>> streams,
    Map<int, XDFStreamInfo> streamInfos,
    int chunkSize,
    int boundaryInterval,
  ) {
    // Create a list of all samples with their stream IDs, sorted by timestamp
    final allSamples = <({int streamId, XDFSample sample})>[];
    
    for (final entry in streams.entries) {
      final streamId = entry.key;
      final samples = entry.value;
      for (final sample in samples) {
        allSamples.add((streamId: streamId, sample: sample));
      }
    }
    
    // Sort by timestamp
    allSamples.sort((a, b) => a.sample.timestamp.compareTo(b.sample.timestamp));
    
    // Group samples by stream and write in chunks
    final streamChunks = <int, List<XDFSample>>{};
    int sampleCount = 0;
    
    for (final item in allSamples) {
      final streamId = item.streamId;
      final sample = item.sample;
      
      streamChunks.putIfAbsent(streamId, () => []);
      streamChunks[streamId]!.add(sample);
      
      // Check if we should write chunks for any stream
      if (streamChunks[streamId]!.length >= chunkSize) {
        _writeSampleChunk(buffer, streamId, streamChunks[streamId]!, streamInfos[streamId]!);
        streamChunks[streamId]!.clear();
      }
      
      sampleCount++;
      
      // Write boundary chunk
      if (sampleCount % boundaryInterval == 0) {
        _writeBoundaryChunk(buffer);
      }
    }
    
    // Write remaining samples in chunks
    for (final entry in streamChunks.entries) {
      if (entry.value.isNotEmpty) {
        _writeSampleChunk(buffer, entry.key, entry.value, streamInfos[entry.key]!);
      }
    }
  }

  /// Write a single sample chunk
  static void _writeSampleChunk(
    BytesBuilder buffer,
    int streamId,
    List<XDFSample> samples,
    XDFStreamInfo streamInfo,
  ) {
    final content = BytesBuilder();
    
    // Stream ID
    content.add(_int32ToBytes(streamId));
    
    // Number of samples (variable length integer)
    content.add(_variableLengthInt(samples.length));
    
    // Write each sample
    for (final sample in samples) {
      _writeSample(content, sample, streamInfo);
    }
    
    _writeChunk(buffer, _tagSamples, content.toBytes());
  }

  /// Write a single sample with proper data type handling
  static void _writeSample(BytesBuilder content, XDFSample sample, XDFStreamInfo streamInfo) {
    // Timestamp bytes (8 indicates timestamp present)
    content.add([8]);
    
    // Timestamp (double, 8 bytes, little endian)
    content.add(_doubleToBytes(sample.timestamp));
    
    // Sample data based on channel format
    switch (streamInfo.channelFormat) {
      case XDFDataType.string:
        _writeStringSample(content, sample.data);
        break;
      case XDFDataType.float32:
        _writeFloat32Sample(content, sample.data);
        break;
      case XDFDataType.double64:
        _writeDouble64Sample(content, sample.data);
        break;
      case XDFDataType.int8:
        _writeInt8Sample(content, sample.data);
        break;
      case XDFDataType.int16:
        _writeInt16Sample(content, sample.data);
        break;
      case XDFDataType.int32:
        _writeInt32Sample(content, sample.data);
        break;
      case XDFDataType.int64:
        _writeInt64Sample(content, sample.data);
        break;
    }
  }

  /// Write string sample data
  static void _writeStringSample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final stringValue = value.toString();
      final stringBytes = utf8.encode(stringValue);
      content.add(_variableLengthInt(stringBytes.length));
      content.add(stringBytes);
    }
  }

  /// Write float32 sample data
  static void _writeFloat32Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final floatValue = value is num ? value.toDouble() : 0.0;
      content.add(_float32ToBytes(floatValue));
    }
  }

  /// Write double64 sample data
  static void _writeDouble64Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final doubleValue = value is num ? value.toDouble() : 0.0;
      content.add(_doubleToBytes(doubleValue));
    }
  }

  /// Write int8 sample data
  static void _writeInt8Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final intValue = value is num ? value.toInt() : 0;
      content.add([intValue & 0xFF]);
    }
  }

  /// Write int16 sample data
  static void _writeInt16Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final intValue = value is num ? value.toInt() : 0;
      content.add(_int16ToBytes(intValue));
    }
  }

  /// Write int32 sample data
  static void _writeInt32Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final intValue = value is num ? value.toInt() : 0;
      content.add(_int32ToBytes(intValue));
    }
  }

  /// Write int64 sample data
  static void _writeInt64Sample(BytesBuilder content, List<dynamic> data) {
    for (final value in data) {
      final intValue = value is num ? value.toInt() : 0;
      content.add(_int64ToBytes(intValue));
    }
  }

  /// Write stream footer chunk
  static void _writeStreamFooter(
    BytesBuilder buffer,
    int streamId,
    List<XDFSample> samples,
  ) {
    if (samples.isEmpty) return;
    
    final firstTimestamp = samples.first.timestamp;
    final lastTimestamp = samples.last.timestamp;
    final sampleCount = samples.length;
    
    // Calculate measured sample rate
    double measuredSampleRate = 0.0;
    if (samples.length > 1) {
      final duration = lastTimestamp - firstTimestamp;
      if (duration > 0) {
        measuredSampleRate = (samples.length - 1) / duration;
      }
    }
    
    final xml = '''<?xml version="1.0"?>
<info>
    <first_timestamp>$firstTimestamp</first_timestamp>
    <last_timestamp>$lastTimestamp</last_timestamp>
    <sample_count>$sampleCount</sample_count>
    <measured_srate>$measuredSampleRate</measured_srate>
</info>''';

    final content = BytesBuilder();
    content.add(_int32ToBytes(streamId));
    content.add(utf8.encode(xml));
    
    _writeChunk(buffer, _tagStreamFooter, content.toBytes());
  }

  /// Write boundary chunk for seeking
  static void _writeBoundaryChunk(BytesBuilder buffer) {
    // Generate 16-byte UUID for boundary
    final uuid = _generateBinaryUID();
    _writeChunk(buffer, _tagBoundary, uuid);
  }

  /// Write a generic chunk with tag and content
  static void _writeChunk(BytesBuilder buffer, int tag, List<int> content) {
    final length = content.length;
    
    // Determine number of bytes needed for length
    int lengthBytes;
    if (length <= 0xFF) {
      lengthBytes = 1;
    } else if (length <= 0xFFFFFFFF) {
      lengthBytes = 4;
    } else {
      lengthBytes = 8;
    }
    
    // Write NumLengthBytes
    buffer.add([lengthBytes]);
    
    // Write Length
    if (lengthBytes == 1) {
      buffer.add([length]);
    } else if (lengthBytes == 4) {
      buffer.add(_int32ToBytes(length));
    } else {
      buffer.add(_int64ToBytes(length));
    }
    
    // Write Tag (2 bytes, little endian)
    buffer.add(_int16ToBytes(tag));
    
    // Write Content
    buffer.add(content);
  }

  // Byte conversion methods (little endian)
  
  /// Convert int8 to bytes
  static List<int> _int8ToBytes(int value) {
    return [value & 0xFF];
  }

  /// Convert int16 to little endian bytes
  static List<int> _int16ToBytes(int value) {
    final data = ByteData(2);
    data.setInt16(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Convert int32 to little endian bytes
  static List<int> _int32ToBytes(int value) {
    final data = ByteData(4);
    data.setInt32(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Convert int64 to little endian bytes
  static List<int> _int64ToBytes(int value) {
    final data = ByteData(8);
    data.setInt64(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Convert float32 to little endian bytes
  static List<int> _float32ToBytes(double value) {
    final data = ByteData(4);
    data.setFloat32(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Convert double64 to little endian bytes
  static List<int> _doubleToBytes(double value) {
    final data = ByteData(8);
    data.setFloat64(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Encode variable length integer
  static List<int> _variableLengthInt(int value) {
    if (value <= 0xFF) {
      return [1, value];
    } else if (value <= 0xFFFFFFFF) {
      return [4, ...(_int32ToBytes(value))];
    } else {
      return [8, ...(_int64ToBytes(value))];
    }
  }

  /// Generate 16-byte binary UID for boundary chunks
  static List<int> _generateBinaryUID() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final bytes = List<int>.filled(16, 0);
    
    // Fill with timestamp and some pseudo-random data
    final timestampBytes = _int64ToBytes(timestamp);
    for (int i = 0; i < 8; i++) {
      bytes[i] = timestampBytes[i];
    }
    
    // Fill remaining bytes with pseudo-random data
    for (int i = 8; i < 16; i++) {
      bytes[i] = (timestamp + i) % 256;
    }
    
    return bytes;
  }
}
