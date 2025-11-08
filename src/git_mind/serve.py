from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .plumbing import MindRepo
from .util.repo import owner_repo_from_env_or_git
from .adapters.github_select import select as select_github
from git_mind.domain.github import PullRequest


VERSION = "0.1"


def _ok(id_: Any, result: Dict[str, Any], state_ref: str | None) -> Dict[str, Any]:
    return {"id": id_, "ok": True, "result": result, "state_ref": state_ref}


def _err(id_: Any, code: str, message: str, state_ref: str | None, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    return {"id": id_, "ok": False, "error": err, "state_ref": state_ref}


def _state_guard(mr: MindRepo, session: str | None, expect: str | None) -> Tuple[bool, str | None]:
    head = mr.head(session=session)
    if expect and head and expect != head:
        return False, head
    return True, head


def handle_command(mr: MindRepo, payload: Dict[str, Any], session: str | None) -> Dict[str, Any]:
    id_ = payload.get("id")
    cmd = (payload.get("cmd") or "").strip()
    args = payload.get("args") or {}
    expect_state = payload.get("expect_state")

    # Read-only commands --------------------------------------------------
    if cmd in ("mind.hello", "hello"):
        owner, repo = owner_repo_from_env_or_git(mr.root)
        return _ok(id_, {"version": VERSION, "repo": {"owner": owner, "name": repo}, "session": session or mr.default_session}, mr.head(session=session))

    if cmd == "state.show":
        data = mr.read_state(session=session)
        return _ok(id_, data, mr.head(session=session))

    # Mutating commands (CAS guarded if expect_state provided) -----------
    if cmd == "repo.detect":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        owner, repo = owner_repo_from_env_or_git(mr.root)
        state = mr.read_state(session=session)
        state.setdefault("repo", {})
        state["repo"].update({"owner": owner, "name": repo})
        commit = mr.write_snapshot(session=session, state=state, op="repo.detect", args={"source": "git"})
        return _ok(id_, {"owner": owner, "name": repo}, commit)

    if cmd == "pr.list":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        owner, repo = owner_repo_from_env_or_git(mr.root)
        gh = select_github(owner, repo)
        prs: list[PullRequest] = gh.list_open_prs()
        cache = [{"number": p.number, "head": p.head_ref, "title": p.title} for p in prs]
        state = mr.read_state(session=session)
        state.setdefault("repo", {"owner": owner, "name": repo})
        state["pr_cache"] = cache
        commit = mr.write_snapshot(session=session, state=state, op="pr.list", args={"count": len(cache)})
        return _ok(id_, {"items": cache, "total": len(cache)}, commit)

    if cmd == "pr.select":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        number = args.get("number")
        if not isinstance(number, int):
            return _err(id_, "INVALID_ARGS", "number (int) is required", head)
        state = mr.read_state(session=session)
        state.setdefault("selection", {})
        state["selection"]["pr"] = number
        commit = mr.write_snapshot(session=session, state=state, op="pr.select", args={"number": number})
        return _ok(id_, {"current_pr": number}, commit)

    return _err(id_, "UNKNOWN_COMMAND", f"unknown cmd: {cmd}", mr.head(session=session))

