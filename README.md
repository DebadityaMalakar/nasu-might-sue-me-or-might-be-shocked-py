# Fate Ren'Py port

This is an early community Ren'Py port that relies on the original game files. It is not guaranteed to work exactly like the original game. The setup screen and startup/title prototype are implemented; the story and original save import are not yet available.

## Run setup

Use Python 3.10 or newer with Tkinter installed:

```sh
python src/setup.py
```

Choose one game or all three, select each required game directory and the patch directory, and optionally select an existing save directory. The game labels are placeholders until the actual installation layout is verified. Settings are stored in `FateRenpyPort/setup.json` under `%LOCALAPPDATA%` on Windows (or `~/.config` elsewhere). The screen currently checks only that directories exist; it does not verify XP3 files, import saves, or launch gameplay. Existing saves are never modified.

Run the synthetic tests with `python -m pytest test` after installing pytest.

## Original game files

The finished port is intended to require the appropriate original XP3 archives at runtime and validate them before gameplay, even when a local cache exists. Required archives, supported versions, and hashes remain to be established. A file check establishes file identity, not ownership.

Game archives, extracted assets, scenes, dialogue, images, audio, and locally generated game content must not be committed or distributed with the port. `.ref/` holds local reference material and is ignored by Git. The implementation must generate or access game content locally from verified original archives.

## Project layout

- `src/` â€” setup and future port code.
- `test/` â€” automated tests using synthetic fixtures.
- `.ref/` â€” local, untracked extracted reference assets.
- `PLAN.PORT.MD` and `REPORT.MD` â€” local planning and investigation notes, ignored by Git.


## Startup animation prototype

Install a Ren'Py SDK separately, run `python src/setup.py`, then launch the prototype through:

```powershell
python src/startup.py --renpy "C:\path\to\renpy-sdk\renpy.exe"
```

The launcher verifies SHA-256 hashes for the supported `etc.xp3` and `bgimage.xp3` in the selected game directory on every launch, then extracts only the needed logo assets to the ignored local `src/renpy/game/generated/` cache. The prototype also requires and verifies the observed 1600-pixel HD patch archive in the configured patch directory. Only the observed archive versions are supported. The prototype also verifies the archives when the Ren'Py project starts directly. The launcher prepares assets before starting Ren'Py. The animation is an approximation: the original spline and mask effects have not been recreated. The logo plays once before the title screen. Start opens a 15-page English opening preview; Load is a placeholder and Config controls sound volume. Game content and original save import are not implemented.



## Resolution scope

The planned port targets only the 1600-wide and 1920-wide (1080p) HD asset variants. The current title prototype supports the verified 1600-wide patch only; 1920-wide support remains to be implemented.

## Scenario conversion status

The source parser in `src/kag_parser.py` reads plain UTF-8 and UTF-16 KAG scripts into strict Pydantic records while retaining source lines. It does not yet implement scene conversion, KiriKiri wrapped scripts, flowchart interpretation, or gameplay. Install the tooling dependencies with `python -m pip install -r requirements-dev.txt` and run `python -m pytest test` to check the synthetic tests. Scenes 01â€“05 are not yet playable.

## Route-specific choices

The route selection rules in `src/route_selection.py` treat a choice with no route requirement as common. A route-specific choice is available only when one of its required games is loaded; unselected route options should remain visible but disabled. Selecting all three in setup does not itself verify or load all three games. The mapping from original choices to game identifiers and integration with the reusable Ren'Py story-choice screen are not implemented yet, so these rules do not alter gameplay today.


The opening preview requires the verified `patch_lang_english.xp3` in the configured patch directory. It generates 15 pages locally and does not yet reproduce the original effects, voices, music, branching, or Japanese text. It is not a full scene or route port.

The opening preview uses the classic English text and H-enabled condition values. Scene 00 is not complete, and scenes 01?05 are not yet playable.

## License

The port's original code is licensed under the [MIT License](LICENSE). The original game and its assets are separately owned and are not covered by this license.
