import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
import tempfile
import os
from PIL import Image, ImageDraw

# --- COM/Windows API Definitions ---
from comtypes import IUnknown, GUID, COMMETHOD, HRESULT
from comtypes.client import CreateObject
import win32gui
import win32con

# 1. Define the ITaskbarList3 Interface
# This tells comtypes exactly which methods exist and in what order (VTable).
class ITaskbarList3(IUnknown):
    _iid_ = GUID("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF}")
    _methods_ = [
        # ITaskbarList methods
        COMMETHOD([], HRESULT, 'HrInit'),
        COMMETHOD([], HRESULT, 'AddTab', (['in'], wintypes.HWND, 'hwnd')),
        COMMETHOD([], HRESULT, 'DeleteTab', (['in'], wintypes.HWND, 'hwnd')),
        COMMETHOD([], HRESULT, 'ActivateTab', (['in'], wintypes.HWND, 'hwnd')),
        COMMETHOD([], HRESULT, 'SetActiveAlt', (['in'], wintypes.HWND, 'hwnd')),
        # ITaskbarList2 methods
        COMMETHOD([], HRESULT, 'MarkFullscreenWindow', (['in'], wintypes.HWND, 'hwnd'), (['in'], wintypes.BOOL, 'fFullscreen')),
        # ITaskbarList3 methods
        COMMETHOD([], HRESULT, 'SetProgressValue', (['in'], wintypes.HWND, 'hwnd'), (['in'], ctypes.c_uint64, 'ullCompleted'), (['in'], ctypes.c_uint64, 'ullTotal')),
        COMMETHOD([], HRESULT, 'SetProgressState', (['in'], wintypes.HWND, 'hwnd'), (['in'], ctypes.c_int, 'tbpFlags')),
        COMMETHOD([], HRESULT, 'RegisterTab', (['in'], wintypes.HWND, 'hwndTab'), (['in'], wintypes.HWND, 'hwndMDI')),
        COMMETHOD([], HRESULT, 'UnregisterTab', (['in'], wintypes.HWND, 'hwndTab')),
        COMMETHOD([], HRESULT, 'SetTabOrder', (['in'], wintypes.HWND, 'hwndTab'), (['in'], wintypes.HWND, 'hwndInsertBefore')),
        COMMETHOD([], HRESULT, 'SetTabActive', (['in'], wintypes.HWND, 'hwndTab'), (['in'], wintypes.HWND, 'hwndMDI'), (['in'], ctypes.c_uint, 'dwReserved')),
        COMMETHOD([], HRESULT, 'ThumbBarAddButtons', (['in'], wintypes.HWND, 'hwnd'), (['in'], ctypes.c_uint, 'cButtons'), (['in'], ctypes.c_void_p, 'pButton')),
        COMMETHOD([], HRESULT, 'ThumbBarUpdateButtons', (['in'], wintypes.HWND, 'hwnd'), (['in'], ctypes.c_uint, 'cButtons'), (['in'], ctypes.c_void_p, 'pButton')),
        COMMETHOD([], HRESULT, 'ThumbBarSetImageList', (['in'], wintypes.HWND, 'hwnd'), (['in'], ctypes.c_void_p, 'himl')),
        COMMETHOD([], HRESULT, 'SetOverlayIcon', (['in'], wintypes.HWND, 'hwnd'), (['in'], wintypes.HICON, 'hIcon'), (['in'], wintypes.LPCWSTR, 'pszDescription')),
    ]

CLSID_TaskbarList = GUID("{56FDF344-FD6D-11d0-958A-006097C9A090}")



class TaskbarFlasher:
    def __init__(self, root):
        self.root = root
        self.is_flashing = False
        self.is_visible = False
        self.timer_id = None
        
        # Get correct HWND (Parent of the Tkinter canvas)
        self.root.update_idletasks() 
        self.hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())

        # Initialize Windows Taskbar Interface with our custom definition
        # We explicitly pass `interface=ITaskbarList3` so comtypes casts it correctly
        self.taskbar = CreateObject(CLSID_TaskbarList, interface=ITaskbarList3)
        self.taskbar.HrInit()

        # Create Cached Red Dot Icon
        self.hicon_on = self._create_red_dot_icon()

    def _create_red_dot_icon(self):
        """Generates a 16x16 red circle .ico and returns the HICON."""
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, 16, 16), fill=(255, 0, 0, 255))
        
        fd, path = tempfile.mkstemp(suffix=".ico")
        os.close(fd)
        img.save(path, format="ICO", sizes=[(16, 16)])
        
        hicon = win32gui.LoadImage(
            0, path, win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE
        )
        os.remove(path)
        return hicon

    def _flash_loop(self):
        if not self.is_flashing:
            return

        try:
            if self.is_visible:
                self.taskbar.SetOverlayIcon(self.hwnd, None, "")
                self.is_visible = False
            else:
                self.taskbar.SetOverlayIcon(self.hwnd, self.hicon_on, "Recording")
                self.is_visible = True
        except Exception as e:
            print(f"Overlay Error: {e}")
            
        self.timer_id = self.root.after(800, self._flash_loop)

    def start(self):
        if not self.is_flashing:
            self.is_flashing = True
            self._flash_loop()

    def stop(self):
        self.is_flashing = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        try:
            self.taskbar.SetOverlayIcon(self.hwnd, None, "")
        except:
            pass
        self.is_visible = False

# --- Main App ---
def main():
    root = tk.Tk()
    root.title("Tkinter Recorder")
    root.geometry("300x200")

    # Initialize flasher
    flasher = TaskbarFlasher(root)
    
    is_recording = False
    
    def toggle_record():
        nonlocal is_recording
        if not is_recording:
            is_recording = True
            btn.config(text="Stop Recording")
            flasher.start()
        else:
            is_recording = False
            btn.config(text="Start Recording")
            flasher.stop()

    btn = ttk.Button(root, text="Start Recording", command=toggle_record)
    btn.pack(expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()