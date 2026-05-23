# Audio Booker Quick Start Guide

## ⚠️ CURRENT STATUS: Need Python 3.11

The app is ready but needs Python 3.11 installed in the venv.

### 🚀 Quick Fix (3 steps)

1. **Check what Python you have:**
   ```
   Double-click: CHECK_PYTHON_VERSIONS.bat
   ```
   Look for Python 3.11 in the list.

2. **If you have Python 3.11:**
   ```
   Double-click: RECREATE_VENV_PY311.bat
   ```
   This will backup old venv and create new one with Python 3.11.

3. **If you DON'T have Python 3.11:**
   - Download Python 3.11 from https://www.python.org/downloads/
   - Install it (check "Add to PATH")
   - Then run `RECREATE_VENV_PY311.bat`

### 📦 After Python 3.11 is installed

4. **Install offline voices:**
   ```
   Double-click: INSTALL_OFFLINE_VOICE.bat
   ```
   This downloads Coqui TTS (~300MB first time).

5. **Run the app:**
   ```
   Double-click: CHECK_FFMPEG_AND_RUN.bat
   ```

### 🎯 Using the App

1. **Step 1**: Choose "Offline (Coqui TTS)" mode (default)
2. **Step 2**: Click "Select folder with .md files"
   - Navigate to: `C:\Users\Baxter\Desktop\kicker report\`
   - Click "Select Folder"
3. **Step 3**: Check "Auto-merge to single 160k MP3" (if you want one file)
4. **Step 4**: Click "Run Batch TTS"

Output will be in the report folder.

### 📝 Notes

- **Offline mode**: No internet required, neural voices, ~5-10 sec per paragraph
- **Online mode**: Requires internet, slightly better quality, faster
- **Auto-merge**: Combines all MP3s into one `report_160k.mp3` file at 160 kbps

### ❓ Troubleshooting

**"ffmpeg not found"**: Run as administrator:
```
choco install ffmpeg -y
```

**"Python 3.11 not found"**: Download from python.org and install.

**Terminal crashes**: This is a known Windows bug. Use the batch files instead of typing commands.
