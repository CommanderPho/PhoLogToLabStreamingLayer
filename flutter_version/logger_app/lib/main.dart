import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'dart:async';
import 'models/lsl_service.dart';
import 'models/recording_service.dart';
import 'models/log_entry.dart';
import 'models/eventboard_config.dart';

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
  final ScrollController _logScrollController = ScrollController();
  
  bool _isRecording = false;
  String _lslStatus = 'Initializing...';
  String _recordingStatus = 'Not Recording';
  String _statusInfo = 'Ready';
  String? _currentRecordingFile;
  String? _recordingDirectory;
  EventBoardConfig? _eventBoardConfig;
  final Map<String, bool> _toggleStates = {};
  final Map<String, TextEditingController> _offsetControllers = {};

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
      // Load EventBoard configuration
      final cfg = await EventBoardConfigLoader.load();
      setState(() {
        _eventBoardConfig = cfg;
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
      
      _recordingDirectory = Platform.isWindows 
          ? defaultFolder.path.replaceAll('/', '\\')
          : defaultFolder.path;
      
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

  double _parseOffsetSeconds(String raw) {
    final s = raw.trim().toLowerCase();
    if (s.isEmpty) return 0;
    final regex = RegExp(r'^(\d+(?:\.\d+)?)\s*([smh]?)$');
    final m = regex.firstMatch(s);
    if (m == null) return 0;
    final value = double.tryParse(m.group(1)!) ?? 0;
    final unit = (m.group(2) ?? 's');
    switch (unit) {
      case 'm':
        return value * 60.0;
      case 'h':
        return value * 3600.0;
      default:
        return value;
    }
  }

  Future<void> _emitEventBoard(String id, EventButtonConfig btn) async {
    final now = DateTime.now();
    final offsetText = _offsetControllers[id]?.text ?? '';
    final offsetSec = _parseOffsetSeconds(offsetText);
    final actualTs = now.subtract(Duration(milliseconds: (offsetSec * 1000).round()));

    String message;
    if (btn.type == 'toggleable') {
      final current = _toggleStates[id] ?? false;
      final next = !current;
      _toggleStates[id] = next;
      if (next) {
        message = '${btn.eventName}_START|${btn.text}|${actualTs.toIso8601String()}|TOGGLE:true';
      } else {
        message = '${btn.eventName}_END|${btn.text}|${actualTs.toIso8601String()}|TOGGLE:false';
      }
    } else {
      message = '${btn.eventName}|${btn.text}|${actualTs.toIso8601String()}';
    }

    // Send to dedicated EventBoard outlet (real LSL)
    try {
      await _lslService.sendEvent(message);
    } catch (e) {
      // Fallback: still try to send via TextLogger to avoid data loss
      await _sendLSLMessage('EventBoardFallback|$message');
    }
    _addLogEntry('EventBoard: ${btn.text}${btn.type == 'toggleable' ? (_toggleStates[id]! ? ' ON' : ' OFF') : ''} (${btn.eventName}${btn.type == 'toggleable' ? (_toggleStates[id]! ? '_START' : '_END') : ''})${offsetSec > 0 ? ' [offset: -$offsetText]' : ''}');

    // Reset offset field placeholder behavior
    if (_offsetControllers[id] != null && (_offsetControllers[id]!.text).isNotEmpty) {
      // keep user-entered text; optional: clear after send
    }
    setState(() {});
  }

  Future<void> _startRecording() async {
    try {
      final documentsDir = await getApplicationDocumentsDirectory();
      final defaultFolder = Directory('${documentsDir.path}/PhoLogToLabStreamingLayer_logs');
      await defaultFolder.create(recursive: true);
      
      _recordingDirectory = Platform.isWindows 
          ? defaultFolder.path.replaceAll('/', '\\')
          : defaultFolder.path;
      
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
    // Ensure the log list scrolls to bottom after new entry is rendered
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_logScrollController.hasClients) {
        _logScrollController.animateTo(
          _logScrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
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

  Future<void> _openRecordingDirectory() async {
    try {
      String? directoryPath = _recordingDirectory;
      
      // If no directory set yet, use default
      if (directoryPath == null) {
        final documentsDir = await getApplicationDocumentsDirectory();
        directoryPath = '${documentsDir.path}/PhoLogToLabStreamingLayer_logs';
        await Directory(directoryPath).create(recursive: true);
        _recordingDirectory = directoryPath;
      }
      
      // Verify directory exists
      if (!await Directory(directoryPath).exists()) {
        await Directory(directoryPath).create(recursive: true);
      }
      
      // Open directory based on platform
      if (Platform.isWindows) {
        // Use the properly formatted Windows path
        await Process.run('explorer.exe', [directoryPath]);
        _showSuccessSnackBar('Opened recording directory');
      } else if (Platform.isMacOS) {
        await Process.run('open', [directoryPath]);
        _showSuccessSnackBar('Opened recording directory');
      } else if (Platform.isLinux) {
        await Process.run('xdg-open', [directoryPath]);
        _showSuccessSnackBar('Opened recording directory');
      } else {
        _showWarningSnackBar('Opening directories not supported on this platform');
      }
    } catch (e) {
      _showErrorSnackBar('Failed to open directory: $e');
    }
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
            // LSL Status with folder button
            Row(
              children: [
                IconButton(
                  onPressed: _openRecordingDirectory,
                  icon: const Icon(Icons.folder_open),
                  tooltip: 'Open Recording Directory',
                  iconSize: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.all(8.0),
                    decoration: BoxDecoration(
                      color: _lslStatus.contains('Error') ? Colors.red.shade100 : 
                             _lslStatus == 'Connected' ? Colors.green.shade100 : Colors.orange.shade100,
                      borderRadius: BorderRadius.circular(4.0),
                    ),
                    child: Text('LSL Status: $_lslStatus'),
                  ),
                ),
              ],
            ),
            
            const SizedBox(height: 16),
            
            // EventBoard UI
            if (_eventBoardConfig != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_eventBoardConfig!.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      LayoutBuilder(
                        builder: (context, constraints) {
                          // Create a 3x5 grid from config
                          final buttons = _eventBoardConfig!.buttons;
                          // Initialize controllers/states
                          for (final b in buttons) {
                            _toggleStates.putIfAbsent(b.id, () => false);
                            _offsetControllers.putIfAbsent(b.id, () => TextEditingController(text: '0s'));
                          }
                          return Column(
                            children: List.generate(3, (row) {
                              final rowButtons = buttons.where((b) => b.row == row + 1).toList()
                                ..sort((a, b) => a.col.compareTo(b.col));
                              return Row(
                                children: List.generate(5, (col) {
                                  final btn = rowButtons.firstWhere(
                                    (b) => b.col == col + 1,
                                    orElse: () => EventButtonConfig(
                                      id: 'empty_${row}_${col}', row: row + 1, col: col + 1,
                                      text: '', eventName: 'NONE', colorHex: '#EEEEEE', type: 'instantaneous'),
                                  );
                                  final isEmpty = btn.text.isEmpty;
                                  final color = parseHexColor(btn.colorHex);
                                  final editable = !isEmpty;
                                  final controller = _offsetControllers[btn.id]!;
                                  final isToggle = btn.type == 'toggleable';
                                  final onState = _toggleStates[btn.id] ?? false;
                                  return Expanded(
                                    child: Container(
                                      margin: const EdgeInsets.all(2),
                                      padding: const EdgeInsets.all(2),
                                      decoration: BoxDecoration(
                                        color: color,
                                        borderRadius: BorderRadius.circular(6),
                                        border: isToggle && onState ? Border.all(color: Colors.red, width: 2) : null,
                                      ),
                                      child: Row(
                                        children: [
                                          Expanded(
                                            flex: 4,
                                            child: ElevatedButton(
                                              style: ElevatedButton.styleFrom(
                                                backgroundColor: color,
                                                foregroundColor: Colors.white,
                                                elevation: 0,
                                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                                              ),
                                              onPressed: editable ? () => _emitEventBoard(btn.id, btn) : null,
                                              child: Align(
                                                alignment: Alignment.centerLeft,
                                                child: Text(
                                                  isToggle ? (onState ? '🔴 ${btn.text}' : '🔘 ${btn.text}') : btn.text,
                                                  style: const TextStyle(fontWeight: FontWeight.bold),
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ),
                                            ),
                                          ),
                                          const SizedBox(width: 4),
                                          Expanded(
                                            flex: 1,
                                            child: TextField(
                                              controller: controller,
                                              textAlign: TextAlign.center,
                                              style: const TextStyle(color: Colors.white, fontSize: 12),
                                              decoration: const InputDecoration(
                                                isDense: true,
                                                contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                                                border: OutlineInputBorder(borderSide: BorderSide.none),
                                                hintText: '0s',
                                                hintStyle: TextStyle(color: Colors.white70),
                                              ),
                                              onSubmitted: (_) => _emitEventBoard(btn.id, btn),
                                              enabled: editable,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                }),
                              );
                            }),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
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
                  controller: _logScrollController,
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
    _logScrollController.dispose();
    super.dispose();
  }
}
