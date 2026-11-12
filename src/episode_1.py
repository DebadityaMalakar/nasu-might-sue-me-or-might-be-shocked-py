"""Extract a limited Day 1 preview with explicitly supported source conditions."""
import re

PAGE = re.compile(r"(?m)^\*page(\d+)\|[^\r\n]*")
PREVIEW_PAGE_COUNT = 73
INLINE = re.compile(r"\[([^\]]+)\]")


def render_inline(text, page):
    def replace(match):
        tag = match.group(1).strip().lower()
        if tag in ("lr", "l", "r"):
            return "\n"
        if tag in ("indent", "endindent") or tag.startswith("wsay ") or tag == "wsay":
            return ""
        if re.fullmatch(r"line\d+", tag):
            return "\u2014"
        raise ValueError(f"Unsupported inline tag on page {page}: {tag}")
    return INLINE.sub(replace, text)


def opening_preview(source, count=PREVIEW_PAGE_COUNT, *, mature=True, text_version="classic"):
    if text_version not in ("classic", "realta"):
        raise ValueError("Unsupported text version")
    matches = list(PAGE.finditer(source))
    pages = []
    conditions = []
    for number in range(count):
        matches_for_page = [i for i, match in enumerate(matches) if int(match.group(1)) == number]
        if len(matches_for_page) != 1:
            raise ValueError(f"Opening page {number} is missing or ambiguous")
        index = matches_for_page[0]
        start = matches[index].end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        body = source[start:end]
        if re.search(r"(?mi)^\s*@(elsif|jump|call|select)\b", body):
            raise ValueError(f"Opening page {number} contains unsupported control flow")
        lines = []
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("@if "):
                expr_match = re.fullmatch(r"@if\s+exp=[\"'](.*)[\"']", stripped)
                if not expr_match:
                    raise ValueError(f"Unsupported condition on page {number}: {stripped}")
                expr = expr_match.group(1)
                allowed = {
                    "sf.gmature": mature,
                    "sf.gtext=='classic'": text_version == "classic",
                    "sf.gtext=='realta'": text_version == "realta",
                    "sf.gtext!='realta'": text_version != "realta",
                }
                if expr not in allowed:
                    raise ValueError(f"Unsupported condition on page {number}: {expr}")
                conditions.append((allowed[expr], False))
                continue
            if stripped == "@else":
                if not conditions or conditions[-1][1]:
                    raise ValueError(f"Unexpected else on page {number}")
                value, _ = conditions[-1]
                conditions[-1] = (not value, True)
                continue
            if stripped == "@endif":
                if not conditions:
                    raise ValueError(f"Unexpected endif on page {number}")
                conditions.pop()
                continue
            if not all(value for value, _ in conditions):
                continue
            if not stripped or stripped.startswith(("@", ";", "*")):
                continue
            lines.append(render_inline(stripped, number).strip())
        text = "\n".join(lines).strip()
        pages.append(text)
    if conditions:
        raise ValueError("Unclosed condition at end of preview")
    return pages


def opening_voice_cues(source, pages):
    """Map each @say to the position of its following dialogue in the page text."""
    matches = list(PAGE.finditer(source))
    result = []
    for number, text in enumerate(pages):
        page_matches = [i for i, match in enumerate(matches) if int(match.group(1)) == number]
        if len(page_matches) != 1:
            raise ValueError(f"Opening page {number} is missing or ambiguous")
        index = page_matches[0]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        lines = source[matches[index].end():end].splitlines()
        cues = []
        previous = 0
        for i, raw in enumerate(lines):
            match = re.match(r"^\s*@say\s+storage=([A-Za-z0-9_]+)(?:\s|$)", raw, re.I)
            if not match:
                continue
            spoken = next((line.strip() for line in lines[i + 1:] if line.strip() and not line.lstrip().startswith(("@", ";", "*"))), "")
            spoken = render_inline(spoken, number).strip()
            if not spoken:
                raise ValueError(f"Missing dialogue after voice cue on page {number}")
            offset = text.find(spoken, previous)
            if offset < 0:
                raise ValueError(f"Cannot locate voice dialogue on page {number}: {match.group(1)}")
            cues.append({"offset": offset, "name": match.group(1)})
            previous = offset + len(spoken)
        result.append(cues)
    return result
