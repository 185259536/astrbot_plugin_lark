from __future__ import annotations

import re
from typing import Tuple

_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def parse_front_matter_and_body(text: str) -> tuple[dict[str, str], str]:
    match = _FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    front_matter = match.group(1)
    body = text[match.end() :]
    return parse_front_matter(front_matter), body


def parse_front_matter(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue

        if ":" not in line:
            i += 1
            continue

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value == "|":
            i += 1
            block: list[str] = []
            while i < len(lines):
                current = lines[i]
                if current.startswith("  ") or current.startswith("\t") or current == "":
                    block.append(current[2:] if current.startswith("  ") else current.lstrip("\t"))
                    i += 1
                    continue
                break
            result[key] = "\n".join(block).strip()
            continue

        result[key] = value.strip('"\'')
        i += 1

    return result


def extract_title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback


def extract_sections(text: str) -> dict[str, str]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[normalize_heading(title)] = text[start:end].strip()
    return sections


def normalize_heading(text: str) -> str:
    normalized = re.sub(r"\s+", "", text.lower())
    normalized = normalized.replace("：", ":")
    return normalized


def split_head_tail(text: str) -> Tuple[str, str]:
    stripped = text.strip()
    if not stripped:
        return "", ""
    parts = stripped.split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1].strip()
