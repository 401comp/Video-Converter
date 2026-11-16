#!/usr/bin/env python3
"""A small, local-only GUI wrapper around FFmpeg for everyday video conversion."""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
import colorsys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "Video Converter"
FORMATS = ("MP4", "MOV", "MKV", "WEBM", "AVI")
VIDEO_FILETYPES = [
    ("Video files", "*.mp4 *.mov *.mkv *.webm *.avi *.m4v *.mpeg *.mpg *.wmv *.flv"),
    ("All files", "*.*"),
]


def bundled_tool(name: str) -> Path | None:
    """Find an FFmpeg executable next to a frozen app before consulting PATH."""
    suffix = ".exe" if os.name == "nt" else ""
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(getattr(sys, "_MEIPASS", "")) / f"{name}{suffix}")
        candidates.append(Path(sys.executable).resolve().parent / f"{name}{suffix}")
    candidates.append(Path(__file__).resolve().parent / "vendor" / f"{name}{suffix}")
    return next((item for item in candidates if item.is_file()), None)


def find_ffmpeg() -> str | None:
    bundled = bundled_tool("ffmpeg")
    return str(bundled) if bundled else shutil.which("ffmpeg")


def codec_arguments(output_format: str, quality: str) -> list[str]:
    """Use portable codecs and settings that work in the standard FFmpeg builds."""
    fmt = output_format.lower()
    if fmt == "webm":
        crf = {"High": "28", "Balanced": "32", "Smaller file": "38"}[quality]
        return ["-c:v", "libvpx-vp9", "-crf", crf, "-b:v", "0", "-c:a", "libopus"]
    qscale = {"High": "2", "Balanced": "5", "Smaller file": "8"}[quality]
    # Native MPEG-4 + AAC is broadly playable across the app's container choices.
    return ["-c:v", "mpeg4", "-q:v", qscale, "-c:a", "aac", "-b:a", "192k"]


def unique_output_path(folder: Path, source: Path, output_format: str) -> Path:
    extension = output_format.lower()
    initial = folder / f"{source.stem}_converted.{extension}"
    if not initial.exists():
        return initial
    index = 2
    while True:
        candidate = folder / f"{source.stem}_converted_{index}.{extension}"
        if not candidate.exists():
            return candidate
        index += 1


class VideoConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.minsize(720, 510)
        self.geometry("780x570")
        self.files: list[Path] = []
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.cancel_event = threading.Event()
        self.current_process: subprocess.Popen[str] | None = None
        self.spinner_active = False
        self.spinner_visible = False
        self.spinner_progress = 0.0
        self.output_folder = tk.StringVar()
        self.output_format = tk.StringVar(value="MP4")
        self.quality = tk.StringVar(value="Balanced")
        self.status = tk.StringVar(value="Add one or more videos to get started.")
        self._build_ui()
        self.after(100, self._drain_events)
        self.after(575, self._animate_spinner)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Helvetica", 20, "bold"))
        style.configure("Hint.TLabel", foreground="#4b5563")
        style.configure("Action.TButton", font=("Helvetica", 13, "bold"), padding=(16, 10))
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Video Converter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Convert locally with no uploads. Your original files stay untouched.", style="Hint.TLabel").pack(anchor="w", pady=(2, 16))

        files_box = ttk.LabelFrame(frame, text="Videos", padding=10)
        files_box.pack(fill="both", expand=True)
        self.file_list = tk.Listbox(files_box, height=9, activestyle="none", font=("Helvetica", 13))
        self.file_list.pack(side="left", fill="both", expand=True)
        buttons = ttk.Frame(files_box)
        buttons.pack(side="left", fill="y", padx=(10, 0))
        ttk.Button(buttons, text="Add videos…", command=self.add_files).pack(fill="x")
        ttk.Button(buttons, text="Remove selected", command=self.remove_selected).pack(fill="x", pady=7)
        ttk.Button(buttons, text="Clear list", command=self.clear_files).pack(fill="x")

        choices = ttk.Frame(frame)
        choices.pack(fill="x", pady=16)
        ttk.Label(choices, text="Convert to:").grid(row=0, column=0, sticky="w")
        format_box = ttk.Combobox(choices, textvariable=self.output_format, values=FORMATS, state="readonly", width=12, font=("Helvetica", 13))
        format_box.grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(choices, text="Quality:").grid(row=0, column=1, sticky="w", padx=(20, 0))
        quality_box = ttk.Combobox(choices, textvariable=self.quality, values=("High", "Balanced", "Smaller file"), state="readonly", width=16, font=("Helvetica", 13))
        quality_box.grid(row=1, column=1, sticky="w", padx=(20, 0), pady=(4, 0))
        ttk.Label(choices, text="Save in:").grid(row=0, column=2, sticky="w", padx=(20, 0))
        ttk.Entry(choices, textvariable=self.output_folder, width=34, font=("Helvetica", 12)).grid(row=1, column=2, sticky="ew", padx=(20, 6), pady=(4, 0))
        ttk.Button(choices, text="Choose…", command=self.choose_folder).grid(row=1, column=3, sticky="e", pady=(4, 0))
        choices.columnconfigure(2, weight=1)

        progress_row = ttk.Frame(frame)
        progress_row.pack(fill="x")
        self.spinner_canvas = tk.Canvas(progress_row, width=28, height=28, highlightthickness=0, background=self.cget("background"))
        self.spinner_canvas.pack(side="left", padx=(0, 9))
        self.spinner_dot = self.spinner_canvas.create_oval(3, 3, 25, 25, fill="#d1d5db", outline="")
        self.progress = ttk.Progressbar(progress_row, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True)
        ttk.Label(frame, textvariable=self.status, style="Hint.TLabel", wraplength=720).pack(anchor="w", pady=(7, 14))
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        self.convert_button = ttk.Button(actions, text="Convert videos", style="Action.TButton", command=self.start_conversion)
        self.convert_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=10)

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Choose videos", filetypes=VIDEO_FILETYPES)
        known = {str(item) for item in self.files}
        for raw_path in paths:
            path = Path(raw_path)
            if str(path) not in known:
                self.files.append(path)
                known.add(str(path))
        self._refresh_files()

    def remove_selected(self) -> None:
        selected = list(self.file_list.curselection())
        for index in reversed(selected):
            self.files.pop(index)
        self._refresh_files()

    def clear_files(self) -> None:
        self.files.clear()
        self._refresh_files()

    def _refresh_files(self) -> None:
        self.file_list.delete(0, tk.END)
        for path in self.files:
            self.file_list.insert(tk.END, str(path))
        self.status.set(f"{len(self.files)} video{'s' if len(self.files) != 1 else ''} ready." if self.files else "Add one or more videos to get started.")

    def choose_folder(self) -> None:
        initial = self.output_folder.get() or (str(self.files[0].parent) if self.files else str(Path.home()))
        chosen = filedialog.askdirectory(title="Choose output folder", initialdir=initial)
        if chosen:
            self.output_folder.set(chosen)

    def start_conversion(self) -> None:
        if not self.files:
            messagebox.showinfo(APP_NAME, "Add at least one video first.")
            return
        ffmpeg = find_ffmpeg()
        if not ffmpeg:
            messagebox.showerror(APP_NAME, "FFmpeg was not found. Reinstall this app or install FFmpeg and try again.")
            return
        folder_text = self.output_folder.get().strip()
        output_dir = Path(folder_text).expanduser() if folder_text else self.files[0].parent
        if not output_dir.is_dir():
            messagebox.showerror(APP_NAME, "Choose an existing output folder.")
            return
        self.cancel_event.clear()
        self.progress.configure(value=0)
        self.convert_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.spinner_active = True
        self.spinner_progress = 0
        self._update_spinner_color()
        self.worker = threading.Thread(target=self._convert_worker, args=(ffmpeg, output_dir), daemon=True)
        self.worker.start()

    def _convert_worker(self, ffmpeg: str, output_dir: Path) -> None:
        total = len(self.files)
        completed: list[Path] = []
        for index, source in enumerate(self.files, start=1):
            if self.cancel_event.is_set():
                break
            destination = unique_output_path(output_dir, source, self.output_format.get())
            command = [ffmpeg, "-hide_banner", "-y", "-i", str(source), *codec_arguments(self.output_format.get(), self.quality.get()), str(destination)]
            self.events.put(("status", f"Converting {index} of {total}: {source.name}"))
            try:
                self.current_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                _, stderr = self.current_process.communicate()
                if self.cancel_event.is_set():
                    if destination.exists():
                        destination.unlink(missing_ok=True)
                    break
                if self.current_process.returncode != 0:
                    self.events.put(("error", f"Could not convert {source.name}.\n\n{stderr[-1400:]}"))
                    continue
                completed.append(destination)
                self.events.put(("progress", index * 100 / total))
            except OSError as exc:
                self.events.put(("error", f"Could not start FFmpeg: {exc}"))
                break
            finally:
                self.current_process = None
        self.events.put(("done", completed))

    def cancel(self) -> None:
        self.cancel_event.set()
        self.spinner_active = False
        self.spinner_canvas.itemconfigure(self.spinner_dot, state="normal")
        if self.current_process and self.current_process.poll() is None:
            self.current_process.terminate()
        self.status.set("Cancelling after the current file…")
        self.cancel_button.configure(state="disabled")

    def _drain_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "status":
                    self.status.set(str(value))
                elif kind == "progress":
                    self.progress.configure(value=float(value))
                    self.spinner_progress = float(value)
                    self._update_spinner_color()
                elif kind == "error":
                    messagebox.showerror(APP_NAME, str(value))
                elif kind == "done":
                    outputs = value
                    self.convert_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.spinner_active = False
                    self.spinner_canvas.itemconfigure(self.spinner_dot, state="normal")
                    if self.cancel_event.is_set():
                        self.status.set(f"Cancelled. {len(outputs)} video{'s' if len(outputs) != 1 else ''} completed.")
                    elif outputs:
                        self.progress.configure(value=100)
                        self.status.set(f"Done — {len(outputs)} converted video{'s' if len(outputs) != 1 else ''} saved.")
                        messagebox.showinfo(APP_NAME, "Conversion complete.\n\nSaved files:\n" + "\n".join(str(path) for path in outputs))
                    else:
                        self.status.set("No videos were converted. Check the error messages and try again.")
        except queue.Empty:
            pass
        self.after(100, self._drain_events)

    def _update_spinner_color(self) -> None:
        """A solid blink-only status circle: red through yellow to green."""
        hue = max(0.0, min(100.0, self.spinner_progress)) * 1.2 / 360
        red, green, blue = colorsys.hls_to_rgb(hue, 0.52, 0.86)
        color = f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"
        self.spinner_canvas.itemconfigure(self.spinner_dot, fill=color)

    def _animate_spinner(self) -> None:
        if self.spinner_active:
            self.spinner_visible = not self.spinner_visible
            self.spinner_canvas.itemconfigure(self.spinner_dot, state="normal" if self.spinner_visible else "hidden")
        else:
            self.spinner_visible = True
            self.spinner_canvas.itemconfigure(self.spinner_dot, state="normal")
        self.after(575, self._animate_spinner)


if __name__ == "__main__":
    VideoConverterApp().mainloop()
