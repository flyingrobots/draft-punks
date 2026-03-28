from abc import ABC, abstractmethod
from ..domain.snapshot import Snapshot

class StoragePort(ABC):
    """Port for persisting snapshots locally."""

    @abstractmethod
    def save_snapshot(self, repo: str, pr_id: int, snapshot: Snapshot) -> None:
        """Persist a snapshot to local storage."""

    @abstractmethod
    def list_snapshots(self, repo: str, pr_id: int) -> list[Snapshot]:
        """List all historical snapshots for a PR."""

    @abstractmethod
    def get_latest_snapshot(self, repo: str, pr_id: int) -> Snapshot | None:
        """Retrieve the most recent snapshot for a PR."""
