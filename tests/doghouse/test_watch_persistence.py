"""Tests for watch/recorder persistence behavior.

Verifies that repeated identical polls do not create duplicate snapshots,
and that meaningful transitions do get persisted.
"""
import datetime
from unittest.mock import MagicMock
from doghouse.core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from doghouse.core.domain.snapshot import Snapshot
from doghouse.core.services.recorder_service import RecorderService
from doghouse.core.services.delta_engine import DeltaEngine


def _make_service(
    head_sha: str = "abc123",
    remote_blockers: list[Blocker] | None = None,
    local_blockers: list[Blocker] | None = None,
    stored_baseline: Snapshot | None = None,
) -> tuple[RecorderService, MagicMock]:
    """Build a RecorderService with fake adapters."""
    github = MagicMock()
    github.get_head_sha.return_value = head_sha
    github.fetch_blockers.return_value = remote_blockers or []
    github.get_pr_metadata.return_value = {"title": "test"}

    storage = MagicMock()
    storage.get_latest_snapshot.return_value = stored_baseline

    git = MagicMock()
    git.get_local_blockers.return_value = local_blockers or []

    engine = DeltaEngine()
    service = RecorderService(github, storage, engine, git=git)
    return service, storage


def test_identical_poll_does_not_persist():
    """When current state matches the stored baseline, no new snapshot is saved."""
    thread = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[thread],
    )

    service, storage = _make_service(
        head_sha="abc123",
        remote_blockers=[thread],
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_not_called()


def test_head_sha_change_persists():
    """When head SHA changes, the new snapshot must be saved."""
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="old_sha",
        blockers=[],
    )

    service, storage = _make_service(
        head_sha="new_sha",
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_called_once()


def test_blocker_added_persists():
    """When a new blocker appears, the snapshot must be saved."""
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[],
    )
    new_blocker = Blocker(id="t1", type=BlockerType.FAILING_CHECK, message="CI broke")

    service, storage = _make_service(
        head_sha="abc123",
        remote_blockers=[new_blocker],
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_called_once()


def test_blocker_removed_persists():
    """When a blocker is resolved, the snapshot must be saved."""
    old_blocker = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="fix")
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[old_blocker],
    )

    service, storage = _make_service(
        head_sha="abc123",
        remote_blockers=[],  # blocker resolved
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_called_once()


def test_blocker_severity_change_persists():
    """When a blocker's severity changes, that's a meaningful transition."""
    b_v1 = Blocker(id="t1", type=BlockerType.NOT_APPROVED, message="review",
                   severity=BlockerSeverity.BLOCKER)
    b_v2 = Blocker(id="t1", type=BlockerType.NOT_APPROVED, message="review",
                   severity=BlockerSeverity.WARNING)
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[b_v1],
    )

    service, storage = _make_service(
        head_sha="abc123",
        remote_blockers=[b_v2],
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_called_once()


def test_message_only_change_does_not_persist():
    """When only a blocker's message changes (same id/type/severity/is_primary),
    the snapshot is equivalent and must not be saved."""
    b_v1 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="old msg")
    b_v2 = Blocker(id="t1", type=BlockerType.UNRESOLVED_THREAD, message="new msg")
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="abc123",
        blockers=[b_v1],
    )

    service, storage = _make_service(
        head_sha="abc123",
        remote_blockers=[b_v2],
        stored_baseline=baseline,
    )

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_not_called()


def test_first_snapshot_always_persists():
    """When there is no baseline (first run), always persist."""
    service, storage = _make_service(stored_baseline=None)

    service.record_sortie("owner/repo", 1)
    storage.save_snapshot.assert_called_once()
