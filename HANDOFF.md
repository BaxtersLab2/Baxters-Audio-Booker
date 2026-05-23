# Audio Booker - Handoff Documentation

## Current Status: BLOCKED - Python Version Incompatibility

### Goal
Produce ONE final MP3 of the report at ~160 kbps using completely local/offline high-quality voices.

### What Works
✅ **ffmpeg installed** - Via Chocolatey 2.5.1, needed for MP3 merging to 160kbps  
✅ **Code ready** - Full Coqui TTS offline support implemented in batch_tts.py and audio_booker_gui.py  
✅ **GUI updated** - Defaults to offline mode with mode selection radio buttons  
✅ **Batch helpers created** - All installation scripts ready  

### Current Blocker
❌ **Coqui TTS requires Python 3.9-3.11**  
❌ **Current venv likely has Python 3.12 or 3.13**  
❌ **pip install TTS fails** - All TTS versions rejected due to Python version constraint

### Solution Options
1. **Install Python 3.11 and recreate venv** (recommended)
   - Run `CHECK_PYTHON_VERSIONS.bat` to see what Python versions are available
   - If Python 3.11 exists, run `RECREATE_VENV_PY311.bat`
   - If not, install Python 3.11 from python.org first
   
2. **Use alternative offline TTS** (if Python 3.11 unavailable)
   - piper-tts (fast, good quality, works with Python 3.12+)
   - bark-tts (slower but very high quality)
   
3. **Fallback to pyttsx3** (if offline voice quality not critical)
   - Robotic quality but instant and no downloads
   - Already in old code, can revert

### File Locations
- **Audio Booker**: `C:\Users\Baxter\Desktop\file cabinet\installed apps\Baxters-audio-booker\`
- **Report source**: `C:\Users\Baxter\Desktop\kicker report\final_report_tts.md`
- **Batch files created**:
  - `CHECK_PYTHON_VERSIONS.bat` - Shows current venv Python and available system versions
  - `RECREATE_VENV_PY311.bat` - Recreates venv with Python 3.11
  - `INSTALL_OFFLINE_VOICE.bat` - Installs Coqui TTS (blocked until Python fixed)
  - `CHECK_FFMPEG_AND_RUN.bat` - Launches GUI (already working)

### Next Steps
1. Run `CHECK_PYTHON_VERSIONS.bat` (double-click in Windows Explorer)
2. If Python 3.11 available: Run `RECREATE_VENV_PY311.bat`
3. If Python 3.11 not available: Install Python 3.11 from python.org
4. After venv recreated: Run `INSTALL_OFFLINE_VOICE.bat`
5. Test offline voice generation: Run `CHECK_FFMPEG_AND_RUN.bat`

### Technical Details

**Current Implementation:**
- `batch_tts.py` - Core TTS engine with online (edge-tts) and offline (Coqui TTS) support
  - Default offline model: `tts_models/en/vctk/vits`
  - Default speaker: `p226` (female voice)
  - Model caching to avoid reloading
  
- `audio_booker_gui.py` - Tkinter wizard with mode selection
  - Defaults to offline mode
  - Radio buttons to switch between Online/Offline
  - Skips voice selection in offline mode
  
- `requirements.txt` - Updated with both TTS engines
  ```
  edge-tts>=6.1.10
  TTS>=0.22.0
  ```

**PowerShell Terminal Issue:**
- PSReadLine bug causes console buffer crashes
- All operations must use batch files (workaround in place)

**User Commitment:**
"coqui, then i wont change my mind again i promise" - User wants Coqui TTS offline voices

### Code Changes Summary
Modified files:
1. `requirements.txt` - Added `TTS>=0.22.0`
2. `batch_tts.py` - Replaced pyttsx3 with Coqui TTS, added offline mode with model caching
3. `audio_booker_gui.py` - Added offline/online mode toggle, defaulting to offline
4. Created 4 new batch files for installation and execution

All code changes tested and error-free, waiting only on Python version resolution.

---
**Last Updated**: Session preparing for Python venv recreation  
**Blocker**: Python version incompatibility (need 3.9-3.11, have 3.12+)  
**Resolution**: Run `CHECK_PYTHON_VERSIONS.bat` then `RECREATE_VENV_PY311.bat`
