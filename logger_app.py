import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pylsl
from datetime import datetime
import os
import threading
import time

class LoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LSL Logger")
        self.root.geometry("500x400")
        
        # Create LSL outlet
        self.setup_lsl_outlet()
        
        # Create log file
        self.log_file_path = "log_messages.txt"
        
        # Create GUI elements
        self.setup_gui()
        
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
            
            # Create outlet
            self.outlet = pylsl.StreamOutlet(info)
            self.lsl_status_label.config(text="LSL Status: Connected", fg="green")
            
        except Exception as e:
            self.lsl_status_label.config(text=f"LSL Status: Error - {str(e)}", fg="red")
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
        main_frame.rowconfigure(2, weight=1)
        
        # LSL Status label
        self.lsl_status_label = ttk.Label(main_frame, text="LSL Status: Initializing...", foreground="orange")
        self.lsl_status_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Text input label
        ttk.Label(main_frame, text="Message:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        # Text input box
        self.text_entry = tk.Entry(main_frame, width=50)
        self.text_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        self.text_entry.bind('<Return>', lambda event: self.log_message())
        
        # Log button
        self.log_button = ttk.Button(main_frame, text="Log", command=self.log_message)
        self.log_button.grid(row=1, column=2, padx=(10, 0), pady=(0, 5))
        
        # Log display area
        ttk.Label(main_frame, text="Log History:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        
        # Scrolled text widget for log history
        self.log_display = scrolledtext.ScrolledText(main_frame, height=15, width=60)
        self.log_display.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Clear log button
        ttk.Button(main_frame, text="Clear Log Display", command=self.clear_log_display).grid(row=4, column=0, sticky=tk.W)
        
        # File info label
        self.file_info_label = ttk.Label(main_frame, text=f"Log file: {self.log_file_path}")
        self.file_info_label.grid(row=4, column=1, columnspan=2, sticky=tk.E)
        
        # Focus on text entry
        self.text_entry.focus()
    
    def log_message(self):
        """Handle log button click"""
        message = self.text_entry.get().strip()
        
        if not message:
            messagebox.showwarning("Warning", "Please enter a message to log.")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Send LSL message
        self.send_lsl_message(message)
        
        # Write to file
        self.write_to_file(message, timestamp)
        
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
    
    def write_to_file(self, message, timestamp):
        """Write message to log file"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
            print(f"Message written to file: {message}")
        except Exception as e:
            print(f"Error writing to file: {e}")
            messagebox.showerror("File Error", f"Failed to write to log file: {str(e)}")
    
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
        if self.outlet:
            del self.outlet
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

