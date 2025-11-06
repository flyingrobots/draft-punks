from __future__ import annotations
from typing import List, Tuple
import re

FENCE_RE = re.compile(r"```(?:[A-Za-z0-9_-]+)?\n(.*?)```", re.DOTALL)


def parse_suggestion_pairs(body: str) -> List[Tuple[str,str]]:
    """Best-effort: if a comment contains two fenced blocks and a line with
    'Suggested replacement' between them, treat them as (before, after).
    Allows multiple pairs.
    """
    pairs: List[Tuple[str,str]] = []
    # Split on 'Suggested replacement' markers and gather preceding/next code fences
    idx = 0
    while True:
        m = re.search(r"(?i)suggested\s+replacement", body[idx:])
        if not m:
            break
        mid = idx + m.start()
        # find last fence before marker
        before_blocks = list(FENCE_RE.finditer(body[:mid]))
        after_blocks = list(FENCE_RE.finditer(body[mid:]))
        if before_blocks and after_blocks:
            before = before_blocks[-1].group(1).strip("\n")
            after = after_blocks[0].group(1).strip("\n")
            if before and after:
                pairs.append((before, after))
        idx = mid + 1
    return pairs


def apply_suggestions(path: str, pairs: List[Tuple[str,str]]) -> int:
    """Apply replacements (before->after) literally to given file.
    Returns number of hunks applied. Does not create files.
    """
    if not pairs:
        return 0
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except OSError:
        return 0
    applied = 0
    for before, after in pairs:
        if before in text:
            text = text.replace(before, after, 1)
            applied += 1
    if applied:
        with open(path, 'w', encoding='utf-8') as w:
            w.write(text)
    return applied
