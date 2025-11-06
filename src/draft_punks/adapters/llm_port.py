from __future__ import annotations
from draft_punks.ports.llm import LlmPort
from draft_punks.adapters.llm_cmd import run_prompt

class LlmCmdAdapter(LlmPort):
    def run(self, prompt: str) -> str:
        return run_prompt(prompt)
