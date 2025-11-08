from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional, List


def _run(args, cwd: Optional[str] = None, input: Optional[bytes] = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def _hash_blob(data: bytes, cwd: str) -> str:
    cp = _run(["git", "hash-object", "-w", "--stdin"], cwd=cwd, input=data)
    return cp.stdout.decode().strip()


def _make_tree(entries: Dict[str, str], cwd: str) -> str:
    """Create a tree containing only files at the root level.

    entries: mapping of filename -> blob_sha
    Note: minimal implementation for initial milestones; does not create subdirectories.
    """
    lines = []
    for name, blob in entries.items():
        lines.append(f"100644 blob {blob}\t{name}\n")
    data = "".join(lines).encode()
    cp = _run(["git", "mktree"], cwd=cwd, input=data)
    return cp.stdout.decode().strip()


def _commit_tree(tree_sha: str, message: str, parent: Optional[str], cwd: str) -> str:
    args = ["git", "commit-tree", tree_sha]
    if parent:
        args += ["-p", parent]
    args += ["-m", message]
    cp = _run(args, cwd=cwd)
    return cp.stdout.decode().strip()


def _rev_parse(ref: str, cwd: str) -> Optional[str]:
    try:
        cp = _run(["git", "rev-parse", "-q", "--verify", ref], cwd=cwd)
        return cp.stdout.decode().strip()
    except subprocess.CalledProcessError:
        return None


def _update_ref(ref: str, new: str, old: Optional[str], msg: str, cwd: str) -> None:
    args = ["git", "update-ref", "--create-reflog", ref, new]
    if old:
        args.append(old)
    if msg:
        args += ["-m", msg]
    _run(args, cwd=cwd)


def _delete_ref(ref: str, cwd: str) -> None:
    try:
        _run(["git", "update-ref", "-d", ref], cwd=cwd)
    except subprocess.CalledProcessError:
        pass


def _for_each_ref(prefix: str, cwd: str) -> List[str]:
    try:
        cp = _run(["git", "for-each-ref", "--format=%(refname)", prefix], cwd=cwd)
        return [line.strip() for line in cp.stdout.decode().splitlines() if line.strip()]
    except subprocess.CalledProcessError:
        return []


@dataclass
class MindRepo:
    root: str  # path to repo working tree

    @property
    def default_session(self) -> str:
        return "main"

    def write_snapshot(self, *, session: Optional[str] = None, state: Dict, op: str, args: Dict | None = None, result: str = "ok") -> str:
        """Write a minimal snapshot commit under refs/mind/sessions/<session>.

        Returns the new commit sha.
        """
        sess = session or self.default_session
        cwd = self.root
        # Serialize state.json
        state_bytes = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
        blob_state = _hash_blob(state_bytes, cwd)
        tree = _make_tree({"state.json": blob_state}, cwd)
        # Build commit message with trailers
        trailers = []
        trailers.append(f"DP-Op: {op}")
        if args:
            # encode as key=value pairs joined by & for grepability
            kv = "&".join([f"{k}={v}" for k, v in args.items()])
            trailers.append(f"DP-Args: {kv}")
        trailers.append(f"DP-Result: {result}")
        trailers.append(f"DP-State-Hash: {blob_state}")
        trailers.append("DP-Version: 0")
        message = f"mind: {op}\n\n" + "\n".join(trailers) + "\n"
        parent = _rev_parse(f"refs/mind/sessions/{sess}", cwd)
        commit = _commit_tree(tree, message, parent, cwd)
        _update_ref(f"refs/mind/sessions/{sess}", commit, parent, f"mind: {op}", cwd)
        return commit

    def read_state(self, *, session: Optional[str] = None) -> Dict:
        sess = session or self.default_session
        ref = f"refs/mind/sessions/{sess}:state.json"
        try:
            cp = _run(["git", "show", ref], cwd=self.root)
        except subprocess.CalledProcessError:
            return {}
        try:
            return json.loads(cp.stdout.decode())
        except Exception:
            return {}

    def head(self, *, session: Optional[str] = None) -> Optional[str]:
        sess = session or self.default_session
        return _rev_parse(f"refs/mind/sessions/{sess}", self.root)

    # --- maintenance -----------------------------------------------------

    def is_worktree_clean(self) -> bool:
        """Return True if there are no staged/unstaged or untracked changes."""
        try:
            _run(["git", "diff", "--quiet"], cwd=self.root)
            _run(["git", "diff", "--quiet", "--cached"], cwd=self.root)
            cp = _run(["git", "ls-files", "--others", "--exclude-standard"], cwd=self.root)
            return cp.stdout.decode().strip() == ""
        except subprocess.CalledProcessError:
            return False

    def nuke_refs(self, prefix: str = "refs/mind/") -> List[str]:
        """Delete all mind refs (under prefix). Returns list of deleted refs."""
        refs = _for_each_ref(prefix, self.root)
        for r in refs:
            _delete_ref(r, self.root)
        return refs
