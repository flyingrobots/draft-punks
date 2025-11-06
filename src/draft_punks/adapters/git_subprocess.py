from __future__ import annotations
import subprocess
from draft_punks.ports.git import GitPort

class GitSubprocess(GitPort):
    def is_commit(self, sha: str) -> bool:
        if not sha:
            return False
        try:
            subprocess.run(['git','cat-file','-e', f'{sha}^{{commit}}'], check=True, capture_output=True)
            return True
        except Exception:
            return False
    def current_branch(self) -> str:
        try:
            cp = subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'], capture_output=True, text=True, check=True)
            return (cp.stdout or '').strip()
        except Exception:
            return ''
    def has_upstream(self) -> bool:
        try:
            subprocess.run(['git','rev-parse','@{u}'], capture_output=True, text=True, check=True)
            return True
        except Exception:
            return False
    def push(self) -> bool:
        try:
            subprocess.run(['git','push'], check=True)
            return True
        except Exception:
            return False
    def push_set_upstream(self, remote: str, upstream_ref: str) -> bool:
        try:
            subprocess.run(['git','push','-u', remote, upstream_ref], check=True)
            return True
        except Exception:
            return False
    def add_and_commit(self, paths: list[str], message: str) -> bool:
        try:
            if not paths:
                return False
            subprocess.run(['git','add', *paths], check=True)
            subprocess.run(['git','commit','-m', message], check=True)
            return True
        except Exception:
            return False
