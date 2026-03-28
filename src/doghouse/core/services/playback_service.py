import json
from pathlib import Path
from typing import Tuple, Optional
from ..domain.snapshot import Snapshot
from ..domain.delta import Delta
from .delta_engine import DeltaEngine

class PlaybackService:
    """Service to run the delta engine against offline fixtures."""
    
    def __init__(self, engine: DeltaEngine):
        self.engine = engine

    def run_playback(self, playback_dir: Path) -> Tuple[Snapshot, Snapshot, Delta]:
        """Run a delta comparison between baseline.json and current.json in the directory."""
        baseline_path = playback_dir / "baseline.json"
        current_path = playback_dir / "current.json"
        
        with open(current_path, "r") as f:
            current = Snapshot.from_dict(json.load(f))
            
        baseline = None
        if baseline_path.exists():
            with open(baseline_path, "r") as f:
                baseline = Snapshot.from_dict(json.load(f))
                
        delta = self.engine.compute_delta(baseline, current)
        return baseline, current, delta
