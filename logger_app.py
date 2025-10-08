import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
from pathlib import Path
from phologtolabstreaminglayer.logger_app import LoggerApp



def main(xdf_folder: Path):
    # Check if another instance is already running
    if LoggerApp.is_instance_running():
        messagebox.showerror("Instance Already Running", 
                           "Another instance of LSL Logger is already running.\n"
                           "Only one instance can run at a time.")
        sys.exit(1)
    
    root = tk.Tk()
    app = LoggerApp(root, xdf_folder=xdf_folder)
    
    # Try to acquire the singleton lock
    if not app.acquire_singleton_lock():
        messagebox.showerror("Startup Error", 
                           "Failed to acquire singleton lock.\n"
                           "Another instance may be running.")
        root.destroy()
        sys.exit(1)
    
    # # Handle window closing - minimize to tray instead of closing
    # def on_closing():
    #     app.minimize_to_tray()
    # root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the GUI
    root.mainloop()



if __name__ == "__main__":
    _default_xdf_folder = Path(r'E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs').resolve()
    # _default_xdf_folder = Path('/media/halechr/MAX/cloud/University of Michigan Dropbox/Pho Hale/Personal/LabRecordedTextLog').resolve() ## Lab computer
    # LoggerApp._default_xdf_folder = _default_xdf_folder
    assert _default_xdf_folder.exists(), f"XDF folder does not exist: {_default_xdf_folder}"
    main(xdf_folder=_default_xdf_folder)
