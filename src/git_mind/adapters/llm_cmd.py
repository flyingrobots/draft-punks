from __future__ import annotations

try:
    # Reuse Draft Punks' command runner for now
    from draft_punks.adapters.llm_cmd import run_prompt as _run_prompt
except Exception:  # pragma: no cover
    def _run_prompt(prompt: str) -> str:  # fallback
        return ""


class LlmCmdAdapter:
    def run(self, prompt: str) -> str:
        return _run_prompt(prompt)

