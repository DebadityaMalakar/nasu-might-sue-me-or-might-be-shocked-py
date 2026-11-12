"""Prepare approximate Day 2 preview media from verified source archives."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from build_episode_manifest import build
from startup import CONVERTER, ENGLISH_NAME, PATCH_NAME, convert_voices, entries, read_asset


def safe_name(category, name, extension):
    return "day2_" + category + "_" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:20] + extension


def compile_scene(scene):
    """Represent page-end visuals and page-level sound cues; not an exact KAG interpreter."""
    pages = []
    wanted = {"image": {}, "music": {}, "sound": {}}
    background = "#000"
    sprites = {}
    music = None
    for page in scene["pages"]:
        audio = []
        for event in page["events"]:
            kind, args = event["type"], event["attributes"]
            name = args.get("file") or args.get("storage")
            if kind == "blackout":
                background, sprites = "#000", {}
            elif kind in ("bg", "fadein") and name:
                if name.lower() in ("black", "white"):
                    background = "#000" if name.lower() == "black" else "#fff"
                else:
                    source = name + ".webp"
                    background = wanted["image"].setdefault(source, safe_name("image", source, ".webp"))
                sprites = {}
            elif kind in ("ld", "ld_auto", "ld_notrans") and name:
                source = name + ".webp"
                position = args.get("pos", "center").lower()
                if position not in ("left", "center", "right"):
                    position = "center"
                sprites[position] = wanted["image"].setdefault(source, safe_name("image", source, ".webp"))
            elif kind in ("cl", "cl_auto", "cl_notrans"):
                position = args.get("pos", "center").lower()
                if position == "all":
                    sprites.clear()
                else:
                    sprites.pop(position, None)
            elif kind == "play" and name:
                source = name + ".ogg"
                music = wanted["music"].setdefault(source, safe_name("music", source, ".ogg"))
                audio.append({"type": "music_play", "asset": music})
            elif kind == "playstop":
                music = None
                audio.append({"type": "music_stop"})
            elif kind in ("se", "seloop") and name:
                source = name + ".wav"
                sound = wanted["sound"].setdefault(source, safe_name("sound", source, ".wav"))
                audio.append({"type": "sound_play", "asset": sound, "loop": kind == "seloop"})
            elif kind == "sestop":
                audio.append({"type": "sound_stop"})
        pages.append({"background": background, "sprites": dict(sprites), "music_state": music, "audio": audio})
    return pages, wanted


def prepare_media(base: Path, patches: Path, destination: Path, scene_id: str, voice_cues):
    # Caller must first verify these original archives using startup.prepare.
    inventory = build(patches / ENGLISH_NAME, 2)
    scene = next((x for x in inventory["scenes"] if x["scene"] == scene_id), None)
    if scene is None:
        raise ValueError("Unknown Day 2 scene")
    pages, wanted = compile_scene(scene)
    sources = {"image": patches / PATCH_NAME, "music": base / "bgm.xp3", "sound": base / "sound.xp3"}
    staged = {}
    for category, archive in sources.items():
        if not wanted[category]:
            continue
        with archive.open("rb") as stream:
            index = {item["name"].lower(): item for item in entries(stream)}
            for name, output in wanted[category].items():
                entry = index.get(name.lower())
                if entry is None:
                    raise ValueError(f"Missing Day 2 {category} asset: {name}")
                staged[output] = read_asset(stream, entry)
    if CONVERTER.is_file() and any(voice_cues):
        staged.update(convert_voices(base / "voice.xp3", voice_cues, CONVERTER))
    else:
        voice_cues = [[] for _ in pages]
    for name, data in staged.items():
        (destination / name).write_bytes(data)
    (destination / "day2_media.json").write_text(json.dumps({"scene": scene_id, "pages": pages, "voice_cues": voice_cues}, ensure_ascii=False), encoding="utf-8")
