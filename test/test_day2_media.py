from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from prepare_day2_media import compile_scene


def test_page_media_tracks_background_sprite_music_and_sound():
    scene = {"pages": [
        {"events": [
            {"type": "bg", "attributes": {"file": "room"}},
            {"type": "ld", "attributes": {"file": "person", "pos": "left"}},
            {"type": "play", "attributes": {"file": "bgm01"}},
        ]},
        {"events": [
            {"type": "cl", "attributes": {"pos": "left"}},
            {"type": "se", "attributes": {"file": "se01"}},
        ]},
        {"events": [{"type": "playstop", "attributes": {}}]},
    ]}
    pages, assets = compile_scene(scene)
    assert pages[0]["background"] == pages[1]["background"] == assets["image"]["room.webp"]
    assert pages[0]["sprites"]["left"] == assets["image"]["person.webp"]
    assert not pages[1]["sprites"]
    assert pages[1]["music_state"] == assets["music"]["bgm01.ogg"]
    assert pages[1]["audio"][0]["asset"] == assets["sound"]["se01.wav"]
    assert pages[2]["music_state"] is None
