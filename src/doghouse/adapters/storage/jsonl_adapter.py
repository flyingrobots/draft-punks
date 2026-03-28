import json
import os
from pathlib import Path
from typing import List, Optional
from ...core.ports.storage_port import StoragePort
from ...core.domain.snapshot import Snapshot

class JSONLStorageAdapter(StoragePort):
    """Adapter for persisting snapshots using JSONL files."""

    def __init__(self, storage_root: Optional[str] = None):
        if storage_root:
            self.root = Path(storage_root)
        else:
            self.root = Path.home() / ".doghouse" / "snapshots"

        self.root.mkdir(parents=True, exist_ok=True)

    def _get_path(self, repo: str, pr_id: int) -> Path:
        # Sanitize repo name (replace / with _)
        safe_repo = repo.replace("/", "_")
        repo_dir = self.root / safe_repo
        repo_dir.mkdir(parents=True, exist_ok=True)
        return repo_dir / f"pr-{pr_id}.jsonl"

    def save_snapshot(self, repo: str, pr_id: int, snapshot: Snapshot) -> None:
        path = self._get_path(repo, pr_id)
        with open(path, "a") as f:
            f.write(json.dumps(snapshot.to_dict()) + "\n")

    def list_snapshots(self, repo: str, pr_id: int) -> List[Snapshot]:
        path = self._get_path(repo, pr_id)
        if not path.exists():
            return []

        snapshots = []
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    snapshots.append(Snapshot.from_dict(json.loads(line)))
        return snapshots

    def get_latest_snapshot(self, repo: str, pr_id: int) -> Optional[Snapshot]:
        snapshots = self.list_snapshots(repo, pr_id)
        if not snapshots:
            return None
        # Assuming they are appended in order
        return snapshots[-1]
