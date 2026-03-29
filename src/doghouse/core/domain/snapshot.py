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

    def __post_init__(self):
        # Ensure immutability by copying input lists/dicts
        object.__setattr__(self, 'blockers', list(self.blockers))
        object.__setattr__(self, 'metadata', dict(self.metadata))

    def blocker_signature(self) -> frozenset:
        """Stable signature of blocker state for equivalence comparison.

        Two snapshots with the same head_sha and blocker_signature represent
        the same meaningful PR state — a repeated poll, not a new sortie.
        """
        return frozenset(
            (b.id, b.type.value, b.severity.value, b.is_primary)
            for b in self.blockers
        )

    def is_equivalent_to(self, other: "Snapshot") -> bool:
        """True if this snapshot represents the same meaningful PR state."""
        if self.head_sha != other.head_sha:
            return False
        return self.blocker_signature() == other.blocker_signature()

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
                    "is_primary": b.is_primary,
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
                    is_primary=b.get("is_primary", True),
                    message=b["message"],
                    metadata=b.get("metadata", {})
                ) for b in data["blockers"]
            ],
            metadata=data.get("metadata", {})
        )
