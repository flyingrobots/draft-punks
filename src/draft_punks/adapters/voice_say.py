from __future__ import annotations
import shutil
import subprocess
from typing import Callable, Optional, List
from draft_punks.ports.voice import VoicePort

class OSXSayVoice(VoicePort):
    def __init__(self, *, runner: Optional[Callable[[List[str]], object]] = None,
                 platform_name: Optional[str] = None,
                 which: Optional[Callable[[str], Optional[str]]] = None):
        self._runner = runner or (lambda argv: subprocess.run(argv, capture_output=True, text=True))
        self._platform = platform_name
        self._which = which or shutil.which

    def speak(self, text: str, *, voice: str = 'Anna') -> bool:
        plat = (self._platform or __import__('sys').platform)
        if plat != 'darwin':
            return False
        if not self._which('say'):
            return False
        argv = ['say','-v', voice, text]
        self._runner(argv)
        return True
