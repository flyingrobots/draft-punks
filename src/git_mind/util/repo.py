from __future__ import annotations

import os
import re
import subprocess
from typing import Tuple


_RE_SSH = re.compile(r'^git@github.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$')
_RE_HTTPS = re.compile(r'^https?://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$')


def owner_repo_from_env_or_git(cwd: str | None = None) -> Tuple[str, str]:
    owner = os.environ.get('DP_OWNER') or os.environ.get('GH_OWNER') or ''
    repo = os.environ.get('DP_REPO') or os.environ.get('GH_REPO') or ''
    if owner and repo:
        return owner, repo
    try:
        cp = subprocess.run(['git','remote','get-url','origin'], cwd=cwd, capture_output=True, text=True, check=True)
        url = (cp.stdout or '').strip()
    except Exception:
        url = ''
    for rx in (_RE_SSH, _RE_HTTPS):
        m = rx.match(url)
        if m:
            return m.group('owner'), m.group('repo')
    # fallback: directory name as repo; owner from USER
    try:
        cp2 = subprocess.run(['git','rev-parse','--show-toplevel'], cwd=cwd, capture_output=True, text=True, check=True)
        path = (cp2.stdout or '').strip()
    except Exception:
        path = os.getcwd()
    return os.environ.get('USER','unknown'), os.path.basename(path or os.getcwd())

