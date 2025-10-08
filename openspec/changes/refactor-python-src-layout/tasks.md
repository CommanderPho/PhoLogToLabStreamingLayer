## 1. Implementation
- [ ] 1.1 Create package skeleton at `src/phologtolabstreaminglayer/` with `__init__.py` and `__main__.py`
- [ ] 1.2 Move `logger_app.py` code into `src/phologtolabstreaminglayer/app.py` and wire `__main__.py:main()`
- [ ] 1.3 Update imports to absolute `phologtolabstreaminglayer.*`
- [ ] 1.4 Update `pyproject.toml` for src layout and console script `pholog-to-lsl=phologtolabstreaminglayer.__main__:main`
- [ ] 1.5 Update PyInstaller spec files to reference module paths under `src/`
- [ ] 1.6 Update `scripts/build_exe.py` to package from new package path
- [ ] 1.7 Update `run_logger.bat` and `install_and_run.bat` to use `python -m phologtolabstreaminglayer` or `pholog-to-lsl`
- [ ] 1.8 Optional: keep root `logger_app.py` as shim that imports and forwards to new `main()`

## 2. Validation
- [ ] 2.1 `pip install -e .` works; `python -c "import phologtolabstreaminglayer; print('ok')"` prints ok
- [ ] 2.2 `python -m phologtolabstreaminglayer` launches GUI
- [ ] 2.3 `pholog-to-lsl` launches GUI after install
- [ ] 2.4 PyInstaller build succeeds and executable runs
- [ ] 2.5 Existing tests and scripts run without import errors

## 3. Documentation
- [ ] 3.1 Update `README.md` run instructions
- [ ] 3.2 Note migration and import path changes in CHANGELOG/Release notes

