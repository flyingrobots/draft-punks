import json
import re
from pathlib import Path

from ...core.ports.storage_port import StoragePort
from ...core.domain.snapshot import Snapshot

_SAFE_REPO_RE = re.compile(r'^[\w.-]+$')


class JSONLStorageAdapter(StoragePort):
    """Adapter for persisting snapshots using JSONL files."""

    def __init__(self, storage_root: str | None = None):
        if storage_root:
            self.root = Path(storage_root)
        else:
            self.root = Path.home() / ".doghouse" / "snapshots"

        self.root.mkdir(parents=True, exist_ok=True)

    def _get_path(self, repo: str, pr_id: int) -> Path:
        safe_repo = repo.replace("/", "_")
        if not _SAFE_REPO_RE.match(safe_repo):
            raise ValueError(f"Invalid repo name for storage: {safe_repo!r}")
        repo_dir = self.root / safe_repo
        repo_dir.mkdir(parents=True, exist_ok=True)
        return repo_dir / f"pr-{pr_id}.jsonl"

    def save_snapshot(self, repo: str, pr_id: int, snapshot: Snapshot) -> None:
        path = self._get_path(repo, pr_id)
        with open(path, "a") as f:
            f.write(json.dumps(snapshot.to_dict()) + "\n")

    def list_snapshots(self, repo: str, pr_id: int) -> list[Snapshot]:
        path = self._get_path(repo, pr_id)
        if not path.exists():
            return []

        snapshots = []
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        snapshots.append(Snapshot.from_dict(json.loads(line)))
                    except json.JSONDecodeError:
                        continue
        return snapshots

    def get_latest_snapshot(self, repo: str, pr_id: int) -> Snapshot | None:
        snapshots = self.list_snapshots(repo, pr_id)
        if not snapshots:
            return None
        return snapshots[-1]
