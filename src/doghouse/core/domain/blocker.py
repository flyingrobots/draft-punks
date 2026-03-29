from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BlockerType(Enum):
    UNRESOLVED_THREAD = "unresolved_thread"
    FAILING_CHECK = "failing_check"
    PENDING_CHECK = "pending_check"
    NOT_APPROVED = "not_approved"
    DIRTY_MERGE_STATE = "dirty_merge_state"
    CODERABBIT_STATE = "coderabbit_state"
    LOCAL_UNCOMMITTED = "local_uncommitted"
    LOCAL_UNPUSHED = "local_unpushed"
    OTHER = "other"


class BlockerSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"

    @property
    def rank(self) -> int:
        """Numeric rank for severity comparison. Higher = more severe."""
        return {"info": 0, "warning": 1, "blocker": 2}[self.value]


@dataclass(frozen=True)
class Blocker:
    id: str
    type: BlockerType
    message: str
    severity: BlockerSeverity = BlockerSeverity.BLOCKER
    is_primary: bool = True  # If False, this is a secondary/dependent blocker
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Defensive copy so callers can't mutate our metadata
        object.__setattr__(self, 'metadata', dict(self.metadata))
