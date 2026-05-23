import argparse
import asyncio
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Add the app folder to sys.path so batch_tts can be found when run from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))


@dataclass(frozen=True)
class VoiceItem:
    short_name: str
    locale: str
    gender: str
    friendly_name: str


def _safe_str(v: object) -> str:
    return "" if v is None else str(v)


async def _fetch_voices_async() -> list[VoiceItem]:
    import edge_tts

    voices_raw = await edge_tts.list_voices()
    voices: list[VoiceItem] = []

    for v in voices_raw:
        voices.append(
            VoiceItem(
                short_name=_safe_str(v.get("ShortName")),
                locale=_safe_str(v.get("Locale")),
                gender=_safe_str(v.get("Gender")),
                friendly_name=_safe_str(v.get("FriendlyName")) or _safe_str(v.get("Name")),
            )
        )

    # Prefer stable ordering: locale then friendly name
    voices.sort(key=lambda x: (x.locale, x.friendly_name, x.short_name))
    return voices


def _default_output_for(input_dir: str) -> str:
    if input_dir:
        p = Path(input_dir)
        if p.exists() and p.is_dir():
            return str(p / "output_mp3")
    # Fall back to repo-local output
    return str(Path(__file__).resolve().parent / "output_mp3")


class AudioBookerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        _src_time = time.strftime(
            "%Y-%m-%d %H:%M",
            time.localtime(Path(__file__).stat().st_mtime),
        )
        self.root.title(f"Baxters Audio Booker  [code: {_src_time}]")
        self.root.geometry("760x520")

        self.voices: list[VoiceItem] = []
        self.filtered_voices: list[VoiceItem] = []
        self.selected_voice_short: str = ""

        self.language_display_to_code: dict[str, str] = {}

        self.step_index = 0

        self.input_mode = tk.StringVar(value="pdf")   # "pdf" or "folder"
        self.pdf_path = tk.StringVar(value="")
        self.input_dir = tk.StringVar(value=str(Path.home() / "Desktop"))
        self.output_dir = tk.StringVar(value=_default_output_for(self.input_dir.get()))
        self.language_choice = tk.StringVar(value="English (en)")
        self.rate = tk.StringVar(value="+0%")
        self.volume = tk.StringVar(value="+0%")
        self.max_chars = tk.IntVar(value=5500)
        self.max_chars_display = tk.StringVar(value=str(self.max_chars.get()))

        self.output_format = tk.StringVar(value="split")   # "split" or "single"
        self.merge_bitrate = tk.StringVar(value="160k")
        self.merge_output = tk.StringVar(value="audiobook.mp3")
        # legacy compat
        self.merge_all = tk.BooleanVar(value=False)

        self.offline_mode = tk.BooleanVar(value=False)  # Default to online (edge-tts)
        self.coqui_model = tk.StringVar(value="tts_models/en/vctk/vits")
        self.coqui_speaker = tk.StringVar(value="p226")  # Female voice

        self.status = tk.StringVar(value="Loading voices...")
        self._running = False
        self._start_time: float | None = None
        self._timer_after_id: str | None = None

        self._build_wizard()
        self._set_busy(False)
        self.status.set("Loading voices...")
        self._fetch_voices_threaded()

    def _build_wizard(self) -> None:
        pad = 10

        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=pad, pady=(pad, 0))
        ttk.Label(header, text="Baxters Audio Booker", font=("Segoe UI", 16, "bold")).pack(anchor=tk.W)
        ttk.Label(header, text="Plain-English steps: Back / Next.").pack(anchor=tk.W)

        self.step_title = tk.StringVar(value="")
        ttk.Label(self.root, textvariable=self.step_title, font=("Segoe UI", 11, "bold")).pack(
            fill=tk.X, padx=pad, pady=(10, 0)
        )

        self.step_container = ttk.Frame(self.root)
        self.step_container.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)

        self.steps: list[ttk.Frame] = []
        self._build_step_1_folders(self.step_container, pad)
        self._build_step_2_locale(self.step_container, pad)
        self._build_step_3_voice(self.step_container, pad)
        self._build_step_4_run(self.step_container, pad)

        nav = ttk.Frame(self.root)
        nav.pack(fill=tk.X, padx=pad, pady=(0, pad))
        self.back_btn = ttk.Button(nav, text="Back", command=self._back)
        self.back_btn.pack(side=tk.LEFT)
        self.next_btn = ttk.Button(nav, text="Next", command=self._next)
        self.next_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.run_btn = ttk.Button(nav, text="Run", command=self._run)
        self.run_btn.pack(side=tk.LEFT, padx=(8, 0))
        self.open_out_btn = ttk.Button(nav, text="Open output folder", command=self._open_output)
        self.open_out_btn.pack(side=tk.LEFT, padx=(8, 0))

        log_box = ttk.LabelFrame(self.root, text="What's happening (progress updates appear here)")
        log_box.pack(fill=tk.BOTH, expand=False, padx=pad, pady=(0, 4))
        self.log = tk.Text(log_box, height=10, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)
        self.log.configure(state=tk.DISABLED)

        self.progress_bar = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress_bar.pack(fill=tk.X, padx=pad, pady=(0, 2))

        ttk.Label(self.root, textvariable=self.status).pack(fill=tk.X, padx=pad, pady=(0, pad))

        self._show_step(0)

    def _build_step_1_folders(self, parent: ttk.Frame, pad: int) -> None:
        step = ttk.Frame(parent)
        self.steps.append(step)

        # ── Input source ──────────────────────────────────────────────────
        src_box = ttk.LabelFrame(step, text="Step 1 — Choose your input")
        src_box.pack(fill=tk.X, padx=pad, pady=(pad, 4))

        ttk.Radiobutton(src_box, text="PDF file  (recommended — chapters extracted automatically)",
                        variable=self.input_mode, value="pdf",
                        command=self._on_input_mode_changed).pack(
            anchor=tk.W, padx=pad, pady=(pad, 2))
        pdf_row = ttk.Frame(src_box)
        pdf_row.pack(fill=tk.X, padx=(pad * 3, pad), pady=(0, pad))
        self._pdf_path_var = self.pdf_path
        ttk.Entry(pdf_row, textvariable=self.pdf_path, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(pdf_row, text="Browse PDF…", command=self._browse_pdf).pack(
            side=tk.LEFT, padx=(6, 0))

        ttk.Radiobutton(src_box, text="Text folder  (folder of .txt chapter files)",
                        variable=self.input_mode, value="folder",
                        command=self._on_input_mode_changed).pack(
            anchor=tk.W, padx=pad, pady=(4, 2))
        folder_row = ttk.Frame(src_box)
        folder_row.pack(fill=tk.X, padx=(pad * 3, pad), pady=(0, pad))
        ttk.Entry(folder_row, textvariable=self.input_dir).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_row, text="Browse folder…", command=self._browse_input).pack(
            side=tk.LEFT, padx=(6, 0))

        # ── Output folder ─────────────────────────────────────────────────
        out_box = ttk.LabelFrame(step, text="Output folder")
        out_box.pack(fill=tk.X, padx=pad, pady=(4, pad))
        out_row = ttk.Frame(out_box)
        out_row.pack(fill=tk.X, padx=pad, pady=pad)
        ttk.Entry(out_row, textvariable=self.output_dir).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_row, text="Browse…", command=self._browse_output).pack(
            side=tk.LEFT, padx=(6, 0))

    def _build_step_2_locale(self, parent: ttk.Frame, pad: int) -> None:
        step = ttk.Frame(parent)
        self.steps.append(step)

        box = ttk.LabelFrame(step, text="Step 2 — Choose a language")
        box.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)

        ttk.Label(box, text="Pick a language. The voice list updates automatically.").pack(
            anchor=tk.W, padx=pad, pady=(pad, 6)
        )

        row = ttk.Frame(box)
        row.pack(fill=tk.X, padx=pad, pady=(0, 8))
        ttk.Label(row, text="Language:").pack(side=tk.LEFT)
        self.language_combo = ttk.Combobox(row, textvariable=self.language_choice, state="readonly")
        self.language_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.language_combo.bind("<<ComboboxSelected>>", lambda _e: self._apply_language_filter())

        row = ttk.Frame(box)
        row.pack(fill=tk.X, padx=pad, pady=(0, pad))
        ttk.Button(row, text="Refresh from internet", command=self._refresh_voices).pack(side=tk.LEFT)

        ttk.Label(box, text="Example: choose English to see all English voices.").pack(
            anchor=tk.W, padx=pad, pady=(0, pad)
        )

    def _build_step_3_voice(self, parent: ttk.Frame, pad: int) -> None:
        step = ttk.Frame(parent)
        self.steps.append(step)

        box = ttk.LabelFrame(step, text="Step 3 — Pick a voice")
        box.pack(fill=tk.BOTH, expand=True, padx=pad, pady=pad)

        ttk.Label(box, text="Click a voice to highlight it, then click Next.").pack(anchor=tk.W, padx=pad, pady=(pad, 6))

        list_row = ttk.Frame(box)
        list_row.pack(fill=tk.BOTH, expand=True, padx=pad, pady=(0, pad))

        self.voice_list = tk.Listbox(list_row, height=14)
        scroll = ttk.Scrollbar(list_row, orient=tk.VERTICAL, command=self.voice_list.yview)
        self.voice_list.configure(yscrollcommand=scroll.set)
        self.voice_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.voice_list.bind("<<ListboxSelect>>", self._on_voice_selected)

        self.voice_selected_label = tk.StringVar(value="Selected voice: (none)")
        ttk.Label(box, textvariable=self.voice_selected_label).pack(anchor=tk.W, padx=pad, pady=(0, pad))

    def _build_step_4_run(self, parent: ttk.Frame, pad: int) -> None:
        step = ttk.Frame(parent)
        self.steps.append(step)

        # ── Output format ─────────────────────────────────────────────────
        fmt_box = ttk.LabelFrame(step, text="Output format")
        fmt_box.pack(fill=tk.X, padx=pad, pady=(pad, 4))

        ttk.Radiobutton(fmt_box,
                        text="One MP3 per chapter  (numbered: 01 - Chapter Title.mp3, 02 - ..., etc.)",
                        variable=self.output_format, value="split").pack(
            anchor=tk.W, padx=pad, pady=(pad, 2))
        ttk.Radiobutton(fmt_box,
                        text="Single combined MP3  (all chapters merged into one file, requires ffmpeg)",
                        variable=self.output_format, value="single").pack(
            anchor=tk.W, padx=pad, pady=(2, 4))

        single_row = ttk.Frame(fmt_box)
        single_row.pack(fill=tk.X, padx=(pad * 3, pad), pady=(0, pad))
        ttk.Label(single_row, text="Filename:").pack(side=tk.LEFT)
        ttk.Entry(single_row, textvariable=self.merge_output, width=28).pack(
            side=tk.LEFT, padx=(6, 16))
        ttk.Label(single_row, text="Bitrate:").pack(side=tk.LEFT)
        ttk.Entry(single_row, textvariable=self.merge_bitrate, width=8).pack(
            side=tk.LEFT, padx=(6, 0))

        # ── Speed / volume ────────────────────────────────────────────────
        settings_box = ttk.LabelFrame(step, text="Playback settings")
        settings_box.pack(fill=tk.X, padx=pad, pady=(4, pad))

        row = ttk.Frame(settings_box)
        row.pack(fill=tk.X, padx=pad, pady=(pad, 4))
        ttk.Label(row, text="Speed:").pack(side=tk.LEFT)
        speed_cb = ttk.Combobox(row, textvariable=self.rate, state="readonly", width=16)
        speed_cb["values"] = ["-25%", "-10%", "+0%", "+10%", "+25%", "+50%"]
        speed_cb.set("+0%")
        speed_cb.pack(side=tk.LEFT, padx=(6, 20))
        ttk.Label(row, text="(+0% = normal, +10% = slightly faster)").pack(side=tk.LEFT)

        row2 = ttk.Frame(settings_box)
        row2.pack(fill=tk.X, padx=pad, pady=(0, pad))
        ttk.Label(row2, text="Volume:").pack(side=tk.LEFT)
        vol_cb = ttk.Combobox(row2, textvariable=self.volume, state="readonly", width=16)
        vol_cb["values"] = ["-10%", "+0%", "+10%", "+20%"]
        vol_cb.set("+0%")
        vol_cb.pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(step, text="Click Run when ready.",
                  font=("Segoe UI", 9)).pack(anchor=tk.W, padx=pad, pady=(0, 4))

    def _show_step(self, index: int) -> None:
        index = max(0, min(index, len(self.steps) - 1))
        for i, step in enumerate(self.steps):
            step.pack_forget()
            if i == index:
                step.pack(fill=tk.BOTH, expand=True)

        self.step_index = index

        titles = [
            "Step 1 of 4: Pick folders",
            "Step 2 of 4: Choose language",
            "Step 3 of 4: Pick a voice",
            "Step 4 of 4: Run",
        ]
        self.step_title.set(titles[index] if index < len(titles) else "")

        self.back_btn.configure(state=tk.NORMAL if index > 0 else tk.DISABLED)
        self.next_btn.configure(state=tk.NORMAL if index < 3 else tk.DISABLED)
        self.run_btn.configure(state=tk.NORMAL if index == 3 else tk.DISABLED)

        # Extra gating: Next shouldn’t allow you to proceed without required choices.
        if index == 0:
            self._sync_nav_for_step_1()
        elif index == 2:
            self._sync_nav_for_step_3()

    def _back(self) -> None:
        self._show_step(self.step_index - 1)

    def _next(self) -> None:
        if self.step_index == 0 and not self._validate_step_1():
            return
        if self.step_index == 2 and not self.selected_voice_short:
            messagebox.showerror("Pick a voice", "Click a voice to highlight it, then click Next.")
            return
        self._show_step(self.step_index + 1)

    def _sync_nav_for_step_1(self) -> None:
        self.next_btn.configure(state=tk.NORMAL if self._validate_step_1(silent=True) else tk.DISABLED)

    def _sync_nav_for_step_3(self) -> None:
        self.next_btn.configure(state=tk.NORMAL if self.selected_voice_short else tk.DISABLED)

    def _on_input_mode_changed(self) -> None:
        self._sync_nav_for_step_1()

    def _validate_step_1(self, silent: bool = False) -> bool:
        if self.input_mode.get() == "pdf":
            p = self.pdf_path.get().strip()
            if not p:
                if not silent:
                    messagebox.showerror("No PDF selected", "Browse for a PDF file first.")
                return False
            if not Path(p).is_file():
                if not silent:
                    messagebox.showerror("PDF not found", f"File not found:\n{p}")
                return False
            return True
        else:
            in_dir = Path(self.input_dir.get()).expanduser().resolve()
            if not in_dir.exists() or not in_dir.is_dir():
                if not silent:
                    messagebox.showerror("Invalid input folder", str(in_dir))
                return False
            txt_files = list(in_dir.glob("*.txt"))
            if not txt_files:
                if not silent:
                    messagebox.showerror("No .txt files", f"No .txt files found in:\n{in_dir}")
                return False
            return True

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        try:
            # Don’t disable navigation permanently; we gate per-step separately.
            self.open_out_btn.configure(state=state)
        except Exception:
            pass
        try:
            if busy:
                self.progress_bar.start(12)
            else:
                self.progress_bar.stop()
                self.progress_bar["value"] = 0
        except Exception:
            pass
    def _log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        self.status.set(message)

    def _browse_input(self) -> None:
        d = filedialog.askdirectory(title="Select folder containing .txt chapters")
        if d:
            self.input_dir.set(d)
            self.output_dir.set(_default_output_for(d))
            self._sync_nav_for_step_1()

    def _browse_output(self) -> None:
        d = filedialog.askdirectory(title="Select output folder for .mp3")
        if d:
            self.output_dir.set(d)

    def _browse_pdf(self) -> None:
        p = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if p:
            self.pdf_path.set(p)
            pdf_stem = Path(p).stem
            self.output_dir.set(str(Path(p).parent / (pdf_stem + "_mp3")))
            self.merge_output.set(pdf_stem + ".mp3")
            self._sync_nav_for_step_1()

    def _open_output(self) -> None:
        out = Path(self.output_dir.get()).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        try:
            import os

            os.startfile(str(out))
        except Exception as e:
            messagebox.showerror("Open folder failed", str(e))

    def _set_max_chars(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("Max chars")
        top.geometry("360x140")
        ttk.Label(
            top,
            text="Max characters per TTS request.\nLong chapters are split into parts.",
        ).pack(padx=12, pady=(12, 6), anchor=tk.W)
        v = tk.IntVar(value=self.max_chars.get())
        entry = ttk.Entry(top, textvariable=v)
        entry.pack(padx=12, pady=6, fill=tk.X)

        def apply() -> None:
            try:
                val = int(v.get())
            except Exception:
                messagebox.showerror("Invalid", "Enter an integer")
                return
            if val < 1000:
                messagebox.showerror("Invalid", "Use at least 1000")
                return
            self.max_chars.set(val)
            self.max_chars_display.set(str(val))
            top.destroy()

        ttk.Button(top, text="Apply", command=apply).pack(padx=12, pady=(6, 12), anchor=tk.E)

    def _fetch_voices_threaded(self) -> None:
        def worker() -> None:
            try:
                voices = asyncio.run(_fetch_voices_async())
                self.root.after(0, lambda: self._on_voices_loaded(voices))
            except Exception as e:
                self.root.after(0, lambda: self._on_voices_failed(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_voices_loaded(self, voices: list[VoiceItem]) -> None:
        self.voices = voices
        self._log(f"Loaded {len(voices)} voices.")
        self._populate_language_list()
        self._apply_language_filter()
        self._set_busy(False)
        self.status.set("Ready")

    def _populate_language_list(self) -> None:
        # Build a nice dropdown from locale prefixes ("en" from "en-US").
        code_to_name = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "nl": "Dutch",
            "sv": "Swedish",
            "no": "Norwegian",
            "da": "Danish",
            "fi": "Finnish",
            "pl": "Polish",
            "cs": "Czech",
            "tr": "Turkish",
            "ru": "Russian",
            "uk": "Ukrainian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
        }

        languages: set[str] = set()
        for v in self.voices:
            prefix = (v.locale.split("-")[0] if v.locale else "").strip().lower()
            if prefix:
                languages.add(prefix)

        # Always offer an "All" option.
        display_values: list[str] = ["All languages"]
        self.language_display_to_code = {"All languages": ""}

        for code in sorted(languages):
            name = code_to_name.get(code, code.upper())
            display = f"{name} ({code})"
            display_values.append(display)
            self.language_display_to_code[display] = code

        # Populate combobox if it exists (it will).
        try:
            self.language_combo["values"] = display_values
        except Exception:
            return

        # Keep user's selection if still valid; otherwise default to English if present.
        current = self.language_choice.get()
        if current in display_values:
            return
        english_display = "English (en)"
        if english_display in display_values:
            self.language_choice.set(english_display)
        else:
            self.language_choice.set(display_values[0])

    def _on_voices_failed(self, err: Exception) -> None:
        self._set_busy(False)
        self._log(f"Failed to fetch voices: {err}")
        messagebox.showwarning(
            "Voice list unavailable",
            "Could not fetch voice list. Check internet access and try 'Refresh voices'.",
        )

    def _refresh_voices(self) -> None:
        self._set_busy(True)
        self._log("Refreshing voice list...")
        self._fetch_voices_threaded()

    def _apply_language_filter(self) -> None:
        # Filter by language prefix ("en" matches en-US, en-GB, etc.)
        choice = (self.language_choice.get() or "").strip()
        lang_code = self.language_display_to_code.get(choice, "")

        if not lang_code:
            filtered = list(self.voices)
        else:
            filtered = [v for v in self.voices if v.locale.lower().startswith(lang_code + "-") or v.locale.lower() == lang_code]

        self.filtered_voices = filtered
        self.selected_voice_short = ""
        if hasattr(self, "voice_selected_label"):
            self.voice_selected_label.set("Selected voice: (none)")

        if hasattr(self, "voice_list"):
            self.voice_list.delete(0, tk.END)
            for v in filtered:
                # Plain English display, but still shows the short name you can reuse.
                self.voice_list.insert(tk.END, f"{v.friendly_name}  [{v.short_name}]")

        if not filtered:
            self._log(f"No voices found for selection: {choice!r}")
        else:
            self._log(f"Voices shown: {len(filtered)}")

        self._sync_nav_for_step_3()

    def _on_voice_selected(self, _evt: object) -> None:
        if not self.filtered_voices:
            return
        sel = getattr(self.voice_list, "curselection", lambda: ())()
        if not sel:
            return
        idx = int(sel[0])
        if idx < 0 or idx >= len(self.filtered_voices):
            return
        v = self.filtered_voices[idx]
        self.selected_voice_short = v.short_name
        self.voice_selected_label.set(f"Selected voice: {v.friendly_name} ({v.short_name})")
        self._sync_nav_for_step_3()

    def _on_mode_changed(self) -> None:
        if self.offline_mode.get():
            self._log("Offline mode selected (Coqui TTS - neural voices)")
            self.status.set("Offline mode - no internet required")
        else:
            self._log("Online mode selected (Edge TTS - requires internet)")
            if not self.voices:
                self._log("Loading voice list...")
                self._fetch_voices_threaded()

    def _run(self) -> None:
        if not self.selected_voice_short:
            messagebox.showerror("No voice selected", "Go back to Step 3 and pick a voice first.")
            return

        if self._running:
            messagebox.showinfo("Already running", "Conversion is already in progress. Please wait for it to finish.")
            return

        out_dir = Path(self.output_dir.get()).expanduser().resolve()
        do_merge = (self.output_format.get() == "single")
        pdf_mode = (self.input_mode.get() == "pdf")

        # capture values for thread
        pdf_path_str = self.pdf_path.get().strip()
        in_dir_str = self.input_dir.get()
        voice = self.selected_voice_short
        rate = self.rate.get()
        volume = self.volume.get()
        max_chars = int(self.max_chars.get())
        merge_output = self.merge_output.get().strip() or "audiobook.mp3"
        merge_bitrate = self.merge_bitrate.get().strip() or "160k"

        self._running = True
        self._start_time = time.time()
        try:
            self.run_btn.configure(state=tk.DISABLED)
        except Exception:
            pass
        self._set_busy(True)
        self._tick_timer()
        self._log("--- Starting conversion ---")
        self._log(f"Voice: {voice} | Rate: {rate} | Volume: {volume}")
        if pdf_mode:
            self._log(f"Input PDF: {pdf_path_str}")
        else:
            self._log(f"Input folder: {in_dir_str}")
        self._log(f"Output folder: {out_dir}")

        def worker() -> None:
            def progress_cb(msg: str) -> None:
                self.root.after(0, lambda m=msg: self._log(m))

            try:
                from batch_tts import main_async, extract_pdf_to_folder
                import tempfile, shutil

                if pdf_mode:
                    tmp_dir = Path(tempfile.mkdtemp(prefix="baxter_audio_"))
                    try:
                        self.root.after(0, lambda: self._log("Extracting chapters from PDF..."))
                        extract_pdf_to_folder(pdf_path_str, tmp_dir, progress_callback=progress_cb)
                        in_dir = tmp_dir
                        args = argparse.Namespace(
                            input=str(in_dir),
                            output=str(out_dir),
                            offline=False,
                            voice=voice,
                            rate=rate,
                            volume=volume,
                            coqui_model="",
                            coqui_speaker="",
                            max_chars=max_chars,
                            merge_all=do_merge,
                            merge_output=merge_output,
                            merge_bitrate=merge_bitrate,
                        )
                        rc = asyncio.run(main_async(args, progress_callback=progress_cb))
                    finally:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                else:
                    args = argparse.Namespace(
                        input=in_dir_str,
                        output=str(out_dir),
                        offline=False,
                        voice=voice,
                        rate=rate,
                        volume=volume,
                        coqui_model="",
                        coqui_speaker="",
                        max_chars=max_chars,
                        merge_all=do_merge,
                        merge_output=merge_output,
                        merge_bitrate=merge_bitrate,
                    )
                    rc = asyncio.run(main_async(args, progress_callback=progress_cb))

                self.root.after(0, lambda: self._on_run_done(rc, out_dir))
            except Exception as e:
                self.root.after(0, lambda: self._on_run_error(e))

        threading.Thread(target=worker, daemon=True).start()

    def _tick_timer(self) -> None:
        if not self._running or self._start_time is None:
            return
        elapsed = int(time.time() - self._start_time)
        mins, secs = divmod(elapsed, 60)
        self.status.set(f"Running... {mins:02d}:{secs:02d} elapsed")
        self._timer_after_id = self.root.after(1000, self._tick_timer)

    def _stop_timer(self) -> str:
        """Cancel the ticker and return a human-readable elapsed string."""
        if self._timer_after_id is not None:
            try:
                self.root.after_cancel(self._timer_after_id)
            except Exception:
                pass
            self._timer_after_id = None
        if self._start_time is not None:
            elapsed = int(time.time() - self._start_time)
            mins, secs = divmod(elapsed, 60)
            self._start_time = None
            return f"{mins:02d}:{secs:02d}"
        return "00:00"

    def _on_run_done(self, rc: int, out_dir: Path) -> None:
        self._running = False
        elapsed = self._stop_timer()
        self._set_busy(False)
        try:
            self.run_btn.configure(state=tk.NORMAL)
        except Exception:
            pass
        self.status.set(f"Done in {elapsed}")
        self._log(f"--- Conversion complete! Total time: {elapsed} --- Output folder opened automatically. ---")
        if rc == 0:
            try:
                import os

                os.startfile(str(out_dir))
            except Exception:
                pass

    def _on_run_error(self, err: Exception) -> None:
        self._running = False
        elapsed = self._stop_timer()
        self._set_busy(False)
        try:
            self.run_btn.configure(state=tk.NORMAL)
        except Exception:
            pass
        self.status.set(f"Failed after {elapsed}")
        self._log(f"Error after {elapsed}: {err}")
        messagebox.showerror("Conversion failed", str(err))


def _enforce_single_instance() -> object:
    """Create a named mutex. If it already exists another instance is running — exit."""
    import ctypes
    ERROR_ALREADY_EXISTS = 183
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "BaxtersAudioBooker_SingleInstance")
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showinfo(
            "Already running",
            "Baxter's Audio Booker is already open.\nCheck your taskbar.")
        root.destroy()
        raise SystemExit(0)
    return mutex  # keep alive — GC release would free the mutex


def _set_app_icon(root: tk.Tk) -> None:
    assets = Path(__file__).resolve().parent / "assets"
    png = assets / "ear_icon_512.png"
    if not png.exists():
        return
    try:
        from PIL import Image, ImageTk
        img = Image.open(png).resize((64, 64), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        root._icon_ref = photo  # keep reference so GC doesn't collect it
    except Exception:
        pass


def main() -> int:
    _mutex = _enforce_single_instance()  # blocks second instance before window opens
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    _set_app_icon(root)
    AudioBookerGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
