import random
from dataclasses import dataclass, field
from typing import List, Set, Optional
from .blocker import Blocker, BlockerType, BlockerSeverity
from .snapshot import Snapshot

# ---------------------------------------------------------------------------
# PhiedBach's theatrical verdicts — 5 variations each, randomly chosen.
# The machine-readable verdict (verdict property) stays terse and stable.
# The display verdict (verdict_display property) is PhiedBach's voice.
#
# Templates use {n} for counts and {noun} for singular/plural instrument
# names.  Both are .format()'d at call time.
# ---------------------------------------------------------------------------

_V_MERGE_READY = [
    "Ze orchestra is in tune. You may merge, mein Freund. 🎼",
    "Ze symphony is complete! Merge vhen you are ready. 🎼",
    "All voices are in harmony. Ze merge gate is open. 🎼",
    "Not a single note out of place. Merge avay! 🎼",
    "Ze score is flawless. PhiedBach beams. You may merge. 🎼",
]

_V_MERGE_CONFLICT = [
    "Ze score has a terrible knot! Resolve ze merge conflicts before anything else. ⚔️",
    "Mein Gott — ze pages are stuck together! Untangle ze conflicts first. ⚔️",
    "Ze voices clash in ze worst vay! Fix ze merge conflicts. ⚔️",
    "Ze manuscript is in disarray! No progress until ze conflicts are resolved. ⚔️",
    "A terrible knot in ze score! Nothing else matters until zis is undone. ⚔️",
]

_V_FAILING_CHECKS = [
    "{n} {noun} {verb} out of tune! Fix ze failing checks. 🛑",
    "{n} {noun} {verb} hitting sour notes! Ze CI section needs attention. 🛑",
    "{n} {noun} {verb} screeching! Fix ze checks before ze audience notices. 🛑",
    "Ze CI section reports {n} {noun} off-key! Attend to zem. 🛑",
    "{n} {noun} {verb} playing in ze wrong key entirely! Fix ze failing checks. 🛑",
]

_V_UNRESOLVED_THREADS = [
    "{n} {noun} {verb} unanswered. Address ze review feedback. 💬",
    "{n} {noun} {verb} calling from ze back of ze concert hall. Respond to zem. 💬",
    "{n} {noun} {verb} still vaiting for a reply. Address ze feedback. 💬",
    "Ze chorus has {n} unacknowledged {noun}. Answer zem. 💬",
    "{n} {noun} {verb} echoing in ze rafters. Ze review threads need attention. 💬",
]

_V_PENDING_CHECKS = [
    "Ze stagehands are still preparing. Vait for CI to finish. ⏳",
    "Ze backstage crew is not yet ready. Patience, mein Freund. ⏳",
    "Ze gears are turning behind ze curtain. Vait for CI. ⏳",
    "Ze orchestra is tuning. CI is still in progress. ⏳",
    "Ze preparation continues. CI has not yet finished its vork. ⏳",
]

_V_APPROVAL_NEEDED = [
    "Ze conductor has not yet given his blessing. Approval is needed. 📋",
    "Ze maestro's baton remains lowered. You need approval to proceed. 📋",
    "Ze seal of approval has not yet been pressed into ze vax. 📋",
    "Ze conductor vaits to see ze final rehearsal. Approval is required. 📋",
    "No blessing from ze podium yet. Seek approval before merging. 📋",
]

_V_DEFAULT = [
    "{n} {noun} {verb} on ze music stand. Resolve zem before ze performance. 🚧",
    "{n} {noun} {verb} in ze margins. Clear ze remaining blockers. 🚧",
    "Ze ledger still shows {n} unresolved {noun}. Attend to zem. 🚧",
    "{n} {noun} {verb} unresolved. Ze symphony cannot begin. 🚧",
    "PhiedBach counts {n} remaining {noun}. Address zem. 🚧",
]


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

    @property
    def verdict_display(self) -> str:
        """PhiedBach's theatrical verdict for human eyes."""
        all_current = self.added_blockers + self.still_open_blockers
        if not all_current:
            return random.choice(_V_MERGE_READY)

        # Priority 0: Merge conflicts
        if any(b.type == BlockerType.DIRTY_MERGE_STATE for b in all_current):
            return random.choice(_V_MERGE_CONFLICT)

        # Priority 1: Failing checks
        failing = [b for b in all_current if b.type == BlockerType.FAILING_CHECK]
        if failing:
            n = len(failing)
            noun = "instrument" if n == 1 else "instruments"
            verb = "is" if n == 1 else "are"
            return random.choice(_V_FAILING_CHECKS).format(n=n, noun=noun, verb=verb)

        # Priority 2: Unresolved threads
        threads = [b for b in all_current if b.type == BlockerType.UNRESOLVED_THREAD]
        if threads:
            n = len(threads)
            noun = "voice" if n == 1 else "voices"
            verb = "remains" if n == 1 else "remain"
            return random.choice(_V_UNRESOLVED_THREADS).format(n=n, noun=noun, verb=verb)

        # Priority 3: Pending checks
        if any(b.type == BlockerType.PENDING_CHECK for b in all_current):
            return random.choice(_V_PENDING_CHECKS)

        # Priority 4: Formal approval required
        if any(b.type == BlockerType.NOT_APPROVED for b in all_current):
            return random.choice(_V_APPROVAL_NEEDED)

        # Default
        n = len(all_current)
        noun = "item" if n == 1 else "items"
        verb = "remains" if n == 1 else "remain"
        return random.choice(_V_DEFAULT).format(n=n, noun=noun, verb=verb)
