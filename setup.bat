@echo off
REM One-time setup: builds the Python environment and installs dependencies.
REM Requires Python 3.11 and ffmpeg installed and on PATH first (see README).
cd /d "%~dp0"

echo === Checking Python ===
python --version || (echo [X] Python not found. Install Python 3.11 and tick "Add to PATH". & pause & exit /b 1)
echo === Checking ffmpeg ===
ffmpeg -version >nul 2>&1 || (echo [X] ffmpeg not found on PATH. Install it first (see README). & pause & exit /b 1)

echo === Creating virtual environment (one time) ===
python -m venv venv

echo === Installing dependencies (a few minutes) ===
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

echo === Verifying ===
venv\Scripts\python.exe -c "import yt_dlp, moviepy, streamlit; from app.config import config; print('OK - ready. No API keys needed.')"

echo.
echo Setup done. Next: run  make_videos.bat  to generate from sample_concepts.json
pause
