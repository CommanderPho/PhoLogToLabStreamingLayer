# Project Context

## Purpose
A minimal but complete logging application that sends timestamped text events to Lab Streaming Layer (LSL) and records them, with an EventBoard for structured markers. Primary goals:
- Provide fast, reliable logging of notes/markers to an LSL Markers stream
- Record events to persistent files with recovery and CSV export
- Offer quick-entry UX (system tray + global hotkey) and a configurable EventBoard UI
- Ship as both Python desktop app and a Flutter cross-platform variant

## Tech Stack
- Python 3.9+
  - UI: `tkinter` + `ttk`
  - LSL: `pylsl`
  - Recording/IO: `mne`, `numpy`, `pyxdf`
  - System Tray: `pystray`, `Pillow`
  - Global Hotkey: `keyboard`
  - Screen/Window helpers: `pyautogui`, `pywin32` (Windows)
  - Packaging: `pyinstaller` (spec files: `logger_app.spec`, `PhoLogToLabStreamingLayer.spec`)
  - Dev tooling: `pytest`, `black`, `isort`, `flake8` (via `tool.uv` dev-dependencies)
- Flutter (alt implementation under `flutter_version/logger_app`)
  - Dart/Flutter with `flutter_lints`
  - Planned LSL via FFI (`ffi`) and `path_provider`
  - Mock LSL service currently
- Assets/Config
  - Icons under `icons/`
  - EventBoard configuration: `eventboard_config.json`

## Project Conventions

### Code Style
- Python
  - Target: Python 3.9.13+
  - Formatting/linting (dev): `black`, `isort`, `flake8`
  - Naming: descriptive, full-word identifiers; avoid 1–2 char names
  - Control flow: early returns over deep nesting; avoid broad try/except
- Dart/Flutter
  - `analysis_options.yaml` includes `package:flutter_lints/flutter.yaml`
  - Project may customize lints via `linter.rules` when needed

### Architecture Patterns
- Python desktop app (`logger_app.py`)
  - Single process Tkinter app with class `LoggerApp`
  - LSL Markers outlet: `TextLogger` for freeform notes
  - LSL EventBoard outlet: `EventBoard` for structured button events
  - Self-recording inlet resolves `TextLogger` and persists samples
  - Background worker thread for recording (`recording_worker`)
  - System tray icon + menu; double-click/activate restores app
  - Global hotkey `Ctrl+Alt+L` opens quick log popover
  - EventBoard: 3x5 grid, supports instantaneous and toggleable buttons
  - Crash recovery via periodic JSON backups; recovery workflow on boot
  - File outputs: MNE `.fif` plus per-session `CSV/*_events.csv`
- Flutter app (experimental)
  - Mirrors core UX; currently uses mock LSL service
  - Plans for LSL via native bindings/FFI

### Testing Strategy
- Python
  - Example scripts: `test_eventboard.py`, `test_popover.py`
  - Manual verification: LSL message send/receive; recording start/stop/split; CSV generation; recovery
  - Recommended automated tests with `pytest` for message formatting, offset parsing, and CSV writer
- Flutter
  - `test/widget_test.dart` present; extend for model/services

### Git Workflow
- Default branch model with feature branches (e.g., `feature/focus-flutter-version`)
- Commit messages: action-led, concise; reference capabilities/changes when relevant
- Treat OpenSpec as source of truth for behavior and changes

## Domain Context
- Lab Streaming Layer (LSL) ecosystem integration
  - Streams:
    - `TextLogger` (Markers): freeform text samples
    - `EventBoard` (Markers): structured events including toggle states
  - Event format examples:
    - Instantaneous: `EVENT_NAME|BUTTON_TEXT|TIMESTAMP`
    - Toggle start/end: `EVENT_NAME_START|BUTTON_TEXT|TIMESTAMP|TOGGLE:True/False`
- EventBoard is user-configurable via `eventboard_config.json` (3x5 grid, button metadata)
- Typical usage: cognitive experiments, EEG/behavioral logging, timestamped notes

## Important Constraints
- Single-instance application enforced via localhost port lock
- Desktop focus; Windows features include registry-based theme detection and `pywin32`
- Timing accuracy: LSL timestamps used for persistence; MNE annotations need relative times
- Packaging via PyInstaller; include binary resources for `mne` and `pylsl`
- Minimum Python: `>=3.9.13`

## External Dependencies
- Libraries
  - `pylsl`, `mne`, `numpy`, `pyxdf`, `pystray`, `Pillow`, `keyboard`, `pyautogui`, `pywin32`
- Tooling
  - `pyinstaller` with spec files (`logger_app.spec`, `PhoLogToLabStreamingLayer.spec`)
- System
  - LSL runtime/liblsl installed and discoverable for full functionality
  - Windows registry access for theme detection (optional)
- Flutter
  - `ffi`, `path_provider`; planned native LSL bindings
