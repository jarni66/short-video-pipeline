@echo off
REM One-click video generator (key-free, generate-only).
REM Usage:  make_videos.bat  [path-to-concepts.json]
REM If no file is given, it uses sample_concepts.json.
cd /d "%~dp0"

set "JSON=%~1"
if "%JSON%"=="" set "JSON=sample_concepts.json"

if not exist "venv\Scripts\python.exe" (
  echo [X] Environment not set up yet. Run  setup.bat  first.
  pause
  exit /b 1
)
if not exist "%JSON%" (
  echo [X] Concepts file not found: %JSON%
  pause
  exit /b 1
)

echo === Loading concepts from "%JSON%" ===
"venv\Scripts\python.exe" -c "import json,pipeline_state as ps; ps.load_concepts_into_state(json.load(open(r'%JSON%',encoding='utf-8')), replace=True); print('queued:', ps.counts(ps.load_state()))"
if errorlevel 1 ( echo [X] Failed to load concepts. & pause & exit /b 1 )

echo.
echo === Generating videos (this takes a few minutes each) ===
"venv\Scripts\python.exe" generate_pool.py

echo.
echo === Done. Your videos are here: ===
echo   %~dp0storage\tasks\^<name^>\final-1.mp4
pause
