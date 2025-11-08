from __future__ import annotations
from typing import Protocol


class LlmPort(Protocol):
    def run(self, prompt: str) -> str: ...  # returns raw stdout text

