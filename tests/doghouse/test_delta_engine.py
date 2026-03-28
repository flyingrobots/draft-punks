import datetime
from doghouse.core.domain.blocker import Blocker, BlockerType
from doghouse.core.domain.snapshot import Snapshot
from doghouse.core.services.delta_engine import DeltaEngine

def test_compute_delta_no_changes():
    engine = DeltaEngine()
    blocker = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg")
    
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[blocker]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[blocker]
    )
    
    delta = engine.compute_delta(baseline, current)
    
    assert delta.baseline_sha == "sha1"
    assert delta.current_sha == "sha1"
    assert len(delta.added_blockers) == 0
    assert len(delta.removed_blockers) == 0
    assert len(delta.still_open_blockers) == 1
    assert not delta.head_changed

def test_compute_delta_with_changes():
    engine = DeltaEngine()
    b1 = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg1")
    b2 = Blocker(id="2", type=BlockerType.FAILING_CHECK, message="msg2")
    
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[b1]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="sha2",
        blockers=[b2]
    )
    
    delta = engine.compute_delta(baseline, current)
    
    assert delta.head_changed
    assert len(delta.added_blockers) == 1
    assert delta.added_blockers[0].id == "2"
    assert len(delta.removed_blockers) == 1
    assert delta.removed_blockers[0].id == "1"
    assert len(delta.still_open_blockers) == 0

def test_compute_delta_empty_blockers():
    engine = DeltaEngine()
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[]
    )
    delta = engine.compute_delta(baseline, current)
    assert len(delta.added_blockers) == 0
    assert len(delta.removed_blockers) == 0
    assert len(delta.still_open_blockers) == 0

def test_compute_delta_overlapping_blockers():
    engine = DeltaEngine()
    b1 = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg1")
    b2 = Blocker(id="2", type=BlockerType.UNRESOLVED_THREAD, message="msg2")
    b3 = Blocker(id="3", type=BlockerType.UNRESOLVED_THREAD, message="msg3")
    
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[b1, b2]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[b2, b3]
    )
    
    delta = engine.compute_delta(baseline, current)
    assert len(delta.added_blockers) == 1
    assert delta.added_blockers[0].id == "3"
    assert len(delta.removed_blockers) == 1
    assert delta.removed_blockers[0].id == "1"
    assert len(delta.still_open_blockers) == 1
    assert delta.still_open_blockers[0].id == "2"

def test_compute_delta_mutated_blocker():
    # If ID is same but content changes, it's still "still_open" in current logic
    # because ID is the primary key for delta.
    engine = DeltaEngine()
    b1_v1 = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg1")
    b1_v2 = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg1-updated")
    
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[b1_v1]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2, tzinfo=datetime.timezone.utc),
        head_sha="sha1",
        blockers=[b1_v2]
    )
    
    delta = engine.compute_delta(baseline, current)
    assert len(delta.still_open_blockers) == 1
    assert delta.still_open_blockers[0].message == "msg1-updated"
