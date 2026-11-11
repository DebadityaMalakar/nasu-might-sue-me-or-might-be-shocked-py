"""Inspect local Saber Day 1 scripts without copying game content into the project."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re

DAY_PREFIX = "\u30bb\u30a4\u30d0\u30fc\u30eb\u30fc\u30c8\u4e00\u65e5\u76ee"
COMMAND = re.compile(r"^\s*@([\w]+)")


def inventory(directory: Path) -> tuple[list[Path], Counter[str], int]:
    files = sorted(directory.glob(DAY_PREFIX + "-*.ks"))
    commands: Counter[str] = Counter()
    lines = 0
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        for line in text.splitlines():
            lines += 1
            match = COMMAND.match(line)
            if match:
                commands[match.group(1).lower()] += 1
    return files, commands, lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Locally extracted English retranslation directory")
    args = parser.parse_args()
    try:
        files, commands, lines = inventory(args.directory)
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f"Cannot inspect scripts: {exc}\n")
    if not files:
        parser.exit(2, "No readable Saber Day 1 script files found in that directory.\n")
    print(f"Saber Day 1: {len(files)} files, {lines} lines, {len(commands)} command names")
    print("Scene suffixes:", ", ".join(path.stem.rsplit("-", 1)[-1] for path in files))
    for name, count in commands.most_common():
        print(f"{name}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
