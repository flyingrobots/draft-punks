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


def test_roundtrip_to_dict_from_dict():
    """Snapshot survives a to_dict -> from_dict roundtrip."""
    b = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix",
                severity=BlockerSeverity.BLOCKER, is_primary=False,
                metadata={"key": "val"})
    original = Snapshot(
        timestamp=datetime.datetime(2026, 3, 15, 12, 0, 0, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[b],
        metadata={"pr": 42},
    )
    restored = Snapshot.from_dict(original.to_dict())
    assert restored.head_sha == original.head_sha
    assert restored.timestamp == original.timestamp
    assert len(restored.blockers) == 1
    rb = restored.blockers[0]
    assert rb.id == b.id
    assert rb.type == b.type
    assert rb.message == b.message
    assert rb.severity == b.severity
    assert rb.is_primary == b.is_primary
    assert rb.metadata == b.metadata
    assert restored.metadata == original.metadata


def test_not_equivalent_is_primary_change():
    """Changing is_primary on a blocker is a meaningful state change."""
    b1 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix",
                 is_primary=True)
    b2 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix",
                 is_primary=False)
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


def test_equivalent_message_only_change():
    """A message-only change does not affect equivalence (message is not in signature)."""
    b1 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="old msg")
    b2 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="new msg")
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
