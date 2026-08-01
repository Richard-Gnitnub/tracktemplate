"""Shared structural helpers for governance Markdown validators."""

from __future__ import annotations

import re


def direct_section_content(
    text: str,
    heading: str,
    level: int = 2,
) -> str:
    """Return raw content owned directly by one exact Markdown heading.

    Content beneath a child heading belongs to that child, so it cannot
    satisfy the parent section's contract. The returned slice is otherwise
    unchanged, preserving paragraphs, links, lists, blockquotes and tables.
    """
    if not 1 <= level <= 6:
        raise ValueError("Markdown heading level must be between 1 and 6")

    marker = "{} {}".format("#" * level, heading)
    matches = list(
        re.finditer(
            r"^{}$".format(re.escape(marker)),
            text,
            re.MULTILINE,
        )
    )
    if len(matches) != 1:
        raise AssertionError(
            "missing or duplicate Markdown heading: " + marker
        )

    tail = text[matches[0].end():]
    next_heading = re.search(r"^#{1,6} ", tail, re.MULTILINE)
    return tail if next_heading is None else tail[:next_heading.start()]
