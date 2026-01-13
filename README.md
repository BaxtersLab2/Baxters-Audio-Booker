# Baxters Audio Booker

Turns a folder of chapter `.txt` files into `.mp3` voice audio files using open-source tooling.

## What this is
- Input: a folder full of `.txt` chapter files (one chapter per file)
- Output: `.mp3` files (one per chapter, or split into `__partXX` if a chapter is too long)
- Windows-first: includes one-click `.bat` launchers you can shortcut to Desktop

## Open-source parts used
- `edge-tts` (MIT) — Python library that wraps Microsoft Edge TTS voices.
  - PyPI: https://pypi.org/project/edge-tts/
  - GitHub: https://github.com/rany2/edge-tts

## Quick start (Windows)
1) Double-click `run_audio_booker_prompt.bat`
2) Press ENTER to accept defaults, or type:
   - the folder containing your chapter `.txt` files
   - the output folder for `.mp3`
   - voice/rate/volume (optional)

First run will create a local venv in `venv/` and install dependencies.

## Non-interactive runner
Edit these variables at the top of `run_audio_booker.bat`:
- `INPUT_DIR`
- `OUTPUT_DIR`
- `VOICE`
- `RATE`
- `VOLUME`

Then double-click it.

## Output
- Writes MP3 files to `output_mp3/` by default.
- If a chapter is long, it is split into multiple parts:
  - `ChapterName__part01.mp3`
  - `ChapterName__part02.mp3`

## Audacity (optional polish)
After generating MP3s, you can open them in Audacity to:
- trim silence
- normalize loudness
- apply light EQ
- export final audiobook chapters

## Notes
- This project intentionally keeps everything self-contained in this folder.
- `venv/` and `output_mp3/` are gitignored.
