from __future__ import annotations
from typing import Iterable
from draft_punks.ports.github import GitHubPort
from draft_punks.ports.logging import LoggingPort
from draft_punks.core.domain.github import Comment


def flatten_review_threads(gh: GitHubPort, *, pr_number: int, log: LoggingPort) -> Iterable[Comment]:
    # stream comments in page/thread order
    count = 0
    for thread in gh.iter_review_threads(pr_number):
        for c in thread.comments:
            count += 1
            yield c
    log.info(f"flattened {count} comments from review threads")
