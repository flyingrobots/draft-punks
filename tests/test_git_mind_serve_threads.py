from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import subprocess

import pytest

from git_mind.plumbing import MindRepo
from git_mind.serve import handle_command
from git_mind.domain.github import PullRequest, ReviewThread, Comment


def _run(args, cwd=None, input=None):
    return subprocess.run(args, cwd=cwd, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init"], cwd=str(repo))
    _run(["git", "config", "user.name", "Test User"], cwd=str(repo))
    _run(["git", "config", "user.email", "test@example.com"], cwd=str(repo))
    _run(["git", "commit", "--allow-empty", "-m", "init"], cwd=str(repo))
    return repo


class _FakeGH:
    def __init__(self):
        self._prs = [PullRequest(number=1, head_ref="deadbeef", title="One")]
        self._threads = [
            ReviewThread(id="t1", path="a.py", comments=[Comment(body="c1")]),
            ReviewThread(id="t2", path="b.py", comments=[Comment(body="c2"), Comment(body="c3")]),
        ]

    def list_open_prs(self):
        return self._prs

    def iter_review_threads(self, pr_number: int):
        assert pr_number == 1
        for t in self._threads:
            yield t

    def post_reply(self, thread_id: str, body: str) -> bool:
        return True

    def resolve_thread(self, thread_id: str) -> bool:
        return True


def test_thread_list_and_select_and_show(monkeypatch, tmp_path: Path, temp_repo: Path):
    mr = MindRepo(str(temp_repo))

    # Patch the GitHub adapter selector used inside handle_command
    import git_mind.serve as serve

    monkeypatch.setattr(serve, "select_github", lambda owner, repo: _FakeGH())

    # Detect repo (mutates state)
    out = handle_command(mr, {"id": 1, "cmd": "repo.detect", "args": {}}, session="main")
    assert out["ok"] is True and out["state_ref"]

    # Choose PR 1
    out = handle_command(mr, {"id": 2, "cmd": "pr.select", "args": {"number": 1}, "expect_state": out["state_ref"]}, session="main")
    assert out["ok"] is True and out["result"]["current_pr"] == 1
    state_ref = out["state_ref"]

    # List threads (should reflect 2 items)
    out = handle_command(mr, {"id": 3, "cmd": "thread.list", "args": {}, "expect_state": state_ref}, session="main")
    assert out["ok"] is True
    items = out["result"]["items"]
    assert len(items) == 2
    assert {i["id"] for i in items} == {"t1", "t2"}
    state_ref = out["state_ref"]

    # Select a specific thread
    out = handle_command(mr, {"id": 4, "cmd": "thread.select", "args": {"id": "t1"}, "expect_state": state_ref}, session="main")
    assert out["ok"] is True
    state_ref = out["state_ref"]

    # Show selected thread (should echo details)
    out = handle_command(mr, {"id": 5, "cmd": "thread.show", "args": {}, "expect_state": state_ref}, session="main")
    assert out["ok"] is True
    result = out["result"]
    assert result["id"] == "t1"
    assert result["path"] == "a.py"
    assert result["comment_count"] == 1

