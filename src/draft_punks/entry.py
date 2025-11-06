from __future__ import annotations

import json
import os
import sys
from typing import List

from draft_punks.adapters.github_ghcli import GhCliGitHub
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git

APP_NAME = "draft-punks"
APP_VERSION = "0.0.1"


def _print_version() -> int:
    print(f"{APP_NAME} {APP_VERSION}")
    return 0


def _format_list(prs) -> str:
    lines = []
    for pr in prs:
        lines.append(f"- #{pr.number} ({pr.head_ref}) {pr.title}")
    return "\n".join(lines)


def run(argv: List[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: draft-punks [--version] tui | review [--format-list]")
        return 0
    if argv[0] == "--version":
        return _print_version()
    if argv[0] == "tui":
        # defer heavy import
        from draft_punks.tui.app import DraftPunksApp
        DraftPunksApp().run()
        return 0
    cmd = argv.pop(0)
    if cmd == "review":
        if argv and argv[0] == "--format-list":
            # test hook: DP_FAKE_GH_PRS for predictable output
            blob = os.environ.get("DP_FAKE_GH_PRS")
            if blob:
                data = json.loads(blob).get("prs", [])
                class _PR:  # tiny shim
                    def __init__(self, n, h, t): self.number=n; self.head_ref=h; self.title=t
                prs = [_PR(x.get('number'), x.get('headRefName'), x.get('title')) for x in data]
                print(_format_list(prs))
                return 0
            owner, repo = owner_repo_from_env_or_git()
            gh = GhCliGitHub(owner=owner, repo=repo)
            prs = gh.list_open_prs()
            print(_format_list(prs))
            return 0
        print("review: nothing to do (try --format-list)")
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(run())

