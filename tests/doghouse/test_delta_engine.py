import datetime
from doghouse.core.domain.blocker import Blocker, BlockerType
from doghouse.core.domain.snapshot import Snapshot
from doghouse.core.services.delta_engine import DeltaEngine

def test_compute_delta_no_changes():
    engine = DeltaEngine()
    blocker = Blocker(id="1", type=BlockerType.UNRESOLVED_THREAD, message="msg")
    
    baseline = Snapshot(
        timestamp=datetime.datetime(2026, 1, 1),
        head_sha="sha1",
        blockers=[blocker]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2),
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
        timestamp=datetime.datetime(2026, 1, 1),
        head_sha="sha1",
        blockers=[b1]
    )
    current = Snapshot(
        timestamp=datetime.datetime(2026, 1, 2),
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
