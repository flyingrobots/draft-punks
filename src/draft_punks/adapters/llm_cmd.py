from __future__ import annotations

import os
import shlex
import subprocess
from typing import List, Optional, Protocol
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.adapters.config_fs import ConfigFS


_CAPS = {
    # Known capability flags to force JSON when requested
    'claude': {'force_json_flag': ['--output-format', 'json']},
    # add others when available
}


def build_command_for_prompt(prompt: str) -> List[str]:
    """Resolve provider from env and construct argv for a one-shot prompt.
    Env variables:
      - DP_LLM: one of {codex, claude, gemini}
      - DP_LLM_CMD: custom template with {prompt} placeholder
    """
    tpl = os.environ.get("DP_LLM_CMD")
    provider = os.environ.get("DP_LLM", "").strip().lower()
    force_json = False
    if not tpl and not provider:
        cfg = ConfigFS(); data = cfg.read() or {}
        provider = (data.get('llm') or '').strip().lower()
        tpl = data.get('llm_cmd')
        force_json = bool(data.get('force_json'))
    else:
        # If env set, still consult config for force_json fallback
        try:
            data = ConfigFS().read() or {}
            force_json = bool(data.get('force_json'))
        except Exception:
            force_json = False
    if tpl:
        # Simple template replacement; split with shlex for argv
        return shlex.split(tpl.replace("{prompt}", prompt))
    if provider == "codex":
        argv = ["codex", "exec", prompt]
        # no known json flag; rely on prompt contract
        return argv
    if provider == "claude":
        argv = ["claude", "-p", prompt]
        if force_json:
            argv += _CAPS['claude']['force_json_flag']
        else:
            argv += ["--output-format", "json"]  # default to json
        return argv
    if provider == "gemini":
        argv = ["gemini", "-p", prompt]
        # no known json flag; rely on prompt contract
        return argv
    # Default fallback: try to read from DP_LLM_CMD next time
    return ["sh", "-lc", shlex.quote(prompt)]


class _Runner(Protocol):
    def __call__(self, argv: List[str], text: bool = True) -> subprocess.CompletedProcess[str]:
        ...


def run_prompt(prompt: str, runner: Optional[_Runner] = None) -> str:
    argv = build_command_for_prompt(prompt)
    run = runner or (lambda a, text=True: subprocess.run(a, capture_output=True, text=text))
    try:
        cp = run(argv, text=True)
        return (cp.stdout or "")
    except FileNotFoundError:
        return ""
