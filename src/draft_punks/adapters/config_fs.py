from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Mapping, Any
from draft_punks.ports.config import ConfigPort

class ConfigFS(ConfigPort):
    def __init__(self, repo_name: str | None = None, base: Path | None = None):
        if repo_name is None:
            # try env hint, else fallback to cwd basename
            repo_name = os.environ.get('DP_REPO_NAME') or Path.cwd().name
        self._repo = repo_name
        base_dir = base or Path(os.environ.get('HOME', str(Path.home())))
        self._path = base_dir / '.draft-punks' / repo_name / 'config.json'

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> Mapping[str, Any]:
        p = self._path
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}

    def write(self, data: Mapping[str, Any]) -> None:
        p = self._path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(data), indent=2))
