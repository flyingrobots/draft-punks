from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Comment:
    body: str
    author: Optional[str] = ""

@dataclass
class ReviewThread:
    id: str
    path: str
    comments: List[Comment] = field(default_factory=list)

@dataclass
class PullRequest:
    number: int
    head_ref: str
    title: str
