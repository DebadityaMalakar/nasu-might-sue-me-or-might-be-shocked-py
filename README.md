# Fate Ren'Py community port

An early community port that runs using original Fate/stay night Realta Nua files supplied by the user. It is not guaranteed to behave exactly like the original game. The current build includes a title screen and a 73-page English opening preview; the full story, branching, original save import, and Japanese support are not implemented.

## Requirements

- Windows, Python 3.10 or newer with Tkinter, and a separately installed Ren'Py 8.5.3 SDK.
- A supported local base-game installation with `etc.xp3`, `bgimage.xp3`, `bgm.xp3`, and `sound.xp3`.
- A patch directory with `patch_hd_1600.xp3` and `patch_lang_english.xp3`. The current implementation accepts only the archive hashes recorded in `src/startup.py`; other editions or variants will be rejected until explicitly supported.
- For character voices, the base game's `voice.xp3` and the separate `tcwfutil.exe` converter at `.cache/tcwfutil/bin/build/tcwfutil.exe` in the project folder. Without the converter, the preview runs without character voices. When present, the launcher verifies the supported voice archive and converts the required `.tcw` entries to local WAV files.
- For development and tests, install `requirements-dev.txt` with `python -m pip install -r requirements-dev.txt`. The game uses Ren'Py's bundled Python; the parser and test tools use the separately installed Python.

The converter is a separate GPL-2.0 program, not part of this project's MIT-licensed code: [tcwfutil](https://github.com/uyjulian/tcwfutil). Obtain the Windows AMD64 build from its release page and place the extracted executable at the path above. The local `.cache/` directory and converted game content are ignored by Git; neither the converter nor game assets are bundled with the port.

## Setup and launch

```powershell
python src/setup.py
python src/startup.py --renpy "C:\path\to\renpy-sdk\renpy.exe"
```

Setup records local game and patch paths and an optional save directory. Game labels are placeholders until the original installation layouts are fully mapped. Setup checks directory existence; the launcher verifies archive hashes before generating local content. Checking file identity does not establish ownership. Original save files are not modified or imported.

The launcher and Ren'Py startup verify the required archives, then generate assets under the ignored `src/renpy/game/generated/` directory. Verification and conversion can take time on large archives. Starting directly from the Ren'Py SDK also performs verification. Only the observed 1600-wide HD patch is currently supported; 1920-wide support is planned.

## Preview and limitations

The opening uses classic English text with H-enabled condition values. It includes original background music, selected sound effects, and character voice cues when the external converter is available. Voice cues are associated with text positions; skipping text stops the current voice. Timing and visual effects are approximate, music loop points are not yet reproduced, and not all original behavior has been compared against the game. Scenes 01-05 remain unported.

Run tests with `python -m pytest test`. The scripts in `src/` include the archive reader, setup, episode parser, and route-choice rules. Tests use synthetic fixtures. `.ref/` and the investigation notes are local references excluded from Git.

## Development jump tool

The standalone Tkinter tool is outside the Ren'Py game directory and is not packaged with the game:

```powershell
python tools/jump_tool.py
# Or, using the normal launcher:
python src/startup.py --renpy "C:\path\to\renpy-sdk\renpy.exe" --cheat tools
```

It currently jumps only within Day 1 opening scene 00, pages 1-73. It starts a fresh session and restores only the preview's background and music; it does not reconstruct skipped choices, flags, or saves. Archive checks still apply.

## License

The port's original code is licensed under the [MIT License](LICENSE). The original game and its assets are separately owned and are not covered by this license. The optional `tcwfutil` converter has its own GPL-2.0 license.
