import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'dart:async';
import 'dart:convert';
import 'models/lsl_service.dart';
import 'models/recording_service.dart';
import 'models/log_entry.dart';

void main() {
  runApp(const LoggerApp());
}

class LoggerApp extends StatelessWidget {
  const LoggerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'LSL Logger with XDF Recording',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const LoggerHomePage(),
    );
  }
}

class LoggerHomePage extends StatefulWidget {
  const LoggerHomePage({super.key});

  @override
  State<LoggerHomePage> createState() => _LoggerHomePageState();
}

class _LoggerHomePageState extends State<LoggerHomePage> {
  final TextEditingController _messageController = TextEditingController();
  final FocusNode _messageFocusNode = FocusNode();
  final LSLService _lslService = LSLService();
  final RecordingService _recordingService = RecordingService();
  final List<LogEntry> _logHistory = [];
  
  bool _isRecording = false;
  String _lslStatus = 'Initializing...';
  String _recordingStatus = 'Not Recording';
  String _statusInfo = 'Ready';
  String? _currentRecordingFile;

  @override
  void initState() {
    super.initState();
    _initializeServices();
    
    // Focus the message field when app starts
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _messageFocusNode.requestFocus();
    });
  }

  Future<void> _initializeServices() async {
    try {
      await _lslService.initialize();
      setState(() {
        _lslStatus = 'Connected';
      });
      
      // Auto-start recording after a delay
      Timer(const Duration(milliseconds: 1000), () {
        _autoStartRecording();
      });
    } catch (e) {
      setState(() {
        _lslStatus = 'Error: $e';
      });
    }
  }

  Future<void> _autoStartRecording() async {
    try {
      final documentsDir = await getApplicationDocumentsDirectory();
      final defaultFolder = Directory('${documentsDir.path}/PhoLogToLabStreamingLayer_logs');
      await defaultFolder.create(recursive: true);
      
      final timestamp = DateTime.now().toIso8601String().replaceAll(':', '-').substring(0, 19);
      final filename = '${timestamp}_log.xdf';
      final filepath = '${defaultFolder.path}/$filename';
      
      await _recordingService.startRecording(filepath);
      
      setState(() {
        _isRecording = true;
        _recordingStatus = 'Recording...';
        _currentRecordingFile = filename;
        _statusInfo = 'Auto-recording to: $filename';
      });
      
      _addLogEntry('XDF Recording auto-started');
      await _sendLSLMessage('RECORDING_AUTO_STARTED: $filename');
    } catch (e) {
      _addLogEntry('Auto-start failed: $e');
    }
  }

  Future<void> _startRecording() async {
    try {
      final documentsDir = await getApplicationDocumentsDirectory();
      final defaultFolder = Directory('${documentsDir.path}/PhoLogToLabStreamingLayer_logs');
      await defaultFolder.create(recursive: true);
      
      final timestamp = DateTime.now().toIso8601String().replaceAll(':', '-').substring(0, 19);
      final filename = '${timestamp}_log.xdf';
      final filePath = '${defaultFolder.path}/$filename';
      
      await _recordingService.startRecording(filePath);
      
      setState(() {
        _isRecording = true;
        _recordingStatus = 'Recording...';
        _currentRecordingFile = filename;
        _statusInfo = 'Recording to: $filename';
      });
      
      _addLogEntry('XDF Recording started');
      _showSuccessSnackBar('Recording started');
    } catch (e) {
      _showErrorSnackBar('Failed to start recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      await _sendLSLMessage('RECORDING_STOPPED: $_currentRecordingFile');
      
      final savedPath = await _recordingService.stopRecording();
      
      setState(() {
        _isRecording = false;
        _recordingStatus = 'Not Recording';
        _statusInfo = 'Ready';
        _currentRecordingFile = null;
      });
      
      _addLogEntry('XDF Recording stopped and saved');
      if (savedPath != null) {
        _showSuccessSnackBar('Recording saved successfully');
      }
    } catch (e) {
      _showErrorSnackBar('Failed to stop recording: $e');
    }
  }

  Future<void> _splitRecording() async {
    if (!_isRecording) return;
    
    try {
      await _stopRecording();
      
      // Wait a moment then start new recording
      Timer(const Duration(milliseconds: 100), () async {
        await _autoStartRecording();
        _addLogEntry('Recording split to new file');
      });
    } catch (e) {
      _addLogEntry('Split recording failed: $e');
    }
  }

  Future<void> _sendLSLMessage(String message) async {
    try {
      await _lslService.sendMessage(message);
      await _recordingService.recordMessage(message, DateTime.now());
    } catch (e) {
      _showErrorSnackBar('Failed to send LSL message: $e');
    }
  }

  void _logMessage() async {
    final message = _messageController.text.trim();
    
    if (message.isEmpty) {
      _showWarningSnackBar('Please enter a message to log');
      return;
    }
    
    await _sendLSLMessage(message);
    _addLogEntry(message);
    
    _messageController.clear();
    
    // Maintain focus on the text field
    _messageFocusNode.requestFocus();
  }

  void _addLogEntry(String message) {
    setState(() {
      _logHistory.add(LogEntry(
        message: message,
        timestamp: DateTime.now(),
      ));
    });
  }

  void _clearLogDisplay() {
    setState(() {
      _logHistory.clear();
    });
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red.shade600,
        duration: const Duration(seconds: 4),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Dismiss',
          textColor: Colors.white,
          onPressed: () => ScaffoldMessenger.of(context).hideCurrentSnackBar(),
        ),
      ),
    );
  }

  void _showWarningSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.orange.shade600,
        duration: const Duration(seconds: 3),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green.shade600,
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('LSL Logger with XDF Recording'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // LSL Status
            Container(
              padding: const EdgeInsets.all(8.0),
              decoration: BoxDecoration(
                color: _lslStatus.contains('Error') ? Colors.red.shade100 : 
                       _lslStatus == 'Connected' ? Colors.green.shade100 : Colors.orange.shade100,
                borderRadius: BorderRadius.circular(4.0),
              ),
              child: Text('LSL Status: $_lslStatus'),
            ),
            
            const SizedBox(height: 16),
            
            // Recording Control
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('XDF Recording', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _isRecording ? Colors.green.shade100 : Colors.red.shade100,
                            borderRadius: BorderRadius.circular(4.0),
                          ),
                          child: Text(_recordingStatus),
                        ),
                        const SizedBox(width: 16),
                        ElevatedButton(
                          onPressed: _isRecording ? null : _startRecording,
                          child: const Text('Start Recording'),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: _isRecording ? _stopRecording : null,
                          child: const Text('Stop Recording'),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: _isRecording ? _splitRecording : null,
                          child: const Text('Split Recording'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Message Input
            Row(
              children: [
                const Text('Message: '),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    focusNode: _messageFocusNode,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      hintText: 'Enter message to log',
                    ),
                    onSubmitted: (_) => _logMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _logMessage,
                  child: const Text('Log'),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // Log History
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Log History:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                TextButton(
                  onPressed: _clearLogDisplay,
                  child: const Text('Clear Log Display'),
                ),
              ],
            ),
            
            const SizedBox(height: 8),
            
            // Log Display
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(4.0),
                ),
                child: ListView.builder(
                  itemCount: _logHistory.length,
                  itemBuilder: (context, index) {
                    final entry = _logHistory[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 2.0),
                      child: Text(
                        '[${entry.timestamp.toString().substring(0, 19)}] ${entry.message}',
                        style: const TextStyle(fontFamily: 'monospace'),
                      ),
                    );
                  },
                ),
              ),
            ),
            
            const SizedBox(height: 8),
            
            // Status Info
            Text(_statusInfo, style: const TextStyle(fontStyle: FontStyle.italic)),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _messageFocusNode.dispose();
    _lslService.dispose();
    _recordingService.dispose();
    super.dispose();
  }
}
