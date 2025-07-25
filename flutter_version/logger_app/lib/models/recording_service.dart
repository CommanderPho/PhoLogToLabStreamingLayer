import 'dart:io';
import 'dart:convert';
import 'dart:async';
import 'log_entry.dart';
import 'xdf_writer.dart';

class RecordingService {
  bool _isRecording = false;
  String? _currentFilePath;
  final List<Map<String, dynamic>> _recordedData = [];
  final List<Map<String, dynamic>> _unsavedData = [];
  DateTime? _recordingStartTime;
  Timer? _backupTimer;
  Timer? _writeTimer;
  bool _isWriting = false;
  int _lastSavedIndex = 0;
  
  Future<void> startRecording(String filePath) async {
    try {
      _currentFilePath = filePath;
      _recordedData.clear();
      _unsavedData.clear();
      _recordingStartTime = DateTime.now();
      _isRecording = true;
      _lastSavedIndex = 0;
      
      // Create initial empty file structure
      await _writeInitialFile();
      
      // Create backup timer to save data every 30 seconds as safety net
      _backupTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
        _saveBackup();
      });
      
      print('Recording started: $filePath');
      
    } catch (e) {
      throw Exception('Failed to start recording: $e');
    }
  }

  Future<String?> stopRecording() async {
    if (!_isRecording || _currentFilePath == null) {
      return null;
    }
    
    try {
      _isRecording = false;
      _backupTimer?.cancel();
      _writeTimer?.cancel();
      
      // Force final write of any unsaved data
      await _flushPendingWrites();
      
      // Finalize recording file
      final savedPath = await _finalizeRecordingFile();
      
      // Clean up backup file
      await _cleanupBackup();
      
      print('Recording stopped and saved: $savedPath');
      return savedPath;
      
    } catch (e) {
      throw Exception('Failed to stop recording: $e');
    }
  }

  Future<void> recordMessage(String message, DateTime timestamp) async {
    if (!_isRecording) return;
    
    try {
      final dataPoint = {
        'sample': [message],
        'timestamp': timestamp.millisecondsSinceEpoch / 1000.0,
        'readable_timestamp': timestamp.toIso8601String(),
      };
      
      _recordedData.add(dataPoint);
      _unsavedData.add(dataPoint);
      
      // Schedule async write with 3-second delay (debounced)
      _scheduleAsyncWrite();
      
    } catch (e) {
      print('Error recording message: $e');
    }
  }

  /// Schedule an async write with debouncing
  void _scheduleAsyncWrite() {
    // Cancel any existing timer
    _writeTimer?.cancel();
    
    // Schedule new write after 3 seconds
    _writeTimer = Timer(const Duration(seconds: 3), () {
      _performAsyncWrite();
    });
  }

  /// Perform the actual async write
  Future<void> _performAsyncWrite() async {
    if (_isWriting || _unsavedData.isEmpty || !_isRecording) return;
    
    try {
      _isWriting = true;
      await _writeIncrementalData();
      _unsavedData.clear();
    } catch (e) {
      print('Error in async write: $e');
    } finally {
      _isWriting = false;
    }
  }

  /// Flush any pending writes immediately
  Future<void> _flushPendingWrites() async {
    _writeTimer?.cancel();
    if (_unsavedData.isNotEmpty) {
      await _performAsyncWrite();
    }
  }

  /// Write initial file structure
  Future<void> _writeInitialFile() async {
    if (_currentFilePath == null) return;
    
    try {
      await Directory(_currentFilePath!).parent.create(recursive: true);
      
      // Create initial file with header
      final isXdfFormat = _currentFilePath!.toLowerCase().endsWith('.xdf');
      
      if (isXdfFormat) {
        await _writeInitialXDF();
      } else {
        await _writeInitialJSON();
      }
      
      print('Initial file structure created');
    } catch (e) {
      print('Error creating initial file: $e');
    }
  }

  /// Write incremental data to existing file
  Future<void> _writeIncrementalData() async {
    if (_currentFilePath == null || _unsavedData.isEmpty) return;
    
    try {
      final isXdfFormat = _currentFilePath!.toLowerCase().endsWith('.xdf');
      
      if (isXdfFormat) {
        await _appendToXDF();
      } else {
        await _updateJSON();
      }
      
      // Always update CSV incrementally
      await _appendToCSV();
      
      _lastSavedIndex = _recordedData.length;
      print('Incremental write completed: ${_unsavedData.length} samples');
      
    } catch (e) {
      print('Error in incremental write: $e');
    }
  }

  Future<String> _finalizeRecordingFile() async {
    if (_currentFilePath == null) {
      throw Exception('No current file path');
    }
    
    try {
      await Directory(_currentFilePath!).parent.create(recursive: true);
      
      // Determine file format based on extension
      final isXdfFormat = _currentFilePath!.toLowerCase().endsWith('.xdf');
      
      if (isXdfFormat) {
        // Save as XDF binary format
        await _saveAsXDF();
      } else {
        // Save as JSON format (fallback)
        await _saveAsJSON();
      }
      
      // Also save as CSV for easy reading
      await _saveEventsCSV();
      
      return _currentFilePath!;
      
    } catch (e) {
      throw Exception('Failed to save recording file: $e');
    }
  }

  Future<void> _saveAsXDF() async {
    final streamInfo = {
      'name': 'TextLogger',
      'type': 'Markers',
      'source_id': 'textlogger_001',
      'manufacturer': 'PhoLogToLabStreamingLayer',
      'hostname': 'flutter_app',
      'uid': 'flutter-${DateTime.now().millisecondsSinceEpoch}',
    };
    
    await XDFWriter.writeXDF(
      filePath: _currentFilePath!,
      recordedData: _recordedData,
      streamInfo: streamInfo,
    );
    
    print('XDF file saved: $_currentFilePath');
  }

  Future<void> _saveAsJSON() async {
    final file = File(_currentFilePath!);
    
    // Create recording metadata
    final recordingData = {
      'metadata': {
        'stream_name': 'TextLogger',
        'stream_type': 'Markers',
        'channel_count': 1,
        'source_id': 'textlogger_001',
        'manufacturer': 'PhoLogToLabStreamingLayer',
        'version': '1.0',
        'recording_start_time': _recordingStartTime?.toIso8601String(),
        'recording_end_time': DateTime.now().toIso8601String(),
        'sample_count': _recordedData.length,
      },
      'data': _recordedData,
    };
    
    // Save as JSON
    final jsonString = const JsonEncoder.withIndent('  ').convert(recordingData);
    await file.writeAsString(jsonString);
    
    print('JSON file saved: $_currentFilePath');
  }

  Future<void> _saveEventsCSV() async {
    if (_currentFilePath == null) return;
    
    try {
      // Create CSV path by replacing extension
      String csvPath = _currentFilePath!;
      if (csvPath.toLowerCase().endsWith('.xdf')) {
        csvPath = csvPath.substring(0, csvPath.length - 4) + '_events.csv';
      } else if (csvPath.toLowerCase().endsWith('.json')) {
        csvPath = csvPath.substring(0, csvPath.length - 5) + '_events.csv';
      } else {
        csvPath = '$csvPath.events.csv';
      }
      
      final csvFile = File(csvPath);
      
      final buffer = StringBuffer();
      buffer.writeln('Timestamp,LSL_Time,Message');
      
      for (final dataPoint in _recordedData) {
        final message = dataPoint['sample'][0];
        final lslTime = dataPoint['timestamp'];
        final readableTime = dataPoint['readable_timestamp'];
        
        // Escape CSV values
        final escapedMessage = message.toString().replaceAll('"', '""');
        buffer.writeln('"$readableTime",$lslTime,"$escapedMessage"');
      }
      
      await csvFile.writeAsString(buffer.toString());
      print('Events CSV saved: $csvPath');
      
    } catch (e) {
      print('Error saving CSV: $e');
    }
  }

  Future<void> _saveBackup() async {
    if (!_isRecording || _currentFilePath == null) return;
    
    try {
      final backupPath = '${_currentFilePath!}.backup';
      final backupFile = File(backupPath);
      
      final backupData = {
        'recorded_data': _recordedData,
        'recording_start_time': _recordingStartTime?.toIso8601String(),
        'sample_count': _recordedData.length,
      };
      
      final jsonString = jsonEncode(backupData);
      await backupFile.writeAsString(jsonString);
      
    } catch (e) {
      print('Error saving backup: $e');
    }
  }

  Future<void> _cleanupBackup() async {
    if (_currentFilePath == null) return;
    
    try {
      final backupPath = '${_currentFilePath!}.backup';
      final backupFile = File(backupPath);
      
      if (await backupFile.exists()) {
        await backupFile.delete();
      }
    } catch (e) {
      print('Error cleaning up backup: $e');
    }
  }

  Future<void> checkForRecovery() async {
    // Implementation for checking and recovering from backup files
    // This would scan for .backup files and offer recovery options
  }

  bool get isRecording => _isRecording;
  int get sampleCount => _recordedData.length;

  /// Write initial XDF file structure
  Future<void> _writeInitialXDF() async {
    final streamInfo = {
      'name': 'TextLogger',
      'type': 'Markers',
      'source_id': 'textlogger_001',
      'manufacturer': 'PhoLogToLabStreamingLayer',
      'hostname': 'flutter_app',
      'uid': 'flutter-${DateTime.now().millisecondsSinceEpoch}',
    };
    
    // Create initial XDF with empty data
    await XDFWriter.writeXDF(
      filePath: _currentFilePath!,
      recordedData: [],
      streamInfo: streamInfo,
    );
  }

  /// Write initial JSON file structure
  Future<void> _writeInitialJSON() async {
    final file = File(_currentFilePath!);
    
    final recordingData = {
      'metadata': {
        'stream_name': 'TextLogger',
        'stream_type': 'Markers',
        'channel_count': 1,
        'source_id': 'textlogger_001',
        'manufacturer': 'PhoLogToLabStreamingLayer',
        'version': '1.0',
        'recording_start_time': _recordingStartTime?.toIso8601String(),
        'sample_count': 0,
      },
      'data': [],
    };
    
    final jsonString = const JsonEncoder.withIndent('  ').convert(recordingData);
    await file.writeAsString(jsonString);
  }

  /// Append new data to XDF file
  Future<void> _appendToXDF() async {
    // For XDF, we need to rewrite the entire file with new data
    // This is because XDF doesn't support true appending due to its binary structure
    final streamInfo = {
      'name': 'TextLogger',
      'type': 'Markers',
      'source_id': 'textlogger_001',
      'manufacturer': 'PhoLogToLabStreamingLayer',
      'hostname': 'flutter_app',
      'uid': 'flutter-${DateTime.now().millisecondsSinceEpoch}',
    };
    
    await XDFWriter.writeXDF(
      filePath: _currentFilePath!,
      recordedData: _recordedData,
      streamInfo: streamInfo,
    );
  }

  /// Update JSON file with new data
  Future<void> _updateJSON() async {
    final file = File(_currentFilePath!);
    
    final recordingData = {
      'metadata': {
        'stream_name': 'TextLogger',
        'stream_type': 'Markers',
        'channel_count': 1,
        'source_id': 'textlogger_001',
        'manufacturer': 'PhoLogToLabStreamingLayer',
        'version': '1.0',
        'recording_start_time': _recordingStartTime?.toIso8601String(),
        'recording_end_time': DateTime.now().toIso8601String(),
        'sample_count': _recordedData.length,
      },
      'data': _recordedData,
    };
    
    final jsonString = const JsonEncoder.withIndent('  ').convert(recordingData);
    await file.writeAsString(jsonString);
  }

  /// Append new data to CSV file (true incremental)
  Future<void> _appendToCSV() async {
    if (_currentFilePath == null || _unsavedData.isEmpty) return;
    
    try {
      // Create CSV path
      String csvPath = _currentFilePath!;
      if (csvPath.toLowerCase().endsWith('.xdf')) {
        csvPath = csvPath.substring(0, csvPath.length - 4) + '_events.csv';
      } else if (csvPath.toLowerCase().endsWith('.json')) {
        csvPath = csvPath.substring(0, csvPath.length - 5) + '_events.csv';
      } else {
        csvPath = '$csvPath.events.csv';
      }
      
      final csvFile = File(csvPath);
      final buffer = StringBuffer();
      
      // Write header if file doesn't exist
      if (!await csvFile.exists()) {
        buffer.writeln('Timestamp,LSL_Time,Message');
      }
      
      // Append only unsaved data
      for (final dataPoint in _unsavedData) {
        final message = dataPoint['sample'][0];
        final lslTime = dataPoint['timestamp'];
        final readableTime = dataPoint['readable_timestamp'];
        
        // Escape CSV values
        final escapedMessage = message.toString().replaceAll('"', '""');
        buffer.writeln('"$readableTime",$lslTime,"$escapedMessage"');
      }
      
      // Append to file
      await csvFile.writeAsString(buffer.toString(), mode: FileMode.append);
      
    } catch (e) {
      print('Error appending to CSV: $e');
    }
  }

  void dispose() {
    _backupTimer?.cancel();
    _writeTimer?.cancel();
    _isRecording = false;
    print('Recording Service disposed');
  }
}
