## Context
We need a small, robust, cross-platform way to persist per-user preferences for the Python `LoggerApp` without adding heavyweight dependencies.

## Goals / Non-Goals
- Goals: Simple JSON-based preferences in per-user config dir; minimal UI for editing; safe defaults.
- Non-Goals: Sync across machines; encrypted secrets management.

## Decisions
- Use `platformdirs` if available (already common) or fallback to a small helper using `~/.config` (Linux), `%APPDATA%` (Windows), and `~/Library/Application Support` (macOS).
- Store as `config.json` under `PhoLogToLabStreamingLayer` app dir.
- Keep schema flat-ish and explicit; validate on load.

## Risks / Trade-offs
- JSON editing by users could corrupt file → mitigate with defaults and overwrite on save.

## Open Questions
- Do we want to persist window geometry and last-used XDF folder? (out of scope for initial minimal change)

