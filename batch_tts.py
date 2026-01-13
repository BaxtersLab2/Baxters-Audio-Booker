import argparse
import asyncio
import re
from pathlib import Path

import edge_tts


def _sanitize_stem(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[<>:\\"/|?*]", "_", name)
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


async def _render_to_mp3(text: str, out_path: Path, voice: str, rate: str, volume: str) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    await communicate.save(str(out_path))


async def main_async(args: argparse.Namespace) -> int:
    in_dir = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not in_dir.exists() or not in_dir.is_dir():
        raise SystemExit(f"Input folder not found: {in_dir}")

    txt_files = sorted([p for p in in_dir.glob("*.txt") if p.is_file()])
    if not txt_files:
        raise SystemExit(f"No .txt files found in: {in_dir}")

    print(f"Found {len(txt_files)} text file(s) in {in_dir}")
    print(f"Output folder: {out_dir}")
    print(f"Voice: {args.voice} | Rate: {args.rate} | Volume: {args.volume}")

    for i, txt_path in enumerate(txt_files, start=1):
        raw_text = _read_text_file(txt_path)
        chunks = _split_text(raw_text, args.max_chars)

        safe_stem = _sanitize_stem(txt_path.stem)
        if not chunks:
            print(f"[{i}/{len(txt_files)}] Skipping empty file: {txt_path.name}")
            continue

        if len(chunks) == 1:
            out_path = out_dir / f"{safe_stem}.mp3"
            print(f"[{i}/{len(txt_files)}] Rendering: {txt_path.name} -> {out_path.name}")
            await _render_to_mp3(chunks[0], out_path, args.voice, args.rate, args.volume)
        else:
            print(f"[{i}/{len(txt_files)}] Long text ({len(chunks)} chunk(s)); creating parts for: {txt_path.name}")
            for part_index, chunk in enumerate(chunks, start=1):
                out_path = out_dir / f"{safe_stem}__part{part_index:02d}.mp3"
                print(f"  - part {part_index:02d} -> {out_path.name}")
                await _render_to_mp3(chunk, out_path, args.voice, args.rate, args.volume)

    print("Done.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Batch convert .txt chapters to .mp3 using Edge TTS.")
    p.add_argument("--input", required=True, help="Folder containing .txt chapter files")
    p.add_argument("--output", required=True, help="Folder to write .mp3 output")
    p.add_argument(
        "--voice",
        default="en-US-GuyNeural",
        help="Edge TTS voice name (example: en-US-GuyNeural, en-US-JennyNeural)",
    )
    p.add_argument("--rate", default="+0%", help="Speaking rate (example: +0%, +10%, -10%)")
    p.add_argument("--volume", default="+0%", help="Volume adjustment (example: +0%, +10%, -10%)")
    p.add_argument(
        "--max-chars",
        type=int,
        default=5500,
        help="Max characters per request; longer chapters will be split into numbered parts",
    )
    return p


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
