@echo off
setlocal enabledelayedexpansion

REM Lists available Edge TTS voices (requires venv).

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PY_EXE=%VENV_DIR%\Scripts\python.exe"
set "EDGE_TTS_EXE=%VENV_DIR%\Scripts\edge-tts.exe"

set "DEFAULT_FILTER=en-US"

echo.
echo === List Edge TTS Voices ===
echo.

echo Optional: filter results (example: en-US, en-GB, fr-FR)
set "FILTER="
set /p FILTER=Locale filter [!DEFAULT_FILTER!]: 
if "!FILTER!"=="" set "FILTER=!DEFAULT_FILTER!"

echo.

if not exist "%SCRIPT_DIR%requirements.txt" (
  echo ERROR: requirements.txt missing in "%SCRIPT_DIR%"
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
echo Fetching voices (this can take a moment)...
if exist "%EDGE_TTS_EXE%" (
  "%EDGE_TTS_EXE%" --list-voices | findstr /i "Locale: %FILTER%" /c:"Name:" /c:"Locale:" /c:"Gender:" /c:"ShortName:" /c:"FriendlyName:" 
) else (
  "%PY_EXE%" -m edge_tts --list-voices | findstr /i "Locale: %FILTER%" /c:"Name:" /c:"Locale:" /c:"Gender:" /c:"ShortName:" /c:"FriendlyName:" 
)

echo.
echo Tip: copy a voice like "en-US-GuyNeural" into run_audio_booker*.bat
pause
