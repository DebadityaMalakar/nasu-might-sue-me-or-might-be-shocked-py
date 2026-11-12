import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from episode_manifest import load_manifest
from episode_1 import PREVIEW_PAGE_COUNT
import startup

MANIFEST = ROOT / "src" / "renpy" / "game" / "episodes" / "episode_1.json"


def test_manifest_covers_pages_and_references_prepared_assets():
    manifest = load_manifest(MANIFEST, PREVIEW_PAGE_COUNT)
    assets = {value for mapping in startup.ASSETS.values() for value in mapping.values()} | set(startup.TITLE_ASSETS.values())
    for page in manifest["pages"]:
        for item in (page["background"], page["sprite"], page["music_state"]):
            assert item is None or item.startswith("#") or item in assets
        for event in page["events"]:
            assert "asset" not in event or event["asset"] in assets


def test_music_state_matches_prior_events_for_jumps():
    manifest = load_manifest(MANIFEST, PREVIEW_PAGE_COUNT)
    music = None
    for page in manifest["pages"]:
        for event in page["events"]:
            if event["type"] == "music_play":
                music = event["asset"]
            elif event["type"] == "music_stop":
                music = None
        assert page["music_state"] == music


def test_invalid_page_and_asset_rejected(tmp_path):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    path = tmp_path / "manifest.json"
    for change in ("page", "asset"):
        invalid = copy.deepcopy(data)
        if change == "page":
            invalid["pages"][5]["page"] = 0
        else:
            invalid["pages"][5]["background"] = "../outside.webp"
        path.write_text(json.dumps(invalid), encoding="utf-8")
        with pytest.raises(ValueError):
            load_manifest(path, PREVIEW_PAGE_COUNT)
