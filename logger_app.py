import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pylsl
import pyxdf
from datetime import datetime, timedelta
import os
import threading
import time
import numpy as np
import json
import pickle
import mne
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import keyboard
import pyautogui
import socket
import sys

# _default_xdf_folder = Path(r'E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs').resolve()
_default_xdf_folder = Path('/media/halechr/MAX/cloud/University of Michigan Dropbox/Pho Hale/Personal/LabRecordedTextLog').resolve() ## Lab computer

class LoggerApp:
    # Class variable to track if an instance is already running
    _instance_running = False
    _lock_port = 12345  # Port to use for singleton check
    
    @classmethod
    def is_instance_running(cls):
        """Check if another instance is already running"""
        try:
            # Try to bind to a specific port
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind(('localhost', cls._lock_port))
            test_socket.close()
            return False
        except OSError:
            # Port is already in use, another instance is running
            return True
    
    @classmethod
    def mark_instance_running(cls):
        """Mark that an instance is now running"""
        cls._instance_running = True
    
    @classmethod
    def mark_instance_stopped(cls):
        """Mark that the instance has stopped"""
        cls._instance_running = False
    
    def __init__(self, root):
        self.root = root
        self.root.title("LSL Logger with XDF Recording")
        self.root.geometry("600x500")
        
        # Set application icon
        self.setup_app_icon()
        
        # Recording state
        self.recording = False
        self.recording_thread = None
        self.inlet = None
        self.recorded_data = []
        self.recording_start_time = None
        
        # System tray and hotkey state
        self.system_tray = None
        self.hotkey_popover = None
        self.is_minimized = False
        
        # Singleton lock socket
        self._lock_socket = None
        
        # Shutdown flag to prevent GUI updates during shutdown
        self._shutting_down = False
        
        # Timestamp tracking for text entry
        self.main_text_timestamp = None
        self.popover_text_timestamp = None
        
        # EventBoard configuration and outlet
        self.eventboard_config = None
        self.eventboard_outlet = None
        self.eventboard_buttons = {}
        self.eventboard_toggle_states = {}  # Track toggle states
        self.eventboard_time_offsets = {}   # Track time offset dropdowns
        
        # Load EventBoard configuration
        self.load_eventboard_config()
        
        # Create GUI elements first
        self.setup_gui()
        
        # Check for recovery files
        self.check_for_recovery()
        
        # Then create LSL outlets
        self.setup_lsl_outlet()
        self.setup_eventboard_outlet()
        
        # Setup system tray and global hotkey
        self.setup_system_tray()
        self.setup_global_hotkey()
    
    def load_eventboard_config(self):
        """Load EventBoard configuration from file"""
        config_file = Path("eventboard_config.json")
        
        if not config_file.exists():
            print(f"EventBoard config file not found: {config_file}")
            print("Using default configuration")
            self.eventboard_config = self.get_default_eventboard_config()
            return
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                self.eventboard_config = config_data.get('eventboard_config', {})
                print(f"EventBoard configuration loaded from {config_file}")
        except Exception as e:
            print(f"Error loading EventBoard config: {e}")
            print("Using default configuration")
            self.eventboard_config = self.get_default_eventboard_config()
    
    def get_default_eventboard_config(self):
        """Get default EventBoard configuration"""
        return {
            "title": "Event Board",
            "buttons": [
                {"id": f"button_{i}_{j}", "row": i, "col": j, "text": f"Button {i}-{j}", 
                 "event_name": f"EVENT_{i}_{j}", "color": "#2196F3", "type": "instantaneous"}
                for i in range(1, 4) for j in range(1, 6)
            ]
        }
    
    def setup_app_icon(self):
        """Setup application icon from PNG file"""
        try:
            icon_path = Path("LogToLabStreamingLayerIcon.png")
            if icon_path.exists():
                # Set window icon
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
                print(f"Application icon set from {icon_path}")
            else:
                print(f"Icon file not found: {icon_path}")
        except Exception as e:
            print(f"Error setting application icon: {e}")
    
    def parse_time_offset(self, time_str):
        """Parse time offset string (e.g., '5s', '2m', '1h') to seconds"""
        if not time_str or not time_str.strip():
            return 0
        
        time_str = time_str.strip().lower()
        
        # Extract number and unit
        import re
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([smh]?)$', time_str)
        
        if not match:
            return 0
        
        value = float(match.group(1))
        unit = match.group(2) or 's'  # Default to seconds if no unit
        
        # Convert to seconds
        if unit == 's':
            return value
        elif unit == 'm':
            return value * 60
        elif unit == 'h':
            return value * 3600
        else:
            return 0

    def acquire_singleton_lock(self):
        """Acquire the singleton lock by binding to the port"""
        try:
            self._lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._lock_socket.bind(('localhost', self._lock_port))
            self._lock_socket.listen(1)
            self.mark_instance_running()
            print("Singleton lock acquired successfully")
            return True
        except OSError as e:
            print(f"Failed to acquire singleton lock: {e}")
            return False
    
    def release_singleton_lock(self):
        """Release the singleton lock and clean up the socket"""
        try:
            if self._lock_socket:
                self._lock_socket.close()
                self._lock_socket = None
            self.mark_instance_stopped()
            print("Singleton lock released")
        except Exception as e:
            print(f"Error releasing singleton lock: {e}")
    
    def setup_recording_inlet(self):
        """Setup inlet to record our own stream"""
        try:
            # Look for our own stream
            streams = pylsl.resolve_byprop('name', 'TextLogger', timeout=2.0)
            if streams:
                self.inlet = pylsl.StreamInlet(streams[0])
                print("Recording inlet created successfully")
                
                # Auto-start recording after inlet is ready
                self.root.after(500, self.auto_start_recording)
                
            else:
                print("Could not find TextLogger stream for recording")
                self.inlet = None
        except Exception as e:
            print(f"Error creating recording inlet: {e}")
            self.inlet = None
    # ---------------------------------------------------------------------------- #
    #                               Recording Methods                              #
    # ---------------------------------------------------------------------------- #

    def setup_lsl_outlet(self):
        """Create an LSL outlet for sending messages"""
        try:
            # Create stream info
            info = pylsl.StreamInfo(
                name='TextLogger',
                type='Markers',
                channel_count=1,
                nominal_srate=pylsl.IRREGULAR_RATE,
                channel_format=pylsl.cf_string,
                source_id='textlogger_001'
            )
            
            # Add some metadata
            info.desc().append_child_value("manufacturer", "PhoLogToLabStreamingLayer")
            info.desc().append_child_value("version", "2.0")
            
            # Create outlet
            self.outlet = pylsl.StreamOutlet(info)
            
            # Update LSL status label safely
            try:
                if not self._shutting_down:
                    self.lsl_status_label.config(text="LSL Status: Connected", foreground="green")
            except tk.TclError:
                pass  # GUI is being destroyed
            
            # Setup inlet for recording our own stream (with delay to allow outlet to be discovered)
            self.root.after(1000, self.setup_recording_inlet)
            
        except Exception as e:
            try:
                if not self._shutting_down:
                    self.lsl_status_label.config(text=f"LSL Status: Error - {str(e)}", foreground="red")
            except tk.TclError:
                pass  # GUI is being destroyed
            self.outlet = None
    
    def setup_eventboard_outlet(self):
        """Create an LSL outlet for EventBoard events"""
        try:
            # Create stream info for EventBoard
            info = pylsl.StreamInfo(
                name='EventBoard',
                type='Markers',
                channel_count=1,
                nominal_srate=pylsl.IRREGULAR_RATE,
                channel_format=pylsl.cf_string,
                source_id='eventboard_001'
            )
            
            # Add some metadata
            info.desc().append_child_value("manufacturer", "PhoLogToLabStreamingLayer")
            info.desc().append_child_value("version", "2.0")
            info.desc().append_child_value("description", "EventBoard button events")
            
            # Create outlet
            self.eventboard_outlet = pylsl.StreamOutlet(info)
            print("EventBoard LSL outlet created successfully")
            
        except Exception as e:
            print(f"Error creating EventBoard LSL outlet: {e}")
            self.eventboard_outlet = None
    
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        try:
            # Create a simple icon (you can replace this with a custom icon file)
            icon_image = self.create_tray_icon()
            
            # Create system tray menu
            menu = pystray.Menu(
                pystray.MenuItem("Show App", self.show_app),
                pystray.MenuItem("Quick Log", self.show_hotkey_popover),
                pystray.MenuItem("Exit", self.quit_app)
            )
            
            # Create system tray icon
            self.system_tray = pystray.Icon(
                "logger_app",
                icon_image,
                "LSL Logger",
                menu
            )
            
            # Add double-click handler to show app
            self.system_tray.on_activate = self.show_app ## double-clicking doesn't foreground the app by default. Also clicking the windows close "X" just hides it to taskbar by default which I don't want. 
            
            # Start system tray in a separate thread
            threading.Thread(target=self.system_tray.run, daemon=True).start()
            
        except Exception as e:
            print(f"Error setting up system tray: {e}")
    
    def create_tray_icon(self):
        """Create icon for the system tray from PNG file"""
        try:
            icon_path = Path("LogToLabStreamingLayerIcon.png")
            if icon_path.exists():
                # Load and resize the PNG icon for system tray
                image = Image.open(str(icon_path))
                # Resize to appropriate size for system tray (16x16 or 32x32)
                image = image.resize((16, 16), Image.Resampling.LANCZOS)
                return image
            else:
                print(f"Tray icon file not found: {icon_path}, using default")
                return self.create_default_tray_icon()
        except Exception as e:
            print(f"Error loading tray icon: {e}, using default")
            return self.create_default_tray_icon()
    
    def create_default_tray_icon(self):
        """Create a simple default icon for the system tray"""
        # Create a 16x16 icon with a simple design
        width = 16
        height = 16
        
        # Create image with a dark background
        image = Image.new('RGB', (width, height), color='#2c3e50')
        draw = ImageDraw.Draw(image)
        
        # Draw a simple "L" shape in white
        draw.rectangle([2, 2, 6, 14], fill='white')  # Vertical line
        draw.rectangle([2, 10, 12, 14], fill='white')  # Horizontal line
        
        return image
    
    def setup_global_hotkey(self):
        """Setup global hotkey for quick log entry"""
        try:
            # Register Ctrl+Alt+L as the global hotkey
            keyboard.add_hotkey('ctrl+alt+l', self.show_hotkey_popover)
            print("Global hotkey Ctrl+Alt+L registered successfully")
        except Exception as e:
            print(f"Error setting up global hotkey: {e}")
    
    def show_hotkey_popover(self):
        """Show the hotkey popover for quick log entry"""
        if self.hotkey_popover:
            # If popover already exists, just focus it and select text
            self.hotkey_popover.focus_force()
            self.hotkey_popover.lift()
            self.quick_log_entry.focus()
            self.quick_log_entry.select_range(0, tk.END)
            # Additional focus handling for existing popover
            self.hotkey_popover.after(10, self.ensure_focus)
            return
        
        # Create popover window
        self.hotkey_popover = tk.Toplevel()
        self.hotkey_popover.title("Quick Log Entry")
        self.hotkey_popover.geometry("600x220")
        
        # Center the popover on the screen
        self.center_popover_on_active_monitor()
        
        # Make it always on top
        self.hotkey_popover.attributes('-topmost', True)
        
        # Remove window decorations for a cleaner look
        self.hotkey_popover.overrideredirect(True)
        
        # Force the popover to grab focus first
        self.hotkey_popover.focus_force()
        self.hotkey_popover.grab_set()  # Make it modal
        
        # Create content
        content_frame = ttk.Frame(self.hotkey_popover, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(content_frame, text="Quick Log Entry", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))
        
        # Entry field
        entry_frame = ttk.Frame(content_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))
        
        entry_label = ttk.Label(entry_frame, text="Message:")
        entry_label.pack(anchor=tk.W)
        
        self.quick_log_entry = tk.Entry(entry_frame, font=("Arial", 12))
        self.quick_log_entry.pack(fill=tk.X, pady=(5, 0))
        self.quick_log_entry.bind('<Key>', self.on_popover_text_change)  # Track first keystroke
        self.quick_log_entry.bind('<BackSpace>', self.on_popover_text_clear)
        self.quick_log_entry.bind('<Delete>', self.on_popover_text_clear)
        
        # Instructions label
        instructions_label = ttk.Label(content_frame, text="Press Enter to log, Esc to cancel", 
                                     font=("Arial", 9), foreground="gray")
        instructions_label.pack(pady=(5, 0))
        
        # Bind Enter key to log and close
        self.quick_log_entry.bind('<Return>', lambda e: self.quick_log_and_close())
        
        # Bind Escape key to close without logging
        self.hotkey_popover.bind('<Escape>', lambda e: self.close_hotkey_popover())
        
        # Focus the entry field and select all text
        self.quick_log_entry.focus()
        self.quick_log_entry.select_range(0, tk.END)
        
        # Additional focus handling to ensure it works reliably
        self.hotkey_popover.after(10, self.ensure_focus)
        
        # Handle window close
        self.hotkey_popover.protocol("WM_DELETE_WINDOW", self.close_hotkey_popover)
    
    def ensure_focus(self):
        """Ensure the text entry field has focus"""
        if self.hotkey_popover and self.quick_log_entry:
            self.quick_log_entry.focus_force()
            self.quick_log_entry.select_range(0, tk.END)
    
    def on_main_text_change(self, event=None):
        """Track when user first types in main text field"""
        if self.main_text_timestamp is None:
            self.main_text_timestamp = datetime.now()
    
    def on_popover_text_change(self, event=None):
        """Track when user first types in popover text field"""
        if self.popover_text_timestamp is None:
            self.popover_text_timestamp = datetime.now()
    
    def on_main_text_clear(self, event=None):
        """Reset timestamp when main text field is cleared"""
        if event and event.keysym in ['BackSpace', 'Delete']:
            # Check if field is now empty
            if not self.text_entry.get().strip():
                self.main_text_timestamp = None
    
    def on_popover_text_clear(self, event=None):
        """Reset timestamp when popover text field is cleared"""
        if event and event.keysym in ['BackSpace', 'Delete']:
            # Check if field is now empty
            if not self.quick_log_entry.get().strip():
                self.popover_text_timestamp = None
    
    def get_main_text_timestamp(self):
        """Get the timestamp when user first started typing in main field"""
        if self.main_text_timestamp:
            timestamp = self.main_text_timestamp
            self.main_text_timestamp = None  # Reset for next entry
            return timestamp
        return datetime.now()
    
    def get_popover_text_timestamp(self):
        """Get the timestamp when user first started typing in popover field"""
        if self.popover_text_timestamp:
            timestamp = self.popover_text_timestamp
            self.popover_text_timestamp = None  # Reset for next entry
            return timestamp
        return datetime.now()
    
    def center_popover_on_active_monitor(self):
        """Center the popover on the currently active monitor"""
        try:
            # Get screen dimensions and center the popover
            screen_width = self.hotkey_popover.winfo_screenwidth()
            screen_height = self.hotkey_popover.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 150) // 2
            self.hotkey_popover.geometry(f"+{x}+{y}")
                
        except Exception as e:
            print(f"Error centering popover: {e}")
            # Fallback to screen center
            screen_width = self.hotkey_popover.winfo_screenwidth()
            screen_height = self.hotkey_popover.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 150) // 2
            self.hotkey_popover.geometry(f"+{x}+{y}")
    
    def quick_log_and_close(self):
        """Log the message and close the popover"""
        message = self.quick_log_entry.get().strip()
        if message:
            # Send LSL message
            self.send_lsl_message(message)
            
            # Update main app display if visible
            if not self.is_minimized:
                # Use the timestamp when user first started typing in popover
                timestamp = self.get_popover_text_timestamp().strftime("%Y-%m-%d %H:%M:%S")
                self.update_log_display(message, timestamp)
            
            # Clear entry
            self.quick_log_entry.delete(0, tk.END)
        
        # Close popover
        self.close_hotkey_popover()
    
    def close_hotkey_popover(self):
        """Close the hotkey popover"""
        if self.hotkey_popover:
            self.hotkey_popover.destroy()
            self.hotkey_popover = None
    
    def show_app(self):
        """Show the main application window"""
        self.is_minimized = False
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def minimize_to_tray(self):
        """Minimize the app to system tray"""
        self.is_minimized = True
        self.root.withdraw()  # Hide the window
        try:
            if not self._shutting_down:
                self.minimize_button.config(text="Restore from Tray")
        except tk.TclError:
            pass  # GUI is being destroyed
    
    def restore_from_tray(self):
        """Restore the app from system tray"""
        self.is_minimized = False
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        try:
            if not self._shutting_down:
                self.minimize_button.config(text="Minimize to Tray")
        except tk.TclError:
            pass  # GUI is being destroyed
    
    def toggle_minimize(self):
        """Toggle between minimize and restore"""
        if self.is_minimized:
            self.restore_from_tray()
        else:
            self.minimize_to_tray()
    
    def quit_app(self):
        """Quit the application completely"""
        if self.system_tray:
            self.system_tray.stop()
        self.on_closing()


    def setup_gui(self):
        """Create the GUI elements"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # LSL Status label
        self.lsl_status_label = ttk.Label(main_frame, text="LSL Status: Initializing...", foreground="orange")
        self.lsl_status_label.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Recording control frame
        recording_frame = ttk.LabelFrame(main_frame, text="XDF Recording", padding="5")
        recording_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        recording_frame.columnconfigure(1, weight=1)
        
        # Recording status
        self.recording_status_label = ttk.Label(recording_frame, text="Not Recording", foreground="red")
        self.recording_status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Recording buttons
        self.start_recording_button = ttk.Button(recording_frame, text="Start Recording", command=self.start_recording)
        self.start_recording_button.grid(row=0, column=1, padx=5)
        
        self.stop_recording_button = ttk.Button(recording_frame, text="Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_recording_button.grid(row=0, column=2, padx=5)
        
        # Add Split Recording button
        self.split_recording_button = ttk.Button(recording_frame, text="Split Recording", command=self.split_recording, state="disabled")
        self.split_recording_button.grid(row=0, column=3, padx=5)
        
        # Add Minimize to Tray button
        self.minimize_button = ttk.Button(recording_frame, text="Minimize to Tray", command=self.toggle_minimize)
        self.minimize_button.grid(row=0, column=4, padx=5)
        
        # EventBoard frame
        self.setup_eventboard_gui(main_frame)

        # Text input label and entry frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Message:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Text input box
        self.text_entry = tk.Entry(input_frame, width=50)
        self.text_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.text_entry.bind('<Return>', lambda event: self.log_message())
        self.text_entry.bind('<Key>', self.on_main_text_change)  # Track first keystroke
        self.text_entry.bind('<BackSpace>', self.on_main_text_clear)
        self.text_entry.bind('<Delete>', self.on_main_text_clear)
        
        # Log button
        self.log_button = ttk.Button(input_frame, text="Log", command=self.log_message)
        self.log_button.grid(row=0, column=2)
        
        # Log display area
        ttk.Label(main_frame, text="Log History:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        
        # Scrolled text widget for log history
        self.log_display = scrolledtext.ScrolledText(main_frame, height=15, width=70)
        self.log_display.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Bottom frame for buttons and info
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        bottom_frame.columnconfigure(1, weight=1)
        
        # Clear log button
        ttk.Button(bottom_frame, text="Clear Log Display", command=self.clear_log_display).grid(row=0, column=0, sticky=tk.W)
        
        # Status info
        self.status_info_label = ttk.Label(bottom_frame, text="Ready")
        self.status_info_label.grid(row=0, column=2, sticky=tk.E)
        
        # Focus on text entry
        self.text_entry.focus()
    
    def setup_eventboard_gui(self, parent):
        """Setup EventBoard GUI with 3x5 grid of buttons and time offset dropdowns"""
        if not self.eventboard_config:
            return
        
        # EventBoard frame
        eventboard_frame = ttk.LabelFrame(parent, text=self.eventboard_config.get('title', 'Event Board'), padding="10")
        eventboard_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure grid for 3 rows and 5 columns (each cell has button + dropdown)
        for i in range(3):
            eventboard_frame.rowconfigure(i, weight=1)
        for j in range(5):
            eventboard_frame.columnconfigure(j, weight=1)
        
        # Create buttons based on configuration
        buttons = self.eventboard_config.get('buttons', [])
        for button_config in buttons:
            row = button_config.get('row', 1) - 1  # Convert to 0-based indexing
            col = button_config.get('col', 1) - 1  # Convert to 0-based indexing
            text = button_config.get('text', 'Button')
            event_name = button_config.get('event_name', 'UNKNOWN_EVENT')
            color = button_config.get('color', '#2196F3')
            button_type = button_config.get('type', 'instantaneous')
            button_id = button_config.get('id', f'button_{row}_{col}')
            
            # Create container frame for button and dropdown with integrated styling
            cell_frame = tk.Frame(eventboard_frame, bg=color, relief="raised", bd=2)
            cell_frame.grid(row=row, column=col, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
            cell_frame.columnconfigure(0, weight=4)  # Button takes 80% of width
            cell_frame.columnconfigure(1, weight=1)  # Dropdown takes 20% of width
            cell_frame.rowconfigure(0, weight=1)
            
            # Create button with custom styling (no border to integrate with container)
            button_text = text
            if button_type == 'toggleable':
                button_text = f"🔘 {text}"  # Add indicator for toggleable buttons
            
            button = tk.Button(
                cell_frame,
                text=button_text,
                font=("Arial", 9, "bold"),
                bg=color,
                fg="white",
                relief="flat",  # Flat relief to integrate with container
                bd=0,  # No border
                padx=5,
                pady=5,
                command=lambda e=event_name, t=text, bt=button_type, bid=button_id: self.on_eventboard_button_click(e, t, bt, bid)
            )
            
            button.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 1))
            
            # Create time offset entry with matching styling
            time_offset_var = tk.StringVar()
            time_offset_entry = tk.Entry(
                cell_frame,
                textvariable=time_offset_var,
                font=("Arial", 8),
                width=4,
                justify='center',
                bg=color,  # Match button background
                fg="white",  # Match button text color
                relief="flat",  # Flat relief to integrate
                bd=0,  # No border
                insertbackground="white"  # White cursor for visibility
            )
            time_offset_entry.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(1, 0))
            
            # Add placeholder text
            time_offset_entry.insert(0, "0s")
            time_offset_entry.config(fg='lightgray')  # Light gray for better visibility on colored background
            
            # Bind events for placeholder behavior and Enter key
            time_offset_entry.bind('<FocusIn>', lambda e, entry=time_offset_entry: self.on_time_offset_focus_in(entry))
            time_offset_entry.bind('<FocusOut>', lambda e, entry=time_offset_entry: self.on_time_offset_focus_out(entry))
            time_offset_entry.bind('<Key>', lambda e, entry=time_offset_entry: self.on_time_offset_key(entry))
            time_offset_entry.bind('<Return>', lambda e, entry=time_offset_entry, bid=button_id: self.on_time_offset_enter(entry, bid))
            
            # Store references
            self.eventboard_buttons[button_id] = button
            self.eventboard_time_offsets[button_id] = time_offset_var
            
            # Store original color for toggleable buttons
            if button_type == 'toggleable':
                self.eventboard_toggle_states[button_id] = False
                # Store the original color for later restoration
                if not hasattr(self, 'eventboard_original_colors'):
                    self.eventboard_original_colors = {}
                self.eventboard_original_colors[button_id] = color
    
    def on_time_offset_focus_in(self, entry):
        """Handle focus in on time offset entry"""
        if entry.get() == "0s":
            entry.delete(0, tk.END)
            entry.config(fg='white')  # White text for active input
    
    def on_time_offset_focus_out(self, entry):
        """Handle focus out on time offset entry"""
        if not entry.get().strip():
            entry.insert(0, "0s")
            entry.config(fg='lightgray')  # Light gray for placeholder
        else:
            entry.config(fg='white')  # White text for actual content
    
    def on_time_offset_key(self, entry):
        """Handle key press in time offset entry"""
        entry.config(fg='white')  # White text when typing
    
    def on_time_offset_enter(self, entry, button_id):
        """Handle Enter key press in time offset entry - trigger button click"""
        # Get the button and trigger its click
        button = self.eventboard_buttons.get(button_id)
        if button:
            # Get button configuration to determine type and event details
            buttons = self.eventboard_config.get('buttons', [])
            button_config = next((b for b in buttons if b.get('id') == button_id), None)
            
            if button_config:
                event_name = button_config.get('event_name', 'UNKNOWN_EVENT')
                button_text = button_config.get('text', 'Button')
                button_type = button_config.get('type', 'instantaneous')
                
                # Trigger the button click
                self.on_eventboard_button_click(event_name, button_text, button_type, button_id)
        
        # Clear the field and reset to placeholder
        entry.delete(0, tk.END)
        entry.insert(0, "0s")
        entry.config(fg='lightgray')  # Reset to placeholder color
        
        # Release focus from the entry field
        entry.master.focus_set()  # Focus the container frame instead
    
    def on_eventboard_button_click(self, event_name, button_text, button_type, button_id):
        """Handle EventBoard button click"""
        try:
            # Get time offset
            time_offset_str = self.eventboard_time_offsets.get(button_id, tk.StringVar()).get()
            time_offset_seconds = self.parse_time_offset(time_offset_str)
            
            # Calculate actual timestamp (current time - offset)
            actual_timestamp = datetime.now() - timedelta(seconds=time_offset_seconds)
            
            if button_type == 'toggleable':
                # Toggle the state
                current_state = self.eventboard_toggle_states.get(button_id, False)
                new_state = not current_state
                self.eventboard_toggle_states[button_id] = new_state
                
                # Update button appearance with enhanced visual feedback
                button = self.eventboard_buttons[button_id]
                original_color = self.eventboard_original_colors.get(button_id, "#2196F3")  # Default fallback
                
                if new_state:
                    # ON state - more prominent visual indicators
                    button.config(
                        text=f"🔴 {button_text}",
                        font=("Arial", 10, "bold"),  # Slightly larger, bolder font
                        bg="#FF4444"  # Brighter red background for active state
                    )
                    # Update container frame to show pressed state with enhanced styling
                    button.master.config(
                        relief="sunken",
                        bd=3,  # Thicker border for active state
                        bg="#FF4444"  # Match button background
                    )
                    event_suffix = "_START"
                else:
                    # OFF state - normal appearance
                    button.config(
                        text=f"🔘 {button_text}",
                        font=("Arial", 9, "bold"),  # Normal font size
                        bg=original_color  # Original button color
                    )
                    # Update container frame to show normal state
                    button.master.config(
                        relief="raised",
                        bd=2,  # Normal border thickness
                        bg=original_color  # Original color
                    )
                    event_suffix = "_END"
                
                # Update time offset entry field to match active state
                time_offset_entry = None
                for widget in button.master.winfo_children():
                    if isinstance(widget, tk.Entry):
                        time_offset_entry = widget
                        break
                
                if time_offset_entry:
                    if new_state:
                        # Active state - match the bright red theme
                        time_offset_entry.config(bg="#FF4444", fg="white")
                    else:
                        # Normal state - match original button color
                        time_offset_entry.config(bg=original_color, fg="white")
                
                # Send LSL event with toggle state
                self.send_eventboard_message(f"{event_name}{event_suffix}", button_text, actual_timestamp, new_state)
                
                # Update log display
                log_message = f"EventBoard: {button_text} {'ON' if new_state else 'OFF'} ({event_name}{event_suffix})"
                if time_offset_seconds > 0:
                    log_message += f" [offset: -{time_offset_str}]"
                
            else:
                # Instantaneous event
                self.send_eventboard_message(event_name, button_text, actual_timestamp, None)
                
                # Update log display
                log_message = f"EventBoard: {button_text} ({event_name})"
                if time_offset_seconds > 0:
                    log_message += f" [offset: -{time_offset_str}]"
            
            # Update log display
            timestamp = actual_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            self.update_log_display(log_message, timestamp)
            
            print(f"EventBoard button clicked: {button_text} -> {event_name} (type: {button_type})")
            
        except Exception as e:
            print(f"Error handling EventBoard button click: {e}")
            messagebox.showerror("EventBoard Error", f"Failed to send event: {str(e)}")
    
    def send_eventboard_message(self, event_name, button_text, timestamp=None, toggle_state=None):
        """Send EventBoard message via LSL"""
        if self.eventboard_outlet:
            try:
                # Use provided timestamp or current time
                if timestamp is None:
                    timestamp = datetime.now()
                
                # Create event message with timestamp, button info, and toggle state
                event_message = f"{event_name}|{button_text}|{timestamp.isoformat()}"
                
                # Add toggle state if provided
                if toggle_state is not None:
                    event_message += f"|TOGGLE:{toggle_state}"
                
                self.eventboard_outlet.push_sample([event_message])
                print(f"EventBoard LSL message sent: {event_message}")
            except Exception as e:
                print(f"Error sending EventBoard LSL message: {e}")
                raise
        else:
            print("EventBoard LSL outlet not available")
            raise Exception("EventBoard LSL outlet not available")

    # ---------------------------------------------------------------------------- #
    #                               Recording Methods                              #
    # ---------------------------------------------------------------------------- #
    def start_recording(self):
        """Start XDF recording"""
        if not self.inlet:
            messagebox.showerror("Error", "No LSL inlet available for recording")
            return
        
        # Create default filename with timestamp
        current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{current_timestamp}_log.xdf"
        
        # Ensure the default directory exists
        _default_xdf_folder.mkdir(parents=True, exist_ok=True)
        
        filename = filedialog.asksaveasfilename(
            initialdir=str(_default_xdf_folder),
            initialfile=default_filename,
            defaultextension=".xdf",
            filetypes=[("XDF files", "*.xdf"), ("All files", "*.*")],
            title="Save XDF Recording As"
        )
        
        if not filename:
            return
        
        self.recording = True
        self.recorded_data = []
        self.recording_start_time = pylsl.local_clock()
        self.xdf_filename = filename
        
        # Create backup file for crash recovery
        self.backup_filename = str(Path(filename).with_suffix('.backup.json'))
        
        # Update GUI
        try:
            if not self._shutting_down:
                self.recording_status_label.config(text="Recording...", foreground="green")
                self.start_recording_button.config(state="disabled")
                self.stop_recording_button.config(state="normal")
                self.split_recording_button.config(state="normal")  # Enable split button
                self.status_info_label.config(text=f"Recording to: {os.path.basename(filename)}")
        except tk.TclError:
            pass  # GUI is being destroyed
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
        self.recording_thread.start()
        
        self.update_log_display("XDF Recording started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def auto_start_recording(self):
        """Automatically start recording on app launch if inlet is available"""
        if not self.inlet:
            print("Cannot auto-start recording: no inlet available")
            return
        
        try:
            # Create default filename with timestamp
            current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{current_timestamp}_log.xdf"
            
            # Ensure the default directory exists
            _default_xdf_folder.mkdir(parents=True, exist_ok=True)
            
            # Set filename directly without dialog
            self.xdf_filename = str(_default_xdf_folder / default_filename)
            
            self.recording = True
            self.recorded_data = []
            self.recording_start_time = pylsl.local_clock()
            
            # Create backup file for crash recovery
            self.backup_filename = str(Path(self.xdf_filename).with_suffix('.backup.json'))
            
            # Update GUI
            try:
                if not self._shutting_down:
                    self.recording_status_label.config(text="Recording...", foreground="green")
                    self.start_recording_button.config(state="disabled")
                    self.stop_recording_button.config(state="normal")
                    self.split_recording_button.config(state="normal")  # Enable split button
                    self.status_info_label.config(text=f"Auto-recording to: {os.path.basename(self.xdf_filename)}")
            except tk.TclError:
                pass  # GUI is being destroyed
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
            self.recording_thread.start()
            
            self.update_log_display("XDF Recording auto-started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"Auto-started recording to: {self.xdf_filename}")
            
            # Log the auto-start event both in GUI and via LSL
            auto_start_message = f"RECORDING_AUTO_STARTED: {default_filename}"
            self.send_lsl_message(auto_start_message)  # Send via LSL
            self.update_log_display("XDF Recording auto-started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"Auto-started recording to: {self.xdf_filename}")

        except Exception as e:
            print(f"Error auto-starting recording: {e}")
            self.update_log_display(f"Auto-start failed: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    def recording_worker(self):
        """Background thread for recording LSL data with incremental backup"""
        sample_count = 0
        
        while self.recording and self.inlet:
            try:
                sample, timestamp = self.inlet.pull_sample(timeout=1.0)
                if sample:
                    data_point = {
                        'sample': sample,
                        'timestamp': timestamp
                    }
                    self.recorded_data.append(data_point)
                    sample_count += 1
                    
                    # Auto-save every 10 samples to backup file
                    if sample_count % 10 == 0:
                        self.save_backup()
                        
            except Exception as e:
                print(f"Error in recording worker: {e}")
                break

    def stop_recording(self):
        """Stop XDF recording and save file"""
        if not self.recording:
            return
        
        self.recording = False

        # Log the stop event via LSL before saving
        stop_message = f"RECORDING_STOPPED: {os.path.basename(self.xdf_filename)}"
        self.send_lsl_message(stop_message)
   
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        

        # Save XDF file
        self.save_xdf_file()
        
        # Clean up backup file
        try:
            if hasattr(self, 'backup_filename') and os.path.exists(self.backup_filename):
                os.remove(self.backup_filename)
        except Exception as e:
            print(f"Error removing backup file: {e}")
        
        # Update GUI
        try:
            if not self._shutting_down:
                self.recording_status_label.config(text="Not Recording", foreground="red")
                self.start_recording_button.config(state="normal")
                self.stop_recording_button.config(state="disabled")
                self.split_recording_button.config(state="disabled")  # Disable split button
                self.status_info_label.config(text="Ready")
        except tk.TclError:
            pass  # GUI is being destroyed
        
        self.update_log_display("XDF Recording stopped and saved", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    def split_recording(self):
        """Split recording into a new file - stop current and start new"""
        if not self.recording:
            return
        
        try:
            # Stop current recording (this will save the current data)
            self.stop_recording()
            
            # Wait a moment for the stop to complete
            self.root.after(100, self.start_new_split_recording)
            
        except Exception as e:
            print(f"Error splitting recording: {e}")
            self.update_log_display(f"Split recording failed: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    def start_new_split_recording(self):
        """Start new recording after split"""
        if not self.inlet:
            print("Cannot split recording: no inlet available")
            return
        
        try:
            # Create new filename with timestamp
            current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{current_timestamp}_log.xdf"
            
            # Ensure the default directory exists
            _default_xdf_folder.mkdir(parents=True, exist_ok=True)
            
            # Set new filename directly
            self.xdf_filename = str(_default_xdf_folder / new_filename)
            
            self.recording = True
            self.recorded_data = []
            self.recording_start_time = pylsl.local_clock()
            
            # Create backup file for crash recovery
            self.backup_filename = str(Path(self.xdf_filename).with_suffix('.backup.json'))
            
            # Update GUI
            try:
                if not self._shutting_down:
                    self.recording_status_label.config(text="Recording...", foreground="green")
                    self.start_recording_button.config(state="disabled")
                    self.stop_recording_button.config(state="normal")
                    self.split_recording_button.config(state="normal")
                    self.status_info_label.config(text=f"Split to: {os.path.basename(self.xdf_filename)}")
            except tk.TclError:
                pass  # GUI is being destroyed
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
            self.recording_thread.start()
            
            self.update_log_display(f"Recording split to new file: {new_filename}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"Split recording to new file: {self.xdf_filename}")
            
            # Log the split event both in GUI and via LSL
            split_message = f"RECORDING_SPLIT_NEW_FILE: {new_filename}"
            self.send_lsl_message(split_message)  # Send via LSL
            self.update_log_display(f"Recording split to new file: {new_filename}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print(f"Split recording to new file: {self.xdf_filename}")
            
        except Exception as e:
            print(f"Error starting new split recording: {e}")
            self.update_log_display(f"Split restart failed: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


    # ---------------------------------------------------------------------------- #
    #                             Backups and Recovery                             #
    # ---------------------------------------------------------------------------- #
    def save_backup(self):
        """Save current data to backup file"""
        try:
            backup_data = {
                'recorded_data': self.recorded_data,
                'recording_start_time': self.recording_start_time,
                'sample_count': len(self.recorded_data)
            }
            
            with open(self.backup_filename, 'w') as f:
                json.dump(backup_data, f, default=str)
                
        except Exception as e:
            print(f"Error saving backup: {e}")


    def check_for_recovery(self):
        """Check for backup files and offer recovery on startup"""
        backup_files = list(_default_xdf_folder.glob('*.backup.json'))
        
        if backup_files:
            response = messagebox.askyesno(
                "Recovery Available", 
                f"Found {len(backup_files)} backup file(s) from previous sessions. "
                "Would you like to recover them?"
            )
            
            if response:
                for backup_file in backup_files:
                    self.recover_from_backup(backup_file)

    def recover_from_backup(self, backup_file):
        """Recover data from backup file"""
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Ask user for recovery filename
            original_name = backup_file.stem.replace('.backup', '')
            recovery_filename = filedialog.asksaveasfilename(
                initialdir=str(_default_xdf_folder),
                initialfile=f"{original_name}_recovered.xdf",
                defaultextension=".xdf",
                filetypes=[("XDF files", "*.xdf"), ("All files", "*.*")],
                title="Save Recovered XDF As"
            )
            
            if recovery_filename:
                # Restore data
                self.recorded_data = backup_data['recorded_data']
                self.xdf_filename = recovery_filename
                
                # Save as XDF
                self.save_xdf_file()
                
                # Remove backup file
                os.remove(backup_file)
                
                messagebox.showinfo("Recovery Complete", 
                    f"Recovered {len(self.recorded_data)} samples to {recovery_filename}")
                
        except Exception as e:
            messagebox.showerror("Recovery Error", f"Failed to recover from backup: {str(e)}")

    # ---------------------------------------------------------------------------- #
    #                              Save/Write Methods                              #
    # ---------------------------------------------------------------------------- #
    def save_xdf_file(self):
        """Save recorded data using MNE"""
        if not self.recorded_data:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        try:
            # Extract messages and timestamps
            messages = []
            timestamps = []
            
            for data_point in self.recorded_data:
                message = data_point['sample'][0] if data_point['sample'] else ''
                timestamp = data_point['timestamp']
                messages.append(message)
                timestamps.append(timestamp)
            
            # Convert timestamps to relative times (from first sample)
            if timestamps:
                first_timestamp = timestamps[0]
                relative_timestamps = [ts - first_timestamp for ts in timestamps]
            else:
                relative_timestamps = []
            
            # Create annotations (MNE's way of handling markers/events)
            # Set orig_time=None to avoid timing conflicts
            annotations = mne.Annotations(
                onset=relative_timestamps,
                duration=[0.0] * len(relative_timestamps),  # Instantaneous events
                description=messages,
                orig_time=None  # This fixes the timing conflict
            )
            
            # Create a minimal info structure for the markers
            info = mne.create_info(
                ch_names=['TextLogger_Markers'],
                sfreq=1000,  # Dummy sampling rate for the minimal channel
                ch_types=['misc']
            )
            
            # Create raw object with minimal dummy data
            # We need at least some data points to create a valid Raw object
            if len(timestamps) > 0:
                # Create dummy data spanning the recording duration
                duration = relative_timestamps[-1] if relative_timestamps else 1.0
                n_samples = int(duration * 1000) + 1000  # Add buffer
                dummy_data = np.zeros((1, n_samples))
            else:
                dummy_data = np.zeros((1, 1000))  # Minimum 1 second of data
            
            raw = mne.io.RawArray(dummy_data, info)
            
            # Set measurement date to match the first timestamp
            if timestamps:
                raw.set_meas_date(timestamps[0])
            
            raw.set_annotations(annotations)
            
            # Add metadata to the raw object
            raw.info['description'] = 'TextLogger LSL Stream Recording'
            raw.info['experimenter'] = 'PhoLogToLabStreamingLayer'

            # Determine output filename and format
            if self.xdf_filename.endswith('.xdf'):
                # Save as FIF (MNE's native format)
                fif_filename = self.xdf_filename.replace('.xdf', '.fif')
                raw.save(fif_filename, overwrite=True)
                actual_filename = fif_filename
                file_type = "FIF"
            else:
                # Use the original filename
                raw.save(self.xdf_filename, overwrite=True)
                actual_filename = self.xdf_filename
                file_type = "FIF"
            
            # Also save a CSV for easy reading

            
            if isinstance(actual_filename, str):
                actual_filename = Path(actual_filename).resolve()

            _default_CSV_folder = actual_filename.parent.joinpath('CSV')
            _default_CSV_folder.mkdir(parents=True, exist_ok=True)
            print(f'_default_CSV_folder: "{_default_CSV_folder}"')

            csv_filename: str = actual_filename.name.replace('.fif', '_events.csv')
            csv_filepath: Path = _default_CSV_folder.joinpath(csv_filename).resolve()

            self.save_events_csv(csv_filepath, messages, timestamps)
            
            _status_str: str = (f"{file_type} file saved: '{actual_filename}'\n"
                f"Events CSV saved: '{csv_filepath}'\n"
                f"Recorded {len(self.recorded_data)} samples")
            self.update_log_display(_status_str, timestamp=None)
            # messagebox.showinfo("Success", _status_str)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            print(f"Detailed error: {e}")
            import traceback
            traceback.print_exc()


    def save_events_csv(self, csv_filename, messages, timestamps):
        """Save events as CSV for easy reading"""
        try:
            import csv
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'LSL_Time', 'Message'])
                
                for i, (message, lsl_time) in enumerate(zip(messages, timestamps)):
                    # Convert LSL timestamp to readable datetime
                    readable_time = datetime.fromtimestamp(lsl_time).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    writer.writerow([readable_time, lsl_time, message])
                    
        except Exception as e:
            print(f"Error saving CSV: {e}")


    def log_message(self):
        """Handle log button click"""
        message = self.text_entry.get().strip()
        
        if not message:
            messagebox.showwarning("Warning", "Please enter a message to log.")
            return
        
        # Use the timestamp when user first started typing
        timestamp = self.get_main_text_timestamp().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send LSL message
        self.send_lsl_message(message)
        
        # Update display
        self.update_log_display(message, timestamp)
        
        # Clear text entry
        self.text_entry.delete(0, tk.END)
        self.text_entry.focus()
    
    def send_lsl_message(self, message):
        """Send message via LSL"""
        if self.outlet:
            try:
                # Send message with timestamp
                self.outlet.push_sample([message])
                print(f"LSL message sent: {message}")
            except Exception as e:
                print(f"Error sending LSL message: {e}")
                messagebox.showerror("LSL Error", f"Failed to send LSL message: {str(e)}")
        else:
            print("LSL outlet not available")
    
    def update_log_display(self, message, timestamp=None):
        """Update the log display area"""
        # Don't update GUI if app is shutting down
        if self._shutting_down:
            return
            
        if timestamp is None:
            ## get now as the timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            log_entry = f"[{timestamp}] {message}\n"
            self.log_display.insert(tk.END, log_entry)
            self.log_display.see(tk.END)  # Auto-scroll to bottom
        except tk.TclError:
            # GUI is being destroyed, ignore the error
            pass
    
    def clear_log_display(self):
        """Clear the log display area"""
        self.log_display.delete(1.0, tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        # Set shutdown flag to prevent GUI updates
        self._shutting_down = True
        
        # Stop recording if active
        if self.recording:
            self.stop_recording()
        
        # Clean up hotkey
        try:
            keyboard.remove_hotkey('ctrl+alt+l')
        except:
            pass
        
        # Clean up system tray
        if self.system_tray:
            self.system_tray.stop()
        
        # Clean up LSL resources
        if hasattr(self, 'outlet') and self.outlet:
            del self.outlet
        if hasattr(self, 'inlet') and self.inlet:
            del self.inlet
        if hasattr(self, 'eventboard_outlet') and self.eventboard_outlet:
            del self.eventboard_outlet
        
        # Release singleton lock
        self.release_singleton_lock()
        
        self.root.destroy()



def main():
    # Check if another instance is already running
    if LoggerApp.is_instance_running():
        messagebox.showerror("Instance Already Running", 
                           "Another instance of LSL Logger is already running.\n"
                           "Only one instance can run at a time.")
        sys.exit(1)
    
    root = tk.Tk()
    app = LoggerApp(root)
    
    # Try to acquire the singleton lock
    if not app.acquire_singleton_lock():
        messagebox.showerror("Startup Error", 
                           "Failed to acquire singleton lock.\n"
                           "Another instance may be running.")
        root.destroy()
        sys.exit(1)
    
    # # Handle window closing - minimize to tray instead of closing
    # def on_closing():
    #     app.minimize_to_tray()
    # root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
