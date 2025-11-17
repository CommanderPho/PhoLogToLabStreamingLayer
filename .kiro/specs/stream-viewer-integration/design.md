# Design Document

## Overview

This design document describes the architecture and implementation approach for integrating the stream_viewer application launcher into PhoLogToLabStreamingLayer. The integration will be minimal and non-invasive, adding a button to launch stream_viewer as an independent process while maintaining proper process lifecycle management.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────┐
│   PhoLogToLabStreamingLayer App    │
│  ┌───────────────────────────────┐  │
│  │   UI Layer (Qt/Tk)            │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │  Launch Button          │  │  │
│  │  │  Status Indicator       │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   StreamViewerLauncher        │  │
│  │  - Process management         │  │
│  │  - Discovery logic            │  │
│  │  - State tracking             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │
              │ subprocess.Popen()
              ▼
┌─────────────────────────────────────┐
│   stream_viewer Process             │
│   (Independent Application)         │
│  - Stream discovery                 │
│  - Visualization rendering          │
│  - User controls                    │
└─────────────────────────────────────┘
```

### Component Interaction Flow

```
User clicks "Open Stream Viewer"
    │
    ▼
StreamViewerLauncher.launch()
    │
    ├─> Check if process already running
    │   ├─> Yes: Bring to foreground (platform-specific)
    │   └─> No: Continue
    │
    ├─> Discover stream_viewer installation
    │   ├─> Check current Python environment
    │   ├─> Check sibling directory
    │   └─> Return path or None
    │
    ├─> Validate installation
    │   └─> Try importing stream_viewer
    │
    ├─> Launch subprocess
    │   ├─> python -m stream_viewer
    │   └─> Store process handle
    │
    └─> Update UI status
        └─> "Stream Viewer: Running"
