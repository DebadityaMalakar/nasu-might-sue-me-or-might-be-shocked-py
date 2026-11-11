from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from episode_1 import opening_preview


def source(page_content="Text[lr]Next"):
    return "\n".join(f"*page{i}|\n@r\n{page_content}\n@pg" for i in range(5))


def test_extracts_five_pages_and_line_breaks():
    assert opening_preview(source(), count=5) == ["Text\nNext"] * 5


def test_rejects_unsupported_flow_and_tags():
    with pytest.raises(ValueError, match="control flow"):
        opening_preview(source("@jump target=x\nText"), count=5)
    with pytest.raises(ValueError, match="inline tag"):
        opening_preview(source("[unknown]Text"), count=5)


def test_label_metadata_is_not_shown():
    script = "\n".join(f"*page{i}|&f.scripttitle\nText\n@pg" for i in range(5))
    assert opening_preview(script, count=5) == ["Text"] * 5


def test_mature_condition_selects_only_the_matching_branch():
    body = "@if exp=\"sf.gmature\"\nMature\n@else\nAlternate\n@endif"
    assert opening_preview(source(body), count=5, mature=True) == ["Mature"] * 5
    assert opening_preview(source(body), count=5, mature=False) == ["Alternate"] * 5


def test_unknown_condition_is_not_silently_ignored():
    with pytest.raises(ValueError, match="Unsupported condition"):
        opening_preview(source("@if exp=\"unrecognized\"\nText\n@endif"), count=5)
