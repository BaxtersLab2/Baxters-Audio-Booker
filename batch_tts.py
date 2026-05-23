import argparse
import asyncio
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from TTS.api import TTS as CoquiTTS
    COQUI_TTS_AVAILABLE = True
except ImportError:
    COQUI_TTS_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def extract_pdf_to_folder(pdf_path: str | Path, out_folder: str | Path, progress_callback=None) -> Path:
    """Extract a PDF into per-chapter .txt files in out_folder. Returns out_folder."""
    def _report(msg: str) -> None:
        print(msg)
        if progress_callback:
            progress_callback(msg)

    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF not installed. Run: pip install PyMuPDF")

    pdf_path = Path(pdf_path)
    out_folder = Path(out_folder)
    out_folder.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    all_lines: list[tuple[str, float]] = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                text = "".join(s["text"] for s in line["spans"]).strip()
                size = max((s["size"] for s in line["spans"]), default=0)
                if text:
                    all_lines.append((text, size))
    doc.close()

    if not all_lines:
        raise RuntimeError(f"No readable text found in PDF: {pdf_path.name}")

    sizes = sorted(s for _, s in all_lines if s > 0)
    median_size = sizes[len(sizes) // 2]
    heading_thresh = median_size * 1.25

    chapter_re = re.compile(
        r'^(chapter\s+\d+|part\s+[ivxlc\d]+|introduction|preface|foreword|'
        r'appendix\s*[a-z]?|epilogue|prologue|conclusion|acknowledgments?)$',
        re.IGNORECASE,
    )

    chapters: list[tuple[str, list[str]]] = []
    cur_title = "Opening"
    cur_lines: list[str] = []

    for text, size in all_lines:
        is_heading = (
            size >= heading_thresh
            or chapter_re.match(text)
            or (text.isupper() and 4 < len(text) < 80)
        )
        if is_heading and cur_lines:
            cleaned = _clean_lines(cur_lines)
            if cleaned:
                chapters.append((cur_title, cleaned))
            cur_title = text
            cur_lines = []
        elif not is_heading:
            cur_lines.append(text)

    if cur_lines:
        cleaned = _clean_lines(cur_lines)
        if cleaned:
            chapters.append((cur_title, cleaned))

    if not chapters:
        fallback = _clean_lines([t for t, _ in all_lines])
        chapters = [("Audiobook", fallback)] if fallback else []

    if not chapters:
        raise RuntimeError("PDF appears to contain no extractable text.")

    for i, (title, text) in enumerate(chapters):
        safe = re.sub(r'[<>:\\"/|?*]', '_', title)[:60].strip()
        fname = out_folder / f"{i+1:02d} - {safe}.txt"
        fname.write_text(text, encoding="utf-8")
        _report(f"  Extracted chapter {i+1}: {fname.name}")

    _report(f"Extracted {len(chapters)} chapter(s) from {pdf_path.name}")
    return out_folder


def _clean_lines(lines: list[str]) -> str:
    text = "\n".join(lines)
    text = re.sub(r'-\n(\w)', r'\1', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _sanitize_stem(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[<>:\\"/|?*]', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name[:120] if len(name) > 120 else name


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")


def _split_text(text: str, max_chars: int) -> list[str]:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if current:
            chunks.append("\n\n".join(current).strip())
            current = []
            current_len = 0

    for para in paragraphs:
        if len(para) > max_chars:
            flush()
            sentences = re.split(r"(?<=[.!?])\s+", para)
            sentence_buf: list[str] = []
            sentence_len = 0
            for s in sentences:
                if not s:
                    continue
                if sentence_len + len(s) + 1 > max_chars and sentence_buf:
                    chunks.append(" ".join(sentence_buf).strip())
                    sentence_buf = [s]
                    sentence_len = len(s)
                else:
                    sentence_buf.append(s)
                    sentence_len += len(s) + 1
            if sentence_buf:
                chunks.append(" ".join(sentence_buf).strip())
            continue

        add_len = len(para) + (2 if current else 0)
        if current_len + add_len > max_chars:
            flush()
        current.append(para)
        current_len += add_len

    flush()
    return chunks


_coqui_tts_cache = None

def _render_to_mp3_offline(text: str, out_path: Path, model_name: str = "tts_models/en/vctk/vits", speaker: str = "p226") -> None:
    """Offline TTS using Coqui TTS (neural voices, high quality)"""
    global _coqui_tts_cache
    
    if not COQUI_TTS_AVAILABLE:
        raise RuntimeError("Coqui TTS not installed. Install: pip install TTS")
    
    # Cache the TTS model to avoid reloading for each file
    if _coqui_tts_cache is None or _coqui_tts_cache[0] != model_name:
        print(f"Loading Coqui TTS model: {model_name} (first run downloads ~200-500MB)...")
        _coqui_tts_cache = (model_name, CoquiTTS(model_name=model_name, progress_bar=False))
    
    _, tts = _coqui_tts_cache
    
    # Use speaker if model supports it
    if hasattr(tts, 'speakers') and tts.speakers and speaker in tts.speakers:
        tts.tts_to_file(text=text, file_path=str(out_path), speaker=speaker)
    else:
        tts.tts_to_file(text=text, file_path=str(out_path))


async def _render_to_mp3(text: str, out_path: Path, voice: str, rate: str, volume: str) -> None:
    """Online TTS using edge-tts (requires internet)"""
    if not EDGE_TTS_AVAILABLE:
        raise RuntimeError("edge-tts not installed")
    
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(out_path))


def _find_ffmpeg() -> str | None:
    return shutil.which("ffmpeg")


def _write_concat_file(mp3_paths: list[Path], concat_file: Path) -> None:
    # ffmpeg concat demuxer format: https://ffmpeg.org/ffmpeg-formats.html#concat
    # We keep this simple and rely on typical filenames (no single quotes).
    lines: list[str] = []
    for p in mp3_paths:
        # Use absolute paths to avoid any cwd surprises.
        lines.append(f"file '{str(p)}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _merge_mp3_folder_to_160k(out_dir: Path, output_name: str = "report_160k.mp3", bitrate: str = "160k", progress_callback=None) -> None:
    def _report(msg: str) -> None:
        print(msg)
        if progress_callback:
            progress_callback(msg)

    ffmpeg = _find_ffmpeg()
    if not ffmpeg:
        _report("Merge: ffmpeg not found on PATH — install ffmpeg and try again.")
        return

    out_dir = out_dir.expanduser().resolve()
    if not out_dir.exists():
        _report(f"Merge: output folder not found: {out_dir}")
        return

    output_path = (out_dir / output_name).resolve()

    mp3_paths = sorted(
        [p for p in out_dir.glob("*.mp3") if p.is_file() and p.resolve() != output_path],
        key=lambda p: p.name.lower(),
    )

    if not mp3_paths:
        _report("Merge: no MP3 files found; skipping.")
        return

    # If there is only one MP3, still re-encode it to the desired bitrate.
    if len(mp3_paths) == 1:
        src = mp3_paths[0]
        _report(f"Merge: re-encoding {src.name} -> {output_path.name} at {bitrate}")
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(src), "-c:a", "libmp3lame", "-b:a", bitrate, str(output_path)],
            check=True,
        )
        src.unlink(missing_ok=True)
        return

    concat_file = out_dir / "files.txt"
    _write_concat_file(mp3_paths, concat_file)

    _report(f"Merge: combining {len(mp3_paths)} MP3 files -> {output_path.name} at {bitrate}")
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:a",
            "libmp3lame",
            "-b:a",
            bitrate,
            str(output_path),
        ],
        check=True,
    )
    # Clean up individual chapter/part files now that the merged file exists
    concat_file.unlink(missing_ok=True)
    for p in mp3_paths:
        p.unlink(missing_ok=True)
    _report(f"Merge: cleaned up {len(mp3_paths)} source files.")