```

## Components and Interfaces

### 1. StreamViewerLauncher Class

**Purpose**: Manages the lifecycle of the stream_viewer process, including discovery, launching, and state tracking.

**Location**: `src/phologtolabstreaminglayer/stream_viewer_launcher.py`

**Interface**:

```python
class StreamViewerLauncher:
    """Manages launching and tracking the stream_viewer application."""
    
    def __init__(self):
        """Initialize the launcher with discovery and state tracking."""
        self._process: Optional[subprocess.Popen] = None
        self._stream_viewer_path: Optional[Path] = None
        self._last_check_time: float = 0
        
    def discover_stream_viewer(self) -> Optional[Path]:
        """
        Discover the stream_viewer installation.
        
        Returns:
            Path to stream_viewer package or None if not found
        """
        
    def is_available(self) -> bool:
        """
        Check if stream_viewer is available to launch.
        
        Returns:
            True if stream_viewer can be launched
        """
        
    def is_running(self) -> bool:
        """
        Check if a stream_viewer process is currently running.
        
        Returns:
            True if process is alive
        """
        
    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        Launch the stream_viewer application.
        
        Args:
            args: Optional command-line arguments
            
        Returns:
            True if launch successful, False otherwise
        """
        
    def bring_to_foreground(self) -> bool:
        """
        Attempt to bring existing stream_viewer window to foreground.
        
        Returns:
            True if successful
        """
        
    def get_status_message(self) -> str:
        """
        Get current status message for UI display.
        
        Returns:
            Status string like "Stream Viewer: Running"
        """
```

**Key Methods**:

- `discover_stream_viewer()`: Implements the discovery logic
  1. Try importing `stream_viewer` in current environment
  2. Check `../stream_viewer` relative to application root
  3. Check user-configured paths from config file
  4. Cache the result for performance

- `launch()`: Implements the launch logic
  1. Check if already running
  2. Validate installation
  3. Build command: `[sys.executable, "-m", "stream_viewer"]`
  4. Launch with `subprocess.Popen()`
  5. Store process handle
  6. Return success/failure

- `is_running()`: Checks process state
  1. If no process handle, return False
  2. Call `process.poll()` to check if alive
  3. Update internal state
  4. Return result

### 2. UI Integration - Qt Implementation

**Location**: `src/phologtolabstreaminglayer/ui_qt/main_window.py`

**Changes**:

```python
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ...):
        # ... existing code ...
        self.stream_viewer_launcher = StreamViewerLauncher()
        
    def _build_tab_recording(self, parent: QtWidgets.QWidget) -> None:
        # ... existing controls ...
        
        # Add stream viewer controls
        viewer_group = QtWidgets.QGroupBox("Stream Visualization", parent)
        layout.addWidget(viewer_group)
        viewer_layout = QtWidgets.QHBoxLayout(viewer_group)
        
        self.btn_launch_viewer = QtWidgets.QPushButton("Open Stream Viewer", viewer_group)
        self.btn_launch_viewer.setToolTip("Launch stream_viewer to visualize LSL streams")
        self.btn_launch_viewer.clicked.connect(self._on_launch_viewer)
        viewer_layout.addWidget(self.btn_launch_viewer)
        
        self.lbl_viewer_status = QtWidgets.QLabel("Stream Viewer: Not Running", viewer_group)
        viewer_layout.addWidget(self.lbl_viewer_status)
        viewer_layout.addStretch(1)
        
        # Check availability
        if not self.stream_viewer_launcher.is_available():
            self.btn_launch_viewer.setEnabled(False)
            self.btn_launch_viewer.setToolTip(
                "stream_viewer not found. Install with: pip install stream_viewer"
            )
        
        # Start status update timer
        self.viewer_status_timer = QtCore.QTimer(self)
        self.viewer_status_timer.timeout.connect(self._update_viewer_status)
        self.viewer_status_timer.start(5000)  # Check every 5 seconds
        
    def _on_launch_viewer(self) -> None:
        """Handle launch button click."""
        if self.stream_viewer_launcher.is_running():
            # Bring to foreground
            if not self.stream_viewer_launcher.bring_to_foreground():
                QtWidgets.QMessageBox.information(
                    self, "Stream Viewer", 
                    "Stream viewer is already running."
                )
        else:
            # Launch new process
            success = self.stream_viewer_launcher.launch()
            if not success:
                QtWidgets.QMessageBox.critical(
                    self, "Launch Failed",
                    "Failed to launch stream_viewer. Check logs for details."
                )
        self._update_viewer_status()
        
    def _update_viewer_status(self) -> None:
        """Update the status label and button text."""
        status_msg = self.stream_viewer_launcher.get_status_message()
        self.lbl_viewer_status.setText(status_msg)
        
        if self.stream_viewer_launcher.is_running():
            self.btn_launch_viewer.setText("Show Stream Viewer")
        else:
            self.btn_launch_viewer.setText("Open Stream Viewer")
```

### 3. UI Integration - Tkinter Implementation

**Location**: `src/phologtolabstreaminglayer/logger_app.py`

**Changes**:

```python
class LoggerApp(...):
    def __init__(self, ...):
        # ... existing code ...
        self.stream_viewer_launcher = StreamViewerLauncher()
        
    def setup_gui(self):
        # ... existing code ...
        
        # Add stream viewer controls in recording frame
        viewer_frame = ttk.LabelFrame(self.recording_frame, text="Stream Visualization", padding="10")
        viewer_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        self.btn_launch_viewer = ttk.Button(
            viewer_frame, 
            text="Open Stream Viewer",
            command=self.on_launch_viewer
        )
        self.btn_launch_viewer.grid(row=0, column=0, padx=5)
        
        self.lbl_viewer_status = ttk.Label(
            viewer_frame, 
            text="Stream Viewer: Not Running"
        )
        self.lbl_viewer_status.grid(row=0, column=1, padx=10)
        
        # Check availability
        if not self.stream_viewer_launcher.is_available():
            self.btn_launch_viewer.config(state='disabled')
            # Add tooltip using existing tooltip mechanism
            
        # Start status update loop
        self.update_viewer_status()
        
    def on_launch_viewer(self):
        """Handle launch button click."""
        if self.stream_viewer_launcher.is_running():
            if not self.stream_viewer_launcher.bring_to_foreground():
                messagebox.showinfo(
                    "Stream Viewer", 
                    "Stream viewer is already running."
                )
        else:
            success = self.stream_viewer_launcher.launch()
            if not success:
                messagebox.showerror(
                    "Launch Failed",
                    "Failed to launch stream_viewer. Check logs for details."
                )
        self.update_viewer_status()
        
    def update_viewer_status(self):
        """Update status label periodically."""
        if self._shutting_down:
            return
            
        status_msg = self.stream_viewer_launcher.get_status_message()
        self.lbl_viewer_status.config(text=status_msg)
        
        if self.stream_viewer_launcher.is_running():
            self.btn_launch_viewer.config(text="Show Stream Viewer")
        else:
            self.btn_launch_viewer.config(text="Open Stream Viewer")
            
        # Schedule next update
        self.root.after(5000, self.update_viewer_status)
```

## Data Models

### Configuration Schema

**File**: `stream_viewer_config.json` (optional, in application config directory)

```json
{
  "stream_viewer": {
    "custom_path": null,
    "launch_args": [],
    "auto_launch": false
  }
}
```

**Fields**:
- `custom_path`: Optional path to stream_viewer installation
- `launch_args`: Additional command-line arguments to pass
- `auto_launch`: Whether to automatically launch stream_viewer on app startup

### Process State

Internal state tracked by `StreamViewerLauncher`:

```python
@dataclass
class ViewerState:
    process: Optional[subprocess.Popen]
    installation_path: Optional[Path]
    last_check_time: float
    is_available: bool
```

## Error Handling

### Error Scenarios and Responses

1. **stream_viewer Not Found**
   - Detection: Import fails, path checks fail
   - Response: Disable button, show tooltip with install instructions
   - Logging: INFO level - "stream_viewer not found in environment"

2. **Launch Failure**
   - Detection: `subprocess.Popen()` raises exception
   - Response: Show error dialog with exception message
   - Logging: ERROR level - Full traceback

3. **Process Crash**
   - Detection: Process exits with non-zero code within 5 seconds
   - Response: Show warning dialog
   - Logging: WARNING level - "stream_viewer process exited unexpectedly"

4. **Import Validation Failure**
   - Detection: Can import but missing required components
   - Response: Show error with version mismatch message
   - Logging: ERROR level - "stream_viewer installation incomplete"

### Error Messages

```python
ERROR_MESSAGES = {
    'not_found': (
        "stream_viewer is not installed.\n\n"
        "To install, run:\n"
        "pip install stream_viewer\n\n"
        "Or install from source:\n"
        "cd ../stream_viewer && pip install -e ."
    ),
    'launch_failed': (
        "Failed to launch stream_viewer.\n\n"
        "Error: {error}\n\n"
        "Check the application log for more details."
    ),
    'crashed': (
        "stream_viewer process exited unexpectedly.\n\n"
        "Exit code: {code}\n\n"
        "Check the stream_viewer logs for error details."
    ),
}
```

## Testing Strategy

### Unit Tests

**File**: `tests/test_stream_viewer_launcher.py`

Test cases:
1. `test_discover_in_environment()` - Mock successful import
2. `test_discover_sibling_directory()` - Mock file system
3. `test_discover_not_found()` - All discovery methods fail
4. `test_launch_success()` - Mock subprocess.Popen
5. `test_launch_already_running()` - Process already exists
6. `test_is_running_alive()` - Process poll returns None
7. `test_is_running_dead()` - Process poll returns exit code
8. `test_bring_to_foreground()` - Platform-specific mocking

### Integration Tests

**File**: `tests/integration/test_viewer_integration.py`

Test cases:
1. `test_button_enabled_when_available()` - UI state
2. `test_button_disabled_when_unavailable()` - UI state
3. `test_launch_from_ui()` - End-to-end launch
4. `test_status_updates()` - Timer-based updates
5. `test_multiple_launch_attempts()` - Idempotency

### Manual Testing Checklist

- [ ] Button appears in Recording tab (Qt)
- [ ] Button appears in Recording tab (Tk)
- [ ] Button launches stream_viewer successfully
- [ ] Status updates to "Running" after launch
- [ ] Second click brings window to foreground
- [ ] Status updates to "Not Running" after closing viewer
- [ ] Button disabled when stream_viewer not installed
- [ ] Tooltip shows install instructions when disabled
- [ ] Error dialog appears on launch failure
- [ ] Works on Windows
- [ ] Works on macOS
- [ ] Works on Linux

## Implementation Notes

### Platform-Specific Considerations

**Windows**:
- Use `pythonw.exe` instead of `python.exe` to avoid console window
- Window activation via `win32gui.SetForegroundWindow()` (if pywin32 available)
- Process creation flags: `CREATE_NO_WINDOW`

**macOS**:
- Window activation via AppleScript: `osascript -e 'tell application "Python" to activate'`
- May need to handle app bundle vs script execution

**Linux**:
- Window activation via `wmctrl` if available
- Fallback: No foreground activation, just show info message

### Discovery Algorithm

```python
def discover_stream_viewer(self) -> Optional[Path]:
    # Method 1: Try importing in current environment
    try:
        import stream_viewer
        return Path(stream_viewer.__file__).parent
    except ImportError:
        pass
    
    # Method 2: Check sibling directory
    app_root = Path(__file__).parents[2]  # Adjust based on file location
    sibling_path = app_root.parent / "stream_viewer"
    if sibling_path.exists() and (sibling_path / "stream_viewer" / "__init__.py").exists():
        return sibling_path / "stream_viewer"
    
    # Method 3: Check custom config path
    config = self._load_config()
    if config and config.get("stream_viewer", {}).get("custom_path"):
        custom_path = Path(config["stream_viewer"]["custom_path"])
        if custom_path.exists():
            return custom_path
    
    return None
```

### Launch Command Construction

```python
def _build_launch_command(self, args: Optional[List[str]] = None) -> List[str]:
    """Build the command to launch stream_viewer."""
    cmd = [sys.executable, "-m", "stream_viewer"]
    
    if args:
        cmd.extend(args)
    
    # Add any config-specified args
    config = self._load_config()
    if config:
        config_args = config.get("stream_viewer", {}).get("launch_args", [])
        cmd.extend(config_args)
    
    return cmd
```

### Process Management

```python
def launch(self, args: Optional[List[str]] = None) -> bool:
    """Launch stream_viewer process."""
    if self.is_running():
        return self.bring_to_foreground()
    
    if not self.is_available():
        logger.error("stream_viewer not available")
        return False
    
    try:
        cmd = self._build_launch_command(args)
        logger.info(f"Launching stream_viewer: {' '.join(cmd)}")
        
        # Platform-specific process creation
        if sys.platform == "win32":
            # Use pythonw to avoid console window
            cmd[0] = cmd[0].replace("python.exe", "pythonw.exe")
            self._process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            self._process = subprocess.Popen(cmd)
        
        # Wait briefly to check for immediate crashes
        time.sleep(0.5)
        if self._process.poll() is not None:
            logger.error(f"stream_viewer crashed immediately with code {self._process.returncode}")
            return False
        
        logger.info(f"stream_viewer launched successfully (PID: {self._process.pid})")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to launch stream_viewer: {e}")
        return False
```

## Dependencies

### New Dependencies

None - uses only Python standard library:
- `subprocess` - Process management
- `pathlib` - Path handling
- `importlib` - Import checking
- `sys` - Python executable path
- `time` - Timing checks

### Optional Dependencies

For enhanced functionality (graceful degradation if not available):
- `pywin32` (Windows only) - Window activation
- `wmctrl` (Linux only) - Window activation

## Migration and Deployment

### Deployment Steps

1. Add `stream_viewer_launcher.py` module
2. Update Qt UI (`main_window.py`)
3. Update Tk UI (`logger_app.py`)
4. Add unit tests
5. Update documentation
6. Add to requirements (optional dependency)

### Backward Compatibility

- No breaking changes to existing functionality
- New feature is additive only
- Gracefully handles missing stream_viewer installation

### Configuration Migration

No migration needed - this is a new feature with no existing configuration.

## Performance Considerations

### Resource Usage

- **Memory**: Minimal (<1 MB) - only stores process handle and paths
- **CPU**: Negligible - status checks every 5 seconds use `poll()` which is instant
- **Startup Time**: <100ms for discovery and initialization

### Optimization Strategies

1. **Cache Discovery Results**: Only run discovery once on startup
2. **Lazy Initialization**: Don't check availability until user interacts with button
3. **Efficient Status Checks**: Use `poll()` instead of process enumeration
4. **Debounce Button Clicks**: Prevent rapid repeated launches

## Security Considerations

### Threat Model

1. **Malicious stream_viewer Package**: User installs compromised package
   - Mitigation: Document official installation sources
   - Out of scope: Package verification (user responsibility)

2. **Command Injection**: Malicious config file with crafted launch args
   - Mitigation: Use subprocess with list arguments (not shell=True)
   - Validation: Sanitize config-provided arguments

3. **Path Traversal**: Malicious custom_path in config
   - Mitigation: Validate paths exist and contain expected files
   - Check: Verify `__init__.py` exists before trusting path

### Security Best Practices

```python
def _validate_custom_path(self, path: Path) -> bool:
    """Validate a custom stream_viewer path."""
    if not path.exists():
        return False
    if not path.is_dir():
        return False
    # Must contain __init__.py to be valid Python package
    if not (path / "__init__.py").exists():
        return False
    # Must be within reasonable bounds (not system directories)
    try:
        path.resolve().relative_to(Path.home())
    except ValueError:
        # Path is outside user home - be cautious
        logger.warning(f"Custom path outside user home: {path}")
    return True
```

## Future Enhancements

Potential future improvements (not in current scope):

1. **Auto-Launch Option**: Automatically launch stream_viewer on app startup
2. **Stream Selection**: Pass specific stream names to visualize
3. **Layout Presets**: Launch with predefined visualization layouts
4. **Embedded Mode**: Option to embed stream_viewer in a tab (major refactor)
5. **Process Monitoring**: Restart crashed viewer automatically
6. **Multi-Instance Support**: Allow multiple viewer windows with different configs
