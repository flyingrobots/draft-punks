from ..domain.snapshot import Snapshot
from ..domain.blocker import Blocker
from ..domain.delta import Delta


class DeltaEngine:
    """The core engine for computing semantic deltas between snapshots."""

    def compute_delta(self, baseline: Snapshot | None, current: Snapshot) -> Delta:
        """Compute the delta between a baseline snapshot and a current one."""
        if not baseline:
            return Delta(
                baseline_timestamp=None,
                current_timestamp=current.timestamp.isoformat(),
                baseline_sha=None,
                current_sha=current.head_sha,
                added_blockers=current.blockers,
                removed_blockers=[],
                still_open_blockers=[]
            )

        baseline_ids: set[str] = {b.id for b in baseline.blockers}
        current_ids: set[str] = {b.id for b in current.blockers}

        baseline_map: dict[str, Blocker] = {b.id: b for b in baseline.blockers}
        current_map: dict[str, Blocker] = {b.id: b for b in current.blockers}

        removed_ids = sorted(baseline_ids - current_ids)
        added_ids = sorted(current_ids - baseline_ids)
        still_open_ids = sorted(baseline_ids & current_ids)

        return Delta(
            baseline_timestamp=baseline.timestamp.isoformat(),
            current_timestamp=current.timestamp.isoformat(),
            baseline_sha=baseline.head_sha,
            current_sha=current.head_sha,
            added_blockers=[current_map[bid] for bid in added_ids],
            removed_blockers=[baseline_map[bid] for bid in removed_ids],
            still_open_blockers=[current_map[bid] for bid in still_open_ids]
        )
