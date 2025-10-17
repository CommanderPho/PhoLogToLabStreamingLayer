## Why
Users need a way to configure LoggerApp behavior (e.g., default recording directory, auto-start recording, UI theme, EventBoard layout source) and have those preferences persist across runs in a platform-agnostic way.

## What Changes
- Add a Preferences panel in `LoggerApp` accessible from the menu and tray.
- Persist user preferences across runs using a cross-platform per-user config file.
- Load preferences on startup and apply to LoggerApp (recording, UI, EventBoard).
- Provide sensible defaults and a reset-to-defaults action.

## Impact
- Affected specs: `logging` (new sub-capability: Preferences Panel & Persistence)
- Affected code: `src/phologtolabstreaminglayer/logger_app.py` (menu, UI, load/save), new small persistence helper.

