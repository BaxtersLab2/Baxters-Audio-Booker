@echo off
setlocal enabledelayedexpansion

REM Interactive runner: prompts for input/output folders and voice settings.

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PY_EXE=%VENV_DIR%\Scripts\python.exe"

set "DEFAULT_INPUT=C:\Users\Baxter\Desktop\kicker report"
set "DEFAULT_OUTPUT=%SCRIPT_DIR%output_mp3"
set "DEFAULT_VOICE=en-US-GuyNeural"
set "DEFAULT_RATE=+0%"
set "DEFAULT_VOLUME=+0%"

echo.
echo === Baxters Audio Booker (Prompt) ===
echo (Press ENTER to accept defaults)
echo.

set "INPUT_DIR="
set /p INPUT_DIR=Input folder containing .txt files [!DEFAULT_INPUT!]: 
if "!INPUT_DIR!"=="" set "INPUT_DIR=!DEFAULT_INPUT!"

set "OUTPUT_DIR="
set /p OUTPUT_DIR=Output folder for .mp3 files [!DEFAULT_OUTPUT!]: 
if "!OUTPUT_DIR!"=="" set "OUTPUT_DIR=!DEFAULT_OUTPUT!"

set "VOICE="
set /p VOICE=Voice [!DEFAULT_VOICE!]: 
if "!VOICE!"=="" set "VOICE=!DEFAULT_VOICE!"

set "RATE="
set /p RATE=Rate (e.g. +0%, +10%, -10%) [!DEFAULT_RATE!]: 
if "!RATE!"=="" set "RATE=!DEFAULT_RATE!"

set "VOLUME="
set /p VOLUME=Volume (e.g. +0%, +10%, -10%) [!DEFAULT_VOLUME!]: 
if "!VOLUME!"=="" set "VOLUME=!DEFAULT_VOLUME!"

echo.
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
