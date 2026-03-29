from dataclasses import dataclass, field
from typing import List, Set, Optional
from .blocker import Blocker, BlockerType, BlockerSeverity
from .snapshot import Snapshot

@dataclass(frozen=True)
class Delta:
    baseline_timestamp: Optional[str]
    current_timestamp: str
    baseline_sha: Optional[str]
    current_sha: str
    added_blockers: List[Blocker] = field(default_factory=list)
    removed_blockers: List[Blocker] = field(default_factory=list)
    still_open_blockers: List[Blocker] = field(default_factory=list)

    @property
    def head_changed(self) -> bool:
        return self.baseline_sha != self.current_sha

    @property
    def improved(self) -> bool:
        return len(self.removed_blockers) > 0 and len(self.added_blockers) == 0

    @property
    def regressed(self) -> bool:
        return len(self.added_blockers) > 0

    @property
    def verdict(self) -> str:
        """The 'next action' verdict derived from the delta."""
        all_current = self.added_blockers + self.still_open_blockers
        if not all_current:
            return "Merge ready! All blockers resolved. 🎉"

        # Priority 0: Merge conflicts
        conflicts = [b for b in all_current if b.type == BlockerType.DIRTY_MERGE_STATE]
        if conflicts:
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
        pending = [b for b in all_current if b.type == BlockerType.PENDING_CHECK]
        if pending:
            return "Wait for CI to complete. ⏳"

        # Priority 4: Formal approval required
        approval = [b for b in all_current if b.type == BlockerType.NOT_APPROVED]
        if approval:
            return "Approval needed before merge. 📋"

        # Default: general blockers
        return f"Resolve remaining blockers: {len(all_current)} items. 🚧"

    @property
    def verdict_display(self) -> str:
        """PhiedBach's theatrical verdict for human eyes."""
        all_current = self.added_blockers + self.still_open_blockers
        if not all_current:
            return "Ze orchestra is in tune. You may merge, mein Freund. 🎼"

        # Priority 0: Merge conflicts
        if any(b.type == BlockerType.DIRTY_MERGE_STATE for b in all_current):
            return "Ze score has a terrible knot! Resolve ze merge conflicts before anything else. ⚔️"

        # Priority 1: Failing checks
        failing = [b for b in all_current if b.type == BlockerType.FAILING_CHECK]
        if failing:
            n = len(failing)
            noun = "instrument is" if n == 1 else "instruments are"
            return f"{n} {noun} out of tune! Fix ze failing checks. 🛑"

        # Priority 2: Unresolved threads
        threads = [b for b in all_current if b.type == BlockerType.UNRESOLVED_THREAD]
        if threads:
            n = len(threads)
            noun = "voice remains" if n == 1 else "voices remain"
            return f"{n} {noun} unanswered. Address ze review feedback. 💬"

        # Priority 3: Pending checks
        if any(b.type == BlockerType.PENDING_CHECK for b in all_current):
            return "Ze stagehands are still preparing. Vait for CI to finish. ⏳"

        # Priority 4: Formal approval required
        if any(b.type == BlockerType.NOT_APPROVED for b in all_current):
            return "Ze conductor has not yet given his blessing. Approval is needed. 📋"

        # Default
        n = len(all_current)
        noun = "item remains" if n == 1 else "items remain"
        return f"{n} {noun} on ze music stand. Resolve zem before ze performance. 🚧"
