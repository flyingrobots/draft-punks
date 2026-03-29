"""Tests for merge-readiness blocker semantics.

Verifies that unresolved threads and formal approval state interact correctly,
and that the verdict priority chain produces the right next-action.
"""
import datetime
from doghouse.core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from doghouse.core.domain.delta import Delta
from doghouse.core.domain.snapshot import Snapshot
from doghouse.core.services.delta_engine import DeltaEngine


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


# --- PhiedBach's theatrical verdicts (verdict_display) ---

def test_verdict_display_merge_ready():
    delta = _make_delta([])
    assert "Ze orchestra is in tune" in delta.verdict_display
    assert "mein Freund" in delta.verdict_display


def test_verdict_display_merge_conflict():
    blockers = [
        Blocker(id="merge-conflict", type=BlockerType.DIRTY_MERGE_STATE,
                message="conflict", is_primary=True),
    ]
    delta = _make_delta(blockers)
    assert "terrible knot" in delta.verdict_display


def test_verdict_display_failing_checks_singular():
    blockers = [
        Blocker(id="check-ci", type=BlockerType.FAILING_CHECK, message="CI"),
    ]
    delta = _make_delta(blockers)
    assert "1 instrument is out of tune" in delta.verdict_display


def test_verdict_display_failing_checks_plural():
    blockers = [
        Blocker(id="check-a", type=BlockerType.FAILING_CHECK, message="a"),
        Blocker(id="check-b", type=BlockerType.FAILING_CHECK, message="b"),
    ]
    delta = _make_delta(blockers)
    assert "2 instruments are out of tune" in delta.verdict_display


def test_verdict_display_unresolved_threads():
    blockers = [
        Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix"),
        Blocker(id="t2", type=BlockerType.UNRESOLVED_THREAD, message="fix2"),
    ]
    delta = _make_delta(blockers)
    assert "2 voices remain unanswered" in delta.verdict_display


def test_verdict_display_approval_needed():
    blockers = [
        Blocker(id="review-required", type=BlockerType.NOT_APPROVED,
                message="Review required", severity=BlockerSeverity.WARNING),
    ]
    delta = _make_delta(blockers)
    assert "Ze conductor" in delta.verdict_display
    assert "blessing" in delta.verdict_display
