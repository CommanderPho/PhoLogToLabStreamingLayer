#!/usr/bin/env python3
"""
Simple test script for the hotkey popover functionality.
Run this to test the popover without the full LSL logger app.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import threading
import time
from datetime import datetime
import socket
import sys

class TestPopover:
    # Class variable to track if an instance is already running
    _instance_running = False
    _lock_port = 12346  # Different port for test popover
    
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
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Popover Test")
        self.root.geometry("300x200")
        
        self.hotkey_popover = None
        self.popover_text_timestamp = None  # Track when user first types
        
        # Singleton lock socket
        self._lock_socket = None
        
        # Shutdown flag to prevent GUI updates during shutdown
        self._shutting_down = False
        
        # Test button
        test_btn = ttk.Button(self.root, text="Test Popover", command=self.show_hotkey_popover)
        test_btn.pack(pady=20)
        
        # Instructions
        label = ttk.Label(self.root, text="Press Ctrl+Alt+L to test global hotkey\nOr click the button above")
        label.pack(pady=20)
        
        # Setup global hotkey
        self.setup_global_hotkey()
        
    def acquire_singleton_lock(self):
        """Acquire the singleton lock by binding to the port"""
        try:
            self._lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._lock_socket.bind(('localhost', self._lock_port))
            self._lock_socket.listen(1)
            self.mark_instance_running()
            print("Test popover singleton lock acquired successfully")
            return True
        except OSError as e:
            print(f"Failed to acquire test popover singleton lock: {e}")
            return False
    
    def release_singleton_lock(self):
        """Release the singleton lock and clean up the socket"""
        try:
            if self._lock_socket:
                self._lock_socket.close()
                self._lock_socket = None
            self.mark_instance_stopped()
            print("Test popover singleton lock released")
        except Exception as e:
            print(f"Error releasing test popover singleton lock: {e}")
    
    def on_popover_text_change(self, event=None):
        """Track when user first types in popover text field"""
        if self.popover_text_timestamp is None:
            self.popover_text_timestamp = datetime.now()
    
    def on_popover_text_clear(self, event=None):
        """Reset timestamp when popover text field is cleared"""
        if event and event.keysym in ['BackSpace', 'Delete']:
            # Check if field is now empty
            if not self.quick_log_entry.get().strip():
                self.popover_text_timestamp = None
    
    def get_popover_text_timestamp(self):
        """Get the timestamp when user first started typing in popover field"""
        if self.popover_text_timestamp:
            timestamp = self.popover_text_timestamp
            self.popover_text_timestamp = None  # Reset for next entry
            return timestamp
        return datetime.now()
    
    def setup_global_hotkey(self):
        """Setup global hotkey for quick log entry"""
        try:
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
            return
        
        # Create popover window
        self.hotkey_popover = tk.Toplevel()
        self.hotkey_popover.title("Quick Log Entry")
        self.hotkey_popover.geometry("400x150")
        
        # Center the popover on the screen
        self.center_popover()
        
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
        self.quick_log_entry = tk.Entry(content_frame, font=("Arial", 12))
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
    
    def center_popover(self):
        """Center the popover on the screen"""
        try:
            screen_width = self.hotkey_popover.winfo_screenwidth()
            screen_height = self.hotkey_popover.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 150) // 2
            self.hotkey_popover.geometry(f"+{x}+{y}")
        except Exception as e:
            print(f"Error centering popover: {e}")
    
    def quick_log_and_close(self):
        """Log the message and close the popover"""
        message = self.quick_log_entry.get().strip()
        if message:
            # Get the timestamp when user first started typing
            timestamp = self.get_popover_text_timestamp()
            print(f"Log entry: [{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
            
            # Clear entry
            self.quick_log_entry.delete(0, tk.END)
        
        # Close popover
        self.close_hotkey_popover()
    
    def close_hotkey_popover(self):
        """Close the hotkey popover"""
        if self.hotkey_popover:
            self.hotkey_popover.destroy()
            self.hotkey_popover = None
    
    def run(self):
        """Run the test application"""
        # Try to acquire the singleton lock
        if not self.acquire_singleton_lock():
            messagebox.showerror("Startup Error", 
                               "Failed to acquire test popover singleton lock.\n"
                               "Another test instance may be running.")
            self.root.destroy()
            sys.exit(1)
        
        # Handle window closing
        def on_closing():
            self._shutting_down = True
            self.release_singleton_lock()
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        self.root.mainloop()

if __name__ == "__main__":
    # Check if another test instance is already running
    if TestPopover.is_instance_running():
        print("Error: Another test popover instance is already running.")
        print("Only one test instance can run at a time.")
        sys.exit(1)
    
    app = TestPopover()
    app.run()
