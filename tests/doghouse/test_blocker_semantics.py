"""Tests for merge-readiness blocker semantics.

Verifies that unresolved threads and formal approval state interact correctly,
and that the verdict priority chain produces the right next-action.
"""
import datetime
from doghouse.core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from doghouse.core.domain.delta import Delta
from doghouse.core.domain.snapshot import Snapshot
from doghouse.core.services.delta_engine import DeltaEngine


# --- Severity ranking ---

def test_severity_rank_order():
    """BLOCKER > WARNING > INFO, numerically."""
    assert BlockerSeverity.BLOCKER.rank > BlockerSeverity.WARNING.rank
    assert BlockerSeverity.WARNING.rank > BlockerSeverity.INFO.rank


def test_severity_rank_merge_keeps_more_severe():
    """When merging two blockers with the same ID, the higher severity wins."""
    high = BlockerSeverity.BLOCKER
    low = BlockerSeverity.WARNING
    # Simulate the merge logic from recorder_service
    winner = high if high.rank > low.rank else low
    assert winner == BlockerSeverity.BLOCKER


# --- Delta helpers ---

def _make_delta(blockers: list[Blocker]) -> Delta:
    """Helper: build a Delta where all blockers are 'still open'."""
    engine = DeltaEngine()
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="aaa",
        blockers=blockers,
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="aaa",
        blockers=blockers,
    )
    return engine.compute_delta(baseline, current)


# --- Review decision / thread interaction ---

def test_threads_and_changes_requested_threads_are_the_real_blockers():
    """When unresolved threads exist AND CHANGES_REQUESTED is set,
    the threads should be the blockers — not the approval state.

    This test verifies the adapter-level design decision: when threads
    exist, we don't emit a NOT_APPROVED blocker for CHANGES_REQUESTED.
    We simulate the expected adapter output here.
    """
    # Adapter should produce only the thread blockers, no NOT_APPROVED
    thread = Blocker(
        id="thread-abc",
        type=BlockerType.UNRESOLVED_THREAD,
        message="Fix the null check",
    )
    delta = _make_delta([thread])

    assert delta.verdict == "Address review feedback: 1 unresolved threads. 💬"


def test_changes_requested_no_threads_yields_approval_warning():
    """When CHANGES_REQUESTED is set but all threads are resolved,
    the adapter should emit a WARNING-level NOT_APPROVED blocker.
    """
    approval = Blocker(
        id="review-changes-requested",
        type=BlockerType.NOT_APPROVED,
        message="Re-approval needed (changes were requested, threads resolved)",
        severity=BlockerSeverity.WARNING,
    )
    delta = _make_delta([approval])

    # Should hit the approval verdict, not the generic one
    assert "Approval needed" in delta.verdict


def test_review_required_is_warning_not_blocker():
    """REVIEW_REQUIRED should be WARNING severity."""
    approval = Blocker(
        id="review-required",
        type=BlockerType.NOT_APPROVED,
        message="Review required",
        severity=BlockerSeverity.WARNING,
    )
    assert approval.severity == BlockerSeverity.WARNING


def test_approval_state_distinct_from_threads_in_verdict():
    """Approval-only blockers should produce an approval-specific verdict,
    not the unresolved-threads verdict.
    """
    approval_only = [
        Blocker(
            id="review-required",
            type=BlockerType.NOT_APPROVED,
            message="Review required",
            severity=BlockerSeverity.WARNING,
        )
    ]
    delta = _make_delta(approval_only)
    assert "Approval needed" in delta.verdict
    assert "unresolved threads" not in delta.verdict


# --- Verdict priority chain ---

def test_verdict_merge_ready_when_no_blockers():
    delta = _make_delta([])
    assert "Merge ready" in delta.verdict


def test_verdict_merge_conflict_takes_priority():
    blockers = [
        Blocker(id="merge-conflict", type=BlockerType.DIRTY_MERGE_STATE,
                message="Merge conflict", is_primary=True),
        Blocker(id="thread-1", type=BlockerType.UNRESOLVED_THREAD,
                message="Fix something"),
    ]
    delta = _make_delta(blockers)
    assert "merge conflict" in delta.verdict.lower()


def test_verdict_failing_checks_before_threads():
    blockers = [
        Blocker(id="check-ci", type=BlockerType.FAILING_CHECK,
                message="CI failed"),
        Blocker(id="thread-1", type=BlockerType.UNRESOLVED_THREAD,
                message="Fix something"),
    ]
    delta = _make_delta(blockers)
    assert "failing checks" in delta.verdict.lower()


def test_verdict_threads_before_pending_checks():
    blockers = [
        Blocker(id="thread-1", type=BlockerType.UNRESOLVED_THREAD,
                message="Fix something"),
        Blocker(id="check-ci", type=BlockerType.PENDING_CHECK,
                message="CI pending", severity=BlockerSeverity.INFO),
    ]
    delta = _make_delta(blockers)
    assert "review feedback" in delta.verdict.lower()


def test_verdict_pending_checks_before_approval():
    blockers = [
        Blocker(id="check-ci", type=BlockerType.PENDING_CHECK,
                message="CI pending", severity=BlockerSeverity.INFO),
        Blocker(id="review-required", type=BlockerType.NOT_APPROVED,
                message="Review required", severity=BlockerSeverity.WARNING),
    ]
    delta = _make_delta(blockers)
    assert "Wait for CI" in delta.verdict


# --- PhiedBach's theatrical verdicts (_theatrical_verdict) ---
# _theatrical_verdict is randomized, so tests check that the result is one of
# the known variations (imported from the CLI module) and carries the right emoji.

from doghouse.cli.main import (
    _theatrical_verdict,
    _V_MERGE_READY, _V_MERGE_CONFLICT,
    _V_APPROVAL_NEEDED,
)


def test_theatrical_verdict_merge_ready():
    delta = _make_delta([])
    assert _theatrical_verdict(delta) in _V_MERGE_READY


def test_theatrical_verdict_merge_conflict():
    blockers = [
        Blocker(id="merge-conflict", type=BlockerType.DIRTY_MERGE_STATE,
                message="conflict", is_primary=True),
    ]
    delta = _make_delta(blockers)
    assert _theatrical_verdict(delta) in _V_MERGE_CONFLICT


def test_theatrical_verdict_failing_checks_singular():
    blockers = [
        Blocker(id="check-ci", type=BlockerType.FAILING_CHECK, message="CI"),
    ]
    delta = _make_delta(blockers)
    result = _theatrical_verdict(delta)
    assert "1 instrument" in result
    assert "🛑" in result


def test_theatrical_verdict_failing_checks_plural():
    blockers = [
        Blocker(id="check-a", type=BlockerType.FAILING_CHECK, message="a"),
        Blocker(id="check-b", type=BlockerType.FAILING_CHECK, message="b"),
    ]
    delta = _make_delta(blockers)
    result = _theatrical_verdict(delta)
    assert "2 instruments" in result
    assert "🛑" in result


def test_theatrical_verdict_unresolved_threads():
    blockers = [
        Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix"),
        Blocker(id="t2", type=BlockerType.UNRESOLVED_THREAD, message="fix2"),
    ]
    delta = _make_delta(blockers)
    result = _theatrical_verdict(delta)
    assert "2" in result
    assert "voice" in result
    assert "💬" in result


def test_theatrical_verdict_approval_needed():
    blockers = [
        Blocker(id="review-required", type=BlockerType.NOT_APPROVED,
                message="Review required", severity=BlockerSeverity.WARNING),
    ]
    delta = _make_delta(blockers)
    assert _theatrical_verdict(delta) in _V_APPROVAL_NEEDED
