from __future__ import annotations
import os
import json
from typing import Iterable, List, Optional
import requests
from draft_punks.ports.github import GitHubPort
from draft_punks.core.domain.github import PullRequest, ReviewThread, Comment

GQL_URL = "https://api.github.com/graphql"

class HttpGitHub(GitHubPort):
    def __init__(self, *, owner: str, repo: str, token: Optional[str] = None, session: Optional[requests.Session] = None):
        self._owner = owner
        self._repo = repo
        self._token = token or os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        self._session = session or requests.Session()
        if not self._token:
            raise RuntimeError('GH_TOKEN or GITHUB_TOKEN is required for HTTP adapter')

    def _headers(self) -> dict:
        return { 'Authorization': f'Bearer {self._token}', 'Accept': 'application/json' }

    def list_open_prs(self) -> List[PullRequest]:
        # Use GraphQL for consistency
        query = """
        query($o:String!, $n:String!) { repository(owner:$o, name:$n) {
          pullRequests(first:100, states:OPEN, orderBy:{field:UPDATED_AT, direction:DESC}) {
            nodes { number title headRefName }
          }
        }}
        """
        resp = self._session.post(GQL_URL, json={'query': query, 'variables': {'o': self._owner, 'n': self._repo}}, headers=self._headers(), timeout=30)
        data = resp.json() if resp.ok else {}
        prs: List[PullRequest] = []
        nodes = (((data.get('data') or {}).get('repository') or {}).get('pullRequests') or {}).get('nodes') or []
        for it in nodes:
            prs.append(PullRequest(number=it.get('number',0), head_ref=it.get('headRefName') or '', title=it.get('title') or ''))
        return prs

    def iter_review_threads(self, pr_number: int) -> Iterable[ReviewThread]:
        query = """
        query($o:String!, $n:String!, $num:Int!, $after:String) {
          repository(owner:$o,name:$n){ pullRequest(number:$num){
            reviewThreads(first:100, after:$after){ pageInfo{ hasNextPage endCursor }
              nodes{ id path comments(first:100){ nodes{ body author{ login } } } }
            }
          }}
        }
        """
        after = None
        while True:
            variables = {'o': self._owner, 'n': self._repo, 'num': pr_number, 'after': after}
            resp = self._session.post(GQL_URL, json={'query': query, 'variables': variables}, headers=self._headers(), timeout=30)
            data = resp.json() if resp.ok else {}
            pr = (((data.get('data') or {}).get('repository') or {}).get('pullRequest') or {})
            rt = (pr.get('reviewThreads') or {})
            for node in (rt.get('nodes') or []):
                comments = [Comment(body=(c.get('body') or ''), author=((c.get('author') or {}).get('login') or '')) for c in ((node.get('comments') or {}).get('nodes') or [])]
                yield ReviewThread(id=node.get('id') or '', path=node.get('path') or '', comments=comments)
            if not (rt.get('pageInfo') or {}).get('hasNextPage'):
                break
            after = (rt.get('pageInfo') or {}).get('endCursor')

    def post_reply(self, thread_id: str, body: str) -> bool:
        mutation = "mutation($id:ID!,$body:String!){ addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id, body:$body}){ clientMutationId } }"
        resp = self._session.post(GQL_URL, json={'query': mutation, 'variables': {'id': thread_id, 'body': body}}, headers=self._headers(), timeout=30)
        return bool(resp.ok)
