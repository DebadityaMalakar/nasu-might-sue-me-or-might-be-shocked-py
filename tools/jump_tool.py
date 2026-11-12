"""Development-only jump launcher; it is outside the packaged Ren'Py project."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from episode_1 import PREVIEW_PAGE_COUNT
from startup import CONFIG_PATH, ENGLISH_NAME
from build_episode_manifest import build


def day2_scene_counts():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inventory = build(Path(config["patches"]) / ENGLISH_NAME, 2)
    return {scene["scene"]: scene["page_count"] for scene in inventory["scenes"]}


def command_for(sdk: str, page: str, day="1", scene="00", page_limit=PREVIEW_PAGE_COUNT) -> list[str]:
    path = Path(sdk.strip())
    if not sdk.strip() or not path.is_file():
        raise ValueError("Choose the Ren'Py SDK executable.")
    try:
        number = int(page)
    except ValueError:
        raise ValueError("Choose a page number.") from None
    if day not in ("1", "2") or len(scene) != 2 or not scene.isdecimal() or (day == "1" and scene != "00"):
        raise ValueError("Choose an available day and scene.")
    if not 1 <= number <= page_limit:
        raise ValueError(f"Choose a page from 1 to {page_limit}.")
    command = [sys.executable, str(ROOT / "src" / "startup.py"), "--renpy", str(path), "--jump-page", str(number)]
    if day == "2":
        command.extend(["--jump-day", day, "--jump-scene", scene])
    return command


class JumpTool(tk.Tk):
    def __init__(self, sdk_path=None):
        super().__init__()
        self.title("Fate Port - Development Jump")
        self.geometry("620x430")
        self.resizable(False, False)
        self.sdk = tk.StringVar(value=str(sdk_path or (Path.home() / "Documents" / "renpy-8.5.3-sdk" / "renpy.exe")))
        self.page = tk.StringVar(value="1")
        self.day = tk.StringVar(value="Day 1")
        self.scene = tk.StringVar(value="00")
        try:
            self.day2_counts = day2_scene_counts()
            self.day2_error = None
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.day2_counts = {}
            self.day2_error = str(exc)
        self.status = tk.StringVar(value="Choose a destination. The tool starts a new game process.")
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", padding=(10, 6))
        root = ttk.Frame(self, padding=24)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        ttk.Label(root, text="Development jump", style="Header.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(root, text="Only implemented destinations are available.").grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 18))
        ttk.Label(root, text="Episode / day").grid(row=2, column=0, sticky="w", pady=5)
        day_box = ttk.Combobox(root, textvariable=self.day, values=("Day 1", "Day 2"), state="readonly", width=33)
        day_box.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)
        day_box.bind("<<ComboboxSelected>>", self.update_scenes)
        ttk.Label(root, text="Scene").grid(row=3, column=0, sticky="w", pady=5)
        self.scene_box = ttk.Combobox(root, textvariable=self.scene, state="readonly", width=33)
        self.scene_box.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)
        self.scene_box.bind("<<ComboboxSelected>>", self.update_page_limit)
        ttk.Label(root, text="Page").grid(row=5, column=0, sticky="w", pady=5)
        self.page_box = ttk.Spinbox(root, from_=1, to=PREVIEW_PAGE_COUNT, textvariable=self.page, width=8)
        self.page_box.grid(row=5, column=1, sticky="w", pady=5)
        ttk.Label(root, text="Ren'Py SDK").grid(row=6, column=0, sticky="w", pady=(12, 5))
        ttk.Entry(root, textvariable=self.sdk).grid(row=6, column=1, sticky="ew", pady=(12, 5), padx=(0, 8))
        ttk.Button(root, text="Browse...", command=self.browse).grid(row=6, column=2, pady=(12, 5))
        ttk.Label(root, textvariable=self.status, wraplength=550).grid(row=7, column=0, columnspan=3, sticky="w", pady=(16, 12))
        self.go = ttk.Button(root, text="Launch at page", command=self.launch)
        self.go.grid(row=8, column=2, sticky="e")
        self.update_scenes()

    def update_scenes(self, event=None):
        values = ("00",) if self.day.get() == "Day 1" else tuple(sorted(self.day2_counts))
        self.scene_box.configure(values=values)
        self.scene.set(values[0] if values else "")
        if self.day.get() == "Day 2":
            self.status.set("Day 2 is a text-only preview; route state, voices, and effects are not implemented." if values else f"Day 2 unavailable: {self.day2_error}")
        else:
            self.status.set("Day 1 opening preview. The tool starts a new game process.")
        self.update_page_limit()

    def update_page_limit(self, event=None):
        limit = PREVIEW_PAGE_COUNT if self.day.get() == "Day 1" else self.day2_counts.get(self.scene.get(), 0)
        self.page_box.configure(to=max(1, limit))
        self.page.set("1")
        self.go.configure(state="normal" if limit else "disabled")

    def browse(self):
        path = filedialog.askopenfilename(parent=self, title="Select Ren'Py executable", filetypes=[("Executable", "*.exe"), ("All files", "*")])
        if path:
            self.sdk.set(path)

    def launch(self):
        try:
            day = "1" if self.day.get() == "Day 1" else "2"
            limit = PREVIEW_PAGE_COUNT if day == "1" else self.day2_counts.get(self.scene.get(), 0)
            command = command_for(self.sdk.get(), self.page.get(), day, self.scene.get(), limit)
        except ValueError as exc:
            messagebox.showerror("Check destination", str(exc), parent=self)
            return
        self.go.configure(state="disabled")
        self.status.set("Verifying archives and starting the port...")
        def work():
            try:
                result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                message = result.stderr.strip() or result.stdout.strip() or f"Port exited with code {result.returncode}."
                self.after(0, lambda: self.finished(result.returncode, message))
            except OSError as exc:
                message = str(exc)
                self.after(0, lambda: self.finished(1, message))
        threading.Thread(target=work, daemon=True).start()

    def finished(self, code, message):
        self.go.configure(state="normal")
        self.status.set("Port closed." if code == 0 else "Could not launch the selected destination.")
        if code:
            messagebox.showerror("Launch failed", message, parent=self)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renpy", type=Path, help="Path to the RenPy SDK executable")
    args = parser.parse_args()
    JumpTool(args.renpy).mainloop()
