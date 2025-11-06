#!/usr/bin/env python3
"""
Print all comments from a GitHub Pull Request as Markdown.

Usage examples:

  # Minimal: infer owner/repo from local git remote
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py pr=123

  # Or specify repo explicitly
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py --owner octo --repo hello --pr 123
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py --repo-slug octo/hello --pr 123
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py --remote https://github.com/octo/hello.git --pr 123
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py pr=123 repo=octo/hello
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py pr=123 remote=git@github.com:octo/hello.git

  # Write to a file
  GITHUB_TOKEN=... python3 tools/review/get_comments_markdown.py pr=123 --out comments.md

The script paginates over review comments and issue comments so very large PRs
are fully captured. It does not filter by author.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
from typing import Dict, List, Tuple
from urllib import error, parse, request


API = "https://api.github.com"


def _http_get(url: str, token: str) -> Tuple[object, Dict[str, str]]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return data, hdrs
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"GitHub API error {exc.code} on {url}: {details}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Network error contacting GitHub: {exc}") from exc


def _parse_link_header(value: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not value:
        return out
    for part in value.split(","):
        part = part.strip()
        if not part or ";" not in part:
            continue
        url_part, meta_part = part.split(";", 1)
        url = url_part.strip().strip("<>")
        meta = {k.strip(): v.strip().strip('"') for k, v in (m.split("=", 1) for m in meta_part.split(";") if "=" in m)}
        rel = meta.get("rel")
        if rel:
            out[rel] = url
    return out


def gh_get_all(path: str, token: str) -> List[dict]:
    """GET and paginate a REST collection, returning all items.

    Adds per_page=100 and follows Link rel="next".
    """
    # Build initial URL with per_page=100
    url = API + path
    parsed = parse.urlparse(url)
    q = parse.parse_qsl(parsed.query, keep_blank_values=True)
    q = [(k, v) for (k, v) in q if k not in ("per_page", "page")]
    q.append(("per_page", "100"))
    url = parse.urlunparse(parsed._replace(query=parse.urlencode(q)))

    items: List[dict] = []
    while True:
        data, headers = _http_get(url, token)
        if isinstance(data, list):
            items.extend(data)
        else:
            # Some APIs respond with { items: [...] }
            seq = None
            for key in ("items", "nodes"):
                if key in data and isinstance(data[key], list):
                    seq = data[key]
                    break
            if seq is None:
                raise SystemExit("Unexpected response shape from GitHub (no list found)")
            items.extend(seq)

        links = _parse_link_header(headers.get("link", ""))
        if "next" in links:
            url = links["next"]
            continue
        break
    return items


def inside_git_repo() -> bool:
    try:
        out = subprocess.check_output([
            "git",
            "rev-parse",
            "--is-inside-work-tree",
        ], text=True, stderr=subprocess.DEVNULL).strip()
        return out == "true"
    except Exception:
        return False


def parse_remote_url(remote: str) -> Tuple[str, str]:
    # Support common formats
    if remote.startswith("git@github.com:"):
        path = remote.split(":", 1)[1]
    elif remote.startswith("https://github.com/"):
        path = remote.split("https://github.com/", 1)[1]
    else:
        # Try to treat whatever after last '/' as path
        if "://" in remote or "@" in remote:
            # Unknown scheme/host; best-effort
            path = remote.split("/", 3)[-1]
        else:
            path = remote
    if path.endswith(".git"):
        path = path[:-4]
    if "/" not in path:
        raise SystemExit(f"Unrecognized Git remote URL: {remote}")
    owner, repo = path.split("/", 1)
    return owner, repo


def owner_repo_from_origin() -> Tuple[str, str]:
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        remote = ""
    if not remote:
        raise SystemExit("No origin remote found. Pass --repo-slug or --owner/--repo.")
    return parse_remote_url(remote)


def parse_slug(slug: str) -> Tuple[str, str]:
    if not slug or "/" not in slug:
        raise SystemExit("Repo slug must be in the form owner/repo")
    owner, repo = slug.split("/", 1)
    if not owner or not repo:
        raise SystemExit("Repo slug must be in the form owner/repo")
    return owner, repo


def normalize(s: str) -> str:
    return (s or "").replace("\r\n", "\n").strip()


def collect_comments(token: str, owner: str, repo: str, pr_number: int) -> List[dict]:
    # Review comments (inline on diffs)
    rev = gh_get_all(f"/repos/{owner}/{repo}/pulls/{pr_number}/comments", token)
    # Issue comments (PR discussion thread)
    iss = gh_get_all(f"/repos/{owner}/{repo}/issues/{pr_number}/comments", token)

    out: List[dict] = []
    for c in rev:
        out.append(
            {
                "created_at": c.get("created_at"),
                "author": (c.get("user") or {}).get("login", "unknown"),
                "body": c.get("body", ""),
                "url": c.get("html_url", ""),
                "type": "review_comment",
            }
        )
    for c in iss:
        out.append(
            {
                "created_at": c.get("created_at"),
                "author": (c.get("user") or {}).get("login", "unknown"),
                "body": c.get("body", ""),
                "url": c.get("html_url", ""),
                "type": "issue_comment",
            }
        )
    # Sort chronologically by created_at (fallback to URL as tie-breaker)
    out.sort(key=lambda d: (d.get("created_at") or "", d.get("url") or ""))
    return out


def format_markdown(comments: List[dict]) -> str:
    lines: List[str] = []
    for i, c in enumerate(comments, 1):
        author = c.get("author", "unknown")
        body = normalize(c.get("body", ""))
        lines.append(f"## Comment {i} by {author}\n")
        if body:
            lines.append(body + "\n")
        else:
            lines.append("(no content)\n")
        # Ensure a blank line between comments
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_kv_args(argv: List[str]) -> Dict[str, str]:
    """Support simple key=value args like pr=123 in addition to flags."""
    kv = {}
    for a in list(argv):
        if "=" in a and not a.startswith("--"):
            k, v = a.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


def main(argv: List[str]) -> int:
    # Basic flags
    ap = argparse.ArgumentParser(description="Print PR comments as Markdown")
    ap.add_argument("--owner", help="GitHub owner/org (optional)")
    ap.add_argument("--repo", help="GitHub repo name (optional)")
    ap.add_argument("--repo-slug", "--slug", dest="slug", help="GitHub repo as 'owner/repo'")
    ap.add_argument("--remote", help="Explicit remote URL to parse for owner/repo")
    ap.add_argument("--pr", type=int, help="Pull request number")
    ap.add_argument("--out", help="Write output to file instead of stdout")
    # Allow pr=123 shorthand
    _, _ = ap.parse_known_args([])

    kv = parse_kv_args(argv)
    # Re-parse with provided argv
    args = ap.parse_args([a for a in argv if "=" not in a])

    pr_number = args.pr or int(kv.get("pr", "0") or 0)
    if not pr_number:
        ap.error("--pr or pr=NUMBER is required")

    # Determine owner/repo precedence:
    # 1) --remote / remote=  2) --repo-slug / repo=owner/repo  3) --owner/--repo or owner=/repo=
    # 4) if inside git repo: origin remote  5) GITHUB_REPOSITORY env
    owner = None
    repo = None

    remote_arg = args.remote or kv.get("remote")
    slug_arg = args.slug or kv.get("slug")
    repo_kv = kv.get("repo")
    owner_arg = args.owner or kv.get("owner")
    repo_name_arg = args.repo or (kv.get("repo_name") if repo_kv and "/" not in repo_kv else None)

    if remote_arg:
        owner, repo = parse_remote_url(remote_arg)
    elif slug_arg:
        owner, repo = parse_slug(slug_arg)
    elif repo_kv and "/" in repo_kv:
        owner, repo = parse_slug(repo_kv)
    elif owner_arg and (args.repo or kv.get("repo")) and "/" not in (args.repo or kv.get("repo")):  # owner/repo split
        owner, repo = owner_arg, (args.repo or kv.get("repo"))
    else:
        if inside_git_repo():
            owner, repo = owner_repo_from_origin()
        else:
            env_repo = os.environ.get("GITHUB_REPOSITORY")
            if env_repo and "/" in env_repo:
                owner, repo = env_repo.split("/", 1)

    if not owner or not repo:
        ap.error("Could not determine repository. Provide --remote, --repo-slug, or --owner and --repo, or run inside a git repo with an origin.")

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN environment variable must be set", file=sys.stderr)
        return 1

    comments = collect_comments(token, owner, repo, pr_number)
    md = format_markdown(comments)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
