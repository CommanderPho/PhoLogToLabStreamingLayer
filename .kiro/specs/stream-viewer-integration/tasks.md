# Implementation Plan

- [ ] 1. Create StreamViewerLauncher core module
  - Create `src/phologtolabstreaminglayer/stream_viewer_launcher.py` with the `StreamViewerLauncher` class
  - Implement `__init__()` method to initialize process tracking state
  - Implement `discover_stream_viewer()` method with three-tier discovery logic (current environment, sibling directory, custom config)
  - Implement `is_available()` method to check if stream_viewer can be launched
  - Implement `is_running()` method to check process state using `poll()`
  - Implement `launch()` method with platform-specific subprocess creation
  - Implement `get_status_message()` method to return UI-friendly status strings
  - Add logging for all major operations (discovery, launch, status checks)
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 7.1, 7.2, 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 2. Implement platform-specific window activation
  - Add `bring_to_foreground()` method to `StreamViewerLauncher`
  - Implement Windows activation using `win32gui.SetForegroundWindow()` if pywin32 available
  - Implement macOS activation using AppleScript via subprocess
  - Implement Linux activation using wmctrl if available
  - Add graceful fallback when platform-specific tools unavailable
  - _Requirements: 2.4_

- [ ] 3. Add configuration file support
  - Create configuration schema for `stream_viewer_config.json`
  - Implement `_load_config()` method to read configuration file
  - Implement `_validate_custom_path()` method with security checks
  - Add support for custom_path, launch_args, and auto_launch settings
  - Handle missing or malformed configuration gracefully
  - _Requirements: 4.2, 4.3, 4.4_

- [ ] 4. Integrate launcher into Qt UI
  - Import `StreamViewerLauncher` in `src/phologtolabstreaminglayer/ui_qt/main_window.py`
  - Add `self.stream_viewer_launcher` instance in `MainWindow.__init__()`
  - Create "Stream Visualization" group box in `_build_tab_recording()`
  - Add "Open Stream Viewer" button with click handler
  - Add status label showing "Stream Viewer: Not Running" / "Stream Viewer: Running"
  - Implement `_on_launch_viewer()` method to handle button clicks
  - Implement `_update_viewer_status()` method to refresh status label
  - Create QTimer to call `_update_viewer_status()` every 5 seconds
  - Disable button and show tooltip when stream_viewer not available
  - Update button text to "Show Stream Viewer" when process is running
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 5. Integrate launcher into Tkinter UI
  - Import `StreamViewerLauncher` in `src/phologtolabstreaminglayer/logger_app.py`
  - Add `self.stream_viewer_launcher` instance in `LoggerApp.__init__()`
  - Create "Stream Visualization" label frame in `setup_gui()`
  - Add "Open Stream Viewer" button with command handler
  - Add status label showing current viewer state
  - Implement `on_launch_viewer()` method to handle button clicks
  - Implement `update_viewer_status()` method with `root.after()` scheduling
  - Disable button and add tooltip when stream_viewer not available
  - Update button text dynamically based on process state
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.4, 2.5, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 6. Implement error handling and user feedback
  - Add error dialog in Qt UI for launch failures using `QMessageBox.critical()`
  - Add error dialog in Tk UI for launch failures using `messagebox.showerror()`
  - Create informative error messages for common failure scenarios
  - Add installation instructions in button tooltip when stream_viewer not found
  - Implement crash detection (process exits within 5 seconds of launch)
  - Log all errors with full context for debugging
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 7. Create unit tests for StreamViewerLauncher
  - Create `tests/test_stream_viewer_launcher.py`
  - Write test for `discover_stream_viewer()` with mocked import
  - Write test for `discover_stream_viewer()` with mocked file system
  - Write test for `discover_stream_viewer()` returning None when not found
  - Write test for `launch()` with mocked subprocess.Popen
  - Write test for `launch()` when process already running
  - Write test for `is_running()` with alive process
  - Write test for `is_running()` with dead process
  - Write test for `bring_to_foreground()` with platform-specific mocking
  - Write test for configuration loading and validation
  - _Requirements: All requirements (validation)_

- [ ]* 8. Create integration tests
  - Create `tests/integration/test_viewer_integration.py`
  - Write test for button enabled state when stream_viewer available
  - Write test for button disabled state when stream_viewer unavailable
  - Write test for end-to-end launch from UI button
  - Write test for status label updates via timer
  - Write test for handling multiple launch attempts
  - Write test for error dialog display on launch failure
  - _Requirements: All requirements (validation)_

- [ ] 9. Add keyboard shortcut support
  - Add Ctrl+V keyboard shortcut in Qt UI using `QShortcut`
  - Add Ctrl+V keyboard shortcut in Tk UI using `bind()`
  - Update tooltips to mention keyboard shortcut
  - Ensure shortcut works from any tab
  - _Requirements: 6.5_

- [ ] 10. Update documentation
  - Add stream viewer integration section to README.md
  - Document installation requirements for stream_viewer
  - Document keyboard shortcuts
  - Document configuration file options
  - Add troubleshooting section for common issues
  - _Requirements: 5.5_

- [ ] 11. Handle edge cases and cleanup
  - Ensure launcher works when stream_viewer is in development mode (pip install -e)
  - Handle spaces and special characters in paths correctly
  - Test with virtual environments and conda environments
  - Verify behavior when Logger_App closes while viewer is running
  - Add cleanup logic if needed (currently viewer runs independently)
  - _Requirements: 2.2, 2.3, 4.5, 8.4, 8.5_
