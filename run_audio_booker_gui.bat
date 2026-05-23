@echo off
setlocal enabledelayedexpansion

REM Launches a simple GUI for selecting folders + voice and running conversion.

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "PY_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%SCRIPT_DIR%requirements.txt" (
  echo ERROR: requirements.txt missing in "%SCRIPT_DIR%"
  pause
  exit /b 1
)

if not exist "%SCRIPT_DIR%audio_booker_gui.py" (
  echo ERROR: audio_booker_gui.py missing in "%SCRIPT_DIR%"
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
echo Launching GUI...
"%VENV_DIR%\Scripts\pythonw.exe" "%SCRIPT_DIR%audio_booker_gui.py"
