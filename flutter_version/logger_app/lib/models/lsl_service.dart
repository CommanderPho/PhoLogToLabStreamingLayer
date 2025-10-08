import 'dart:async';
import 'package:lsl_flutter/lsl_flutter.dart';

class LSLService {
  bool _isInitialized = false;
  OutletWorker? _worker;

  // Stream names
  static const String _textLoggerName = 'TextLogger';
  static const String _eventBoardName = 'EventBoard';

  Future<void> initialize() async {
    if (_isInitialized) return;
    try {
      // Spawn worker isolate
      _worker = await OutletWorker.spawn();

      // Create TextLogger (Markers, 1 channel, string format)
      final textLoggerInfo = StreamInfoFactory.createStringStreamInfo(
        _textLoggerName,
        'Markers',
        const CftStringChannelFormat(),
        channelCount: 1,
        nominalSRate: 0,
        sourceId: 'textlogger_001',
      );

      // Create EventBoard (Markers, 1 channel, string format)
      final eventBoardInfo = StreamInfoFactory.createStringStreamInfo(
        _eventBoardName,
        'Markers',
        const CftStringChannelFormat(),
        channelCount: 1,
        nominalSRate: 0,
        sourceId: 'eventboard_001',
      );

      final okText = await _worker!.addStream(textLoggerInfo);
      final okEvent = await _worker!.addStream(eventBoardInfo);
      if (!okText || !okEvent) {
        throw Exception('Failed creating one or more LSL outlets');
      }

      _isInitialized = true;
    } catch (e) {
      _worker?.shutdown();
      _worker = null;
      rethrow;
    }
  }

  Future<void> sendMessage(String message) async {
    if (!_isInitialized || _worker == null) {
      throw Exception('LSL Service not initialized');
    }
    await _worker!.pushSample(_textLoggerName, <String>[message]);
  }

  Future<void> sendEvent(String event) async {
    if (!_isInitialized || _worker == null) {
      throw Exception('LSL Service not initialized');
    }
    await _worker!.pushSample(_eventBoardName, <String>[event]);
  }

  bool get isInitialized => _isInitialized;

  void dispose() {
    _isInitialized = false;
    _worker?.shutdown();
    _worker = null;
  }
}
