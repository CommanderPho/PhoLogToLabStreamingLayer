import PyInstaller.__main__
from pathlib import Path
import subprocess
import sys


def main() -> None:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.resolve()

    # Best-effort removal of enum34 (which breaks PyInstaller) before building.
    remove_enum34_script = script_dir / "remove_enum34.py"
    if remove_enum34_script.exists():
        result = subprocess.run(
            [sys.executable, str(remove_enum34_script)],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        if result.returncode != 0:
            print(
                "Warning: enum34 removal script exited with a non-zero status; "
                "continuing to PyInstaller anyway.",
                file=sys.stderr,
            )

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
        "--collect-all=RealtimeSTT",
        "--collect-all=pvporcupine",
        "--collect-all=mne",
        "--collect-all=pylsl",
        '--collect-all=whisper_timestamped', 
        '--collect-all=whisper',
        "--collect-all=dtw",
        "--collect-all=torch",
        "--collect-all=matplotlib",
        "--collect-all=PIL",
        "--collect-all=pyxdf",
        "--collect-all=pystray",
        "--collect-all=mne_lsl",
        "--collect-all=sounddevice",
        "--collect-all=soundfile",
        "--collect-all=phopylslhelper",
        "--collect-all=labrecorder",
        f"--distpath={repo_root}/dist",
        f"--workpath={repo_root}/build",
        f"--specpath={repo_root}",
        "--noconfirm",
        "--clean",
    ])



if __name__ == "__main__":
    main()


