"""Availability rules for route-specific story choices.

Names here are setup identifiers; source flowchart branches are mapped separately.
"""
from __future__ import annotations

GAMES = ("Game 1", "Game 2", "Game 3")


def selected_games(mode: str, selected: str) -> frozenset[str]:
    if mode not in ("one", "all") or selected not in GAMES:
        raise ValueError("Invalid game selection")
    return frozenset(GAMES if mode == "all" else (selected,))


def choice_available(required_games: frozenset[str], loaded_games: frozenset[str]) -> bool:
    """Common choices have no requirements; specific choices require a loaded game."""
    if not required_games <= frozenset(GAMES) or not loaded_games <= frozenset(GAMES):
        raise ValueError("Unknown game identifier")
    return not required_games or bool(required_games & loaded_games)
