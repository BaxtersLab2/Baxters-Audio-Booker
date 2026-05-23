@echo off
echo ====================================
echo Recreating venv with Python 3.11
echo ====================================
echo.

echo Step 1: Backing up old venv folder name...
if exist venv_old (
    echo Removing previous backup...
    rmdir /s /q venv_old
)
if exist venv (
    echo Renaming current venv to venv_old...
    ren venv venv_old
)
echo.

echo Step 2: Creating new venv with Python 3.11...
py -3.11 -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create venv with Python 3.11
    echo Restoring old venv...
    if exist venv_old (
        ren venv_old venv
    )
    pause
    exit /b 1
)
echo.

echo Step 3: Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip
echo.

echo Step 4: Installing requirements...
venv\Scripts\pip.exe install -r requirements.txt
echo.

echo ====================================
echo SUCCESS! venv recreated with Python 3.11
echo Old venv backed up as venv_old
echo ====================================
pause
