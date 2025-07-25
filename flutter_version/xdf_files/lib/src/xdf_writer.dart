import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';

/// XDF (Extensible Data Format) Writer for Lab Streaming Layer data
/// Based on XDF Specification 1.0: https://github.com/sccn/xdf/wiki/Specifications
class XDFWriter {
  static const String _magicCode = 'XDF:';
  
  // Chunk tags as defined in XDF specification
  static const int _tagFileHeader = 1;
  static const int _tagStreamHeader = 2;
  static const int _tagSamples = 3;
  static const int _tagClockOffset = 4;
  static const int _tagBoundary = 5;
  static const int _tagStreamFooter = 6;

  /// Write XDF file with LSL text logger data
  static Future<void> writeXDF({
    required String filePath,
    required List<Map<String, dynamic>> recordedData,
    required Map<String, dynamic> streamInfo,
  }) async {
    final file = File(filePath);
    final buffer = BytesBuilder();
    
    // Write magic code
    buffer.add(utf8.encode(_magicCode));
    
    // Write file header
    _writeFileHeader(buffer);
    
    // Write stream header
    final streamId = 1; // Use stream ID 1 for text logger
    _writeStreamHeader(buffer, streamId, streamInfo);
    
    // Write samples in chunks
    _writeSampleChunks(buffer, streamId, recordedData);
    
    // Write stream footer
    _writeStreamFooter(buffer, streamId, recordedData);
    
    // Write to file
    await file.writeAsBytes(buffer.toBytes());
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
    Map<String, dynamic> streamInfo,
  ) {
    final xml = '''<?xml version="1.0"?>
<info>
    <n>${streamInfo['name'] ?? 'TextLogger'}</n>
    <type>${streamInfo['type'] ?? 'Markers'}</type>
    <channel_count>1</channel_count>
    <nominal_srate>0</nominal_srate>
    <channel_format>string</channel_format>
    <source_id>${streamInfo['source_id'] ?? 'textlogger_001'}</source_id>
    <version>1.0</version>
    <created_at>${DateTime.now().millisecondsSinceEpoch / 1000.0}</created_at>
    <uid>${streamInfo['uid'] ?? _generateUID()}</uid>
    <session_id>default</session_id>
    <hostname>${streamInfo['hostname'] ?? 'flutter_app'}</hostname>
    <manufacturer>${streamInfo['manufacturer'] ?? 'PhoLogToLabStreamingLayer'}</manufacturer>
    <desc/>
</info>''';

    final content = BytesBuilder();
    content.add(_int32ToBytes(streamId)); // Stream ID
    content.add(utf8.encode(xml));
    
    _writeChunk(buffer, _tagStreamHeader, content.toBytes());
  }

  /// Write sample chunks
  static void _writeSampleChunks(
    BytesBuilder buffer,
    int streamId,
    List<Map<String, dynamic>> recordedData,
  ) {
    // Write samples in chunks of 100 to keep file structure reasonable
    const chunkSize = 100;
    
    for (int i = 0; i < recordedData.length; i += chunkSize) {
      final endIndex = (i + chunkSize < recordedData.length) 
          ? i + chunkSize 
          : recordedData.length;
      
      final chunkData = recordedData.sublist(i, endIndex);
      _writeSampleChunk(buffer, streamId, chunkData);
      
      // Write boundary chunk every 1000 samples for seeking
      if ((i + chunkSize) % 1000 == 0) {
        _writeBoundaryChunk(buffer);
      }
    }
  }

  /// Write a single sample chunk
  static void _writeSampleChunk(
    BytesBuilder buffer,
    int streamId,
    List<Map<String, dynamic>> samples,
  ) {
    final content = BytesBuilder();
    
    // Stream ID
    content.add(_int32ToBytes(streamId));
    
    // Number of samples (variable length integer)
    content.add(_variableLengthInt(samples.length));
    
    // Write each sample
    for (final sample in samples) {
      _writeSample(content, sample);
    }
    
    _writeChunk(buffer, _tagSamples, content.toBytes());
  }

  /// Write a single sample
  static void _writeSample(BytesBuilder content, Map<String, dynamic> sample) {
    // Timestamp bytes (8 indicates timestamp present)
    content.add([8]);
    
    // Timestamp (double, 8 bytes, little endian)
    final timestamp = sample['timestamp'] as double;
    content.add(_doubleToBytes(timestamp));
    
    // String value (variable length)
    final message = sample['sample'][0] as String;
    final messageBytes = utf8.encode(message);
    content.add(_variableLengthInt(messageBytes.length));
    content.add(messageBytes);
  }

  /// Write stream footer chunk
  static void _writeStreamFooter(
    BytesBuilder buffer,
    int streamId,
    List<Map<String, dynamic>> recordedData,
  ) {
    if (recordedData.isEmpty) return;
    
    final firstTimestamp = recordedData.first['timestamp'] as double;
    final lastTimestamp = recordedData.last['timestamp'] as double;
    
    final xml = '''<?xml version="1.0"?>
<info>
    <first_timestamp>$firstTimestamp</first_timestamp>
    <last_timestamp>$lastTimestamp</last_timestamp>
    <sample_count>${recordedData.length}</sample_count>
    <measured_srate>0</measured_srate>
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

  /// Convert int16 to little endian bytes
  static List<int> _int16ToBytes(int value) {
    final data = ByteData(2);
    data.setInt16(0, value, Endian.little);
    return data.buffer.asUint8List();
  }

  /// Convert double to little endian bytes
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

  /// Generate a simple UID string
  static String _generateUID() {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final random = (timestamp % 0xFFFFFFFF).toRadixString(16);
    return '$timestamp-$random-flutter-xdf';
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
