# **Baxters Audio Booker >👂))**

> Turn any PDF or folder of text chapters into a polished MP3 audiobook — in minutes, with a simple point-and-click wizard.

![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)
![TTS](https://img.shields.io/badge/TTS-Microsoft%20Edge-blue?logo=microsoftedge)

---

## What It Does

**Baxters Audio Booker** converts PDFs or `.txt` chapter files into high-quality MP3 audio using Microsoft's Edge neural voices — the same voices used by Windows Narrator. No subscription, no API key, no cloud account required.

| Input | Output |
|---|---|
| A PDF (chapters extracted automatically) | One MP3 per chapter **or** one combined audiobook MP3 |
| A folder of `.txt` files (one per chapter) | Named and ordered to match your source files |

---

## Features

- **PDF support** — drop in a PDF and chapters are extracted automatically
- **300+ voices** — filter by language, pick male or female neural voices
- **Single audiobook output** — merge all chapters into one MP3 at 160 kbps (requires ffmpeg)
- **Live progress log** — see exactly which chapter is rendering and how long it has been running
- **Elapsed timer** — shows total conversion time in the status bar and log when done
- **One-click launcher** — no terminal needed; everything runs from `run_audio_booker_gui.bat`
- **Self-contained** — installs its own Python virtual environment on first run

---

## Requirements

### Python
- **Python 3.9 or later** — [python.org/downloads](https://www.python.org/downloads/)
- The launcher creates a local `venv/` automatically on first run

### Python packages (auto-installed on first launch)
| Package | Version | Purpose |
|---|---|---|
| `edge-tts` | >= 7.0.0 | Microsoft Edge neural TTS voices |
| `PyMuPDF` | >= 1.24.0 | PDF text extraction |

### ffmpeg (only needed for single-file output)
Required to merge all chapters into one combined MP3.

```
winget install Gyan.FFmpeg
```

After installing, close and reopen the GUI for the change to take effect.

---

## Installation

1. **Download or clone this repo**
   ```
   git clone https://github.com/BaxtersLab2/Baxters-Audio-Booker.git
   ```

2. **No further setup needed** — double-click the launcher and it handles everything.

---

## How to Use

### GUI (recommended)

Double-click **`run_audio_booker_gui.bat`**

On first run it creates a `venv/` folder and installs all dependencies. Then the four-step wizard opens:

| Step | What to do |
|---|---|
| **Step 1** | Browse to your PDF or a folder of `.txt` files. Set the output folder. |
| **Step 2** | Choose a language (e.g. English). |
| **Step 3** | Pick a voice from the list (e.g. `en-US-GuyNeural` — male, or `en-US-JennyNeural` — female). |
| **Step 4** | Choose **separate MP3s per chapter** or **one combined audiobook MP3**, then click **Run**. |

Progress updates appear in the log box in real time. An elapsed timer runs during conversion and the final time is shown when complete.

### Command Line

```bash
# Activate the venv first
venv\Scripts\activate

# Convert a folder of .txt files — one MP3 per chapter
python batch_tts.py --input "C:\path\to\chapters" --output "C:\path\to\output"

# Specify a voice and speed
python batch_tts.py --input "C:\chapters" --output "C:\output" --voice en-US-GuyNeural --rate +10%

# Merge everything into one audiobook MP3
python batch_tts.py --input "C:\chapters" --output "C:\output" --merge-all --merge-output audiobook.mp3 --merge-bitrate 160k
```

### List available voices

Double-click **`list_voices.bat`** to print all available Edge TTS voices.
Filter by locale — enter `en-US`, `en-GB`, `es-MX`, etc. when prompted.

---

## Output

- MP3 files are written to the output folder you choose (default: `output_mp3/` next to your input).
- If you selected **single combined MP3**, a merged `audiobook.mp3` is produced and the individual chapter files are removed automatically.
- If a chapter is very long it is split into parts while rendering — each part appears in the progress log.

---

## Optional: Post-Processing with Audacity

For professional-quality results, open your MP3s in [Audacity](https://www.audacityteam.org/) to:
- Normalize loudness (Effect → Normalize)
- Trim leading/trailing silence
- Apply light EQ for warmth
- Export as a final master audiobook file

---

## Project Structure

```
Baxters-Audio-Booker/
├── audio_booker_gui.py         # Main GUI application (Tkinter wizard)
├── batch_tts.py                # Core conversion engine (PDF -> TTS -> MP3)
├── requirements.txt            # Python dependencies
├── run_audio_booker_gui.bat    # <- Double-click this to launch
├── run_audio_booker.bat        # Non-interactive CLI launcher
├── run_audio_booker_prompt.bat # Interactive prompt-based launcher
├── list_voices.bat             # List available TTS voices
└── output_mp3/                 # Default output location (git-ignored)
```

---

## Dependencies & Licences

| Dependency | Licence | Notes |
|---|---|---|
| [edge-tts](https://github.com/rany2/edge-tts) | MIT | Wraps Microsoft Edge online TTS service |
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | AGPL-3.0 | PDF parsing and text extraction |
| [ffmpeg](https://ffmpeg.org/) | LGPL-2.1+ | MP3 merging; installed separately via winget |
| Python standard library | PSF | tkinter, asyncio, threading, etc. |

> **Note on PyMuPDF:** PyMuPDF is licensed under AGPL-3.0. If you distribute a modified version of this software you must comply with its terms. Personal and internal business use is unrestricted.

---

## Licence

```
MIT License

Copyright (c) 2026 BaxtersLab2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
