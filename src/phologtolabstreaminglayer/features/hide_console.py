# Cross-platform console window suppression utility
# Copyright (C) 2025 Pho Hale. All rights reserved.

"""
Utility to hide the console window on Windows when running Python GUI applications.

On Windows, running a Python script with python.exe (not pythonw.exe) opens a console window.
This module provides functions to hide that console window programmatically.

On macOS and Linux, GUI apps don't typically spawn a console window, so this is a no-op.
"""

import sys
import os
import io


# Module-level state to track if console was hidden
_console_hidden = False
_original_stdout = None
_original_stderr = None


class NullWriter:
    """A null writer that discards all output to prevent hangs when console is hidden."""
    def write(self, text: str) -> int:
        return len(text) if text else 0
    
    def flush(self):
        pass
    
    def isatty(self) -> bool:
        return False
    
    def readable(self) -> bool:
        return False
    
    def writable(self) -> bool:
        return True
    
    def seekable(self) -> bool:
        return False
    
    @property
    def encoding(self) -> str:
        return 'utf-8'
    
    @property
    def errors(self) -> str:
        return 'replace'


def hide_console_window() -> bool:
    """
    Hide the console window on Windows. No-op on other platforms.
    
    After hiding, redirects stdout/stderr to safe null writers to prevent hangs
    when code tries to print before ConsoleOutputFrame is ready.
    
    Returns:
        True if the console was successfully hidden or if running on non-Windows platform.
        False if hiding failed (console may still be visible).
    
    Note:
        This should be called early in the application startup, before creating the main window.
        The console window may briefly flash before being hidden.
    """
    global _console_hidden, _original_stdout, _original_stderr
    
    if sys.platform != 'win32':
        # No console window to hide on macOS/Linux GUI apps
        return True
    
    # Store original streams before hiding
    if _original_stdout is None:
        _original_stdout = sys.stdout
    if _original_stderr is None:
        _original_stderr = sys.stderr
    
    try:
        import ctypes
        
        # Method 1: Hide the console window (preferred - keeps stdout/stderr working)
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Get the console window handle
        console_window = kernel32.GetConsoleWindow()
        
        if console_window:
            # SW_HIDE = 0 - Hides the window
            user32.ShowWindow(console_window, 0)
            # Redirect to safe streams to prevent hangs
            sys.stdout = NullWriter()
            sys.stderr = NullWriter()
            _console_hidden = True
            return True
        else:
            # No console window exists (e.g., running from pythonw.exe or frozen app)
            return True
            
    except Exception as e:
        # Fallback: try FreeConsole (detaches console entirely)
        try:
            import ctypes
            ctypes.windll.kernel32.FreeConsole()
            # After FreeConsole, stdout/stderr become invalid - redirect to safe streams
            sys.stdout = NullWriter()
            sys.stderr = NullWriter()
            _console_hidden = True
            return True
        except Exception:
            pass
        
        # If all methods fail, log the error but don't crash
        # Use sys.__stderr__ to bypass any redirection
        try:
            if sys.__stderr__:
                print(f"Warning: Could not hide console window: {e}", file=sys.__stderr__)
        except Exception:
            pass  # Even __stderr__ might be unavailable
        return False


def is_frozen() -> bool:
    """
    Check if the application is running as a frozen executable (e.g., PyInstaller).
    
    Returns:
        True if running as frozen executable, False otherwise.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def should_hide_console() -> bool:
    """
    Determine if the console window should be hidden.
    
    Returns:
        True if console should be hidden (Windows, not frozen, not in debug mode).
    """
    # Don't hide if not on Windows
    if sys.platform != 'win32':
        return False
    
    # Don't hide if already frozen (PyInstaller handles this via console=False)
    if is_frozen():
        return False
    
    # Don't hide if DEBUG environment variable is set
    if os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes'):
        return False
    
    # Don't hide if running in an IDE debugger (check for common debugger env vars)
    if any(var in os.environ for var in ('PYCHARM_DEBUG', 'VSCODE_PID', 'CURSOR_PID')):
        return False
    
    return True


def auto_hide_console() -> bool:
    """
    Automatically hide the console window if appropriate.
    
    This is a convenience function that combines should_hide_console() and hide_console_window().
    
    Returns:
        True if console was hidden or hiding was not needed.
        False if hiding was attempted but failed.
    """
    if should_hide_console():
        return hide_console_window()
    return True


def is_console_hidden() -> bool:
    """
    Check if the console window was hidden by this module.
    
    Returns:
        True if console was hidden, False otherwise.
    """
    return _console_hidden


def get_original_stdout():
    """
    Get the original stdout stream before console was hidden.
    
    Returns:
        Original stdout stream, or None if console was not hidden.
    """
    return _original_stdout


def get_original_stderr():
    """
    Get the original stderr stream before console was hidden.
    
    Returns:
        Original stderr stream, or None if console was not hidden.
    """
    return _original_stderr
