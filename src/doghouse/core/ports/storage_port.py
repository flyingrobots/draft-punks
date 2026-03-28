from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain.snapshot import Snapshot

class StoragePort(ABC):
    """Port for persisting snapshots locally."""
    
    @abstractmethod
    def save_snapshot(self, repo: str, pr_id: int, snapshot: Snapshot) -> None:
        """Persist a snapshot to local storage."""
        pass
        
    @abstractmethod
    def list_snapshots(self, repo: str, pr_id: int) -> List[Snapshot]:
        """List all historical snapshots for a PR."""
        pass
        
    @abstractmethod
    def get_latest_snapshot(self, repo: str, pr_id: int) -> Optional[Snapshot]:
        """Retrieve the most recent snapshot for a PR."""
        pass
