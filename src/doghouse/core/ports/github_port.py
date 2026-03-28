from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..domain.blocker import Blocker

class GitHubPort(ABC):
    """Port for interacting with GitHub to fetch PR state."""
    
    @abstractmethod
    def get_head_sha(self, pr_id: Optional[int] = None) -> str:
        """Get the current head SHA of the PR."""
        pass
        
    @abstractmethod
    def fetch_blockers(self, pr_id: Optional[int] = None) -> List[Blocker]:
        """Fetch all blockers (threads, checks, etc.) for the PR."""
        pass
        
    @abstractmethod
    def get_pr_metadata(self, pr_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch metadata for the PR (title, author, etc.)."""
        pass
