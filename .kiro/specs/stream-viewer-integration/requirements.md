# Requirements Document

## Introduction

This document specifies the requirements for integrating the `stream_viewer` real-time LSL visualization software into the `PhoLogToLabStreamingLayer` application. The integration will enable users to launch the stream_viewer from the logger application to preview and display the LSL streams that the logger is recording and producing.

## Glossary

- **LSL (Lab Streaming Layer)**: A system for synchronizing streaming data for live analysis or recording
- **PhoLogToLabStreamingLayer**: The logging application that records timestamped notes and events to LSL streams and files
- **stream_viewer**: A separate Python package that provides real-time visualization of LSL streams
- **Logger_App**: The main application class in PhoLogToLabStreamingLayer
- **Stream_Outlet**: An LSL component that publishes data to the network
- **Stream_Viewer_Process**: The separate process running the stream_viewer application
- **Launch_Button**: A UI button that starts the stream_viewer application
- **Qt_UI**: The PyQt6-based user interface implementation
- **Tk_UI**: The Tkinter-based user interface implementation (legacy)

## Requirements

### Requirement 1: Stream Viewer Launch Button

**User Story:** As a user, I want a button in the logger application to launch the stream viewer, so that I can easily open the visualization tool when needed.

#### Acceptance Criteria

1. THE Logger_App SHALL display a Launch_Button labeled "Open Stream Viewer" in the Recording tab
2. THE Launch_Button SHALL be positioned near the recording controls for easy access
3. WHEN a user clicks the Launch_Button, THE Logger_App SHALL launch the stream_viewer application in a separate process
4. THE Launch_Button SHALL be enabled at all times regardless of recording state

### Requirement 2: Stream Viewer Process Management

**User Story:** As a user, I want the stream viewer to run independently from the logger, so that closing one application doesn't affect the other.

#### Acceptance Criteria

1. WHEN the Launch_Button is clicked, THE Logger_App SHALL start the Stream_Viewer_Process as a separate subprocess
2. THE Stream_Viewer_Process SHALL continue running if the Logger_App is closed
3. THE Logger_App SHALL continue running if the Stream_Viewer_Process is closed
4. WHEN the Launch_Button is clicked and a Stream_Viewer_Process is already running, THE Logger_App SHALL bring the existing window to the foreground instead of launching a duplicate
5. THE Logger_App SHALL track the Stream_Viewer_Process state and update the Launch_Button text to "Show Stream Viewer" when a process is already running

### Requirement 3: Stream Viewer Executable Discovery

**User Story:** As a user, I want the logger to automatically find the stream viewer installation, so that I don't have to manually configure paths.

#### Acceptance Criteria

1. THE Logger_App SHALL search for the stream_viewer package in the Python environment
2. WHEN stream_viewer is installed in the same virtual environment, THE Logger_App SHALL use that installation
3. WHEN stream_viewer is not found in the current environment, THE Logger_App SHALL check the sibling directory "../stream_viewer"
4. WHEN stream_viewer cannot be found, THE Logger_App SHALL disable the Launch_Button and display a tooltip with installation instructions
5. THE Logger_App SHALL validate the stream_viewer installation on startup and log the discovery result

### Requirement 4: Launch Configuration

**User Story:** As a user, I want the stream viewer to launch with appropriate settings, so that it automatically discovers my logger's streams.

#### Acceptance Criteria

1. WHEN launching the Stream_Viewer_Process, THE Logger_App SHALL pass no additional command-line arguments by default
2. THE Logger_App SHALL allow users to specify custom launch arguments through a configuration file
3. THE Stream_Viewer_Process SHALL use its default stream discovery mechanism to find LSL streams
4. THE Logger_App SHALL set the working directory of the Stream_Viewer_Process to the stream_viewer package directory
5. THE Logger_App SHALL inherit the current Python environment when launching the Stream_Viewer_Process

### Requirement 5: Error Handling and User Feedback

**User Story:** As a user, I want clear feedback when the stream viewer fails to launch, so that I can troubleshoot issues.

#### Acceptance Criteria

1. WHEN the Stream_Viewer_Process fails to start, THE Logger_App SHALL display an error dialog with the failure reason
2. WHEN stream_viewer dependencies are missing, THE Logger_App SHALL display installation instructions including the command "pip install stream_viewer" or equivalent
3. THE Logger_App SHALL log all stream viewer launch attempts and their outcomes to the application log
4. WHEN the Stream_Viewer_Process crashes within 5 seconds of launch, THE Logger_App SHALL detect this and notify the user
5. THE Logger_App SHALL provide a "Help" button or link in error dialogs that opens documentation for stream viewer setup

### Requirement 6: UI Integration

**User Story:** As a user, I want the stream viewer button to fit naturally into the existing interface, so that it feels like a cohesive feature.

#### Acceptance Criteria

1. THE Launch_Button SHALL use the same styling and theme as other buttons in the Logger_App
2. THE Launch_Button SHALL work identically in both Qt_UI and Tk_UI implementations
3. THE Launch_Button SHALL include an icon representing visualization or streaming if available
4. THE Launch_Button SHALL display a tooltip explaining its function when the user hovers over it
5. THE Launch_Button SHALL be keyboard accessible with an appropriate shortcut key (e.g., Ctrl+V)

### Requirement 7: Status Indication

**User Story:** As a user, I want to know if the stream viewer is currently running, so that I don't accidentally launch multiple instances.

#### Acceptance Criteria

1. WHEN a Stream_Viewer_Process is running, THE Logger_App SHALL display a status indicator showing "Stream Viewer: Running"
2. WHEN no Stream_Viewer_Process is running, THE Logger_App SHALL display "Stream Viewer: Not Running"
3. THE Logger_App SHALL periodically check if the Stream_Viewer_Process is still alive every 5 seconds
4. WHEN a running Stream_Viewer_Process terminates, THE Logger_App SHALL update the status indicator within 5 seconds
5. THE Status_Indicator SHALL be visible in the Recording tab near the Launch_Button

### Requirement 8: Cross-Platform Compatibility

**User Story:** As a user on Windows, macOS, or Linux, I want the stream viewer launch to work correctly on my platform, so that I have a consistent experience.

#### Acceptance Criteria

1. THE Logger_App SHALL use platform-appropriate process launching mechanisms for Windows, macOS, and Linux
2. THE Logger_App SHALL handle path separators correctly for the current operating system
3. WHEN launching on Windows, THE Logger_App SHALL use pythonw.exe if available to avoid console windows
4. THE Logger_App SHALL handle spaces and special characters in file paths correctly on all platforms
5. THE Logger_App SHALL test stream_viewer availability using platform-independent Python import checks
