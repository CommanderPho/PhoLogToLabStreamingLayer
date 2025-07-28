/// XDF Files - A Dart package for working with XDF (Extensible Data Format) files
/// Used for Lab Streaming Layer data export and manipulation.
/// 
/// This package supports the full XDF specification including:
/// - Multiple data types (int8, int16, int32, int64, float32, double64, string)
/// - EEG streams with comprehensive metadata
/// - Marker/event streams
/// - Multi-stream XDF files
/// - Standard electrode locations and filtering configurations
library xdf_files;

// Core XDF functionality
export 'src/xdf_stream_info.dart';
export 'src/xdf_writer_general.dart';
export 'src/xdf_helpers.dart';

// Legacy compatibility
export 'src/xdf_writer.dart';
