from __future__ import annotations

import os
import shlex
import subprocess
from typing import List, Optional, Protocol


def build_command_for_prompt(prompt: str) -> List[str]:
    """Resolve provider from env and construct argv for a one-shot prompt.
    Env variables:
      - DP_LLM: one of {codex, claude, gemini}
      - DP_LLM_CMD: custom template with {prompt} placeholder
    """
    tpl = os.environ.get("DP_LLM_CMD")
    provider = os.environ.get("DP_LLM", "").strip().lower()
    if tpl:
        # Simple template replacement; split with shlex for argv
        return shlex.split(tpl.replace("{prompt}", prompt))
    if provider == "codex":
        return ["codex", "exec", prompt]
    if provider == "claude":
        # Prefer JSON output
        return ["claude", "-p", prompt, "--output-format", "json"]
    if provider == "gemini":
        return ["gemini", "-p", prompt]
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
