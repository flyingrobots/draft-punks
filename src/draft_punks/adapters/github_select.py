from __future__ import annotations
import os
from typing import Tuple
from draft_punks.adapters.github_http import HttpGitHub
from draft_punks.adapters.github_ghcli import GhCliGitHub, _default_runner


def select(owner: str, repo: str):
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        try:
            return HttpGitHub(owner=owner, repo=repo, token=token)
        except Exception:
            pass
    # Use real subprocess-backed runner for gh CLI
    return GhCliGitHub(owner=owner, repo=repo, runner=_default_runner)
