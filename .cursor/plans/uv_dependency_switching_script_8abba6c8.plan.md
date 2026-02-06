---
name: UV dependency switching script
overview: Create a Python script that automatically switches UV dependency sources between dev (local editable paths) and release (git URLs) configurations across all projects in the workspace that have templating folders.
todos:
  - id: create_package_structure
    content: Create ACTIVE_DEV/uv-deps-switcher/ package structure with pyproject.toml, src/ directory, and README.md
    status: pending
  - id: implement_config_parser
    content: Implement config.py to read and parse .uv-deps-switcher.toml files with group definitions, support workspace and home directory lookup
    status: pending
  - id: implement_main_logic
    content: Implement main.py with workspace-aware auto-detection, template reading, pyproject.toml modification, and group-based repo selection
    status: pending
  - id: add_cli_entry_point
    content: Configure pyproject.toml with console script entry point and add CLI interface with argparse supporting --group, --all, --repo options and list-groups command
    status: pending
  - id: add_example_config
    content: Create .uv-deps-switcher.toml.example with example group definitions
    status: pending
  - id: add_readme
    content: Create README.md with installation instructions, config file format, and usage examples including group switching
    status: pending
  - id: test_installation
    content: Test package installation and verify the command is available globally
    status: pending
  - id: test_switching
    content: Test the command with groups, individual repos, and --all option from different project directories to verify workspace detection and switching works correctly
    status: pending
---

# UV Dependency Switching Script

## Overview

Create a Python script that automatically detects projects with templating folders and switches their `[tool.uv.sources]` sections between dev and release configurations.

## Implementation Details

### Package Location and Structure

Create a standalone Python package that can be installed globally:

**Location**: `ACTIVE_DEV/uv-deps-switcher/` (or separate repository if preferred)

**Package Structure**:

```
uv-deps-switcher/
├── pyproject.toml          # Package configuration with console script entry point
├── README.md               # Installation and usage instructions
├── src/
│   └── uv_deps_switcher/
│       ├── __init__.py
│       └── main.py         # Main CLI logic
└── uv.lock                 # Optional, if using uv for dependencies
```

The package will be installable globally with:

```bash
cd uv-deps-switcher
uv pip install -e .
# or
uv pip install .
```

After installation, the command `switch-uv-deps` (or `switch_uv_deps`) will be available globally from any directory.

The package should be workspace-aware and automatically detect:

- The current workspace root (from VSCode workspace file or current directory)
- All projects with templating folders within the workspace or parent directory structure
- Support being run from any project directory

### Core Functionality

1. **Repo Group Configuration**

   - Support configuration file (`.uv-deps-switcher.toml` or `uv-deps-switcher.toml`) to define groups of repos
   - Config file can be placed in workspace root or user home directory
   - Groups allow switching multiple related repos together with a single command
   - Example config structure:
     ```toml
     [groups.main]
     repos = ["PhoLogToLabStreamingLayer", "whisper-timestamped"]
     
     [groups.all]
     repos = ["PhoLogToLabStreamingLayer", "whisper-timestamped", "PhoPyLSLhelper"]
     ```


2. **Auto-detection**

   - Scan the workspace root (`ACTIVE_DEV`) for projects containing `templating/pyproject_template_dev.toml_fragment` and `templating/pyproject_template_release.toml_fragment`
   - Match project names to groups defined in config file
   - Support both group-based and individual repo switching

3. **Template Reading**

   - Read the appropriate template file based on the mode (dev/release)
   - Handle missing templates gracefully with clear error messages

4. **pyproject.toml Modification**

   - Parse `pyproject.toml` using TOML library (or simple string replacement for the `[tool.uv.sources]` section)
   - Replace the entire `[tool.uv.sources]` section with template content
   - If `[tool.uv.sources]` doesn't exist, append it after `[tool.uv]` or at the end of the file
   - Preserve all other sections and formatting

