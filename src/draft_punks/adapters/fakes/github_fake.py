from __future__ import annotations
from typing import Iterable, List
from draft_punks.ports.github import GitHubPort
from draft_punks.core.domain.github import PullRequest, ReviewThread, Comment

class FakeGitHub(GitHubPort):
    def __init__(self, pages: List[dict]):
        self._pages = pages
    def list_open_prs(self) -> List[PullRequest]:
        return []
    def iter_review_threads(self, pr_number: int) -> Iterable[ReviewThread]:
        for page in self._pages:
            for t in page.get('threads', []):
                yield ReviewThread(
                    id=t['id'],
                    path=t.get('path',''),
                    comments=[Comment(body=c.get('body','')) for c in t.get('comments', [])]
                )
            if not page.get('has_next'):
                break
