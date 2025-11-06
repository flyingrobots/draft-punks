from __future__ import annotations
import json
from typing import Iterable, List, Optional, Callable
from types import SimpleNamespace
from draft_punks.ports.github import GitHubPort
from draft_punks.core.domain.github import PullRequest, ReviewThread, Comment

Runner = Callable[[List[str]], SimpleNamespace]

_GQL_THREADS = """
query($o:String!, $n:String!, $num:Int!, $after:String){
  repository(owner:$o, name:$n){
    pullRequest(number:$num){
      reviewThreads(first:100, after:$after){
        pageInfo{ hasNextPage endCursor }
        nodes{
          id path comments(first:100){ nodes{ body } }
        }
      }
    }
  }
}
"""

class GhCliGitHub(GitHubPort):
    def __init__(self, *, owner: str, repo: str, runner: Optional[Runner] = None):
        self._owner = owner
        self._repo = repo
        self._runner = runner or (lambda argv: SimpleNamespace(stdout="{}", returncode=0))

    def list_open_prs(self) -> List[PullRequest]:
        return []

    def _gh_graphql(self, query: str, vars: dict) -> dict:
        argv = ['gh','api','graphql','-F',f"o={self._owner}",'-F',f"n={self._repo}",'-F',f"num={vars['num']}"]
        after = vars.get('after')
        if after is None:
            argv.extend(['-F','after=null'])
        else:
            argv.extend(['-F',f"after={after}"])
        argv.extend(['-f', f"query={query}"])
        cp = self._runner(argv)
        txt = cp.stdout or '{}'
        try:
            return json.loads(txt)
        except Exception:
            return {}

    def iter_review_threads(self, pr_number: int) -> Iterable[ReviewThread]:
        after = None
        while True:
            resp = self._gh_graphql(_GQL_THREADS, {'num': pr_number, 'after': after})
            pr = (((resp.get('data') or {}).get('repository') or {}).get('pullRequest') or {})
            rt = (pr.get('reviewThreads') or {})
            for node in (rt.get('nodes') or []):
                comments = [Comment(body=(c.get('body') or '')) for c in ((node.get('comments') or {}).get('nodes') or [])]
                yield ReviewThread(id=node.get('id') or '', path=node.get('path') or '', comments=comments)
            if not (rt.get('pageInfo') or {}).get('hasNextPage'):
                break
            after = (rt.get('pageInfo') or {}).get('endCursor')
