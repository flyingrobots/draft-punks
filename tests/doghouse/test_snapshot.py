"""Tests for Snapshot equivalence and serialization."""
import datetime
from doghouse.core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from doghouse.core.domain.snapshot import Snapshot


def test_is_equivalent_same_state():
    b = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b],
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b],
    )
    assert s1.is_equivalent_to(s2)


def test_not_equivalent_different_sha():
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[],
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="def",
        blockers=[],
    )
    assert not s1.is_equivalent_to(s2)


def test_not_equivalent_different_blockers():
    b1 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    b2 = Blocker(id="t2", type=BlockerType.FAILING_CHECK, message="ci")
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b1],
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b2],
    )
    assert not s1.is_equivalent_to(s2)


def test_not_equivalent_severity_change():
    b1 = Blocker(id="t1", type=BlockerType.NOT_APPROVED, message="review",
                 severity=BlockerSeverity.BLOCKER)
    b2 = Blocker(id="t1", type=BlockerType.NOT_APPROVED, message="review",
                 severity=BlockerSeverity.WARNING)
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b1],
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b2],
    )
    assert not s1.is_equivalent_to(s2)


def test_equivalent_ignores_timestamp_and_metadata():
    b = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b],
        metadata={"old": True},
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 6, 15, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b],
        metadata={"new": True},
    )
    assert s1.is_equivalent_to(s2)


def test_blocker_signature_order_independent():
    b1 = Blocker(id="a", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    b2 = Blocker(id="b", type=BlockerType.FAILING_CHECK, message="ci")
    s1 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b1, b2],
    )
    s2 = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="abc",
        blockers=[b2, b1],  # reversed order
    )
    assert s1.is_equivalent_to(s2)
