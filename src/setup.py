"""Initial local setup for the planned Fate port."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

BASE_DEFAULT = r"C:\Program Files (x86)\Fate_StayNight_Realta_NuaFate"
PATCH_DEFAULT = r"C:\Program Files (x86)\Fate_StayNight_Realta_NuaUltimateEdition"
GAMES = ("Game 1", "Game 2", "Game 3")
CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config")) / "FateRenpyPort" / "setup.json"


def validate_paths(mode: str, selected: str, games: dict[str, str], patches: str, saves: str) -> list[str]:
    """Check directory availability only; archive identity is not yet known."""
    errors = []
    if mode not in ("one", "all") or selected not in GAMES:
        return ["Choose a valid game selection."]
    required = GAMES if mode == "all" else (selected,)
    for name in required:
        value = games.get(name, "").strip()
        if not value or not Path(value).is_dir():
            errors.append(f"{name}: select an existing game directory.")
    if not patches.strip() or not Path(patches.strip()).is_dir():
        errors.append("Patches: select an existing directory.")
    if saves.strip() and not Path(saves.strip()).is_dir():
        errors.append("Save data: select an existing directory or leave it blank.")
    return errors


class Setup(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fate | Setup")
        self.geometry("800x760")
        self.minsize(700, 660)
        self.configure(bg="#f3f2ef")
        self.mode = tk.StringVar(value="one")
        self.selected = tk.StringVar(value=GAMES[0])
        self.games = {name: tk.StringVar(value=BASE_DEFAULT if name == GAMES[0] else "") for name in GAMES}
        self.patches = tk.StringVar(value=PATCH_DEFAULT)
        self.saves = tk.StringVar()
        self.load_config()
        self.build()
        self.refresh()

    def load_config(self):
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return
            if data.get("mode") in ("one", "all"):
                self.mode.set(data["mode"])
            if data.get("selected") in GAMES:
                self.selected.set(data["selected"])
            games = data.get("games", {})
            if isinstance(games, dict):
                for name in GAMES:
                    if isinstance(games.get(name), str):
                        self.games[name].set(games[name])
            for key, var in (("patches", self.patches), ("saves", self.saves)):
                if isinstance(data.get(key), str):
                    var.set(data[key])
        except (OSError, ValueError):
            pass

    def build(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#f3f2ef")
        style.configure("TLabel", background="#f3f2ef", foreground="#262831", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Muted.TLabel", foreground="#626773", font=("Segoe UI", 9))
        style.configure("TRadiobutton", background="#f3f2ef", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
        style.configure("Accent.TButton", background="#714b57", foreground="white")
        style.map("Accent.TButton", background=[("active", "#593b46")])
        outer = ttk.Frame(self, padding=(30, 24))
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        ttk.Label(outer, text="FATE / SETUP", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(outer, text="Find your game files", style="Title.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 4))
        ttk.Label(outer, text="Choose what to load and where your original files are stored.", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 18))
        ttk.Label(outer, text="01  Choose games", style="Section.TLabel").grid(row=3, column=0, sticky="w")
        choices = ttk.Frame(outer)
        choices.grid(row=4, column=0, sticky="w", pady=(6, 4))
        ttk.Radiobutton(choices, text="One game", variable=self.mode, value="one", command=self.refresh).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(choices, text="All three games", variable=self.mode, value="all", command=self.refresh).pack(side="left")
        self.combo = ttk.Combobox(outer, textvariable=self.selected, values=GAMES, state="readonly", width=20)
        self.combo.grid(row=5, column=0, sticky="w", pady=(0, 12))
        self.combo.bind("<<ComboboxSelected>>", lambda event: self.refresh())
        ttk.Label(outer, text="02  Game directories", style="Section.TLabel").grid(row=6, column=0, sticky="w")
        ttk.Label(outer, text="Game names and archive requirements will be confirmed during investigation.", style="Muted.TLabel").grid(row=7, column=0, sticky="w", pady=(2, 4))
        self.rows = {}
        for i, name in enumerate(GAMES):
            self.rows[name] = self.path_row(outer, 8 + i, name, self.games[name])
        ttk.Label(outer, text="03  Patches and saves", style="Section.TLabel").grid(row=11, column=0, sticky="w", pady=(12, 3))
        self.path_row(outer, 12, "Patch directory", self.patches)
        self.path_row(outer, 13, "Save directory (optional)", self.saves)
        ttk.Label(outer, text="Existing saves are not modified. Import compatibility is not yet known.", style="Muted.TLabel").grid(row=14, column=0, sticky="w", pady=(4, 0))
        bottom = ttk.Frame(outer)
        bottom.grid(row=15, column=0, sticky="ew", pady=(20, 0))
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, text="Setup only: archive verification and gameplay are not yet available.", style="Muted.TLabel", wraplength=440).grid(row=0, column=0, sticky="w")
        ttk.Button(bottom, text="Save settings", style="Accent.TButton", command=self.save).grid(row=0, column=1, sticky="e", padx=(12, 0))

    def path_row(self, parent, row, label, variable):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=3)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=label, width=22).grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=variable)
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), ipady=4)
        button = ttk.Button(frame, text="Browse...", command=lambda: self.browse(variable, label))
        button.grid(row=0, column=2)
        return entry, button

    def browse(self, variable, label):
        path = filedialog.askdirectory(parent=self, title=f"Select {label}", initialdir=variable.get() if Path(variable.get()).is_dir() else str(Path.home()))
        if path:
            variable.set(path)

    def refresh(self):
        self.combo.configure(state="readonly" if self.mode.get() == "one" else "disabled")
        for name, (entry, button) in self.rows.items():
            active = self.mode.get() == "all" or self.selected.get() == name
            entry.configure(state="normal" if active else "disabled")
            button.configure(state="normal" if active else "disabled")

    def save(self):
        games = {name: variable.get().strip() for name, variable in self.games.items()}
        errors = validate_paths(self.mode.get(), self.selected.get(), games, self.patches.get(), self.saves.get())
        if errors:
            messagebox.showerror("Check your directories", "\n".join(errors), parent=self)
            return
        data = {"mode": self.mode.get(), "selected": self.selected.get(), "games": games, "patches": self.patches.get().strip(), "saves": self.saves.get().strip()}
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Could not save settings", str(exc), parent=self)
            return
        messagebox.showinfo("Settings saved", "Your directories have been saved. Archive verification and gameplay are not available yet.", parent=self)


if __name__ == "__main__":
    Setup().mainloop()
