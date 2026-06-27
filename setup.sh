#!/bin/bash
# One-time setup for macOS / Linux. Builds the Python environment.
# Requires Python 3.11 and ffmpeg installed first (see README).
set -e
cd "$(dirname "$0")"

echo "=== Checking Python ==="
PY=python3.11
command -v $PY >/dev/null 2>&1 || PY=python3
command -v $PY >/dev/null 2>&1 || { echo "[X] Python 3.11 not found. Run: brew install python@3.11"; exit 1; }
$PY --version

echo "=== Checking ffmpeg ==="
command -v ffmpeg >/dev/null 2>&1 || { echo "[X] ffmpeg not found. Run: brew install ffmpeg"; exit 1; }

echo "=== Creating virtual environment (one time) ==="
$PY -m venv venv

echo "=== Installing dependencies (a few minutes) ==="
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements.txt

echo "=== Verifying ==="
venv/bin/python -c "import yt_dlp, moviepy, streamlit; from app.config import config; print('OK - ready. No API keys needed.')"

echo ""
echo "Setup done. Next: ./make_videos.sh   (generates from sample_concepts.json)"
