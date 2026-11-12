import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_episode_manifest import inventory


def test_cue_inventory_excludes_dialogue_and_preserves_known_commands():
    frames = inventory("*page0|\n@bg file=room time=500\nPrivate dialogue\n@say storage=voice_1\n@pg\n")
    assert frames == [{"page": 0, "events": [
        {"type": "bg", "attributes": {"file": "room", "time": "500"}},
        {"type": "say", "attributes": {"storage": "voice_1"}},
    ]}]


def test_episode_inventories_have_consistent_frame_and_graph_counts():
    for name, count in (("episode_1_source.json", 475), ("episode_2.json", 384)):
        path = ROOT / "src" / "renpy" / "game" / "episodes" / name
        if not path.is_file():
            pytest.skip("Source-derived inventory has not been generated locally")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert manifest["page_count"] == count
        assert manifest["scene_count"] == len(manifest["scenes"]) == 14
        scene_ids = [scene["scene"] for scene in manifest["scenes"]]
        assert all(scene.isdecimal() for scene in scene_ids)
        assert len(set(scene_ids)) == len(scene_ids)
        assert sum(scene["page_count"] for scene in manifest["scenes"]) == count
        assert all(scene["page_count"] == len(scene["pages"]) for scene in manifest["scenes"])
        ids = {node["id"] for node in manifest["flowchart"]["nodes"]}
        assert all(edge["source"] in ids and edge["target"] in ids for edge in manifest["flowchart"]["edges"])
