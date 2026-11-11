from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from day1_inventory import DAY_PREFIX, inventory


def test_inventory_counts_only_day_one_and_normalizes_commands(tmp_path):
    (tmp_path / f"{DAY_PREFIX}-00.ks").write_text("@Say name=test\ntext\n @SAY\n@waitT time=3\n", encoding="utf-8")
    (tmp_path / "other.ks").write_text("@ignored\n", encoding="utf-8")
    files, commands, lines = inventory(tmp_path)
    assert len(files) == 1
    assert lines == 4
    assert commands == {"say": 2, "waitt": 1}
