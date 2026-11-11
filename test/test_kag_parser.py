from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kag_parser import parse_scenario, read_scenario


def test_preserves_scenario_lines_and_identifies_structure():
    events = parse_scenario('; comment\n*page0|title\n @say storage=voice01\n  Text [lr]\n\n@return\n')
    assert [event.kind for event in events] == ["comment", "label", "command", "text", "blank", "command"]
    assert [event.line for event in events] == [1, 2, 3, 4, 5, 6]
    assert events[1].name == "page0"
    assert events[2].name == "say"
    assert events[3].content == "  Text [lr]"


def test_invalid_or_wrapped_source_fails_explicitly(tmp_path):
    with pytest.raises(ValueError, match="Invalid command"):
        parse_scenario("@\n")
    script = tmp_path / "wrapped.ks"
    script.write_bytes(b"\xfe\xfe\x02\xff\xfe")
    with pytest.raises(ValueError, match="not yet supported"):
        read_scenario(script)


def test_utf16_script_is_read_without_losing_characters(tmp_path):
    script = tmp_path / "scene.ks"
    script.write_text("*page0\nHello\n", encoding="utf-16")
    assert [line.kind for line in read_scenario(script)] == ["label", "text"]
