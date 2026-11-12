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

Setup records local game and patch paths and an optional save directory. It suggests the known Windows paths on Windows and leaves them blank on other platforms. This does not yet establish Linux or macOS support. Game labels are placeholders until the original installation layouts are fully mapped. Setup checks directory existence; the launcher verifies archive hashes before generating local content. Checking file identity does not establish ownership. Original save files are not modified or imported.

The launcher and Ren'Py startup verify the required archives, then generate assets under the ignored `src/renpy/game/generated/` directory. Verification and conversion can take time on large archives. Starting directly from the Ren'Py SDK also performs verification. The game uses a 1920x1080 logical canvas with the existing 4:3 content centered and scaled without stretching. Only the observed 1600-wide HD patch is currently supported; 1920-wide asset support is planned.

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

Choose Day 1 or Day 2, then a scene and page. The tool reads Day 2 scene counts from the verified English patch and generates the local text cache when launching a Day 2 preview. Day 2 previews include locally extracted page-level background, sprite, music, sound, and (when the optional converter is available) voice cues. They do not restore branch state or faithfully reproduce in-page effects and inherited visuals, and are not a playable route. A jump starts a fresh session and does not reconstruct skipped choices, flags, or saves. Archive checks still apply.

The developer tool `python tools/prepare_saber_days.py "<patch directory>"` can prepare local text, voice-cue, and flowchart data for the Day 1 and Day 2 source files. This cache is ignored by Git and excluded from Ren'Py distributions. It is preparation data, not a playable route: flowchart conditions, choices, effects, and later scenes still require implementation.

The Day 1 source cue inventory is generated locally using `tools/build_episode_manifest.py` and excluded from Git and distributions. The Day 2 cue inventory is tracked for reference but excluded from Ren'Py distributions. Neither inventory contains dialogue. Tests for optional local inventories are skipped if they have not been generated.

## License

The port's original code is licensed under the [MIT License](LICENSE). The original game and its assets are separately owned and are not covered by this license. The optional `tcwfutil` converter has its own GPL-2.0 license.
