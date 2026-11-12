"""Load and validate the data-driven opening presentation manifest."""
from __future__ import annotations
import json
from pathlib import Path


def load_manifest(path: Path, page_count: int) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("pages"), list):
        raise ValueError("Invalid episode manifest")
    pages = data["pages"]
    if len(pages) != page_count:
        raise ValueError(f"Manifest must contain {page_count} pages")
    for number, page in enumerate(pages):
        if not isinstance(page, dict) or page.get("page") != number:
            raise ValueError(f"Invalid page number at index {number}")
        for key in ("background", "sprite", "music_state"):
            value = page.get(key)
            if key == "background" and not isinstance(value, str):
                raise ValueError(f"Missing background on page {number}")
            if value is not None and (not isinstance(value, str) or not value or "/" in value or "\\" in value or ".." in value):
                raise ValueError(f"Invalid {key} on page {number}")
        duration = page.get("transition_seconds")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0 <= duration <= 30:
            raise ValueError(f"Invalid transition on page {number}")
        if not isinstance(page.get("events"), list):
            raise ValueError(f"Invalid events on page {number}")
        for event in page["events"]:
            if not isinstance(event, dict) or event.get("type") not in ("music_play", "music_stop", "sound_play"):
                raise ValueError(f"Invalid event on page {number}")
            if event["type"] != "music_stop":
                asset = event.get("asset")
                if not isinstance(asset, str) or not asset or "/" in asset or "\\" in asset or ".." in asset:
                    raise ValueError(f"Invalid event asset on page {number}")
            for key in ("fadein", "fadeout"):
                if key in event and (isinstance(event[key], bool) or not isinstance(event[key], (int, float)) or not 0 <= event[key] <= 30):
                    raise ValueError(f"Invalid {key} on page {number}")
    return data
