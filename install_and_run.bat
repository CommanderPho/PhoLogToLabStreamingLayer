@echo off
echo Installing dependencies for LSL Logger App...
uv sync --all-extras
.venv\Scripts\activate
echo.
echo Starting LSL Logger App...
echo.
echo Features:
echo - System tray functionality (Ctrl+Alt+L to minimize)
echo - Global hotkey: Ctrl+Alt+L for quick log entry
echo - Minimize to tray instead of closing
echo.
echo Press any key to start...
pause >nul

python logger_app.py