async def main_async(args: argparse.Namespace, progress_callback=None) -> int:
    def _report(msg: str) -> None:
        print(msg)
        if progress_callback:
            progress_callback(msg)

    in_dir = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not in_dir.exists() or not in_dir.is_dir():
        raise SystemExit(f"Input folder not found: {in_dir}")

    txt_files = sorted([p for p in in_dir.glob("*.txt") if p.is_file()])
    if not txt_files:
        raise SystemExit(f"No .txt files found in: {in_dir}")

    offline_mode = getattr(args, "offline", False)

    if offline_mode:
        if not COQUI_TTS_AVAILABLE:
            raise SystemExit("Offline mode requires Coqui TTS. Install: pip install TTS")
        _report("[OFFLINE MODE] Using Coqui TTS (neural voices, high quality)")
        coqui_model = getattr(args, "coqui_model", "tts_models/en/vctk/vits")
        coqui_speaker = getattr(args, "coqui_speaker", "p226")
        _report(f"Model: {coqui_model} | Speaker: {coqui_speaker}")
    else:
        if not EDGE_TTS_AVAILABLE:
            raise SystemExit("Online mode requires edge-tts. Install: pip install edge-tts")
        _report("[ONLINE MODE] Using Microsoft Edge TTS")
        _report(f"Voice: {args.voice} | Rate: {args.rate} | Volume: {args.volume}")

    _report(f"Found {len(txt_files)} file(s) to convert. Output folder: {out_dir}")

    for i, txt_path in enumerate(txt_files, start=1):
        raw_text = _read_text_file(txt_path)
        chunks = _split_text(raw_text, args.max_chars)

        safe_stem = _sanitize_stem(txt_path.stem)
        if not chunks:
            _report(f"[{i}/{len(txt_files)}] Skipping empty file: {txt_path.name}")
            continue

        if len(chunks) == 1:
            out_path = out_dir / f"{safe_stem}.mp3"
            _report(f"[{i}/{len(txt_files)}] Rendering: {txt_path.name} ...")
            if offline_mode:
                _render_to_mp3_offline(chunks[0], out_path, args.coqui_model, args.coqui_speaker)
            else:
                await _render_to_mp3(chunks[0], out_path, args.voice, args.rate, args.volume)
            _report(f"[{i}/{len(txt_files)}] Done: {out_path.name}")
        else:
            _report(f"[{i}/{len(txt_files)}] Long chapter ({len(chunks)} parts): {txt_path.name}")
            for part_index, chunk in enumerate(chunks, start=1):
                out_path = out_dir / f"{safe_stem}__part{part_index:02d}.mp3"
                _report(f"  [{part_index}/{len(chunks)}] Rendering part {part_index} ...")
                if offline_mode:
                    _render_to_mp3_offline(chunk, out_path, args.coqui_model, args.coqui_speaker)
                else:
                    await _render_to_mp3(chunk, out_path, args.voice, args.rate, args.volume)
                _report(f"  [{part_index}/{len(chunks)}] Done: {out_path.name}")

    if getattr(args, "merge_all", False):
        _report("Merging all chapters into single MP3 (this may take a moment)...")
        try:
            _merge_mp3_folder_to_160k(
                out_dir,
                output_name=getattr(args, "merge_output", "report_160k.mp3"),
                bitrate=getattr(args, "merge_bitrate", "160k"),
                progress_callback=progress_callback,
            )
            _report("Merge complete.")
        except subprocess.CalledProcessError as e:
            _report(f"Postprocess: ffmpeg failed (skipping): {e}")
        except Exception as e:
            _report(f"Postprocess: merge failed (skipping): {e}")

    _report("All done!")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Batch convert .txt chapters to .mp3 using Edge TTS or offline SAPI.")
    p.add_argument("--input", required=True, help="Folder containing .txt chapter files")
    p.add_argument("--output", required=True, help="Folder to write .mp3 output")
    p.add_argument(
        "--offline",
        action="store_true",
        help="Use offline Coqui TTS (neural voices, no internet required)",
    )
    p.add_argument(
        "--voice",
        default="en-US-GuyNeural",
        help="[ONLINE] Edge TTS voice name (example: en-US-GuyNeural, en-US-JennyNeural)",
    )
    p.add_argument("--rate", default="+0%", help="[ONLINE] Speaking rate (example: +0%, +10%, -10%)")
    p.add_argument("--volume", default="+0%", help="[ONLINE] Volume adjustment (example: +0%, +10%, -10%)")
    p.add_argument(
        "--coqui-model",
        default="tts_models/en/vctk/vits",
        help="[OFFLINE] Coqui TTS model name (default: tts_models/en/vctk/vits)",
    )
    p.add_argument(
        "--coqui-speaker",
        default="p226",
        help="[OFFLINE] Coqui TTS speaker ID for multi-speaker models (default: p226 - female voice)",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=5500,
        help="Max characters per request; longer chapters will be split into numbered parts",
    )
    p.add_argument(
        "--merge-all",
        action="store_true",
        help="After TTS completes, merge/re-encode all output MP3s into a single 160 kbps MP3 (requires ffmpeg)",
    )
    p.add_argument(
        "--merge-output",
        default="report_160k.mp3",
        help="Filename for the merged MP3 (used with --merge-all)",
    )
    p.add_argument(
        "--merge-bitrate",
        default="160k",
        help="Target bitrate for merged MP3 (used with --merge-all). Example: 160k",
    )
    return p


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
