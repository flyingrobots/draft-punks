from dataclasses import dataclass
from typing import List

from draft_punks.core.services.github import flatten_review_threads
from draft_punks.adapters.fakes.github_fake import FakeGitHub
from draft_punks.ports.logging import LoggingPort

class LogNull(LoggingPort):
    def info(self, msg: str): pass
    def warn(self, msg: str): pass
    def error(self, msg: str): pass
    def markdown(self, md: str): pass


def test_flatten_threads_pages_and_comments_in_order():
    # two pages, first page 2 threads, second page 1 thread
    pages = [
        {
            'threads': [
                {'id': 'T1', 'path': 'a.c', 'comments': [{'body': 'c1'}, {'body': 'c2'}]},
                {'id': 'T2', 'path': 'b.c', 'comments': [{'body': 'c3'}]},
            ],
            'has_next': True,
        },
        {
            'threads': [
                {'id': 'T3', 'path': 'c.c', 'comments': [{'body': 'c4'}]},
            ],
            'has_next': False,
        },
    ]
    gh = FakeGitHub(pages)
    log = LogNull()
    comments = list(flatten_review_threads(gh, pr_number=74, log=log))
    bodies = [c.body for c in comments]
    assert bodies == ['c1','c2','c3','c4']
