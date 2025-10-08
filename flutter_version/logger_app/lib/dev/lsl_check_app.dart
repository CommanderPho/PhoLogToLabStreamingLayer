import 'package:flutter/material.dart';
import 'package:lsl_flutter/lsl_flutter.dart';

void main() {
  runApp(const MaterialApp(home: LslCheckPage()));
}

class LslCheckPage extends StatefulWidget {
  const LslCheckPage({super.key});
  @override
  State<LslCheckPage> createState() => _LslCheckPageState();
}

class _LslCheckPageState extends State<LslCheckPage> {
  String _status = 'Resolving streams...';
  List<ResolvedStreamHandle> _handles = const [];

  @override
  void initState() {
    super.initState();
    _resolve();
  }

  Future<void> _resolve() async {
    try {
      final manager = StreamManager();
      manager.resolveStreams(5.0);
      final handles = manager.getStreamHandles();
      setState(() {
        _handles = handles;
        _status = 'Found ${handles.length} stream(s).';
      });
      for (final h in handles) {
        debugPrint('Stream: ${h.info.name} | ${h.info.type} | ${h.id}');
      }
    } catch (e, st) {
      setState(() {
        _status = 'Error: $e';
      });
      debugPrint('Resolve error: $e\n$st');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('LSL Flutter Check')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_status),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _resolve,
              child: const Text('Resolve Again'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _handles.length,
                itemBuilder: (context, i) {
                  final h = _handles[i];
                  return Text('${h.info.name} (${h.info.type}) - ${h.id}');
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}