import datetime
from typing import Optional, List, Tuple
from ..domain.blocker import Blocker
from ..domain.snapshot import Snapshot
from ..domain.delta import Delta
from ..ports.github_port import GitHubPort
from ..ports.storage_port import StoragePort
from .delta_engine import DeltaEngine

from ...adapters.git.git_adapter import GitAdapter

class RecorderService:
    """Orchestrator for capturing PR state and generating deltas."""

    def __init__(
        self,
        github: GitHubPort,
        storage: StoragePort,
        delta_engine: DeltaEngine,
        git: Optional[GitAdapter] = None
    ):
        self.github = github
        self.storage = storage
        self.delta_engine = delta_engine
        self.git = git or GitAdapter()

    def record_sortie(self, repo: str, pr_id: int) -> Tuple[Snapshot, Delta]:
        """Capture the current state of a PR and compute the delta against the last snapshot."""
        # 1. Capture current state
        head_sha = self.github.get_head_sha(pr_id)

        # Merge remote and local blockers with deduplication
        remote_blockers = self.github.fetch_blockers(pr_id)
        local_blockers = self.git.get_local_blockers()

        blocker_map = {b.id: b for b in remote_blockers}
        for b in local_blockers:
            if b.id in blocker_map:
                # Merge logic: if either is primary, it stays primary
                existing = blocker_map[b.id]
                blocker_map[b.id] = Blocker(
                    id=b.id,
                    type=b.type,
                    message=b.message,
                    severity=b.severity if b.severity.value > existing.severity.value else existing.severity,
                    is_primary=b.is_primary or existing.is_primary,
                    metadata={**existing.metadata, **b.metadata}
                )
            else:
                blocker_map[b.id] = b

        blockers = list(blocker_map.values())
        metadata = self.github.get_pr_metadata(pr_id)

        current_snapshot = Snapshot(
            timestamp=datetime.datetime.now(),
            head_sha=head_sha,
            blockers=blockers,
            metadata=metadata
        )

        # 2. Get baseline
        baseline = self.storage.get_latest_snapshot(repo, pr_id)

        # 3. Compute delta
        delta = self.delta_engine.compute_delta(baseline, current_snapshot)

        # 4. Persist only if the state meaningfully changed.
        # A sortie is a meaningful review episode, not a heartbeat.
        # Identical polls (same head SHA, same blocker set) are not sorties.
        if baseline is None or not current_snapshot.is_equivalent_to(baseline):
            self.storage.save_snapshot(repo, pr_id, current_snapshot)

        return current_snapshot, delta
