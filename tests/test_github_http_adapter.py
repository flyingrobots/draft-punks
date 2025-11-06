from types import SimpleNamespace
from draft_punks.adapters.github_http import HttpGitHub

class StubSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []
    def post(self, url, json=None, headers=None, timeout=30):
        self.calls.append((url, json))
        data = self.payloads.pop(0) if self.payloads else {}
        return SimpleNamespace(ok=True, json=lambda: data)


def _prs(nodes):
    return {'data': {'repository': {'pullRequests': {'nodes': nodes}}}}

def _threads(nodes, has_next=False, end='CUR'):
    return {'data': {'repository': {'pullRequest': {'reviewThreads': {'nodes': nodes, 'pageInfo': {'hasNextPage': has_next, 'endCursor': end}}}}}}


def test_http_list_open_prs_parses_nodes(monkeypatch):
    sess = StubSession([_prs([{'number': 1, 'title': 't', 'headRefName': 'h'}])])
    gh = HttpGitHub(owner='o', repo='r', token='t', session=sess)
    prs = gh.list_open_prs()
    assert prs and prs[0].number == 1 and prs[0].head_ref == 'h'


def test_http_iter_review_threads_pages(monkeypatch):
    page1 = _threads([{'id':'T1','path':'a','comments':{'nodes':[{'body':'b1','author':{'login':'x'}}]}}], has_next=True, end='C1')
    page2 = _threads([{'id':'T2','path':'b','comments':{'nodes':[{'body':'b2','author':{'login':'y'}}]}}], has_next=False)
    sess = StubSession([page1, page2])
    gh = HttpGitHub(owner='o', repo='r', token='t', session=sess)
    ids = [th.id for th in gh.iter_review_threads(1)]
    assert ids == ['T1','T2']
