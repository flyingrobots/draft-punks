from __future__ import annotations

# Re-export Draft Punks domain models for now to avoid duplication.
# In a later pass, we can move these models here and leave shims in draft_punks.
try:
    from draft_punks.core.domain.github import PullRequest, ReviewThread, Comment  # type: ignore
except Exception:  # pragma: no cover - dev convenience if draft_punks not installed
    from dataclasses import dataclass
    from typing import List

    @dataclass
    class PullRequest:
        number: int
        head_ref: str
        title: str

    @dataclass
    class Comment:
        body: str
        author: str | None = None

    @dataclass
    class ReviewThread:
        id: str
        path: str
        comments: List[Comment]

