from __future__ import annotations
import json
from typing import Iterable, List, Optional, Callable
from types import SimpleNamespace
import subprocess
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
          id path comments(first:100){ nodes{ body author{ login } } }
        }
      }
    }
  }
}
"""

def _default_runner(argv: List[str]) -> SimpleNamespace:
    try:
        cp = subprocess.run(argv, capture_output=True, text=True)
        return SimpleNamespace(stdout=cp.stdout, returncode=cp.returncode)
    except Exception:
        # Fall back to an empty JSON so callers handle gracefully
        return SimpleNamespace(stdout="{}", returncode=1)


class GhCliGitHub(GitHubPort):
    def __init__(self, *, owner: str, repo: str, runner: Optional[Runner] = None):
        self._owner = owner
        self._repo = repo
        self._runner = runner or _default_runner

    def list_open_prs(self) -> List[PullRequest]:
        argv = ['gh','pr','list','-R', f'{self._owner}/{self._repo}','--state','open','--json','number,headRefName,title']
        cp = self._runner(argv)
        try:
            data = json.loads(cp.stdout or '[]')
        except Exception:
            data = []
        prs: List[PullRequest] = []
        for item in data or []:
            prs.append(PullRequest(number=item.get('number',0), head_ref=item.get('headRefName') or '', title=item.get('title') or ''))
        return prs

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

    def post_reply(self, thread_id: str, body: str) -> bool:
        mutation = (
            "mutation($id:ID!,$body:String!){ addPullRequestReviewThreadReply("
            "input:{pullRequestReviewThreadId:$id, body:$body}){ clientMutationId } }"
        )
        argv = ['gh','api','graphql','-f', f'query={mutation}','-F', f'id={thread_id}','-F', f'body={body}']
        try:
            cp = self._runner(argv)
            # Minimal validation
            return cp.returncode == 0
        except Exception:
            return False

    def resolve_thread(self, thread_id: str) -> bool:
        mutation = (
            "mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ clientMutationId } }"
        )
        argv = ['gh','api','graphql','-f', f'query={mutation}','-F', f'id={thread_id}']
        try:
            cp = self._runner(argv)
            return cp.returncode == 0
        except Exception:
            return False

    def iter_review_threads(self, pr_number: int) -> Iterable[ReviewThread]:
        after = None
        while True:
            resp = self._gh_graphql(_GQL_THREADS, {'num': pr_number, 'after': after})
            pr = (((resp.get('data') or {}).get('repository') or {}).get('pullRequest') or {})
            rt = (pr.get('reviewThreads') or {})
            for node in (rt.get('nodes') or []):
                comments = [Comment(body=(c.get('body') or ''), author=((c.get('author') or {}).get('login') or '')) for c in ((node.get('comments') or {}).get('nodes') or [])]
                yield ReviewThread(id=node.get('id') or '', path=node.get('path') or '', comments=comments)
            if not (rt.get('pageInfo') or {}).get('hasNextPage'):
                break
            after = (rt.get('pageInfo') or {}).get('endCursor')
