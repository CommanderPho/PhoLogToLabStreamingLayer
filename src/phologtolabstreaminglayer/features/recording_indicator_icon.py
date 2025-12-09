import platform
import io
import tempfile
import os
from typing import Optional
from PIL import Image, ImageDraw

# Windows-specific imports for taskbar overlay
_windows_taskbar_available = False
if platform.system() == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes
        _windows_taskbar_available = True
    except ImportError:
        try:
            import win32gui
            import win32con
            import win32com.client
            _windows_taskbar_available = True
        except ImportError:
            _windows_taskbar_available = False


class RecordingIndicatorIconMixin:
    """
    Mixin class to add Windows taskbar recording indicator functionality.
    Shows a flashing red dot overlay on the taskbar button when recording is active.
    """
    
    def init_RecordingIndicatorIconMixin(self):
        """Initialize Windows taskbar overlay interface"""
        # Windows taskbar recording indicator
        self.taskbar_overlay_flash_timer_id = None
        self.taskbar_overlay_icon_visible = False
        self.taskbar_overlay_icon_data = None
        self.taskbar_overlay_icon_handle = None
        self.taskbar_list = None
        if _windows_taskbar_available:
            self.init_windows_taskbar_overlay()
    
    def init_windows_taskbar_overlay(self):
        """Initialize Windows taskbar overlay interface"""
        if not _windows_taskbar_available:
            return
        
        try:
            # Try using win32com first (if pywin32 is available)
            try:
                import win32com.client
                self.taskbar_list = win32com.client.Dispatch("{56FDF344-FD6D-11d0-958A-006097C9A090}")
                print("Windows taskbar overlay initialized (win32com)")
                return
            except (ImportError, Exception):
                pass
            
            # Fallback to ctypes
            try:
                import ctypes
                from ctypes import wintypes
                
                # Load shell32.dll
                shell32 = ctypes.windll.shell32
                
                # Create ITaskbarList3 interface
                # CLSID_TaskbarList: {56FDF344-FD6D-11d0-958A-006097C9A090}
                CLSID_TaskbarList = ctypes.create_string_buffer(b'\x44\xF3\xFD\x56\x6D\xFD\xD0\x11\x95\x8A\x00\x60\x97\xC9\xA0\x90')
                IID_ITaskbarList3 = ctypes.create_string_buffer(b'\xEA\x1A\xAF\xB9\xB9\xC5\xD5\x11\xA5\x0C\x00\xC0\x4F\xD7\xD0\x62')
                
                # CoCreateInstance
                taskbar_list = ctypes.POINTER(ctypes.c_void_p)()
                ctypes.windll.ole32.CoCreateInstance(
                    ctypes.byref(CLSID_TaskbarList),
                    None,
                    1,  # CLSCTX_INPROC_SERVER
                    ctypes.byref(IID_ITaskbarList3),
                    ctypes.byref(taskbar_list)
                )
                
                self.taskbar_list = taskbar_list
                print("Windows taskbar overlay initialized (ctypes)")
            except Exception as e:
                print(f"Failed to initialize Windows taskbar overlay: {e}")
                self.taskbar_list = None
        except Exception as e:
            print(f"Error initializing Windows taskbar overlay: {e}")
            self.taskbar_list = None
    
    def create_red_dot_icon(self) -> Optional[bytes]:
        """Create a red dot icon for the taskbar overlay"""
        if not _windows_taskbar_available:
            return None
        
        try:
            # Create a 16x16 red dot icon
            size = 16
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a red circle (slightly smaller than the image for padding)
            margin = 2
            draw.ellipse([margin, margin, size - margin, size - margin], fill=(255, 0, 0, 255))
            
            # Convert to ICO format
            ico_buffer = io.BytesIO()
            image.save(ico_buffer, format='ICO', sizes=[(size, size)])
            ico_buffer.seek(0)
            
            return ico_buffer.getvalue()
        except Exception as e:
            print(f"Error creating red dot icon: {e}")
            return None
    
    def get_window_handle(self) -> Optional[int]:
        """Get the Windows HWND for the tkinter root window"""
        if not _windows_taskbar_available:
            return None
        
        try:
            # Get the window ID from tkinter
            window_id = self.root.winfo_id()
            
            # Try using win32gui first
            try:
                import win32gui
                hwnd = win32gui.GetParent(window_id)
                if hwnd == 0:
                    hwnd = window_id
                return hwnd
            except ImportError:
                pass
            
            # Fallback: return the window_id directly (may work for some cases)
            return window_id
        except Exception as e:
            print(f"Error getting window handle: {e}")
            return None
    
    def set_taskbar_overlay_icon(self, icon_data: Optional[bytes] = None):
        """Set the taskbar overlay icon"""
        if not _windows_taskbar_available or not self.taskbar_list:
            return
        
        try:
            hwnd = self.get_window_handle()
            if not hwnd:
                return
            
            # Try using win32com (pywin32)
            try:
                import win32gui
                import win32con
                import win32api
                
                # Clean up previous icon handle if exists
                if self.taskbar_overlay_icon_handle:
                    try:
                        win32gui.DestroyIcon(self.taskbar_overlay_icon_handle)
                    except:
                        pass
                    self.taskbar_overlay_icon_handle = None
                
                if icon_data:
                    # Create icon from data
                    with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as tmp:
                        tmp.write(icon_data)
                        tmp_path = tmp.name
                    
                    try:
                        # Load icon and keep handle alive
                        icon_handle = win32gui.LoadImage(
                            0, tmp_path, win32con.IMAGE_ICON, 16, 16,
                            win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                        )
                        if icon_handle:
                            self.taskbar_overlay_icon_handle = icon_handle
                            self.taskbar_list.SetOverlayIcon(hwnd, icon_handle, "Recording")
                    finally:
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass
                else:
                    # Clear overlay
                    self.taskbar_list.SetOverlayIcon(hwnd, None, "")
                return
            except ImportError:
                pass
            
            # Fallback to ctypes (more complex, may not work perfectly)
            # For now, if win32com is not available, skip
            print("win32com not available, taskbar overlay requires pywin32")
            
        except Exception as e:
            print(f"Error setting taskbar overlay icon: {e}")
    
    def clear_taskbar_overlay_icon(self):
        """Clear the taskbar overlay icon"""
        self.set_taskbar_overlay_icon(None)
    
    def flash_taskbar_overlay(self):
        """Toggle the taskbar overlay icon for flashing effect"""
        if not _windows_taskbar_available or self._shutting_down:
            return
        
        if not self.recording:
            # Stop flashing if recording stopped
            self.stop_taskbar_overlay_flash()
            return
        
        # Toggle visibility
        self.taskbar_overlay_icon_visible = not self.taskbar_overlay_icon_visible
        
        if self.taskbar_overlay_icon_visible:
            if self.taskbar_overlay_icon_data is None:
                self.taskbar_overlay_icon_data = self.create_red_dot_icon()
            self.set_taskbar_overlay_icon(self.taskbar_overlay_icon_data)
        else:
            self.clear_taskbar_overlay_icon()
        
        # Schedule next flash (~1 second)
        if self.recording and not self._shutting_down:
            self.taskbar_overlay_flash_timer_id = self.root.after(1000, self.flash_taskbar_overlay)
    
    def start_taskbar_overlay_flash(self):
        """Start flashing the taskbar overlay icon"""
        if not _windows_taskbar_available:
            return
        
        # Stop any existing flash timer
        self.stop_taskbar_overlay_flash()
        
        # Start flashing immediately
        self.taskbar_overlay_icon_visible = True
        if self.taskbar_overlay_icon_data is None:
            self.taskbar_overlay_icon_data = self.create_red_dot_icon()
        self.set_taskbar_overlay_icon(self.taskbar_overlay_icon_data)
        
        # Schedule first toggle
        self.taskbar_overlay_flash_timer_id = self.root.after(1000, self.flash_taskbar_overlay)
    
    def stop_taskbar_overlay_flash(self):
        """Stop flashing the taskbar overlay icon"""
        if self.taskbar_overlay_flash_timer_id:
            try:
                self.root.after_cancel(self.taskbar_overlay_flash_timer_id)
            except:
                pass
            self.taskbar_overlay_flash_timer_id = None
        
        # Clear the overlay icon
        self.clear_taskbar_overlay_icon()
        self.taskbar_overlay_icon_visible = False
        
        # Clean up icon handle
        if self.taskbar_overlay_icon_handle and _windows_taskbar_available:
            try:
                import win32gui
                win32gui.DestroyIcon(self.taskbar_overlay_icon_handle)
            except:
                pass
            self.taskbar_overlay_icon_handle = None

