from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from git_mind.plumbing import MindRepo


def _run(args, cwd=None, input=None):
    return subprocess.run(args, cwd=cwd, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], cwd=str(repo))
    _run(["git", "config", "user.name", "Test User"], cwd=str(repo))
    _run(["git", "config", "user.email", "test@example.com"], cwd=str(repo))
    # initial empty commit
    _run(["git", "commit", "--allow-empty", "-m", "init"], cwd=str(repo))
    return repo


def test_write_snapshot_and_read_state(temp_repo: Path):
    mr = MindRepo(str(temp_repo))
    state = {"repo": {"owner": "acme", "name": "project"}}
    sha = mr.write_snapshot(session="main", state=state, op="repo.detect", args={"remote": "git@github.com:acme/project.git"})
    assert isinstance(sha, str) and len(sha) == 40
    # Read back state via git show
    cp = _run(["git", "show", "refs/mind/sessions/main:state.json"], cwd=str(temp_repo))
    got = json.loads(cp.stdout.decode())
    assert got == state
    # Commit message contains trailers
    cp2 = _run(["git", "log", "-1", "--pretty=%B", "refs/mind/sessions/main"], cwd=str(temp_repo))
    msg = cp2.stdout.decode()
    assert "DP-Op: repo.detect" in msg
    # Trailer state hash matches blob
    # extract DP-State-Hash
    h = None
    for line in msg.splitlines():
        if line.startswith("DP-State-Hash:"):
            h = line.split(":",1)[1].strip()
            break
    assert h
    # Verify blob exists
    cp3 = _run(["git", "cat-file", "-t", h], cwd=str(temp_repo))
    assert cp3.stdout.decode().strip() == "blob"

