import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pylsl
import pyxdf
from datetime import datetime
import os
import threading
import time
import numpy as np
from pathlib import Path

_default_xdf_folder = Path(r'E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs').resolve()


import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pylsl
import pyxdf
from datetime import datetime
import os
import threading
import time
import numpy as np
from pathlib import Path

_default_xdf_folder = Path(r'E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs').resolve()


class LoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LSL Logger with XDF Recording")
        self.root.geometry("600x500")
        
        # Recording state
        self.recording = False
        self.recording_thread = None
        self.inlet = None
        self.recorded_data = []
        self.recording_start_time = None
        
        # Create GUI elements first
        self.setup_gui()
        
        # Then create LSL outlet
        self.setup_lsl_outlet()
        
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
            info.desc().append_child_value("version", "1.0")
            
            # Create outlet
            self.outlet = pylsl.StreamOutlet(info)
            self.lsl_status_label.config(text="LSL Status: Connected", foreground="green")
            
            # Setup inlet for recording our own stream (with delay to allow outlet to be discovered)
            self.root.after(1000, self.setup_recording_inlet)
            
        except Exception as e:
            self.lsl_status_label.config(text=f"LSL Status: Error - {str(e)}", foreground="red")
            self.outlet = None
    
    def setup_recording_inlet(self):
        """Setup inlet to record our own stream"""
        try:
            # Look for our own stream
            streams = pylsl.resolve_byprop('name', 'TextLogger', timeout=2.0)
            if streams:
                self.inlet = pylsl.StreamInlet(streams[0])
                print("Recording inlet created successfully")
            else:
                print("Could not find TextLogger stream for recording")
                self.inlet = None
        except Exception as e:
            print(f"Error creating recording inlet: {e}")
            self.inlet = None
    
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
        
        # Text input label and entry frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Message:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Text input box
        self.text_entry = tk.Entry(input_frame, width=50)
        self.text_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.text_entry.bind('<Return>', lambda event: self.log_message())
        
        # Log button
        self.log_button = ttk.Button(input_frame, text="Log", command=self.log_message)
        self.log_button.grid(row=0, column=2)
        
        # Log display area
        ttk.Label(main_frame, text="Log History:").grid(row=3, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        
        # Scrolled text widget for log history
        self.log_display = scrolledtext.ScrolledText(main_frame, height=15, width=70)
        self.log_display.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Bottom frame for buttons and info
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))
        bottom_frame.columnconfigure(1, weight=1)
        
        # Clear log button
        ttk.Button(bottom_frame, text="Clear Log Display", command=self.clear_log_display).grid(row=0, column=0, sticky=tk.W)
        
        # Status info
        self.status_info_label = ttk.Label(bottom_frame, text="Ready")
        self.status_info_label.grid(row=0, column=2, sticky=tk.E)
        
        # Focus on text entry
        self.text_entry.focus()
    
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
        
        # Create full default path
        default_path = _default_xdf_folder / default_filename
        
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
        
        # Update GUI
        self.recording_status_label.config(text="Recording...", foreground="green")
        self.start_recording_button.config(state="disabled")
        self.stop_recording_button.config(state="normal")
        self.status_info_label.config(text=f"Recording to: {os.path.basename(filename)}")
        
        # Start recording thread
        self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
        self.recording_thread.start()
        
        self.update_log_display("XDF Recording started", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def stop_recording(self):
        """Stop XDF recording and save file"""
        if not self.recording:
            return
        
        self.recording = False
        
        # Wait for recording thread to finish
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # Save XDF file
        self.save_xdf_file()
        
        # Update GUI
        self.recording_status_label.config(text="Not Recording", foreground="red")
        self.start_recording_button.config(state="normal")
        self.stop_recording_button.config(state="disabled")
        self.status_info_label.config(text="Ready")
        
        self.update_log_display("XDF Recording stopped and saved", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def recording_worker(self):
        """Background thread for recording LSL data"""
        while self.recording and self.inlet:
            try:
                sample, timestamp = self.inlet.pull_sample(timeout=1.0)
                if sample:
                    self.recorded_data.append({
                        'sample': sample,
                        'timestamp': timestamp
                    })
            except Exception as e:
                print(f"Error in recording worker: {e}")
                break
    
    def save_xdf_file(self):
        """Save recorded data to XDF file"""
        if not self.recorded_data:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        try:
            # Create XDF structure
            stream_data = {
                'time_series': [],
                'time_stamps': [],
                'info': {
                    'name': ['TextLogger'],
                    'type': ['Markers'],
                    'channel_count': [1],
                    'nominal_srate': [0],  # Irregular rate
                    'channel_format': ['string'],
                    'source_id': ['textlogger_001']
                }
            }
            
            # Add recorded data
            for data_point in self.recorded_data:
                stream_data['time_series'].append(data_point['sample'])
                stream_data['time_stamps'].append(data_point['timestamp'])
            
            # Convert to numpy arrays
            stream_data['time_series'] = np.array(stream_data['time_series'])
            stream_data['time_stamps'] = np.array(stream_data['time_stamps'])
            
            # Save XDF file
            pyxdf.save_xdf(self.xdf_filename, [stream_data])
            
            messagebox.showinfo("Success", f"XDF file saved: {self.xdf_filename}\nRecorded {len(self.recorded_data)} samples")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save XDF file: {str(e)}")
    
    def log_message(self):
        """Handle log button click"""
        message = self.text_entry.get().strip()
        
        if not message:
            messagebox.showwarning("Warning", "Please enter a message to log.")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
    
    def update_log_display(self, message, timestamp):
        """Update the log display area"""
        log_entry = f"[{timestamp}] {message}\n"
        self.log_display.insert(tk.END, log_entry)
        self.log_display.see(tk.END)  # Auto-scroll to bottom
    
    def clear_log_display(self):
        """Clear the log display area"""
        self.log_display.delete(1.0, tk.END)
    
    def on_closing(self):
        """Handle window closing"""
        # Stop recording if active
        if self.recording:
            self.stop_recording()
        
        # Clean up LSL resources
        if hasattr(self, 'outlet') and self.outlet:
            del self.outlet
        if hasattr(self, 'inlet') and self.inlet:
            del self.inlet
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LoggerApp(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()
