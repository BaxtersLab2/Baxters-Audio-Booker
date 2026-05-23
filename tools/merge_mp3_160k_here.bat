@echo off
setlocal
REM Runs merge/re-encode in the CURRENT folder.
REM Requires: ffmpeg on PATH. Install: winget install Gyan.FFmpeg

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0merge_mp3_160k.ps1" -Folder "%CD%" -PrefixNumbers

echo.
echo Done. Output file: report_160k.mp3
pause
