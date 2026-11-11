import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from setup import GAMES, validate_paths


def test_one_game_requires_only_selected_game_and_patches(tmp_path):
    games = {GAMES[0]: str(tmp_path), GAMES[1]: "", GAMES[2]: ""}
    assert validate_paths("one", GAMES[0], games, str(tmp_path), "") == []
    assert len(validate_paths("all", GAMES[0], games, str(tmp_path), "")) == 2


def test_invalid_optional_save_and_patch_are_reported(tmp_path):
    games = {GAMES[0]: str(tmp_path)}
    errors = validate_paths("one", GAMES[0], games, str(tmp_path / "missing"), str(tmp_path / "missing"))
    assert len(errors) == 2
