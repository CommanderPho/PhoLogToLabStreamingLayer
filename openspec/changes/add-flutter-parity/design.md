## Context
The project has a mature Python desktop app with real LSL integration and robust recording. The Flutter app (Android/iOS focus) is stale, currently uses a mock LSL service, and records to JSON. We need feature parity for mobile while respecting platform constraints (app lifecycle, permissions, background execution, storage sandboxes).

## Goals / Non-Goals
- Goals:
  - Real LSL transport via FFI for `TextLogger` and `EventBoard`
  - EventBoard UI parity (instant/toggle + time offsets) and message format parity
  - On-device recording: XDF writer and CSV mirror; auto-start; split; periodic backups and recovery
  - Config parity or compatible schema
- Non-Goals:
  - Desktop-only features (system tray, global hotkey)
  - Broad EEG processing; only markers/events

## Decisions
- Decision: FFI to liblsl
  - Load platform binaries (`.so`, `.dylib`, `.framework`) with a thin Dart FFI layer
  - Map minimal subset: create/push outlet for text and event channels; optional inlet for self-recording
- Decision: Message formats
  - Match Python: `EVENT_NAME|BUTTON_TEXT|TIMESTAMP` and START/END with `|TOGGLE:<bool>`
- Decision: Recording strategy (XDF/CSV)
  - Prefer native XDF writer via platform plugin (C/C++) bridged to Dart
  - Mirror events to CSV in app documents directory
  - Fallback (temporary): JSON+CSV with an offline converter if XDF writer is not ready
- Decision: Config parity
  - Define a mobile-compatible schema mirroring `eventboard_config.json` keys (id, row, col, text, event_name, color, type)
  - Allow platform-specific overrides where necessary

## Alternatives considered
- Pure-Dart LSL: not feasible (requires native socket/protocol compat and time sync semantics)
- Record-only (no LSL): breaks ecosystem integration; rejected

## Risks / Trade-offs
- Packaging FFI binaries across Android ABIs and iOS architectures → mitigated with CI build matrix and runtime checks
- Background execution and file I/O limits on iOS/Android → mitigated with foreground usage guidance and safe auto-save cadence
- XDF writer availability on mobile → phased approach (CSV+JSON fallback), validate performance and file integrity
- Permissions (storage) → request at runtime with clear UX; use app-scoped storage where possible

## Migration Plan
1) Integrate FFI to liblsl; ship minimal outlets for `TextLogger`/`EventBoard`
2) Implement EventBoard UI parity including time offsets and formatting
3) Add CSV mirror and periodic backups; auto-start recording
4) Implement split recording
5) Add XDF writer via platform plugin; validate on devices; keep JSON/CSV fallback behind a flag
6) Align config schema and document migration

## Open Questions
- Which XDF writer implementation to adopt for mobile (port vs embed)?
- Self-recording inlet necessity on mobile vs relying on local outlets only?
- Expected recording durations and file sizes (impacting buffering strategy)?


