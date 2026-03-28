import json
from pathlib import Path
from ..domain.snapshot import Snapshot
from ..domain.delta import Delta
from .delta_engine import DeltaEngine

class PlaybackService:
    """Service to run the delta engine against offline fixtures."""

    def __init__(self, engine: DeltaEngine) -> None:
        self.engine = engine

    def run_playback(self, playback_dir: Path) -> tuple[Snapshot | None, Snapshot, Delta]:
        """Run a delta comparison between baseline.json and current.json in the directory."""
        baseline_path = playback_dir / "baseline.json"
        current_path = playback_dir / "current.json"

        if not current_path.exists():
            raise FileNotFoundError(f"Required playback file not found: {current_path}")

        with open(current_path) as f:
            current = Snapshot.from_dict(json.load(f))

        baseline = None
        if baseline_path.exists():
            with open(baseline_path) as f:
                baseline = Snapshot.from_dict(json.load(f))

        delta = self.engine.compute_delta(baseline, current)
        return baseline, current, delta
