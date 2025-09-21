#!/usr/bin/env python3
"""
Test script for EventBoard functionality
This script creates a simple LSL inlet to receive EventBoard events
"""

import pylsl
import time
from datetime import datetime

def test_eventboard_receiver():
    """Test receiving EventBoard events"""
    print("Looking for EventBoard LSL stream...")
    
    # Look for EventBoard stream
    streams = pylsl.resolve_byprop('name', 'EventBoard', timeout=5.0)
    
    if not streams:
        print("No EventBoard stream found!")
        return
    
    print(f"Found EventBoard stream: {streams[0].name()}")
    
    # Create inlet
    inlet = pylsl.StreamInlet(streams[0])
    
    print("Listening for EventBoard events... (Press Ctrl+C to stop)")
    
    try:
        while True:
            # Get sample with timeout
            sample, timestamp = inlet.pull_sample(timeout=1.0)
            
            if sample:
                # Parse the event message
                event_message = sample[0]
                parts = event_message.split('|')
                
                if len(parts) >= 3:
                    event_name = parts[0]
                    button_text = parts[1]
                    timestamp_str = parts[2]
                    toggle_state = None
                    
                    # Check for toggle state
                    if len(parts) >= 4 and parts[3].startswith('TOGGLE:'):
                        toggle_state = parts[3].split(':', 1)[1]
                    
                    # Convert LSL timestamp to readable time
                    readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    
                    # Parse event timestamp
                    try:
                        event_time = datetime.fromisoformat(timestamp_str)
                        event_time_str = event_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    except:
                        event_time_str = timestamp_str
                    
                    print(f"[{readable_time}] EventBoard: {button_text} -> {event_name}")
                    print(f"  LSL Time: {timestamp}")
                    print(f"  Event Time: {event_time_str}")
                    
                    if toggle_state is not None:
                        print(f"  Toggle State: {'ON' if toggle_state == 'True' else 'OFF'}")
                    
                    print("-" * 50)
                else:
                    print(f"Received: {event_message}")
    
    except KeyboardInterrupt:
        print("\nStopping EventBoard receiver...")
    
    finally:
        inlet.close()

if __name__ == "__main__":
    test_eventboard_receiver()
