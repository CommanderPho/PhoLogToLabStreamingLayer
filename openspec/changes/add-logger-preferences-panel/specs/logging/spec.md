## ADDED Requirements

### Requirement: Preferences Panel
LoggerApp SHALL provide a Preferences panel for configuring app behavior and appearance.

#### Scenario: Open preferences from menu
- **WHEN** the user selects Preferences from the menu or tray
- **THEN** a Preferences window opens with grouped settings

#### Scenario: Reset to defaults
- **WHEN** the user selects Reset to defaults
- **THEN** all fields revert to documented defaults without crashing

### Requirement: Preference Persistence
LoggerApp SHALL persist user preferences per user across runs in a platform-agnostic manner.

#### Scenario: Save preferences
- **WHEN** the user presses Save in Preferences
- **THEN** the new values are written to the per-user config file

#### Scenario: Load on startup
- **WHEN** the app starts
- **THEN** preferences are loaded and applied before UI is shown

#### Scenario: Missing or corrupt config
- **WHEN** the config file is missing or corrupt
- **THEN** the app falls back to defaults and recreates a valid config on next save

### Requirement: Preference Keys and Defaults
LoggerApp MUST define the following keys with defaults:

#### Scenario: Keys
- **WHEN** preferences are read or written
- **THEN** the following keys exist with defaults:
  - `recording.auto_start`: false
  - `recording.directory`: empty string (prompt when first record if empty)
  - `ui.theme`: `system`
  - `eventboard.config_source`: `file`
  - `eventboard.config_path`: `eventboard_config.json` (relative to app dir if set to file)

### Requirement: Cross-Platform Config Location
Preferences MUST be stored in a per-user configuration directory appropriate to the OS.

#### Scenario: Config path resolution
- **WHEN** resolving the config path
- **THEN** it uses the platform-appropriate per-user config directory and an app-specific subfolder (e.g., `PhoLogToLabStreamingLayer/config.json`)

