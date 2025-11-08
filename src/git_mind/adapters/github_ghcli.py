from __future__ import annotations

# Lightweight wrapper delegating to Draft Punks' GhCliGitHub adapter for now.
# This keeps existing behavior while we converge the packages.

try:
    from draft_punks.adapters.github_ghcli import GhCliGitHub as _DPGhCli
except Exception:  # pragma: no cover
    _DPGhCli = None  # type: ignore


class GhCliGitHub(_DPGhCli):  # type: ignore[misc]
    pass

