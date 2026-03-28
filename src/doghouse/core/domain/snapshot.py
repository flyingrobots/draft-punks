import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from .blocker import Blocker, BlockerType, BlockerSeverity

@dataclass(frozen=True)
class Snapshot:
    timestamp: datetime.datetime
    head_sha: str
    blockers: List[Blocker]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the snapshot to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "head_sha": self.head_sha,
            "blockers": [
                {
                    "id": b.id,
                    "type": b.type.value,
                    "severity": b.severity.value,
                    "message": b.message,
                    "metadata": b.metadata
                } for b in self.blockers
            ],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """Reconstruct a snapshot from a dictionary."""
        return cls(
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            head_sha=data["head_sha"],
            blockers=[
                Blocker(
                    id=b["id"],
                    type=BlockerType(b["type"]),
                    severity=BlockerSeverity(b["severity"]),
                    message=b["message"],
                    metadata=b.get("metadata", {})
                ) for b in data["blockers"]
            ],
            metadata=data.get("metadata", {})
        )
