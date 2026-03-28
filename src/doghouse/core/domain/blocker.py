from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

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
    BLOCKER = "blocker"  # Must be fixed to merge
    WARNING = "warning"  # Should be fixed, but not strictly blocking
    INFO = "info"       # Informational

@dataclass(frozen=True)
class Blocker:
    id: str
    type: BlockerType
    message: str
    severity: BlockerSeverity = BlockerSeverity.BLOCKER
    is_primary: bool = True  # If False, this is a secondary/dependent blocker
    metadata: Dict[str, Any] = field(default_factory=dict)
