import PyInstaller.__main__
from pathlib import Path


def main() -> None:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.resolve()
    # Prefer the app spec; fall back to CLI build
    primary_spec = repo_root / "PhoLogToLabStreamingLayer.spec"
    entry_script = repo_root / "logger_app.py"

    if primary_spec.exists():
        PyInstaller.__main__.run([
            str(primary_spec),
            f"--distpath={repo_root}/dist",
            f"--workpath={repo_root}/build",
            "--noconfirm",
            "--clean",
        ])
        return

    PyInstaller.__main__.run([
        str(entry_script),
        "--onedir",
        "--windowed",
        "--name=PhoLogToLabStreamingLayer",
        "--icon=icons/LogToLabStreamingLayerIcon_Light.ico",
        "--collect-all=mne",
        "--collect-all=pylsl",
        '--collect-all=whisper_timestamped', 
        '--collect-all=whisper',
        "--collect-all=torch",
        "--collect-all=matplotlib",
        "--collect-all=PIL",
        "--collect-all=pyxdf",
        "--collect-all=pystray",
        "--collect-all=mne_lsl",
        "--collect-all=sounddevice",
        "--collect-all=soundfile",
        "--collect-all=phopylslhelper",
        f"--distpath={repo_root}/dist",
        f"--workpath={repo_root}/build",
        f"--specpath={repo_root}",
        "--noconfirm",
        "--clean",
    ])



if __name__ == "__main__":
    main()

import PyInstaller.__main__
import sys
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent
main_app_dir = script_dir.parent.resolve()


# Run PyInstaller with the right options
PyInstaller.__main__.run([
    'logger_app.py',
    '--onefile',  # Create a single executable file
    '--windowed',  # Hide console window (for GUI apps)
    '--name=PhoLogToLabStreamingLayer',
    '--icon=icons/LogToLabStreamingLayerIcon_Light.ico',  # Optional: add an icon file
    '--add-data=*.py;.',  # Include all Python files
    '--hidden-import=pylsl',
    '--hidden-import=mne',
    '--hidden-import=numpy',
    '--hidden-import=tkinter',
    '--hidden-import=threading',
    '--hidden-import=json',
    '--hidden-import=pathlib',
    '--hidden-import=datetime',
    '--collect-all=mne',  # Include all MNE data files
    '--collect-all=pylsl',  # Include all PyLSL data files
    '--collect-all=whisper_timestamped', 
    '--collect-all=whisper',
    '--collect-all=python-dtw',
    '--collect-all=torch',
    '--collect-all=matplotlib',
    '--collect-all=PIL',
    '--collect-all=pyxdf',
    '--collect-all=pystray',
    '--collect-all=mne_lsl',
    '--collect-all=sounddevice',
    '--collect-all=soundfile',
    '--collect-all=phopylslhelper',
    f'--distpath={main_app_dir}/dist',
    f'--workpath={main_app_dir}/build',
    f'--specpath={main_app_dir}',
])
