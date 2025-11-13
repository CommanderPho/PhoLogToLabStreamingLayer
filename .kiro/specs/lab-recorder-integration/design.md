# Design Document

## Overview

This design integrates the `lab-recorder-python` package into the existing `PhoLogToLabStreamingLayer` application to replace the current MNE-based XDF recording with a more robust, multi-stream XDF recording solution. The integration will maintain the existing GUI while adding comprehensive stream monitoring and management capabilities.

## Architecture

### Current State Analysis

The existing `PhoLogToLabStreamingLayer` application has:
- Custom XDF recording using MNE that saves to `.fif` format with CSV export
- Simple recording of its own text logging streams (`TextLogger`, `EventBoard`, `WhisperLiveLogger`)
- Basic recording controls (start, stop, split)
- System tray integration and global hotkeys

### Target Architecture

The enhanced application will:
- Replace MNE-based recording with `lab-recorder-python`'s `LabRecorder` class
- Add comprehensive LSL stream discovery and monitoring
- Maintain existing GUI layout while adding stream management panel
- Preserve all existing functionality (text logging, EventBoard, transcription)

## Components and Interfaces

### 1. Enhanced LoggerApp Class

**Modifications to existing `LoggerApp`:**
- Add `LabRecorder` instance management
- Replace `recording_worker()` method with `LabRecorder` integration
- Add stream discovery and monitoring capabilities
- Maintain backward compatibility with existing recording methods

**New attributes:**
```python
self.lab_recorder: Optional[LabRecorder] = None
self.discovered_streams: Dict[str, StreamInfo] = {}
self.selected_streams: Set[str] = set()
self.stream_monitor_thread: Optional[threading.Thread] = None
```

### 2. Stream Discovery and Management

**StreamDiscoveryManager:**
- Continuous LSL stream discovery using `pylsl.resolve_streams()`
- Stream metadata extraction and caching
- Stream selection state management
- Integration with existing inlet setup

**Key methods:**
```python
def discover_streams(self) -> Dict[str, StreamInfo]
def update_stream_display(self)
def select_streams(self, stream_names: List[str])
def get_selected_streams(self) -> List[StreamInfo]
```

### 3. Enhanced GUI Components

**Stream Monitor Panel:**
- Replaces or extends existing recording frame
- Real-time stream list with checkboxes for selection
- Stream metadata display (name, type, channels, sample rate)
- Connection status indicators
- Stream selection persistence

**Enhanced Recording Controls:**
- Maintains existing start/stop/split functionality
- Adds stream selection controls
- Shows active recording streams
- Displays XDF file information

### 4. XDF Recording Integration

**LabRecorder Integration:**
- Replace `recording_worker()` with `LabRecorder` instance
- Configure `LabRecorder` with selected streams
- Handle recording lifecycle (start, stop, split)
- Maintain existing auto-start functionality

**Recording Configuration:**
```python
recorder_config = {
    'filename': self.xdf_filename,
    'streams': self.get_selected_streams(),
    'enable_remote_control': False,
    'chunk_size': 1024
}
```

## Data Models

### StreamInfo Structure
```python
@dataclass
class StreamInfo:
    name: str
    type: str
    channel_count: int
    nominal_srate: float
    source_id: str
    hostname: str
    created_at: float
    uid: str
    session_id: str
    v4address: str
    v4data_port: int
    v4service_port: int
    v6address: str
    v6data_port: int
    v6service_port: int
```

### Recording Session State
```python
@dataclass
class RecordingSession:
    filename: str
    start_time: datetime
    selected_streams: List[StreamInfo]
    lab_recorder: LabRecorder
    is_active: bool
```

## Error Handling

### Stream Connection Errors
- Graceful handling of stream disconnections during recording
- Automatic retry mechanisms for stream discovery
- User notification of stream status changes
- Fallback to existing streams if new discovery fails

### Recording Errors
- Robust error handling in `LabRecorder` integration
- Backup recording mechanisms using existing MNE approach
- Recovery from partial recording failures
- Detailed error logging and user feedback

### GUI Error Handling
- Thread-safe GUI updates for stream monitoring
- Graceful degradation if stream monitoring fails
- Preservation of existing functionality during errors

## Testing Strategy

### Integration Testing
- Test `LabRecorder` integration with existing LSL streams
- Verify XDF file compatibility with existing analysis tools
- Test stream selection and recording functionality
- Validate auto-start recording with multiple streams

### Compatibility Testing
- Ensure existing text logging functionality remains intact
- Test EventBoard integration with new recording system
- Verify system tray and hotkey functionality
- Test recovery and backup mechanisms

### Performance Testing
- Monitor resource usage with multiple stream recording
- Test recording stability over extended periods
- Validate file size and performance characteristics
- Test split recording functionality under load

## Implementation Phases

### Phase 1: Core Integration
- Integrate `LabRecorder` class into existing application
- Replace basic recording functionality
- Maintain existing GUI and user experience
- Ensure backward compatibility

### Phase 2: Stream Discovery
- Add comprehensive stream discovery
- Implement stream selection interface
- Add stream monitoring capabilities
- Enhance recording controls

### Phase 3: Enhanced Features
- Add advanced stream filtering and selection
- Implement stream metadata display
- Add recording session management
- Enhance error handling and recovery

## Migration Strategy

### Backward Compatibility
- Maintain existing recording file formats during transition
- Preserve existing configuration and settings
- Support recovery of existing backup files
- Gradual migration of recording functionality

### User Experience
- Minimal changes to existing workflow
- Progressive enhancement of stream management
- Optional advanced features for power users
- Clear migration path for existing recordings

## Dependencies

### Required Packages
- `lab-recorder-python`: Core XDF recording functionality
- `pylsl`: LSL stream discovery and management (already present)
- Existing dependencies maintained

### Optional Enhancements
- Stream visualization libraries for advanced monitoring
- Configuration management for stream selection persistence
- Advanced XDF analysis tools for recording validation