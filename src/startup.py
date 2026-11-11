"""Verify the supported archives and prepare local assets for the startup demo."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import wave
import zlib

from episode_1 import opening_preview, opening_voice_cues, PREVIEW_PAGE_COUNT

CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".config")) / "FateRenpyPort" / "setup.json"

EXPECTED = {
    "etc.xp3": "d5aaa80e2284ba2fb2f4a80f391e2d5b791eafc187442839138fad88a36f9d19",
    "bgimage.xp3": "458fae61e0131375526cd05468ef23d3bed33632874df40a9c119d6af2d60448",
    "bgm.xp3": "13379df67b8a94806d854642f41885e8e709c61742c5983038d6b82131665d63",
    "sound.xp3": "c4e78013477685aa63fa3f37d46f3f4bc7679eef84f2183b49c07522502c4ebd",
}
ASSETS = {
    "etc.xp3": {name: name for name in ("rogo_ai.png", "rogo_bi2.png", "rogo_c.png", "rogo_fixb3.png", "rogo_fix0.png", "rogo_fix.png", "typemoon_ci.wav")},
    "bgimage.xp3": {"40\u5929\u306e\u676f.png": "logo_background.png"},
    "bgm.xp3": {"bgm42.ogg": "opening_bgm42.ogg", "bgm43.ogg": "opening_bgm43.ogg", "bgm03.ogg": "opening_bgm03.ogg"},
    "sound.xp3": {"se019.wav": "opening_se019.wav", "se247.wav": "opening_se247.wav"},
}
PATCH_NAME = "patch_hd_1600.xp3"
PATCH_HASH = "32d798202456ff74871682354f73b5b25500caf461ac854bd93051aa99a9dc6c"
TITLE_ASSETS = {
    "ta_logo_ps2.webp": "title_logo.webp",
    "ta_\u9b54\u6cd5\u9663.webp": "title_circle.webp",
    "ta_logo4.webp": "title_subtext.webp",
    "02\u5927\u706b\u707d.webp": "opening_fire.webp",
    "03\u706b\u707d\u3042\u3068\u66c7\u308a.webp": "opening_aftermath.webp",
    "15\u75c5\u5ba4.webp": "opening_hospital.webp",
    "01\u7a7a\u30fb\u9752\u7a7ab.webp": "opening_sky.webp",
    "a04.webp": "opening_shed.webp",
    "i\u571f\u8535\u5185-(\u66c7).webp": "opening_shed_inner.webp",
    "\u685c\u5236\u670d13a\u982c(\u4e2d).webp": "opening_sakura_13a.webp",
    "\u685c\u5236\u670d13b\u982c(\u4e2d).webp": "opening_sakura_13b.webp",
    "\u685c\u5236\u670d06a(\u4e2d).webp": "opening_sakura_06a.webp",
    "\u685c\u5236\u670d09a(\u4e2d).webp": "opening_sakura_09a.webp",
}
ENGLISH_NAME = "patch_lang_english.xp3"
ENGLISH_HASH = "30a883c0281d8ecb038b440f69a1becfe74be44fc3061216ef3c6ad6ccb31d6f"
OPENING_FILE = "\u30bb\u30a4\u30d0\u30fc\u30eb\u30fc\u30c8\u4e00\u65e5\u76ee-00.ks"
MAGIC = b"XP3\r\n \n\x1a\x8bg\x01"
PROJECT = Path(__file__).resolve().parent / "renpy"
CONVERTER = PROJECT.parent.parent / ".cache" / "tcwfutil" / "bin" / "build" / "tcwfutil.exe"
VOICE_HASH = "76660e7db7919340a0b9e625bd98cec2a596ef48fa7884d7d4e0994f864d6cd4"


def chunks(data):
    pos = 0
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("Truncated XP3 index")
        tag, size = struct.unpack_from("<4sQ", data, pos)
        pos += 12
        if size > len(data) - pos:
            raise ValueError("Invalid XP3 chunk length")
        yield tag, data[pos:pos + size]
        pos += size


def entries(stream):
    if stream.read(11) != MAGIC:
        raise ValueError("Invalid XP3 signature")
    pointer = stream.read(8)
    if len(pointer) != 8:
        raise ValueError("Truncated XP3 header")
    stream.seek(struct.unpack("<Q", pointer)[0])
    flag = stream.read(1)
    if flag == b"\x80":
        redirect = stream.read(16)
        if len(redirect) != 16:
            raise ValueError("Truncated XP3 redirect")
        stream.seek(struct.unpack_from("<Q", redirect, 8)[0])
        flag = stream.read(1)
    if flag != b"\x01":
        raise ValueError("Unsupported XP3 index format")
    header = stream.read(16)
    if len(header) != 16:
        raise ValueError("Truncated XP3 index header")
    packed, size = struct.unpack("<QQ", header)
    if packed > 64 * 1024 * 1024 or size > 128 * 1024 * 1024:
        raise ValueError("XP3 index is too large")
    index = zlib.decompress(stream.read(packed))
    if len(index) != size:
        raise ValueError("XP3 index size mismatch")
    for tag, data in chunks(index):
        if tag != b"File":
            continue
        entry = {}
        for kind, value in chunks(data):
            if kind == b"info":
                flags, total, _, length = struct.unpack_from("<IQQH", value)
                entry.update(name=value[22:22 + length * 2].decode("utf-16le"), flags=flags, size=total)
            elif kind == b"segm":
                if len(value) % 28:
                    raise ValueError("Invalid XP3 segment table")
                entry["segments"] = [struct.unpack_from("<IQQQ", value, pos) for pos in range(0, len(value), 28)]
            elif kind == b"adlr":
                entry["adler"] = struct.unpack("<I", value)[0]
        if {"name", "flags", "size", "segments"} <= entry.keys():
            yield entry


def read_asset(stream, entry):
    if entry["flags"] != 0 or entry["size"] > 20 * 1024 * 1024:
        raise ValueError("Unsupported or oversized XP3 asset")
    result = bytearray()
    for flag, offset, original, stored in entry["segments"]:
        if flag not in (0, 1) or stored > 20 * 1024 * 1024:
            raise ValueError("Unsupported XP3 segment")
        stream.seek(offset)
        raw = stream.read(stored)
        if len(raw) != stored:
            raise ValueError("Truncated XP3 segment")
        data = zlib.decompress(raw) if flag == 1 else raw
        if len(data) != original:
            raise ValueError("XP3 segment size mismatch")
        result.extend(data)
    if len(result) != entry["size"] or ("adler" in entry and zlib.adler32(result) != entry["adler"]):
        raise ValueError("XP3 asset checksum mismatch")
    return bytes(result)


def convert_voices(archive: Path, cues, converter: Path):
    """Convert verified voice entries with the separately installed GPL tool."""
    wanted = {cue["name"] + ".tcw" for page in cues for cue in page}
    with archive.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
        if digest.hexdigest() != VOICE_HASH:
            raise ValueError(f"Unsupported or changed archive: {archive}")
        stream.seek(0)
        found = {entry["name"]: entry for entry in entries(stream) if entry["name"] in wanted}
        missing = wanted - found.keys()
        if missing:
            raise ValueError(f"Missing voice entries: {', '.join(sorted(missing))}")
        with tempfile.TemporaryDirectory(prefix="fate-voice-") as folder:
            temp = Path(folder)
            for name, entry in found.items():
                (temp / name).write_bytes(read_asset(stream, entry))
            process = subprocess.run([str(converter.resolve()), *sorted(wanted)], cwd=temp, capture_output=True, text=True, errors="replace", timeout=120)
            if process.returncode:
                raise ValueError(f"TCWF converter failed: {process.stderr or process.stdout}")
            converted = {}
            for name in wanted:
                wav = temp / (name + ".wav")
                if not wav.is_file():
                    raise ValueError(f"TCWF converter did not create {name}.wav")
                with wave.open(str(wav), "rb") as sound:
                    if sound.getnframes() <= 0:
                        raise ValueError(f"Empty converted voice: {name}")
                converted["voice_" + name[:-4] + ".wav"] = wav.read_bytes()
            return converted


def prepare(base: Path, destination: Path, patches: Path):
    # Always recheck source archives, including when a cache exists.
    for name, expected in EXPECTED.items():
        path = base / name
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            digest = digest.hexdigest()
        if digest != expected:
            raise ValueError(f"Unsupported or changed archive: {path}")
    patch_path = patches / PATCH_NAME
    with patch_path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != PATCH_HASH:
        raise ValueError(f"Unsupported or changed archive: {patch_path}")
    english_path = patches / ENGLISH_NAME
    with english_path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != ENGLISH_HASH:
        raise ValueError(f"Unsupported or changed archive: {english_path}")
    with english_path.open("rb") as stream:
        matches = [item for item in entries(stream) if item["name"] == OPENING_FILE]
        if len(matches) != 1:
            raise ValueError("Opening script is missing or ambiguous")
        raw = read_asset(stream, matches[0])
    if not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ValueError("Unsupported English script encoding")
    source = raw.decode("utf-16")
    pages = opening_preview(source)
    cues = opening_voice_cues(source, pages)
    staged = {"opening_preview.json": json.dumps(pages, ensure_ascii=False).encode("utf-8")}
    if CONVERTER.is_file():
        staged.update(convert_voices(base / "voice.xp3", cues, CONVERTER))
    else:
        print("Voice converter not found; opening voice playback is unavailable.", file=sys.stderr)
        cues = [[] for _ in pages]
    staged["opening_voice_cues.json"] = json.dumps(cues).encode("utf-8")
    for archive, wanted in ASSETS.items():
        with (base / archive).open("rb") as stream:
            found = {item["name"]: item for item in entries(stream) if item["name"] in wanted}
            missing = wanted.keys() - found.keys()
            if missing:
                raise ValueError(f"Missing assets in {archive}: {', '.join(sorted(missing))}")
            for name, output in wanted.items():
                staged[output] = read_asset(stream, found[name])
    with patch_path.open("rb") as stream:
        found = {item["name"]: item for item in entries(stream) if item["name"] in TITLE_ASSETS}
        missing = TITLE_ASSETS.keys() - found.keys()
        if missing:
            raise ValueError(f"Missing title assets in {PATCH_NAME}: {', '.join(sorted(missing))}")
        for name, output in TITLE_ASSETS.items():
            staged[output] = read_asset(stream, found[name])
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in staged.items():
        (destination / name).write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renpy", type=Path, required=True, help="Path to renpy.exe in a RenPy SDK")
    parser.add_argument("--cheat", type=Path, metavar="DIRECTORY", help="Open the development jump tool from this directory")
    parser.add_argument("--jump-page", type=int, choices=range(1, PREVIEW_PAGE_COUNT + 1), help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.cheat is not None:
            tool = args.cheat / "jump_tool.py"
            if not tool.is_file():
                raise ValueError(f"No jump_tool.py found in: {args.cheat}")
            if not args.renpy.is_file():
                raise ValueError("Select an existing RenPy SDK executable with --renpy")
            return subprocess.call([sys.executable, str(tool.resolve()), "--renpy", str(args.renpy.resolve())])
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        base = Path(config["games"][config["selected"]])
        if not args.renpy.is_file():
            raise ValueError("Select an existing RenPy SDK executable with --renpy")
        prepare(base, PROJECT / "game" / "generated", Path(config["patches"]))
        launch_env = os.environ.copy()
        launch_env.pop("FATE_PORT_JUMP_PAGE", None)
        if args.jump_page is not None:
            launch_env["FATE_PORT_JUMP_PAGE"] = str(args.jump_page)
        return subprocess.call([str(args.renpy.resolve()), str(PROJECT.resolve())], env=launch_env)
    except (OSError, ValueError, KeyError, TypeError, struct.error, zlib.error) as exc:
        print(f"Startup preparation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
