"""Build Day 1 or Day 2 source cue and flow inventories without copying dialogue."""
from __future__ import annotations

import hashlib
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from startup import ENGLISH_HASH, ENGLISH_NAME, entries, read_asset
from flowchart import parse_flowchart

PREFIX = "\u30bb\u30a4\u30d0\u30fc\u30eb\u30fc\u30c8"
DAYS = {1: "\u4e00\u65e5\u76ee", 2: "\u4e8c\u65e5\u76ee"}
PAGE = re.compile(r"(?m)^\*page(\d+)(?:\|[^\r\n]*)?(?:\r?\n|$)")
COMMAND = re.compile(r"^\s*@([A-Za-z_][\w]*)\b(.*)$")
ATTRIBUTE = re.compile(r'''([A-Za-z_][\w]*)=("[^"]*"|'[^']*'|[^\s]+)''')
CUES = {"bg", "fadein", "blackout", "image", "imageex", "ld", "ld_auto", "ld_notrans", "ldall", "ldallt", "cl", "cl_auto", "cl_notrans", "play", "playstop", "se", "seloop", "sestop", "say", "wait", "waitt", "flushover", "move", "wm", "return"}
FIELDS = {"file", "storage", "time", "pos", "layer", "method", "rule", "index", "vague", "opacity", "left", "top", "path"}


def inventory(source):
    matches = list(PAGE.finditer(source))
    frames = []
    for index, marker in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        events = []
        for raw in source[marker.end():end].splitlines():
            match = COMMAND.match(raw)
            if not match:
                continue
            name = match.group(1).lower()
            if name not in CUES:
                continue
            attrs = {key.lower(): value[1:-1] if value[:1] in ("'", '"') and value[-1:] == value[:1] else value for key, value in ATTRIBUTE.findall(match.group(2)) if key.lower() in FIELDS}
            events.append({"type": name, "attributes": attrs})
        frames.append({"page": int(marker.group(1)), "events": events})
    return frames


def build(archive: Path, day: int):
    if day not in DAYS:
        raise ValueError("Only Day 1 and Day 2 are supported")
    prefix = PREFIX + DAYS[day]
    scene_pattern = re.compile(re.escape(prefix) + r"-(\d+)\.ks")
    with archive.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        if digest.hexdigest() != ENGLISH_HASH:
            raise ValueError("Unsupported English patch archive")
        stream.seek(0)
        archive_entries = list(entries(stream))
        matches = [entry for entry in archive_entries if entry["name"] == prefix + ".fcf"]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous flowchart")
        chart_raw = read_asset(stream, matches[0])
        chart_text = chart_raw.decode("utf-16") if chart_raw.startswith((b"\xff\xfe", b"\xfe\xff")) else chart_raw.decode("utf-8-sig")
        chart = parse_flowchart(chart_text)
        graph = {
            "nodes": [{"id": node.id, "kind": node.kind, "choices": [{"target": c.target, "route": c.route} for c in node.choices], "conditions": list(node.conditions)} for node in chart.nodes.values()],
            "edges": [{"id": edge.id, "source": edge.source, "target": edge.target} for edge in chart.edges.values()],
        }
        items = [(scene_pattern.fullmatch(entry["name"]), entry) for entry in archive_entries]
        scenes = []
        for match, entry in sorted(((m, e) for m, e in items if m), key=lambda pair: int(pair[0].group(1))):
            raw = read_asset(stream, entry)
            if not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                raise ValueError(f"Unsupported encoding in scene {match.group(1)}")
            source = raw.decode("utf-16")
            commands = Counter(command_match.group(1).lower() for line in source.splitlines() if (command_match := COMMAND.match(line)))
            frames = inventory(source)
            if [frame["page"] for frame in frames] != list(range(len(frames))):
                raise ValueError(f"Unexpected page labels in scene {match.group(1)}")
            scenes.append({"scene": match.group(1), "page_count": len(frames), "commands_not_in_cue_inventory": {name: count for name, count in sorted(commands.items()) if name not in CUES}, "pages": frames})
    if not scenes:
        raise ValueError(f"No Day {day} scene scripts found")
    return {"version": 1, "episode": f"day{day}", "source_archive": ENGLISH_NAME, "source_sha256": ENGLISH_HASH, "status": "partial source cue inventory; conditions and omitted commands are not executed; not playable", "scene_count": len(scenes), "page_count": sum(x["page_count"] for x in scenes), "scenes": scenes, "flowchart": graph}


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("1", "2"):
        raise SystemExit("Usage: python tools/build_episode_manifest.py <1|2> <patch directory>")
    day = int(sys.argv[1])
    result = build(Path(sys.argv[2]) / ENGLISH_NAME, day)
    output = ROOT / "src" / "renpy" / "game" / "episodes" / ("episode_1_source.json" if day == 1 else "episode_2.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Day {day}: {result['scene_count']} scene files, {result['page_count']} page labels")
