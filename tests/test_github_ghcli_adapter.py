import json
from types import SimpleNamespace
from draft_punks.adapters.github_ghcli import GhCliGitHub


class StubRunner:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []
    def __call__(self, argv, text=True):
        self.calls.append(argv)
        data = self.payloads.pop(0)
        return SimpleNamespace(stdout=json.dumps(data), returncode=0)


def _page(nodes, has_next, end_cursor=None):
    return {
        'data': {
            'repository': {
                'pullRequest': {
                    'reviewThreads': {
                        'nodes': nodes,
                        'pageInfo': {
                            'hasNextPage': has_next,
                            'endCursor': end_cursor or 'CUR'
                        }
                    }
                }
            }
        }
    }


def test_iter_review_threads_pages_and_yields_threads_in_order():
    # two pages
    p1 = _page([
        {'id':'T1','path':'a.c','comments':{'nodes':[{'body':'c1'},{'body':'c2'}]}},
        {'id':'T2','path':'b.c','comments':{'nodes':[{'body':'c3'}]}},
    ], True, 'CUR1')
    p2 = _page([
        {'id':'T3','path':'c.c','comments':{'nodes':[{'body':'c4'}]}},
    ], False, None)
    runner = StubRunner([p1,p2])
    gh = GhCliGitHub(owner='o', repo='r', runner=runner)
    threads = list(gh.iter_review_threads(pr_number=74))
    assert [t.id for t in threads] == ['T1','T2','T3']
    assert [c.body for t in threads for c in t.comments] == ['c1','c2','c3','c4']
