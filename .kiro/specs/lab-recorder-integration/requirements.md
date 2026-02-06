# Requirements Document

## Introduction

This feature integrates lab-recorder-python functionality into the existing PhoLogToLabStreamingLayer application, replacing the current simple file output with comprehensive XDF recording capabilities that can manage multiple LSL streams from a single interface.

## Glossary

- **LSL**: Lab Streaming Layer - a system for unified collection of measurement time series in research experiments
- **XDF**: Extensible Data Format - the standard file format for storing LSL data
- **PhoLogToLabStreamingLayer**: The existing Python application for LSL logging with GUI
- **lab-recorder-python**: Python implementation of LSL recorder for XDF output
- **Stream**: An LSL data stream from a specific source (e.g., EEG, markers, events)
- **Recording Session**: A continuous XDF recording that captures multiple LSL streams
- **Stream Monitor**: UI component that displays active LSL streams and their status

## Requirements

### Requirement 1

**User Story:** As a researcher, I want to record multiple LSL streams to XDF format from within PhoLogToLabStreamingLayer, so that I can capture all experimental data in a single, standardized file without running separate applications.

#### Acceptance Criteria

1. WHEN the application starts, THE PhoLogToLabStreamingLayer SHALL automatically discover all available LSL streams on the network
2. THE PhoLogToLabStreamingLayer SHALL display discovered streams in a dedicated monitoring panel with stream name, type, and connection status
3. WHEN a user initiates recording, THE PhoLogToLabStreamingLayer SHALL create an XDF file that captures all selected LSL streams simultaneously
4. THE PhoLogToLabStreamingLayer SHALL replace the current simple file output with XDF recording functionality
5. WHEN recording is active, THE PhoLogToLabStreamingLayer SHALL provide real-time feedback on recording status and file size

### Requirement 2

**User Story:** As a researcher, I want to manage XDF recording sessions through the existing GUI, so that I can control recording without switching between multiple applications.

#### Acceptance Criteria

1. THE PhoLogToLabStreamingLayer SHALL integrate XDF recording controls into the existing user interface
2. WHEN a user clicks start recording, THE PhoLogToLabStreamingLayer SHALL begin capturing all selected streams to a timestamped XDF file
3. WHEN a user clicks stop recording, THE PhoLogToLabStreamingLayer SHALL properly close the XDF file and display recording summary
4. THE PhoLogToLabStreamingLayer SHALL provide split recording functionality to create new XDF files without data loss
5. THE PhoLogToLabStreamingLayer SHALL display current recording filename and duration in the status area

### Requirement 3

**User Story:** As a researcher, I want to see which LSL streams are included in my recording, so that I can verify all necessary data sources are captured.

#### Acceptance Criteria

1. THE PhoLogToLabStreamingLayer SHALL display a list of all discovered LSL streams with their metadata
2. WHEN streams are available, THE PhoLogToLabStreamingLayer SHALL show stream name, type, channel count, and sampling rate
3. THE PhoLogToLabStreamingLayer SHALL allow users to select which streams to include in recordings
4. WHEN a stream disconnects, THE PhoLogToLabStreamingLayer SHALL update the display to reflect the disconnection
5. THE PhoLogToLabStreamingLayer SHALL maintain stream selection preferences across application sessions

### Requirement 4

**User Story:** As a researcher, I want automatic recording to work with XDF output, so that I can capture data immediately when streams become available.

#### Acceptance Criteria

1. WHEN LSL streams are detected and auto-recording is enabled, THE PhoLogToLabStreamingLayer SHALL automatically start XDF recording
2. THE PhoLogToLabStreamingLayer SHALL maintain the existing auto-start recording functionality with XDF output
3. WHEN auto-recording starts, THE PhoLogToLabStreamingLayer SHALL create an XDF file with a default timestamp-based filename
4. THE PhoLogToLabStreamingLayer SHALL include the application's own text logging stream in XDF recordings
5. THE PhoLogToLabStreamingLayer SHALL provide visual confirmation when auto-recording begins

### Requirement 5

**User Story:** As a researcher, I want the integrated recorder to handle errors gracefully, so that I don't lose data or crash the application during recording.

#### Acceptance Criteria

1. WHEN XDF recording encounters an error, THE PhoLogToLabStreamingLayer SHALL display an error message and attempt recovery
2. THE PhoLogToLabStreamingLayer SHALL continue operating even if XDF recording fails
3. WHEN a stream disconnects during recording, THE PhoLogToLabStreamingLayer SHALL continue recording other streams
4. THE PhoLogToLabStreamingLayer SHALL provide backup mechanisms to prevent data loss during recording failures
5. THE PhoLogToLabStreamingLayer SHALL log all recording-related errors for debugging purposes