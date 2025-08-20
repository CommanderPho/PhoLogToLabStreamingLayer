# Enhanced LSL Logger App
a complete but minimal python app that allows the user to take timestampped notes to labstreaminglayer and have them simultaneously saved out to file (.xdf/.csv)

This enhanced version of the LSL Logger App includes system tray functionality and global hotkey support for quick log entries.

## New Features

### 1. System Tray Integration
- **Minimize to Tray**: Click the "Minimize to Tray" button or close the window (X) to minimize the app to the system tray
- **Tray Icon**: The app continues running in the background with a system tray icon
- **Tray Menu**: Right-click the tray icon for options:
  - Show App: Restore the main window
  - Quick Log: Open the quick log entry popover
  - Exit: Completely close the application
- **Double-click**: Double-click the tray icon to restore the main window

### 2. Global Hotkey Support
- **Hotkey**: Press `Ctrl+Alt+L` from anywhere to summon a quick log entry popover
- **Popover Features**:
  - Appears centered on the active monitor
  - Always on top
  - Auto-focused text entry
  - Press `Enter` to log and close
  - Press `Escape` to cancel
  - Clean, minimal interface

### 3. Enhanced Window Management
- **Smart Minimizing**: Closing the window (X button) minimizes to tray instead of closing
- **Toggle Button**: The minimize button toggles between "Minimize to Tray" and "Restore from Tray"
- **Background Operation**: App continues recording and logging while minimized

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   python logger_app.py
   ```

   Or use the batch file:
   ```bash
   install_and_run.bat
   ```

## Usage

### Basic Operation
1. Start the app - it will auto-start recording if LSL inlet is available
2. Use the main interface for detailed logging and recording management
3. Minimize to tray when you want the app to run in the background

### Quick Logging
1. Press `Ctrl+Alt+L` from anywhere
2. Type your log message
3. Press `Enter` to log and close, or `Escape` to cancel

### System Tray
1. Right-click the tray icon for options
2. Double-click to restore the main window
3. Use "Exit" to completely close the application

## Dependencies

- `pylsl`: Lab Streaming Layer support
- `pyxdf`: XDF file handling
- `numpy`: Numerical operations
- `mne`: MNE-Python for data processing
- `pystray`: System tray functionality
- `Pillow`: Image processing for tray icon
- `keyboard`: Global hotkey support
- `pyautogui`: Screen positioning
- `pywin32`: Windows API access

## Notes

- The global hotkey `Ctrl+Alt+L` works system-wide
- The app continues recording LSL data while minimized
- All existing functionality (XDF recording, LSL streaming) remains intact
- The app automatically centers the popover on the active monitor
- System tray icon shows a simple "L" design for easy identification

## Troubleshooting

- **Hotkey not working**: Ensure no other application is using `Ctrl+Alt+L`
- **Tray icon not visible**: Check if your system tray is hidden or collapsed
- **Permission errors**: Some features may require administrator privileges on Windows
- **Dependencies**: Ensure all packages are properly installed with `pip install -r requirements.txt`


# Running
```bash
source .venv/bin/activate
python main.py 
python logger_app.py

```

## Installing `liblsl` binaries
https://labstreaminglayer.readthedocs.io/dev/lib_dev.html
```bash
git clone https://github.com/CommanderPho/PhoLogToLabStreamingLayer.git
cd PhoLogToLabStreamingLayer/
uv sync
source .venv/bin/activate


mkdir lib
cd lib
git clone --depth=1 https://github.com/sccn/liblsl.git
cd liblsl/
mkdir build
cd build/
cmake ..
make
sudo make install

```
