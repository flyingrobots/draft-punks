import json
import subprocess
from typing import Dict, Any, List, Optional
from ...core.ports.github_port import GitHubPort
from ...core.domain.blocker import Blocker, BlockerType, BlockerSeverity

class GhCliAdapter(GitHubPort):
    """Adapter for GitHub using the 'gh' CLI."""
    
    def __init__(self, repo_owner: Optional[str] = None, repo_name: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.repo = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else None

    def _run_gh(self, args: List[str]) -> str:
        """Execute a 'gh' command and return stdout."""
        cmd = ["gh"] + args
        if self.repo:
            cmd += ["-R", self.repo]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def _run_gh_json(self, args: List[str]) -> Dict[str, Any]:
        """Execute a 'gh' command and return parsed JSON output."""
        return json.loads(self._run_gh(args))

    def get_head_sha(self, pr_id: Optional[int] = None) -> str:
        fields = ["headRefOid"]
        data = self._run_gh_json(["pr", "view", str(pr_id) if pr_id else "", "--json", ",".join(fields)])
        return data["headRefOid"]

    def _fetch_repo_info(self) -> tuple[str, str]:
        """Fetch owner and name for the current repo if not provided."""
        if self.repo_owner and self.repo_name:
            return self.repo_owner, self.repo_name
        data = self._run_gh_json(["repo", "view", "--json", "owner,name"])
        return data["owner"]["login"], data["name"]

    def fetch_blockers(self, pr_id: Optional[int] = None) -> List[Blocker]:
        # 1. Fetch basic PR data
        fields = ["statusCheckRollup", "reviewDecision", "mergeable", "number"]
        data = self._run_gh_json(["pr", "view", str(pr_id) if pr_id else "", "--json", ",".join(fields)])
        actual_pr_id = data["number"]
        
        blockers = []
        
        # 2. Fetch Unresolved threads via GraphQL (since 'gh pr view --json' lacks it)
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
            ])
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
                            id=f"thread-{first_comment['id']}",
                            type=BlockerType.UNRESOLVED_THREAD,
                            message=msg
                        ))
        except Exception as e:
            # Fallback or log error
            blockers.append(Blocker(
                id="error-threads",
                type=BlockerType.OTHER,
                message=f"Warning: Could not fetch review threads: {e}",
                severity=BlockerSeverity.WARNING
            ))

        # 3. Status checks
        for check in data.get("statusCheckRollup", []):
            # CheckRun uses 'conclusion', StatusContext uses 'state'
            state = check.get("conclusion") or check.get("state")
            name = check.get("context") or check.get("name")
            
            if state in ["FAILURE", "ERROR", "CANCELLED", "ACTION_REQUIRED"]:
                blockers.append(Blocker(
                    id=f"check-{name}",
                    type=BlockerType.FAILING_CHECK,
                    message=f"Check failed: {name}",
                    severity=BlockerSeverity.BLOCKER
                ))
            elif state in ["PENDING", "IN_PROGRESS", "QUEUED", None]:
                # If status is not COMPLETED, it's pending
                if check.get("status") != "COMPLETED" or state in ["PENDING", "IN_PROGRESS"]:
                    blockers.append(Blocker(
                        id=f"check-{name}",
                        type=BlockerType.PENDING_CHECK,
                        message=f"Check pending: {name}",
                        severity=BlockerSeverity.INFO
                    ))
        
        # 4. Review Decision
        decision = data.get("reviewDecision")
        if decision == "CHANGES_REQUESTED":
            blockers.append(Blocker(
                id="review-changes-requested",
                type=BlockerType.NOT_APPROVED,
                message="Reviewer requested changes",
                severity=BlockerSeverity.BLOCKER
            ))
        elif decision == "REVIEW_REQUIRED":
            blockers.append(Blocker(
                id="review-required",
                type=BlockerType.NOT_APPROVED,
                message="Review required",
                severity=BlockerSeverity.WARNING
            ))
            
        # 5. Mergeable state
        if data.get("mergeable") == "CONFLICTING":
            blockers.append(Blocker(
                id="merge-conflict",
                type=BlockerType.DIRTY_MERGE_STATE,
                message="Merge conflict detected",
                severity=BlockerSeverity.BLOCKER
            ))
            
        return blockers

    def get_pr_metadata(self, pr_id: Optional[int] = None) -> Dict[str, Any]:
        fields = ["number", "title", "author", "url"]
        return self._run_gh_json(["pr", "view", str(pr_id) if pr_id else "", "--json", ",".join(fields)])
