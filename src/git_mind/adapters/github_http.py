from __future__ import annotations

try:
    from draft_punks.adapters.github_http import HttpGitHub as _DPHttp
except Exception:  # pragma: no cover
    _DPHttp = None  # type: ignore


class HttpGitHub(_DPHttp):  # type: ignore[misc]
    pass

