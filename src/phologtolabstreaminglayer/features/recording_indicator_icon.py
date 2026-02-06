import platform
import io
import tempfile
import os
from typing import Optional
from PIL import Image, ImageDraw

# Windows-specific imports for taskbar overlay
_windows_taskbar_available = False
ctypes = None
wintypes = None
win32gui = None
win32con = None
IUnknown = None
GUID = None
COMMETHOD = None
HRESULT = None
CreateObject = None
ITaskbarList3 = None
CLSID_TaskbarList = None

if platform.system() == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes
        try:
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
            _windows_taskbar_available = True
        except ImportError:
            _windows_taskbar_available = False
    except ImportError:
        _windows_taskbar_available = False

class TaskbarFlasher:
    """ service class that flashes """

    def __init__(self, root):
        if not _windows_taskbar_available or ctypes is None or win32gui is None or win32con is None or CreateObject is None or ITaskbarList3 is None or CLSID_TaskbarList is None:
            raise RuntimeError("Windows taskbar features are not available on this platform")
        
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

    def toggle(self) -> bool:
        self.is_flashing = (not self.is_flashing)
        if self.is_flashing:
            self.start()
        else:
            self.stop()

        return self.is_flashing


class RecordingIndicatorIconMixin:
    """
    Mixin class to add Windows taskbar recording indicator functionality.
    Shows a flashing red dot overlay on the taskbar button when recording is active.
    """
    
    def init_RecordingIndicatorIconMixin(self):
        """Initialize Windows taskbar overlay interface
        requires: self.root

        """
        # Windows taskbar recording indicator
        self.flasher = None
        if _windows_taskbar_available:
            self.init_windows_taskbar_overlay()



    
    def init_windows_taskbar_overlay(self):
        """Initialize Windows taskbar overlay interface"""
        if not _windows_taskbar_available:
            return
        
        try:
            # Initialize flasher
            self.flasher = TaskbarFlasher(self.root)
        except Exception as e:
            print(f"Error initializing Windows taskbar overlay: {e}")
            self.flasher = None
    

    def flash_taskbar_overlay(self):
        """Toggle the taskbar overlay icon for flashing effect"""
        if not _windows_taskbar_available or self._shutting_down:
            return
        
        if not self.recording:
            # Stop flashing if recording stopped
            self.stop_taskbar_overlay_flash()
            return
        
        # Schedule next flash (~1 second)
        if self.recording and (not self._shutting_down):
            self.start_taskbar_overlay_flash()
    

    def start_taskbar_overlay_flash(self):
        """Start flashing the taskbar overlay icon"""
        if not self.flasher:
            return

        self.flasher.start()

    

    def stop_taskbar_overlay_flash(self):
        """Stop flashing the taskbar overlay icon"""
        if self.flasher:
            self.flasher.stop()



