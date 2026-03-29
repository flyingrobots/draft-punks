import json
import subprocess
from typing import Any

from ...core.ports.github_port import GitHubPort
from ...core.domain.blocker import Blocker, BlockerType, BlockerSeverity


class GhCliAdapter(GitHubPort):
    """Adapter for GitHub using the 'gh' CLI."""

    def __init__(self, repo_owner: str | None = None, repo_name: str | None = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else None

    def _run_gh(self, args: list[str], with_repo: bool = True) -> str:
        """Execute a 'gh' command and return stdout."""
        cmd = ["gh"] + args
        if with_repo and self.repo:
            cmd += ["-R", self.repo]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        return result.stdout

    def _run_gh_json(self, args: list[str], with_repo: bool = True) -> dict[str, Any]:
        """Execute a 'gh' command and return parsed JSON output."""
        return json.loads(self._run_gh(args, with_repo=with_repo))

    def _pr_view_args(self, pr_id: int | None, fields: list[str]) -> list[str]:
        """Build 'gh pr view' args, omitting pr_id when None."""
        args = ["pr", "view"]
        if pr_id is not None:
            args.append(str(pr_id))
        args += ["--json", ",".join(fields)]
        return args

    def get_head_sha(self, pr_id: int | None = None) -> str:
        fields = ["headRefOid"]
        data = self._run_gh_json(self._pr_view_args(pr_id, fields))
        return data["headRefOid"]

    def _fetch_repo_info(self) -> tuple[str, str]:
        """Fetch owner and name for the current repo if not provided."""
        if self.repo_owner and self.repo_name:
            return self.repo_owner, self.repo_name
        data = self._run_gh_json(["repo", "view", "--json", "owner,name"])
        return data["owner"]["login"], data["name"]

    def fetch_blockers(self, pr_id: int | None = None) -> list[Blocker]:
        # 1. Fetch basic PR data
        fields = ["statusCheckRollup", "reviewDecision", "mergeable", "number"]
        data = self._run_gh_json(self._pr_view_args(pr_id, fields))
        actual_pr_id = data["number"]

        blockers: list[Blocker] = []

        # 2. Fetch Unresolved threads via GraphQL
        owner, name = self._fetch_repo_info()
        gql_query = """
        query($owner: String!, $repo: String!, $pr: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $pr) {
              reviewThreads(first: 100) {
                nodes {
                  isResolved
                  comments(first: 1) {
                    nodes {
                      body
                      id
                    }
                  }
                }
              }
            }
          }
        }
        """
        try:
            gql_res = self._run_gh_json([
                "api", "graphql",
                "-F", f"owner={owner}",
                "-F", f"repo={name}",
                "-F", f"pr={actual_pr_id}",
                "-f", f"query={gql_query}"
            ], with_repo=False)
            threads = gql_res.get("data", {}).get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])
            for thread in threads:
                if not thread.get("isResolved"):
                    comments = thread.get("comments", {}).get("nodes", [])
                    if comments:
                        first_comment = comments[0]
                        msg = first_comment.get("body", "Unresolved thread")
                        if len(msg) > 80:
                            msg = msg[:77] + "..."

                        blockers.append(Blocker(
                            id=f"thread-{first_comment.get('id', 'unknown')}",
                            type=BlockerType.UNRESOLVED_THREAD,
                            message=msg
                        ))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                json.JSONDecodeError, KeyError) as e:
            blockers.append(Blocker(
                id="error-threads",
                type=BlockerType.OTHER,
                message=f"Warning: Could not fetch review threads: {e}",
                severity=BlockerSeverity.WARNING
            ))

        # 3. Status checks
        for check in data.get("statusCheckRollup", []):
            state = check.get("conclusion") or check.get("state")
            check_name = check.get("context") or check.get("name") or "unknown"

            if state in ["FAILURE", "ERROR", "CANCELLED", "ACTION_REQUIRED"]:
                blockers.append(Blocker(
                    id=f"check-{check_name}",
                    type=BlockerType.FAILING_CHECK,
                    message=f"Check failed: {check_name}",
                    severity=BlockerSeverity.BLOCKER
                ))
            elif state in ["PENDING", "IN_PROGRESS", "QUEUED", None] and (
                check.get("status") != "COMPLETED" or state in ["PENDING", "IN_PROGRESS"]
            ):
                blockers.append(Blocker(
                    id=f"check-{check_name}",
                    type=BlockerType.PENDING_CHECK,
                    message=f"Check pending: {check_name}",
                    severity=BlockerSeverity.INFO
                ))

        # 4. Review Decision
        # reviewDecision is sticky: CHANGES_REQUESTED persists until the
        # reviewer explicitly re-approves, even after all threads are resolved.
        # Unresolved threads are the real live blockers; the formal approval
        # state is a separate, lower-priority signal.
        has_unresolved_threads = any(
            b.type == BlockerType.UNRESOLVED_THREAD for b in blockers
        )
        decision = data.get("reviewDecision")
        if decision == "CHANGES_REQUESTED":
            if not has_unresolved_threads:
                blockers.append(Blocker(
                    id="review-changes-requested",
                    type=BlockerType.NOT_APPROVED,
                    message="Re-approval needed (changes were requested, threads resolved)",
                    severity=BlockerSeverity.WARNING
                ))
        elif decision == "REVIEW_REQUIRED":
            blockers.append(Blocker(
                id="review-required",
                type=BlockerType.NOT_APPROVED,
                message="Review required",
                severity=BlockerSeverity.WARNING
            ))

        # 5. Mergeable state
        has_conflict = False
        if data.get("mergeable") == "CONFLICTING":
            has_conflict = True
            blockers.append(Blocker(
                id="merge-conflict",
                type=BlockerType.DIRTY_MERGE_STATE,
                message="Merge conflict detected",
                severity=BlockerSeverity.BLOCKER,
                is_primary=True
            ))

        # 6. Apply Blocking Matrix
        if has_conflict:
            final_blockers = []
            for b in blockers:
                if b.id == "merge-conflict":
                    final_blockers.append(b)
                else:
                    final_blockers.append(Blocker(
                        id=b.id,
                        type=b.type,
                        message=b.message,
                        severity=b.severity,
                        is_primary=False,
                        metadata=b.metadata
                    ))
            return final_blockers

        return blockers

    def get_pr_metadata(self, pr_id: int | None = None) -> dict[str, Any]:
        fields = ["number", "title", "author", "url"]
        data = self._run_gh_json(self._pr_view_args(pr_id, fields))
        owner, name = self._fetch_repo_info()
        data["repo_owner"] = owner
        data["repo_name"] = name
        return data
