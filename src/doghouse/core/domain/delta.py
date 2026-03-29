from dataclasses import dataclass, field

from .blocker import Blocker, BlockerType


@dataclass(frozen=True)
class Delta:
    baseline_timestamp: str | None
    current_timestamp: str
    baseline_sha: str | None
    current_sha: str
    added_blockers: list[Blocker] = field(default_factory=list)
    removed_blockers: list[Blocker] = field(default_factory=list)
    still_open_blockers: list[Blocker] = field(default_factory=list)

    @property
    def head_changed(self) -> bool:
        return self.baseline_sha is not None and self.baseline_sha != self.current_sha

    @property
    def improved(self) -> bool:
        return len(self.removed_blockers) > 0 and len(self.added_blockers) == 0

    @property
    def regressed(self) -> bool:
        return len(self.added_blockers) > 0

    @property
    def verdict(self) -> str:
        """Terse, stable verdict for machine consumption (--json)."""
        all_current = self.added_blockers + self.still_open_blockers
        if not all_current:
            return "Merge ready! All blockers resolved. 🎉"

        # Priority 0: Merge conflicts
        if any(b.type == BlockerType.DIRTY_MERGE_STATE for b in all_current):
            return "Resolve merge conflicts first! ⚔️"

        # Priority 1: Failing checks
        failing = [b for b in all_current if b.type == BlockerType.FAILING_CHECK]
        if failing:
            return f"Fix failing checks: {len(failing)} remaining. 🛑"

        # Priority 2: Unresolved threads
        threads = [b for b in all_current if b.type == BlockerType.UNRESOLVED_THREAD]
        if threads:
            return f"Address review feedback: {len(threads)} unresolved threads. 💬"

        # Priority 3: Pending checks
        if any(b.type == BlockerType.PENDING_CHECK for b in all_current):
            return "Wait for CI to complete. ⏳"

        # Priority 4: Formal approval required
        if any(b.type == BlockerType.NOT_APPROVED for b in all_current):
            return "Approval needed before merge. 📋"

        # Default: general blockers
        return f"Resolve remaining blockers: {len(all_current)} items. 🚧"
