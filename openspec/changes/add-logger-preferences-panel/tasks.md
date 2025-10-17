## 1. Implementation
- [ ] 1.1 Add persistence helper using platform-specific user config dir
- [ ] 1.2 Load preferences at LoggerApp startup and apply
- [ ] 1.3 Add Preferences panel UI (menu/tray entry + window)
- [ ] 1.4 Implement Save/Cancel/Reset to defaults
- [ ] 1.5 Wire keys: auto_start, directory, ui.theme, eventboard source/path
- [ ] 1.6 Handle missing/corrupt config with safe defaults

## 2. Validation
- [ ] 2.1 Manual: Save prefs, restart app, verify persisted behavior
- [ ] 2.2 Manual: Delete/garble config; verify defaults and no crash
- [ ] 2.3 Strict validation: `openspec validate add-logger-preferences-panel --strict`

