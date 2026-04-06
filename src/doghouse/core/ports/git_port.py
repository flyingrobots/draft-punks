from abc import ABC, abstractmethod

from ..domain.blocker import Blocker


class GitPort(ABC):
    """Port for local git repository operations."""

    @abstractmethod
    def get_local_blockers(self, repo_path: str | None = None) -> list[Blocker]:
        """Detect local issues (uncommitted changes, unpushed commits)."""
