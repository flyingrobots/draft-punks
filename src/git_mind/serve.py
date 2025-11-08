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

    # --- Threads -------------------------------------------------------------
    if cmd == "thread.list":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        state = mr.read_state(session=session)
        sel = state.get("selection", {})
        pr_number = sel.get("pr")
        if not isinstance(pr_number, int):
            return _err(id_, "INVALID_ARGS", "no PR selected; run pr.select first", head)
        owner, repo = owner_repo_from_env_or_git(mr.root)
        gh = select_github(owner, repo)
        items = []
        for th in gh.iter_review_threads(pr_number):
            # Minimal projection for API; more fields can be added later
            items.append({
                "id": getattr(th, "id", None),
                "path": getattr(th, "path", None),
                "comment_count": len(getattr(th, "comments", []) or []),
            })
        state.setdefault("thread_cache", {})
        state["thread_cache"][str(pr_number)] = items
        commit = mr.write_snapshot(session=session, state=state, op="thread.list", args={"count": len(items)})
        return _ok(id_, {"items": items, "total": len(items)}, commit)

    if cmd == "thread.select":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        tid = args.get("id")
        if not isinstance(tid, str) or not tid:
            return _err(id_, "INVALID_ARGS", "id (str) is required", head)
        state = mr.read_state(session=session)
        state.setdefault("selection", {})
        state["selection"]["thread_id"] = tid
        commit = mr.write_snapshot(session=session, state=state, op="thread.select", args={"id": tid})
        return _ok(id_, {"current_thread": tid}, commit)

    if cmd == "thread.show":
        # read-only helper, but still allowed to be CAS-guarded by caller
        state = mr.read_state(session=session)
        sel = state.get("selection", {})
        tid = args.get("id") or sel.get("thread_id")
        pr_number = sel.get("pr")
        if not tid:
            return _err(id_, "INVALID_ARGS", "no thread selected; pass args.id or run thread.select", mr.head(session=session))
        if not isinstance(pr_number, int):
            return _err(id_, "INVALID_ARGS", "no PR selected; run pr.select first", mr.head(session=session))
        cache = (state.get("thread_cache") or {}).get(str(pr_number)) or []
        found = next((t for t in cache if t.get("id") == tid), None)
        if not found:
            return _err(id_, "NOT_FOUND", f"thread id not in cache for PR {pr_number}", mr.head(session=session))
        return _ok(id_, found, mr.head(session=session))

    # --- LLM -----------------------------------------------------------------
    if cmd == "llm.send":
        ok, head = _state_guard(mr, session, expect_state)
        if not ok:
            return _err(id_, "STATE_MISMATCH", "expect_state does not match current head", head)
        debug = args.get("debug")
        prompt = args.get("prompt", "")
        if debug == "success":
            state = mr.read_state(session=session)
            commit = mr.write_snapshot(session=session, state=state, op="llm.send", args={"mode": "debug", "result": "success"})
            return _ok(id_, {"success": True, "commits": ["deadbeef"], "error": "", "prompt": prompt}, commit)
        if debug == "fail":
            msg = args.get("error") or "debug failure"
            return _err(id_, "LLM_DEBUG_FAIL", msg, mr.head(session=session))
        return _err(id_, "INVALID_ARGS", "llm.send requires debug=success|fail in this build", mr.head(session=session))

    return _err(id_, "UNKNOWN_COMMAND", f"unknown cmd: {cmd}", mr.head(session=session))
