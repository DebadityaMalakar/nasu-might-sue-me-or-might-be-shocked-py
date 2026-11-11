"""Read KAG scenario syntax for inspection before translating it to Ren'Py.

This parser preserves source lines. It does not interpret commands or execute scripts.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    line: int = Field(ge=1)
    kind: Literal["label", "command", "text", "comment", "blank"]
    content: str
    name: str | None = None


COMMAND = re.compile(r"^@([A-Za-z_][\w]*)\b")
LABEL = re.compile(r"^\*([^|\s]+)")


def parse_scenario(source: str) -> list[SourceLine]:
    result = []
    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.lstrip()
        kind = "text"
        name = None
        if not line:
            kind = "blank"
        elif line.startswith(";"):
            kind = "comment"
        elif line.startswith("@"):
            match = COMMAND.match(line)
            if not match:
                raise ValueError(f"Invalid command on line {number}")
            kind, name = "command", match.group(1)
        elif line.startswith("*"):
            match = LABEL.match(line)
            if not match:
                raise ValueError(f"Invalid label on line {number}")
            kind, name = "label", match.group(1)
        result.append(SourceLine(line=number, kind=kind, content=raw, name=name))
    return result


def read_scenario(path: Path) -> list[SourceLine]:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = raw.decode("utf-16")
    elif raw.startswith(b"\xfe\xfe"):
        raise ValueError(f"Wrapped KiriKiri script is not yet supported: {path.name}")
    else:
        text = raw.decode("utf-8-sig")
    if "\x00" in text:
        raise ValueError(f"Unexpected NUL in script: {path.name}")
    return parse_scenario(text)
