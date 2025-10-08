import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

class EventButtonConfig {
  final String id;
  final int row;
  final int col;
  final String text;
  final String eventName;
  final String colorHex;
  final String type; // 'instantaneous' | 'toggleable'

  const EventButtonConfig({
    required this.id,
    required this.row,
    required this.col,
    required this.text,
    required this.eventName,
    required this.colorHex,
    required this.type,
  });

  factory EventButtonConfig.fromJson(Map<String, dynamic> json) {
    return EventButtonConfig(
      id: json['id'] as String,
      row: (json['row'] as num).toInt(),
      col: (json['col'] as num).toInt(),
      text: json['text'] as String,
      eventName: json['event_name'] as String,
      colorHex: json['color'] as String,
      type: json['type'] as String,
    );
  }
}

class EventBoardConfig {
  final String title;
  final List<EventButtonConfig> buttons;

  const EventBoardConfig({
    required this.title,
    required this.buttons,
  });

  factory EventBoardConfig.fromJson(Map<String, dynamic> json) {
    final cfg = json['eventboard_config'] as Map<String, dynamic>? ?? json;
    final title = (cfg['title'] as String?) ?? 'Event Board';
    final buttonsJson = (cfg['buttons'] as List<dynamic>? ?? []);
    final buttons = buttonsJson
        .map((b) => EventButtonConfig.fromJson(b as Map<String, dynamic>))
        .toList();
    return EventBoardConfig(title: title, buttons: buttons);
  }
}

class EventBoardConfigLoader {
  static Future<EventBoardConfig> load() async {
    try {
      final docs = await getApplicationDocumentsDirectory();
      final file = File('${docs.path}/eventboard_config.json');
      if (await file.exists()) {
        final text = await file.readAsString();
        final jsonMap = jsonDecode(text) as Map<String, dynamic>;
        return EventBoardConfig.fromJson(jsonMap);
      }
    } catch (_) {
      // Fall back to default
    }
    return EventBoardConfig(
      title: 'Event Board',
      buttons: _defaultButtons,
    );
  }

  static const List<EventButtonConfig> _defaultButtons = [
    EventButtonConfig(id: 'button_1_1', row: 1, col: 1, text: 'Start Task', eventName: 'TASK_START', colorHex: '#4CAF50', type: 'instantaneous'),
    EventButtonConfig(id: 'button_1_2', row: 1, col: 2, text: 'Pause', eventName: 'TASK_PAUSE', colorHex: '#FF9800', type: 'instantaneous'),
    EventButtonConfig(id: 'button_1_3', row: 1, col: 3, text: 'Resume', eventName: 'TASK_RESUME', colorHex: '#2196F3', type: 'instantaneous'),
    EventButtonConfig(id: 'button_1_4', row: 1, col: 4, text: 'Stop Task', eventName: 'TASK_STOP', colorHex: '#F44336', type: 'instantaneous'),
    EventButtonConfig(id: 'button_1_5', row: 1, col: 5, text: 'Error', eventName: 'ERROR_OCCURRED', colorHex: '#9C27B0', type: 'instantaneous'),
    EventButtonConfig(id: 'button_2_1', row: 2, col: 1, text: 'Focus Mode', eventName: 'FOCUS_MODE', colorHex: '#607D8B', type: 'toggleable'),
    EventButtonConfig(id: 'button_2_2', row: 2, col: 2, text: 'Distracted', eventName: 'DISTRACTED', colorHex: '#FF5722', type: 'toggleable'),
    EventButtonConfig(id: 'button_2_3', row: 2, col: 3, text: 'Memory Lapse', eventName: 'MEMORY_LAPSE', colorHex: '#9C27B0', type: 'instantaneous'),
    EventButtonConfig(id: 'button_2_4', row: 2, col: 4, text: 'Confused', eventName: 'CONFUSED', colorHex: '#795548', type: 'toggleable'),
    EventButtonConfig(id: 'button_2_5', row: 2, col: 5, text: 'Break Time', eventName: 'BREAK_TIME', colorHex: '#4CAF50', type: 'toggleable'),
    EventButtonConfig(id: 'button_3_1', row: 3, col: 1, text: 'Response A', eventName: 'RESPONSE_A', colorHex: '#795548', type: 'instantaneous'),
    EventButtonConfig(id: 'button_3_2', row: 3, col: 2, text: 'Response B', eventName: 'RESPONSE_B', colorHex: '#795548', type: 'instantaneous'),
    EventButtonConfig(id: 'button_3_3', row: 3, col: 3, text: 'Food', eventName: 'Food', colorHex: '#795548', type: 'instantaneous'),
    EventButtonConfig(id: 'button_3_4', row: 3, col: 4, text: 'Dose 0.5+', eventName: 'DOSE_AMPH_15mg', colorHex: '#e9a91e', type: 'instantaneous'),
    EventButtonConfig(id: 'button_3_5', row: 3, col: 5, text: 'Dose 1.0+', eventName: 'DOSE_AMPH_30mg', colorHex: '#e9a91e', type: 'instantaneous'),
  ];
}

Color parseHexColor(String hex) {
  var value = hex.replaceAll('#', '').toUpperCase();
  if (value.length == 6) {
    value = 'FF$value';
  }
  final intColor = int.tryParse(value, radix: 16) ?? 0xFF2196F3;
  return Color(intColor);
}


