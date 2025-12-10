import sys
import ctypes
import tempfile
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from PIL import Image, ImageDraw

# Windows COM requirements
from comtypes import GUID, IUnknown
from comtypes.client import CreateObject
import win32gui
import win32con

# Define ITaskbarList3 Interface GUIDs
CLSID_TaskbarList = GUID("{56FDF344-FD6D-11d0-958A-006097C9A090}")

# TODO 2025-12-09 - NOT WORKING AT ALL, but the Tk version is

# class TaskbarFlasher:
#     def __init__(self, window_handle):
#         self.hwnd = window_handle
#         self.taskbar = CreateObject(CLSID_TaskbarList)
#         # Initialize the interface
#         self.taskbar.HrInit()
        
#         # Create a cached Red Dot HICON
#         self.hicon_on = self._create_red_dot_icon()
#         self.is_visible = False
        
#         # Setup Timer
#         self.timer = QTimer()
#         self.timer.timeout.connect(self._toggle_overlay)
        
#     def _create_red_dot_icon(self):
#         """Generates a 16x16 red circle .ico and returns the Windows HICON handle."""
#         # Create a generic red dot image using PIL
#         img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
#         draw = ImageDraw.Draw(img)
#         draw.ellipse((0, 0, 16, 16), fill=(255, 0, 0, 255))
        
#         # Save to temp file because win32gui prefers loading from file for stability
#         fd, path = tempfile.mkstemp(suffix=".ico")
#         os.close(fd)
#         img.save(path, format="ICO", sizes=[(16, 16)])
        
#         # Load the HICON
#         hicon = win32gui.LoadImage(
#             0, path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE
#         )
#         os.remove(path) # Cleanup
#         return hicon

#     def _toggle_overlay(self):
#         """Toggles the overlay icon on/off."""
#         if self.is_visible:
#             # Remove overlay (Set to 0/None)
#             self.taskbar.SetOverlayIcon(self.hwnd, 0, "")
#             self.is_visible = False
#         else:
#             # Set Red Dot Overlay
#             self.taskbar.SetOverlayIcon(self.hwnd, self.hicon_on, "Recording")
#             self.is_visible = True

#     def start(self, interval_ms=800):
#         self.timer.start(interval_ms)

#     def stop(self):
#         self.timer.stop()
#         self.taskbar.SetOverlayIcon(self.hwnd, 0, "")
#         self.is_visible = False

# # --- Example Usage in Main App ---
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Recorder App")
#         self.resize(300, 200)

#         # UI Setup
#         layout = QVBoxLayout()
#         self.btn = QPushButton("Start Recording")
#         self.btn.clicked.connect(self.toggle_record)
        
#         container = QWidget()
#         container.setLayout(layout)
#         layout.addWidget(self.btn)
#         self.setCentralWidget(container)

#         self.recording = False
        
#         # Initialize the flasher - IMPORTANT: Pass the window ID (HWND)
#         # We use int(self.winId()) to get the handle
#         self.flasher = None 

#     def showEvent(self, event):
#         """Initialize flasher after window is shown to ensure HWND exists."""
#         super().showEvent(event)
#         if not self.flasher:
#             self.flasher = TaskbarFlasher(int(self.winId()))

#     def toggle_record(self):
#         if not self.recording:
#             self.recording = True
#             self.btn.setText("Stop Recording")
#             self.flasher.start(600) # Flash every 600ms
#         else:
#             self.recording = False
#             self.btn.setText("Start Recording")
#             self.flasher.stop()


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())

