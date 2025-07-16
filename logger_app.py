import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pylsl
import pyxdf
from datetime import datetime
import os
import threading
import time
import numpy as np
import json
import pickle
import mne
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
        
        # Check for recovery files
        self.check_for_recovery()
        
        # Then create LSL outlet
        self.setup_lsl_outlet()

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
            info.desc().append_child_value("version", "1.0")
            
            # Create outlet
            self.outlet = pylsl.StreamOutlet(info)
            self.lsl_status_label.config(text="LSL Status: Connected", foreground="green")
            
            # Setup inlet for recording our own stream (with delay to allow outlet to be discovered)
            self.root.after(1000, self.setup_recording_inlet)
            
        except Exception as e:
            self.lsl_status_label.config(text=f"LSL Status: Error - {str(e)}", foreground="red")
            self.outlet = None
    

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
        self.recording_status_label.config(text="Recording...", foreground="green")
        self.start_recording_button.config(state="disabled")
        self.stop_recording_button.config(state="normal")
        self.split_recording_button.config(state="normal")  # Enable split button
        self.status_info_label.config(text=f"Recording to: {os.path.basename(filename)}")
        
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
            self.recording_status_label.config(text="Recording...", foreground="green")
            self.start_recording_button.config(state="disabled")
            self.stop_recording_button.config(state="normal")
            self.split_recording_button.config(state="normal")  # Enable split button
            self.status_info_label.config(text=f"Auto-recording to: {os.path.basename(self.xdf_filename)}")
            
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
        self.recording_status_label.config(text="Not Recording", foreground="red")
        self.start_recording_button.config(state="normal")
        self.stop_recording_button.config(state="disabled")
        self.split_recording_button.config(state="disabled")  # Disable split button
        self.status_info_label.config(text="Ready")
        
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
            self.recording_status_label.config(text="Recording...", foreground="green")
            self.start_recording_button.config(state="disabled")
            self.stop_recording_button.config(state="normal")
            self.split_recording_button.config(state="normal")
            self.status_info_label.config(text=f"Split to: {os.path.basename(self.xdf_filename)}")
            
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
    
    def update_log_display(self, message, timestamp=None):
        """Update the log display area"""
        if timestamp is None:
            ## get now as the timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
