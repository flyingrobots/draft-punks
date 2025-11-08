from __future__ import annotations

from pathlib import Path
import subprocess
import pytest

from git_mind.plumbing import MindRepo
from git_mind.serve import handle_command


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


def test_llm_send_debug_success(temp_repo: Path):
    mr = MindRepo(str(temp_repo))
    # Prepare minimal repo state
    out = handle_command(mr, {"id": 1, "cmd": "repo.detect", "args": {}}, session="main")
    state_ref = out["state_ref"]
    # Send debug success
    out = handle_command(
        mr,
        {
            "id": 2,
            "cmd": "llm.send",
            "args": {"thread_id": "t1", "prompt": "hello", "debug": "success"},
            "expect_state": state_ref,
        },
        session="main",
    )
    assert out["ok"] is True
    res = out["result"]
    assert res.get("success") is True
    assert res.get("commits") == ["deadbeef"]
    assert "prompt" in res and res["prompt"] == "hello"


def test_llm_send_debug_fail(temp_repo: Path):
    mr = MindRepo(str(temp_repo))
    out = handle_command(mr, {"id": 1, "cmd": "repo.detect", "args": {}}, session="main")
    out = handle_command(
        mr,
        {
            "id": 2,
            "cmd": "llm.send",
            "args": {"thread_id": "t1", "prompt": "hello", "debug": "fail", "error": "boom"},
            "expect_state": out["state_ref"],
        },
        session="main",
    )
    assert out["ok"] is False
    assert out["error"]["code"] == "LLM_DEBUG_FAIL"
    assert "boom" in out["error"]["message"]

