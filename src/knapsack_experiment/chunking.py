from __future__ import annotations

import re


_TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def estimate_token_count(text: str) -> int:
    """Approximate token count using words + punctuation units."""
    count = len(_TOKEN_PATTERN.findall(text))
    return max(1, count)


def split_by_period(text: str) -> list[str]:
    """
    Split text on periods and keep sentence punctuation where possible.

    This intentionally stays simple to match the project requirement
    ("chunk between periods").
    """
    stripped = text.strip()
    if not stripped:
        return []

    raw_parts = [part.strip() for part in stripped.split(".")]
    parts = [part for part in raw_parts if part]
    if not parts:
        return []

    # Re-add periods to all but the final segment when the original text ended
    # with a period.
    rebuilt: list[str] = []
    ends_with_period = stripped.endswith(".")
    for idx, part in enumerate(parts):
        is_last = idx == len(parts) - 1
        if not is_last or ends_with_period:
            rebuilt.append(part + ".")
        else:
            rebuilt.append(part)
    return rebuilt
