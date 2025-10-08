## Why
The current Python app lives at the repository root and is packaged primarily for PyInstaller. This makes imports brittle, complicates testing and editable installs, and diverges from modern Python packaging standards. Adopting the standard `src/` layout improves reliability (import path isolation), enables clean `pip install -e .` workflows, and simplifies future modularization.

## What Changes
- Adopt standard `src/` layout with top-level package `phologtolabstreaminglayer`.
- Move all importable Python sources into `src/phologtolabstreaminglayer/` with `__init__.py` and `__main__.py`.
- Update `pyproject.toml` to declare the src-based package and add a console script entry point.
- Update PyInstaller spec files and build scripts to reference the new package path.
- Replace relative/local imports with absolute imports rooted at `phologtolabstreaminglayer`.
- Update run scripts (`run_logger.bat`, `install_and_run.bat`) to launch via module/entry point.
- Optional one-release shim: keep a thin root `logger_app.py` delegating to the new entry point to ease migration.

## Impact
- Affected specs: `specs/packaging/spec.md` (new capability)
- Affected code: `logger_app.py` (moved), `pyproject.toml`, `logger_app.spec`, `PhoLogToLabStreamingLayer.spec`, `scripts/build_exe.py`, `run_logger.bat`, `install_and_run.bat`
- Tooling: editable installs and wheel builds will be supported via Hatch; PyInstaller configs updated accordingly.
- Breaking changes: imports referencing root-level modules must update to `phologtolabstreaminglayer.*`. Entry points change to console script and/or `python -m phologtolabstreaminglayer`.

