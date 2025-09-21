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


# EventBoard Functionality

The Logger App now includes an EventBoard feature that provides a 3x5 grid of customizable buttons for sending LabStreamingLayer (LSL) events.

## Features

- **3x5 Button Grid**: 15 customizable buttons arranged in 3 rows and 5 columns
- **LSL Integration**: Each button click sends events to a dedicated "EventBoard" LSL stream
- **Configurable**: Button text, colors, and event names are defined in a JSON configuration file
- **Real-time Logging**: All button clicks are logged in the main application log

## Configuration

The EventBoard is configured using the `eventboard_config.json` file. This file defines:

- **title**: The title displayed above the button grid
- **buttons**: Array of button configurations, each containing:
  - `id`: Unique identifier for the button
  - `row`: Row position (1-3)
  - `col`: Column position (1-5)
  - `text`: Display text on the button
  - `event_name`: LSL event name sent when clicked
  - `color`: Button background color (hex format)

### Example Configuration

```json
{
  "eventboard_config": {
    "title": "Event Board",
    "buttons": [
      {
        "id": "button_1_1",
        "row": 1,
        "col": 1,
        "text": "Start Task",
        "event_name": "TASK_START",
        "color": "#4CAF50"
      },
      {
        "id": "button_1_2",
        "row": 1,
        "col": 2,
        "text": "Pause",
        "event_name": "TASK_PAUSE",
        "color": "#FF9800"
      }
    ]
  }
}
```

## LSL Stream Details

The EventBoard creates a dedicated LSL stream with the following properties:

- **Stream Name**: "EventBoard"
- **Stream Type**: "Markers"
- **Channel Count**: 1
- **Channel Format**: String
- **Sample Rate**: Irregular (event-driven)

### Event Message Format

Each button click sends a message in the format:
```
EVENT_NAME|BUTTON_TEXT|TIMESTAMP
```

Example:
```
TASK_START|Start Task|2024-01-15T10:30:45.123456
```

## Usage

1. **Start the Logger App**: Run `python logger_app.py`
2. **EventBoard appears**: The 3x5 button grid will be displayed below the recording controls
3. **Click buttons**: Each button click sends an LSL event and logs the action
4. **Monitor events**: Use the provided `test_eventboard.py` script to monitor incoming events

## Testing

To test the EventBoard functionality:

1. Start the Logger App
2. In a separate terminal, run: `python test_eventboard.py`
3. Click buttons in the Logger App
4. Observe the events being received in the test script

## Customization

To customize the EventBoard:

1. Edit `eventboard_config.json` to modify button properties
2. Restart the Logger App to load the new configuration
3. If the config file is missing, the app will use default button configurations

## Integration with Existing Features

The EventBoard integrates seamlessly with existing Logger App features:

- **Recording**: EventBoard events are recorded along with text messages
- **Logging**: All button clicks appear in the main log display
- **LSL**: Events are sent via a separate LSL stream from text messages
- **System Tray**: EventBoard remains accessible when the app is minimized

## Troubleshooting

- **No buttons appear**: Check that `eventboard_config.json` exists and is valid JSON
- **LSL events not received**: Verify that the EventBoard LSL outlet is created successfully (check console output)
- **Button colors not applied**: Ensure color values are in valid hex format (e.g., "#FF0000")




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


# Installing Tk/KTinker on macOS
```bash
brew install tcl-tk
export LDFLAGS="-L$(brew --prefix tcl-tk)/lib"
export CPPFLAGS="-I$(brew --prefix tcl-tk)/include"
export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"
export PATH="$(brew --prefix tcl-tk)/bin:$PATH"

pyenv uninstall 3.9.13
pyenv install 3.9.13

```