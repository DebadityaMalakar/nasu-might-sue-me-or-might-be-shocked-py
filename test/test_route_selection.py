from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from route_selection import GAMES, choice_available, selected_games


def test_one_game_keeps_common_and_selected_choices_available():
    loaded = selected_games("one", GAMES[0])
    assert choice_available(frozenset(), loaded)
    assert choice_available(frozenset({GAMES[0]}), loaded)
    assert not choice_available(frozenset({GAMES[1]}), loaded)
    assert not choice_available(frozenset({GAMES[2]}), loaded)


def test_all_games_enable_all_route_specific_choices():
    loaded = selected_games("all", GAMES[0])
    assert all(choice_available(frozenset({game}), loaded) for game in GAMES)


def test_unknown_games_or_modes_are_rejected():
    with pytest.raises(ValueError):
        selected_games("invalid", GAMES[0])
    with pytest.raises(ValueError):
        choice_available(frozenset({"unknown"}), frozenset(GAMES))
