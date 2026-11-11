"""Development-only jump launcher; it is outside the packaged Ren'Py project."""
from pathlib import Path
import argparse
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from episode_1 import PREVIEW_PAGE_COUNT


def command_for(sdk: str, page: str) -> list[str]:
    path = Path(sdk.strip())
    if not sdk.strip() or not path.is_file():
        raise ValueError("Choose the Ren'Py SDK executable.")
    try:
        number = int(page)
    except ValueError:
        raise ValueError("Choose a page number.") from None
    if not 1 <= number <= PREVIEW_PAGE_COUNT:
        raise ValueError(f"Choose a page from 1 to {PREVIEW_PAGE_COUNT}.")
    return [sys.executable, str(ROOT / "src" / "startup.py"), "--renpy", str(path), "--jump-page", str(number)]


class JumpTool(tk.Tk):
    def __init__(self, sdk_path=None):
        super().__init__()
        self.title("Fate Port - Development Jump")
        self.geometry("620x430")
        self.resizable(False, False)
        self.sdk = tk.StringVar(value=str(sdk_path or (Path.home() / "Documents" / "renpy-8.5.3-sdk" / "renpy.exe")))
        self.page = tk.StringVar(value="1")
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
        for row, label, value in ((2, "Episode", "Episode 1"), (3, "Chapter", "Day 1"), (4, "Scene", "Opening (scene 00)")):
            ttk.Label(root, text=label).grid(row=row, column=0, sticky="w", pady=5)
            ttk.Combobox(root, values=(value,), state="readonly", width=33).grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)
            root.grid_slaves(row=row, column=1)[0].current(0)
        ttk.Label(root, text="Page").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Spinbox(root, from_=1, to=PREVIEW_PAGE_COUNT, textvariable=self.page, width=8).grid(row=5, column=1, sticky="w", pady=5)
        ttk.Label(root, text="Ren'Py SDK").grid(row=6, column=0, sticky="w", pady=(12, 5))
        ttk.Entry(root, textvariable=self.sdk).grid(row=6, column=1, sticky="ew", pady=(12, 5), padx=(0, 8))
        ttk.Button(root, text="Browse...", command=self.browse).grid(row=6, column=2, pady=(12, 5))
        ttk.Label(root, textvariable=self.status, wraplength=550).grid(row=7, column=0, columnspan=3, sticky="w", pady=(16, 12))
        self.go = ttk.Button(root, text="Launch at page", command=self.launch)
        self.go.grid(row=8, column=2, sticky="e")

    def browse(self):
        path = filedialog.askopenfilename(parent=self, title="Select Ren'Py executable", filetypes=[("Executable", "*.exe"), ("All files", "*")])
        if path:
            self.sdk.set(path)

    def launch(self):
        try:
            command = command_for(self.sdk.get(), self.page.get())
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
