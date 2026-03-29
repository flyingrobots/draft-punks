import subprocess

from ...core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from ...core.ports.git_port import GitPort


class GitAdapter(GitPort):
    """Adapter for local git repository operations."""

    def get_local_blockers(self) -> list[Blocker]:
        """Detect local issues (uncommitted, unpushed)."""
        blockers = []

        # Check for uncommitted changes
        status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False, timeout=10)
        if status_res.stdout.strip():
            blockers.append(Blocker(
                id="local-uncommitted",
                type=BlockerType.LOCAL_UNCOMMITTED,
                message="Local uncommitted changes detected",
                severity=BlockerSeverity.WARNING
            ))

        # Check for unpushed commits on the current branch
        branch_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=False, timeout=10)
        branch = branch_res.stdout.strip()
        if branch:
            # Check for commits that are in branch but not in its upstream
            # Use @{u} but handle if it's missing
            unpushed_res = subprocess.run(
                ["git", "rev-list", "@{u}..HEAD"],
                capture_output=True, text=True, check=False, timeout=10
            )
            if unpushed_res.returncode == 0 and unpushed_res.stdout.strip():
                count = len(unpushed_res.stdout.strip().split("\n"))
                blockers.append(Blocker(
                    id="local-unpushed",
                    type=BlockerType.LOCAL_UNPUSHED,
                    message=f"Local branch is ahead of remote by {count} commits",
                    severity=BlockerSeverity.WARNING
                ))
            elif unpushed_res.returncode != 0:
                # Upstream might be missing
                blockers.append(Blocker(
                    id="local-no-upstream",
                    type=BlockerType.LOCAL_UNPUSHED,
                    message="Local branch has no upstream configured",
                    severity=BlockerSeverity.WARNING
                ))

        return blockers
