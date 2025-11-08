from __future__ import annotations

import json
import os
from pathlib import Path
import typer

from .plumbing import MindRepo
from .adapters.github_select import select as select_github
from .util.repo import owner_repo_from_env_or_git
from git_mind.domain.github import PullRequest
from .serve import handle_command

app = typer.Typer(help="git mind — conversational, ref-native state for your repo")


def _repo_root() -> str:
    import subprocess
    try:
        cp = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return cp.stdout.decode().strip()
    except Exception:
        raise typer.Exit(code=128)


@app.command()
def state_show(session: str = typer.Option(None, help="Session name")):
    """Show merged state (currently just snapshot state.json)."""
    mr = MindRepo(_repo_root())
    data = mr.read_state(session=session)
    typer.echo(json.dumps(data, indent=2, sort_keys=True))


@app.command()
def session_new(name: str = typer.Argument("main")):
    """Create a new session (ref) if not present by writing an initial empty snapshot."""
    mr = MindRepo(_repo_root())
    if mr.head(session=name):
        typer.echo(f"session exists: {name}")
        raise typer.Exit(code=0)
    mr.write_snapshot(session=name, state={}, op="session.new", args={"name": name})
    typer.echo(f"created session: {name}")


@app.command()
def repo_detect(session: str = typer.Option(None, help="Session name")):
    """Detect owner/repo from git remote and write to state."""
    # Minimal detector; prefer remote origin URL
    import subprocess, re
    root = _repo_root()
    try:
        cp = subprocess.run(["git", "remote", "get-url", "origin"], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        url = cp.stdout.decode().strip()
    except Exception:
        url = ""
    owner = repo = ""
    m = re.match(r"^git@github.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\\.git)?$", url)
    if not m:
        m = re.match(r"^https?://github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\\.git)?$", url)
    if m:
        owner = m.group("owner"); repo = m.group("repo")
    mr = MindRepo(root)
    state = mr.read_state(session=session)
    state.setdefault("repo", {})
    state["repo"].update({"owner": owner, "name": repo, "remote_url": url})
    commit = mr.write_snapshot(session=session, state=state, op="repo.detect", args={"remote": url})
    typer.echo(commit)


@app.command()
def nuke(
    yes: bool = typer.Option(False, "--yes", help="Proceed without prompt"),
    session: str = typer.Option("main", help="Create this session after nuking"),
):
    """Delete all refs/mind/* and start a fresh mind history (safe for code branches).

    Requires a clean working tree (no staged/unstaged or untracked files).
    """
    mr = MindRepo(_repo_root())
    if not mr.is_worktree_clean():
        typer.echo("worktree is not clean (staged/unstaged or untracked files present)")
        raise typer.Exit(code=2)
    if not yes:
        typer.confirm("This will delete all refs/mind/* in this repo. Continue?", abort=True)
    deleted = mr.nuke_refs()
    typer.echo(f"deleted {len(deleted)} mind refs")
    # seed fresh session
    commit = mr.write_snapshot(session=session, state={}, op="mind.init", args={"session": session})
    typer.echo(f"initialized refs/mind/sessions/{session} at {commit}")


def _fzf(items: list[str]) -> str | None:
    """Run fzf to pick an item; return the selected line or None.

    If fzf is not available, return None.
    """
    from shutil import which
    if which('fzf') is None:
        return None
    import subprocess
    try:
        cp = subprocess.run(['fzf', '-1', '-0'], input=("\n".join(items)+"\n").encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return cp.stdout.decode().strip()
    except Exception:
        return None


def _repo_root_and_state() -> tuple[MindRepo, dict]:
    mr = MindRepo(_repo_root())
    return mr, mr.read_state()


@app.command()
def pr_list(format: str = typer.Option('table', '--format', help='table|json'), session: str = typer.Option(None, help='Session name')):
    """List open PRs from GitHub and cache them in mind state."""
    root = _repo_root()
    owner, repo = owner_repo_from_env_or_git(root)
    gh = select_github(owner, repo)
    prs: list[PullRequest] = gh.list_open_prs()
    # Cache into state
    mr, state = _repo_root_and_state()
    cache = [{"number": p.number, "head": p.head_ref, "title": p.title} for p in prs]
    state.setdefault('repo', {"owner": owner, "name": repo})
    state['pr_cache'] = cache
    mr.write_snapshot(session=session, state=state, op='pr.list', args={"count": len(cache)})
    if format == 'json':
        typer.echo(json.dumps(cache, indent=2))
    else:
        for p in prs:
            typer.echo(f"- #{p.number} ({p.head_ref}) {p.title}")


@app.command()
def pr_pick(session: str = typer.Option(None, help='Session name')):
    """Interactively pick a PR via fzf (if available), otherwise fall back to numbered prompt."""
    root = _repo_root()
    owner, repo = owner_repo_from_env_or_git(root)
    gh = select_github(owner, repo)
    prs: list[PullRequest] = gh.list_open_prs()
    lines = [f"#{p.number} ({p.head_ref}) {p.title}" for p in prs]
    chosen = _fzf(lines)
    idx = -1
    if chosen:
        import re
        m = re.search(r"#(\d+)", chosen)
        if m:
            num = int(m.group(1))
            for i, p in enumerate(prs):
                if p.number == num:
                    idx = i; break
    if idx < 0:
        # fallback: simple numeric choice
        for i, line in enumerate(lines, 1):
            typer.echo(f"{i:2d}. {line}")
        sel = typer.prompt("Select PR #", default="1")
        try:
            n = int(sel)
            idx = n - 1
        except Exception:
            raise typer.Exit(code=2)
    if not (0 <= idx < len(prs)):
        raise typer.Exit(code=2)
    pr = prs[idx]
    # update state selection
    mr, state = _repo_root_and_state()
    state.setdefault('selection', {})
    state['selection']['pr'] = pr.number
    state.setdefault('repo', {"owner": owner, "name": repo})
    mr.write_snapshot(session=session, state=state, op='pr.select', args={"number": pr.number})
    typer.echo(f"selected PR #{pr.number} ({pr.head_ref})")


def run():
    app()


@app.command()
def serve(
    stdio: bool = typer.Option(True, "--stdio", help="Use JSONL stdin/stdout interface"),
    session: str = typer.Option(None, help="Session name"),
):
    """Start the JSON Lines stdio server.

    Protocol: one JSON command per line; one JSON response per line.
    Each response includes the current mind state_ref (commit sha).
    """
    import sys
    mr = MindRepo(_repo_root())
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception as e:
            sys.stdout.write(json.dumps({"id": None, "ok": False, "error": {"code": "BAD_JSON", "message": str(e)}, "state_ref": mr.head(session=session)})+"\n")
            sys.stdout.flush()
            continue
        try:
            resp = handle_command(mr, payload, session)
        except Exception as e:
            resp = {"id": payload.get("id"), "ok": False, "error": {"code": "SERVER_ERROR", "message": str(e)}, "state_ref": mr.head(session=session)}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
