from __future__ import annotations
import os, re, subprocess
from typing import Tuple

_RE_SSH = re.compile(r'^git@github.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$')
_RE_HTTPS = re.compile(r'^https?://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$')


def owner_repo_from_env_or_git() -> Tuple[str,str]:
    owner = os.environ.get('DP_OWNER')
    repo = os.environ.get('DP_REPO')
    if owner and repo:
        return owner, repo
    try:
        cp = subprocess.run(['git','remote','get-url','origin'], capture_output=True, text=True, check=True)
        url = (cp.stdout or '').strip()
    except Exception:
        url = ''
    for rx in (_RE_SSH,_RE_HTTPS):
        m = rx.match(url)
        if m:
            return m.group('owner'), m.group('repo')
    return os.environ.get('USER','unknown'), os.path.basename(os.getcwd())
