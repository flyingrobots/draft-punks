from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

@dataclass
class Comment:
    body: str

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
