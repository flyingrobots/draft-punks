from __future__ import annotations
from typing import Protocol

class VoicePort(Protocol):
    def speak(self, text: str, *, voice: str = 'Anna') -> bool: ...
