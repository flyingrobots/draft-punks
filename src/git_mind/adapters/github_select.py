from __future__ import annotations

import os
from .github_http import HttpGitHub
from .github_ghcli import GhCliGitHub


def select(owner: str, repo: str):
    """Choose a GitHub adapter based on available credentials.

    If GH_TOKEN/GITHUB_TOKEN is set, prefer HTTP (GraphQL). Otherwise use gh CLI.
    """
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            return HttpGitHub(owner=owner, repo=repo, token=token)
        except Exception:
            pass
    return GhCliGitHub(owner=owner, repo=repo)

