@echo off
setlocal enabledelayedexpansion

REM One-click batch: create venv (if missing), install deps, convert chapters to mp3.

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PY_EXE=%VENV_DIR%\Scripts\python.exe"

REM === Configure these paths ===
set "INPUT_DIR=C:\Users\Baxter\Desktop\kicker report"
set "OUTPUT_DIR=%SCRIPT_DIR%output_mp3"

REM === Voice options ===
set "VOICE=en-US-GuyNeural"
set "RATE=+0%"
set "VOLUME=+0%"

echo.
echo === Baxters Audio Booker ===
echo Script folder: "%SCRIPT_DIR%"
echo Input folder : "%INPUT_DIR%"
echo Output folder: "%OUTPUT_DIR%"
echo Voice: %VOICE%  Rate: %RATE%  Volume: %VOLUME%
echo.

if not exist "%SCRIPT_DIR%requirements.txt" (
  echo ERROR: requirements.txt missing in "%SCRIPT_DIR%"
  pause
  exit /b 1
)

if not exist "%SCRIPT_DIR%batch_tts.py" (
  echo ERROR: batch_tts.py missing in "%SCRIPT_DIR%"
  pause
  exit /b 1
)

if not exist "%PY_EXE%" (
  echo Creating venv in "%VENV_DIR%"...
  pushd "%SCRIPT_DIR%"
  py -3 -m venv "%VENV_DIR%" 1>nul 2>nul
  if errorlevel 1 (
    python -m venv "%VENV_DIR%"
  )
  popd
)

if not exist "%PY_EXE%" (
  echo ERROR: Could not create venv. Make sure Python is installed.
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)

echo Installing/updating dependencies...
"%PY_EXE%" -m pip install --upgrade pip
"%PY_EXE%" -m pip install -r "%SCRIPT_DIR%requirements.txt"

echo.
echo Running conversion...
"%PY_EXE%" "%SCRIPT_DIR%batch_tts.py" --input "%INPUT_DIR%" --output "%OUTPUT_DIR%" --voice "%VOICE%" --rate "%RATE%" --volume "%VOLUME%"

echo.
echo Finished. MP3 output is in: "%OUTPUT_DIR%"
pause
