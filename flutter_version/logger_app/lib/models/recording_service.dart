import 'dart:io';
import 'dart:convert';
import 'dart:async';
import 'log_entry.dart';
import 'xdf_writer.dart';

class RecordingService {
  bool _isRecording = false;
  String? _currentFilePath;
  final List<Map<String, dynamic>> _recordedData = [];
  DateTime? _recordingStartTime;
  Timer? _backupTimer;
  
  Future<void> startRecording(String filePath) async {
    try {
      _currentFilePath = filePath;
      _recordedData.clear();
      _recordingStartTime = DateTime.now();
      _isRecording = true;
      
      // Create backup timer to save data every 10 seconds
      _backupTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
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
      
      // Save final recording file
      final savedPath = await _saveRecordingFile();
      
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
      
    } catch (e) {
      print('Error recording message: $e');
    }
  }

  Future<String> _saveRecordingFile() async {
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

  void dispose() {
    _backupTimer?.cancel();
    _isRecording = false;
    print('Recording Service disposed');
  }
}
