from typing import Dict, List, Tuple, Optional, Callable, Union, Any
from copy import deepcopy
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import pylsl
import pyxdf
from datetime import datetime, timedelta
import pytz
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
import socket
import sys
from phopylslhelper.general_helpers import unwrap_single_element_listlike_if_needed, readable_dt_str, from_readable_dt_str, localize_datetime_to_timezone, tz_UTC, tz_Eastern, _default_tz
from phopylslhelper.easy_time_sync import EasyTimeSyncParsingMixin
from phopylslhelper.mixins.app_helpers import SingletonInstanceMixin, AppThemeMixin, SystemTrayAppMixin
from whisper_timestamped.mixins.live_whisper_transcription import LiveWhisperTranscriptionAppMixin
from labrecorder import LabRecorder


class GlobalHotkeyMixin:
	"""
	Mixin class to add global hotkey functionality to an application.
	"""
	# Property to control whether global hotkeys should be registered
	should_register_global_hotkey: bool = False
	
	# ==================================================================================================================================================================================================================================================================================== #
	# Initialization Methods                                                                                                                                                                                                                                                               #
	# ==================================================================================================================================================================================================================================================================================== #
	def init_GlobalHotkeyMixin(self):
		"""Initialize global hotkey mixin state"""
		self.hotkey_popover = None
		self._hotkey_registered = False
	
	# ==================================================================================================================================================================================================================================================================================== #
	# Setup/Cleanup Methods                                                                                                                                                                                                                                                                #
	# ==================================================================================================================================================================================================================================================================================== #
	def setup_global_hotkey(self):
		"""Setup global hotkey for quick log entry"""
		if not self.should_register_global_hotkey:
			print("Global hotkey registration disabled (should_register_global_hotkey=False)")
			return
		
		try:
			# Register Ctrl+Alt+L as the global hotkey
			keyboard.add_hotkey('ctrl+alt+l', self.show_hotkey_popover)
			self._hotkey_registered = True
			print("Global hotkey Ctrl+Alt+L registered successfully")
		except Exception as e:
			print(f"Error setting up global hotkey: {e}")
			self._hotkey_registered = False
	
	def cleanup_GlobalHotkeyMixin(self):
		"""Clean up global hotkey registration"""
		if self._hotkey_registered:
			try:
				keyboard.remove_hotkey('ctrl+alt+l')
				self._hotkey_registered = False
				print("Global hotkey cleaned up successfully")
			except Exception as e:
				print(f"Error cleaning up global hotkey: {e}")
		
		# Close popover if it's open
		if self.hotkey_popover:
			try:
				self.hotkey_popover.destroy()
			except:
				pass
			self.hotkey_popover = None
	
	# ==================================================================================================================================================================================================================================================================================== #
	# Imported Methods                                                                                                                                                                                                                                                                     #
	# ==================================================================================================================================================================================================================================================================================== #

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

