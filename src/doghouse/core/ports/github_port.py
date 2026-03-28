from abc import ABC, abstractmethod
from typing import Any

from ..domain.blocker import Blocker

class GitHubPort(ABC):
    """Port for interacting with GitHub to fetch PR state."""

    @abstractmethod
    def get_head_sha(self, pr_id: int | None = None) -> str:
        """
        Get the current head SHA of the PR.
        If pr_id is None, the implementation should attempt to infer
        the PR from the current local git context (e.g. current branch).
        """

    @abstractmethod
    def fetch_blockers(self, pr_id: int | None = None) -> list[Blocker]:
        """Fetch all blockers (threads, checks, etc.) for the PR."""

    @abstractmethod
    def get_pr_metadata(self, pr_id: int | None = None) -> dict[str, Any]:
        """Fetch metadata for the PR (title, author, etc.)."""
