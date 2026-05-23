@echo off
echo ====================================
echo Checking Python Versions
echo ====================================
echo.

echo Current venv Python version:
venv\Scripts\python.exe --version
echo.

echo All installed Python versions on system:
py -0
echo.

echo ====================================
echo Available Python 3.11?
py -3.11 --version 2>nul
if %errorlevel% equ 0 (
    echo YES - Python 3.11 is available
) else (
    echo NO - Python 3.11 not found
)
echo ====================================
pause
