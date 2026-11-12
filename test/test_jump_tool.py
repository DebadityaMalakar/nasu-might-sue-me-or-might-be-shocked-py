from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from jump_tool import PREVIEW_PAGE_COUNT, command_for


def test_jump_command_passes_selected_page_to_launcher(tmp_path):
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    assert command_for(str(sdk), "12")[-2:] == ["--jump-page", "12"]


def test_jump_rejects_missing_sdk_and_invalid_pages(tmp_path):
    with pytest.raises(ValueError, match="executable"):
        command_for(str(tmp_path / "missing.exe"), "1")
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    for page in ("0", str(PREVIEW_PAGE_COUNT + 1), "invalid"):
        with pytest.raises(ValueError):
            command_for(str(sdk), page)


def test_cheat_flag_opens_tool_with_selected_sdk(tmp_path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    import startup
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    tool = tmp_path / "jump_tool.py"
    tool.touch()
    observed = []
    monkeypatch.setattr(sys, "argv", ["startup.py", "--renpy", str(sdk), "--cheat", str(tmp_path)])
    monkeypatch.setattr(startup.subprocess, "call", lambda args: observed.append(args) or 0)
    assert startup.main() == 0
    assert observed == [[sys.executable, str(tool.resolve()), "--renpy", str(sdk.resolve())]]


def test_cheat_flag_reports_missing_tool(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    import startup
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    monkeypatch.setattr(sys, "argv", ["startup.py", "--renpy", str(sdk), "--cheat", str(tmp_path)])
    assert startup.main() == 1
    assert "No jump_tool.py" in capsys.readouterr().err


def test_day2_command_has_explicit_destination(tmp_path):
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    command = command_for(str(sdk), "19", "2", "00", 19)
    assert command[-4:] == ["--jump-day", "2", "--jump-scene", "00"]
    with pytest.raises(ValueError, match="1 to 19"):
        command_for(str(sdk), "20", "2", "00", 19)


def test_rejects_invalid_scene_identifier(tmp_path):
    sdk = tmp_path / "renpy.exe"
    sdk.touch()
    with pytest.raises(ValueError, match="available day"):
        command_for(str(sdk), "1", "2", "../bad", 19)
