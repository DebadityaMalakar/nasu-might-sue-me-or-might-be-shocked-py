"""Prepare a local, non-distributable Saber Day 1/2 text and flow inventory."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from episode_1 import PAGE, opening_preview, opening_voice_cues
from flowchart import parse_flowchart
from startup import ENGLISH_HASH, ENGLISH_NAME, entries, read_asset

PREFIX = "\u30bb\u30a4\u30d0\u30fc\u30eb\u30fc\u30c8"
DAYS = {"1": "\u4e00\u65e5\u76ee", "2": "\u4e8c\u65e5\u76ee"}


def decode_script(raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    raise ValueError("Unsupported source script encoding")


def prepare(archive: Path) -> dict:
    with archive.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        if digest.hexdigest() != ENGLISH_HASH:
            raise ValueError("Unsupported English patch archive")
        stream.seek(0)
        items = {entry["name"]: entry for entry in entries(stream)}
        days = {}
        for number, day in DAYS.items():
            prefix = PREFIX + day
            match_scene = re.compile(re.escape(prefix) + r"-(\d+)\.ks")
            scenes = {}
            for name, entry in items.items():
                match = match_scene.fullmatch(name)
                if not match:
                    continue
                source = decode_script(read_asset(stream, entry))
                page_count = len(list(PAGE.finditer(source)))
                pages = opening_preview(source, count=page_count)
                scenes[match.group(1)] = {"pages": pages, "voice_cues": opening_voice_cues(source, pages)}
            if not scenes or prefix + ".fcf" not in items:
                raise ValueError(f"Missing Day {number} scene scripts or flowchart")
            chart_raw = read_asset(stream, items[prefix + ".fcf"])
            chart_text = chart_raw.decode("utf-16") if chart_raw.startswith((b"\xff\xfe", b"\xfe\xff")) else chart_raw.decode("utf-8-sig")
            graph = parse_flowchart(chart_text)
            days[number] = {"scenes": scenes, "flowchart": {"nodes": [asdict(node) for node in graph.nodes.values()], "edges": [asdict(edge) for edge in graph.edges.values()]}}
    return {"version": 1, "status": "local text and graph data; not playable", "days": days}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("patch_directory", type=Path)
    args = parser.parse_args()
    result = prepare(args.patch_directory / ENGLISH_NAME)
    output = ROOT / "src" / "renpy" / "game" / "generated" / "saber_days.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Prepared local text and flow data for", sum(len(day["scenes"]) for day in result["days"].values()), "scene files.")
    print("This data does not yet implement scene flow, state, effects, or gameplay.")


if __name__ == "__main__":
    main()
