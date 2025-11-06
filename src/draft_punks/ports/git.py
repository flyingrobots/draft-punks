from __future__ import annotations
from typing import Protocol

class GitPort(Protocol):
    def is_commit(self, sha: str) -> bool: ...
