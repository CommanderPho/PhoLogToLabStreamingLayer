import socket
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import sys
import argparse
from pathlib import Path
from phologtolabstreaminglayer.logger_app import LoggerApp
from phopylslhelper.mixins.app_helpers import SingletonInstanceMixin

parser = argparse.ArgumentParser(description='PhoLogToLabStreamingLayer')
parser.add_argument('--unsafe', action='store_true', help='Override safety checks and allow multiple instances')
args = parser.parse_args()
unsafe = args.unsafe

def main(xdf_folder: Path, unsafe: bool = False):
    """ 
        unsafe: bool = False skips the singleton lock check on startup, the user should first confirmt that there aren't multiple instances running.

    """
    # Check if another instance is already running (unless --unsafe)
    if not unsafe and LoggerApp.is_instance_running():
        messagebox.showerror("Instance Already Running", 
                           "Another instance of LSL Logger is already running.\n"
                           "Only one instance can run at a time.\n"
                           "To override this safety check, launch with --unsafe.")
        sys.exit(1)
    
    root = tk.Tk()
    app = LoggerApp(root, xdf_folder=xdf_folder)
    
    # Try to acquire the singleton lock (unless --unsafe)
    if not unsafe and not app.acquire_singleton_lock():
        messagebox.showerror("Startup Error", 
                           "Failed to acquire singleton lock.\n"
                           "Another instance may be running.\n"
                           "To override this safety check, launch with --unsafe.")
        root.destroy()
        sys.exit(1)
    
    # Handle window closing - cleanly shut down the app
    def on_closing():
        if app is not None:
            app.on_closing()
        else:
            root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    

    # Start the GUI
    root.mainloop()



if __name__ == "__main__":
    _default_xdf_folder = Path(r'E:\Dropbox (Personal)\Databases\UnparsedData\PhoLogToLabStreamingLayer_logs').resolve()
    # _default_xdf_folder = Path('/media/halechr/MAX/cloud/University of Michigan Dropbox/Pho Hale/Personal/LabRecordedTextLog').resolve() ## Lab computer
    # LoggerApp._default_xdf_folder = _default_xdf_folder
    # assert _default_xdf_folder.exists(), f"XDF folder does not exist: {_default_xdf_folder}"
    main(xdf_folder=_default_xdf_folder, unsafe=unsafe)


    

    # inst = SingletonInstanceMixin()
    # inst.acquire_singleton_lock()
    # # inst.release_singleton_lock()
    # print("Singleton lock acquired and released")

    # try:
    #     ## Get the correct lock port
    #     program_lock_port: int = 13372 # self.helper_SingletonInstanceMixin_get_lock_port()

    #     lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     lock_socket.bind(('localhost', program_lock_port))

    #     lock_socket.close()


    #     lock_socket.listen(1)
    #     print("Singleton lock acquired successfully")

    # except OSError as e:
    #     print(f"Failed to acquire singleton lock: {e}")
        
