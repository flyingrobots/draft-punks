import subprocess
from typing import List
from ...core.domain.blocker import Blocker, BlockerType, BlockerSeverity

class GitAdapter:
    """Adapter for local git repository operations."""
    
    def get_local_blockers(self) -> List[Blocker]:
        """Detect local issues (uncommitted, unpushed)."""
        blockers = []
        
        # Check for uncommitted changes
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
        if status.strip():
            blockers.append(Blocker(
                id="local-uncommitted",
                type=BlockerType.LOCAL_UNCOMMITTED,
                message="Local uncommitted changes detected",
                severity=BlockerSeverity.WARNING
            ))
            
        # Check for unpushed commits on the current branch
        branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = branch_res.stdout.strip()
        if branch:
            # Check for commits that are in branch but not in its upstream
            unpushed = subprocess.run(
                ["git", "rev-list", f"@{'{'}u{'}'}..HEAD"], 
                capture_output=True, text=True
            ).stdout
            if unpushed.strip():
                count = len(unpushed.strip().split("\n"))
                blockers.append(Blocker(
                    id="local-unpushed",
                    type=BlockerType.LOCAL_UNPUSHED,
                    message=f"Local branch is ahead of remote by {count} commits",
                    severity=BlockerSeverity.WARNING
                ))
                
        return blockers
