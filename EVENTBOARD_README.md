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
