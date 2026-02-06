@echo off
setlocal
cd /d "%~dp0\.."
python scripts\switch_uv_sources.py --mode release
endlocal


