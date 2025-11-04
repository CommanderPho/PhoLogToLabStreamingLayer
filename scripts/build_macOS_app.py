import PyInstaller.__main__
import sys
import os
import importlib.util
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent
main_app_dir = script_dir.parent.resolve()
print(f'main_app_dir: "{main_app_dir.as_posix()}"')

# Build args with analogous collects to Windows, tuned for macOS
def has_module(mod_name: str) -> bool:
    return importlib.util.find_spec(mod_name) is not None

args = [
    'logger_app.py',
    '--onedir',  # Bundle into an app directory
    '--windowed',  # Hide console window (for GUI apps)
    '--name=PhoLogToLabStreamingLayer',
    '--icon=icons/LogToLabStreamingLayerIcon_Light.ico',
]

# Core packages used by the app
for pkg in [
    'mne',
    'pylsl',
    'whisper_timestamped',
    'whisper',
    'dtw',
    'torch',
    'matplotlib',
    'PIL',
    'pyxdf',
    'pystray',
    'mne_lsl',
    'sounddevice',
    'soundfile',
    'phopylslhelper',
]:
    if has_module(pkg):
        args.append(f'--collect-all={pkg}')

# macOS system tray backend (pystray) via PyObjC, include if available
for hidden in ['AppKit', 'Foundation', 'Quartz']:
    if has_module(hidden):
        args.append(f'--hidden-import={hidden}')

# Optional FFmpeg bundling if provided via env var; use ':' separator on macOS
ffmpeg_path = os.environ.get('FFMPEG_EXE')
if ffmpeg_path and Path(ffmpeg_path).is_file():
    args.append(f'--add-binary={ffmpeg_path}:.')

# Output paths
args.extend([
    f'--distpath={main_app_dir}/dist',
    f'--workpath={main_app_dir}/build',
    f'--specpath={main_app_dir}',
])

PyInstaller.__main__.run(args)
