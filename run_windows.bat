@echo off
REM ============================================================
REM  Charger Link — run from source on Windows (no exe needed)
REM  Prereq: Python 3.10+ on PATH  (python --version works)
REM ============================================================
setlocal
cd /d "%~dp0"

echo == Python check ==
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found on PATH. Install Python 3.10+ and re-run.
    pause & exit /b 1
)
for /f "delims=" %%v in ('python --version 2^>^&1') do echo Using %%v

echo.
echo == Installing runtime deps (PySide6) ==
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed. Do:  python -m pip install -r requirements.txt
    pause & exit /b 1
)

echo.
echo == Launching Charger Link ==
python main.py %*

REM only reached if it closed on its own
echo.
pause
