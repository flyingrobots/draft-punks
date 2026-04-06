import subprocess

from ...core.domain.blocker import Blocker, BlockerType, BlockerSeverity
from ...core.ports.git_port import GitPort


class GitAdapter(GitPort):
    """Adapter for local git repository operations."""

    def _run_git(self, args: list[str], repo_path: str | None) -> subprocess.CompletedProcess[str]:
        """Execute git in the selected repo path, or current cwd when absent."""
        return subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
            cwd=repo_path,
        )

    def get_local_blockers(self, repo_path: str | None = None) -> list[Blocker]:
        """Detect local issues (uncommitted, unpushed)."""
        blockers = []

        # Check for uncommitted changes
        status_res = self._run_git(["status", "--porcelain"], repo_path)
        if status_res.stdout.strip():
            blockers.append(Blocker(
                id="local-uncommitted",
                type=BlockerType.LOCAL_UNCOMMITTED,
                message="Local uncommitted changes detected",
                severity=BlockerSeverity.WARNING
            ))

        # Check for unpushed commits on the current branch
        branch_res = self._run_git(["branch", "--show-current"], repo_path)
        branch = branch_res.stdout.strip()
        if branch:
            # Check for commits that are in branch but not in its upstream
            # Use @{u} but handle if it's missing
            unpushed_res = self._run_git(["rev-list", "@{u}..HEAD"], repo_path)
            if unpushed_res.returncode == 0 and unpushed_res.stdout.strip():
                count = len(unpushed_res.stdout.strip().split("\n"))
                blockers.append(Blocker(
                    id="local-unpushed",
                    type=BlockerType.LOCAL_UNPUSHED,
                    message=f"Local branch is ahead of remote by {count} commits",
                    severity=BlockerSeverity.WARNING
                ))
            elif unpushed_res.returncode != 0:
                stderr = unpushed_res.stderr.strip() if unpushed_res.stderr else ""
                if "no upstream configured" in stderr or unpushed_res.returncode == 128:
                    msg = "Local branch has no upstream configured"
                else:
                    msg = f"Could not determine unpushed commits: {stderr or 'unknown error'}"
                blockers.append(Blocker(
                    id="local-no-upstream",
                    type=BlockerType.LOCAL_UNPUSHED,
                    message=msg,
                    severity=BlockerSeverity.WARNING
                ))

        return blockers
