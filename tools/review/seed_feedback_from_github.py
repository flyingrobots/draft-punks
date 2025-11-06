#!/usr/bin/env python3
"""
Seed a Code Review Feedback doc from a GitHub PR.

Generates docs/code-reviews/PR<PR#>/<commit_sha>.md prefilled with
feedback items extracted from:
- PR review comments (code comments)
- PR issue comments (general discussion)

Authentication: set GITHUB_TOKEN in the environment.

Usage:
  python3 tools/review/seed_feedback_from_github.py \
    --owner flyingrobots --repo draft-punks --pr 69 \
    [--commit <sha>] [--out docs/code-reviews]

If --commit is omitted, the PR head SHA is used.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import textwrap
import urllib.request
import urllib.error


API = "https://api.github.com"


def gh_get_with_headers(url: str, token: str):
    """GET a full URL and return (json, headers)."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read().decode("utf-8"))
            headers = {k.lower(): v for k, v in r.headers.items()}
            return data, headers
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"GitHub API error {e.code} on {url}: {msg}")


def gh_get(path: str, token: str):
    """GET a repository-relative path and return JSON body only."""
    data, _ = gh_get_with_headers(API + path, token)
    return data


def parse_link_header(link_header: str) -> dict:
    """Parse GitHub Link header into a dict of {rel: url}."""
    rels = {}
    if not link_header:
        return rels
    parts = [p.strip() for p in link_header.split(",")]
    for p in parts:
        if ";" not in p:
            continue
        url_part, rel_part = p.split(";", 1)
        url = url_part.strip().strip("<>")
        if "rel=" in rel_part:
            rel = rel_part.split("rel=", 1)[1].strip().strip('"')
            rels[rel] = url
    return rels


def gh_get_all(path: str, token: str):
    """GET and paginate over all pages for a given resource path.

    Appends per_page=100 and follows Link: rel="next" until exhausted.
    Returns a list aggregated across all pages.
    """
    import urllib.parse as up

    url = API + path
    # Ensure per_page=100 is present
    parsed = up.urlparse(url)
    qs = up.parse_qsl(parsed.query, keep_blank_values=True)
    # Remove any existing per_page/page to avoid duplication
    qs = [(k, v) for (k, v) in qs if k not in ("per_page", "page")]
    qs.append(("per_page", "100"))
    url = up.urlunparse(parsed._replace(query=up.urlencode(qs)))

    items = []
    while True:
        data, headers = gh_get_with_headers(url, token)
        if isinstance(data, list):
            items.extend(data)
        else:
            # Some endpoints may return objects; try common list fields
            for key in ("items", "nodes"):
                if key in data and isinstance(data[key], list):
                    items.extend(data[key])
                    break
            else:
                raise SystemExit("Unexpected GitHub response shape during pagination")

        links = parse_link_header(headers.get("link", ""))
        next_url = links.get("next")
        if next_url:
            url = next_url
            continue
        break
    return items


def normalize(s: str) -> str:
    return s.replace("\r\n", "\n").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--commit", default=None, help="Target commit SHA (defaults to PR head)")
    ap.add_argument("--out", default="docs/code-reviews", help="Base output dir")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    pr_path = f"/repos/{args.owner}/{args.repo}/pulls/{args.pr}"
    pr = gh_get(pr_path, token)
    head_sha = (args.commit or pr.get("head", {}).get("sha", "")).strip()
    head_ref = pr.get("head", {}).get("ref", "")
    pr_url = pr.get("html_url", "")

    if not head_sha:
        raise SystemExit("Unable to determine PR head SHA. Pass --commit explicitly.")

    # Collect review comments (paginated)
    rev_comments = gh_get_all(pr_path + "/comments", token)
    # Collect issue comments (discussion, paginated)
    iss_comments = gh_get_all(f"/repos/{args.owner}/{args.repo}/issues/{args.pr}/comments", token)

    # Build output path
    out_dir = pathlib.Path(args.out) / f"PR{args.pr}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{head_sha}.md"

    # Header/front matter
    today = dt.datetime.utcnow().strftime("%Y-%m-%d")
    agent = "CodeRabbit (and reviewers)"

    def fm_line(k, v):
        return f"{k}: {v}\n"

    content = []
    content.append("---\n")
    content.append(fm_line("title", out_file.name))
    content.append("description: Preserved review artifacts and rationale.\n")
    content.append("audience: [contributors]\n")
    content.append("domain: [quality]\n")
    content.append("tags: [review]\n")
    content.append("status: archive\n")
    content.append("---\n\n")

    content.append("# Code Review Feedback\n\n")
    content.append("| Date | Agent | SHA | Branch | PR |\n")
    content.append("|------|-------|-----|--------|----|\n")
    content.append(f"| {today} | {agent} | `{head_sha}` | [{head_ref}](https://github.com/{args.owner}/{args.repo}/tree/{head_ref} \"{args.owner}/{args.repo}:{head_ref}\") | [PR#{args.pr}]({pr_url}) |\n\n")

    content.append("## CODE REVIEW FEEDBACK\n\n")

    # Helper: emit one feedback block
    def emit_feedback(title: str, body: str, meta: str = ""):
        content.append(f"### {title}\n\n")
        fence = "```text\n" + normalize(body) + "\n```\n\n"
        content.append(fence)
        if meta:
            content.append(f"_Meta_: {meta}\n\n")
        content.append("{response}\n\n")

    # Add review comments (code)
    for c in rev_comments:
        path = c.get("path", "")
        line = c.get("line") or c.get("original_line")
        url = c.get("html_url", "")
        user = c.get("user", {}).get("login", "")
        title = f"{path}:{line} — {user}"
        body = c.get("body", "")
        meta = url
        emit_feedback(title, body, meta)

    # Add issue comments (general)
    for c in iss_comments:
        body = c.get("body", "")
        user = c.get("user", {}).get("login", "")
        url = c.get("html_url", "")
        title = f"General comment — {user}"
        emit_feedback(title, body, url)

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("".join(content))

    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