5. **Command-line Interface**

   - Accept argument: `dev` or `release`
   - Support `--group <group-name>` to switch a defined group
   - Support `--all` to switch all detected repos
   - Support `--repo <repo-name>` to switch a single repo
   - Show which projects will be modified
   - Provide confirmation prompt (optional, or use `--yes` flag)
   - Display summary of changes made

### Files to Create/Modify

- **New file**: `ACTIVE_DEV/scripts/switch_uv_deps.py` (or user-level scripts directory)
  - Main switching logic
  - Workspace-aware auto-detection of projects
  - TOML parsing and replacement
  - CLI interface
  - Can be invoked from any project directory

### Workspace Detection Logic

The script should:

1. Detect current workspace by:

   - Checking for `.code-workspace` or `.vscode` folder in current or parent directories
   - Or accepting `--workspace-root` argument
   - Or scanning from current directory upward to find `ACTIVE_DEV` or similar parent structure

2. Search for projects with templating folders within the detected workspace area
3. Support running from any subdirectory within a workspace

### Technical Approach

- **Package Configuration**: Use `pyproject.toml` with `[project.scripts]` entry point for global command
- **Dependencies**: Minimal dependencies - use `tomllib` (Python 3.11+) or `tomli` for TOML parsing
- **Path Handling**: Use `pathlib` for cross-platform path handling
- **CLI**: Use `argparse` for command-line interface
- **Validation**: Check that template files exist before processing
- **Safety**: Create backup of pyproject.toml before modification (optional but recommended)
- **Installation**: Support both `uv pip install -e .` (editable) and `uv pip install .` (regular install)

### Installation

```bash
# Navigate to package directory
cd ACTIVE_DEV/uv-deps-switcher

# Install globally (editable mode for development)
uv pip install -e .

# Or install normally
uv pip install .
```

### Configuration File

Create a config file (`.uv-deps-switcher.toml` or `uv-deps-switcher.toml`) in workspace root or home directory:

```toml
[groups.main]
description = "Main development group"
repos = ["PhoLogToLabStreamingLayer", "whisper-timestamped"]

[groups.all]
description = "All repos with templating"
repos = ["PhoLogToLabStreamingLayer", "whisper-timestamped", "PhoPyLSLhelper"]
```

The tool will search for config files in:

1. Current directory and parent directories (up to workspace root)
2. User home directory (`~/.uv-deps-switcher.toml`)

### Example Usage

After installation, the command is available globally from any directory:

```bash
# Switch a defined group to dev mode
switch-uv-deps dev --group main

# Switch a defined group to release mode
switch-uv-deps release --group main

# Switch all detected repos (ignores groups)
switch-uv-deps dev --all

# Switch a single repo by name
switch-uv-deps dev --repo PhoLogToLabStreamingLayer

# With auto-confirmation (skip prompts)
switch-uv-deps dev --group main --yes

# Specify workspace root explicitly
switch-uv-deps dev --group main --workspace-root C:\Users\pho\repos\EmotivEpoc\ACTIVE_DEV

# Show which projects would be affected (dry run)
switch-uv-deps dev --group main --dry-run

# List available groups
switch-uv-deps list-groups
```

### Global Accessibility

The package will be available in all VSCode/Cursor instances after installation:

1. Install once globally using `uv pip install -e .` or `uv pip install .`
2. The console script entry point makes the command available system-wide
3. Works from any directory - automatically detects workspace context
4. Can be updated by reinstalling the package when changes are made

### Error Handling

- Check that template files exist
- Validate pyproject.toml is valid TOML before and after modification
- Handle cases where `[tool.uv.sources]` section is missing
- Provide clear error messages if projects can't be found or modified

### Testing Considerations

- Test with both projects (PhoLogToLabStreamingLayer and whisper-timestamped)
- Verify that switching dev→release→dev works correctly
- Ensure other sections of pyproject.toml are preserved