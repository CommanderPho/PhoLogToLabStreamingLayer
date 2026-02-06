## ADDED Requirements

### Requirement: Standard `src/` Layout Packaging
The Python application SHALL adopt the standard `src/` layout with a top-level package named `phologtolabstreaminglayer` located at `src/phologtolabstreaminglayer/`.

#### Scenario: Editable install works
- **WHEN** a developer runs `pip install -e .`
- **THEN** the package installs in editable mode
- **AND** `import phologtolabstreaminglayer` resolves successfully

#### Scenario: Module execution works
- **WHEN** a user runs `python -m phologtolabstreaminglayer`
- **THEN** the application starts the same main GUI as the legacy `logger_app.py`

#### Scenario: Console script entry point
- **WHEN** a user runs `pholog-to-lsl`
- **THEN** the application launches the main GUI

### Requirement: pyproject configuration for src layout
The project SHALL declare packages from `src/` and expose a console script.

#### Scenario: Package discovery uses src path
- **WHEN** building a wheel
- **THEN** the wheel contains `phologtolabstreaminglayer` from `src/`

#### Scenario: Console script binding exists
- **WHEN** installing the wheel
- **THEN** an executable `pholog-to-lsl` is created that calls `phologtolabstreaminglayer.__main__:main`

### Requirement: PyInstaller configs updated
The PyInstaller spec files SHALL reference the new package/module paths.

#### Scenario: Spec files import application entry
- **WHEN** building with PyInstaller
- **THEN** the spec files include the package modules from `src/phologtolabstreaminglayer`
- **AND** the resulting executables function the same as before


#### Scenario: Legacy script delegates
- **WHEN** running `python logger_app.py`
- **THEN** it imports `phologtolabstreaminglayer` and calls the new `main()`

### Requirement: Updated developer scripts
Run scripts SHALL launch via module or console script.

#### Scenario: Batch scripts use new entry
- **WHEN** executing `run_logger.bat` or `install_and_run.bat`
- **THEN** they invoke `python -m phologtolabstreaminglayer` or `pholog-to-lsl`

