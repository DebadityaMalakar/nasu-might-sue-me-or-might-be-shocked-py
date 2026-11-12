import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flowchart import parse_flowchart


def flowchart():
    return "\n".join([
        "Day", "0;SELECTER'0'0'0'0'0'0'0'0'0'Prompt'1'1'3'Continue",
        "1;SCENE'1'0'0'0'0'0'0'0'0'Scene'0'0",
        "3;ROUTE'3'0'0'0'0'0'0'0'0'0'0'0'1",
    ])


def test_parses_choice_target_and_edge():
    result = parse_flowchart(flowchart())
    assert result.nodes[0].choices[0].text == "Continue"
    assert result.nodes[0].choices[0].target == 1
    assert result.edges[3].source == 0


def test_rejects_inconsistent_choice_edge():
    with pytest.raises(ValueError, match="does not match"):
        parse_flowchart(flowchart().replace("'1'3'Continue", "'0'3'Continue"))
