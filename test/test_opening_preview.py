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


def test_line_tag_emits_an_em_dash():
    assert opening_preview(source("[line5]Text"), count=5) == ["\u2014Text"] * 5


def test_indentation_tags_are_removed_without_losing_text():
    assert opening_preview(source("[indent]Text[endindent]"), count=5) == ["Text"] * 5


def test_voice_cues_follow_text_positions():
    from episode_1 import opening_voice_cues
    script = "\n".join(f"*page{i}|\n@say storage=voice_a\nFirst[lr]\n@say storage=voice_b\nSecond\n@pg" for i in range(5))
    pages = opening_preview(script, count=5)
    cues = opening_voice_cues(script, pages)
    assert cues[0] == [{"offset": 0, "name": "voice_a"}, {"offset": 6, "name": "voice_b"}]


def test_voice_mapping_rejects_unmatched_dialogue():
    from episode_1 import opening_voice_cues
    script = "*page0|\n@say storage=voice_a\nDialogue\n@pg"
    with pytest.raises(ValueError, match="Cannot locate voice dialogue"):
        opening_voice_cues(script, ["Different text"])


def test_conditions_may_span_multiple_pages():
    script = "\n".join(["*page0|", '@if exp="sf.gtext!=\'realta\'"', "First", "@pg", "*page1|", "Second", "@endif", "After", "@pg"])
    assert opening_preview(script, count=2, text_version="classic") == ["First", "Second\nAfter"]
    assert opening_preview(script, count=2, text_version="realta") == ["", "After"]


def test_condition_must_close_within_requested_pages():
    script = "*page0|\n@if exp=\"sf.gmature\"\nText\n@pg"
    with pytest.raises(ValueError, match="Unclosed condition"):
        opening_preview(script, count=1)
