from dataclasses import dataclass, field
from typing import List, Set, Optional
from .blocker import Blocker, BlockerType
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
        if not self.still_open_blockers and not self.added_blockers:
            return "Merge ready! All blockers resolved. 🎉"
        
        # Priority 1: Failing checks
        failing = [b for b in (self.added_blockers + self.still_open_blockers) if b.type == BlockerType.FAILING_CHECK]
        if failing:
            return f"Fix failing checks: {len(failing)} remaining. 🛑"
            
        # Priority 2: Unresolved threads
        threads = [b for b in (self.added_blockers + self.still_open_blockers) if b.type == BlockerType.UNRESOLVED_THREAD]
        if threads:
            return f"Address review feedback: {len(threads)} unresolved threads. 💬"
            
        # Priority 3: Pending checks
        pending = [b for b in (self.added_blockers + self.still_open_blockers) if b.type == BlockerType.PENDING_CHECK]
        if pending:
            return "Wait for CI to complete. ⏳"
            
        # Default: general blockers
        return f"Resolve remaining blockers: {len(self.added_blockers) + len(self.still_open_blockers)} items. 🚧"
