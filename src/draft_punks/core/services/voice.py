from __future__ import annotations
from typing import Mapping, Any
from draft_punks.ports.config import ConfigPort
from draft_punks.ports.voice import VoicePort

def enable_bonus_mode(cfg: ConfigPort, voice: VoicePort, *, voice_name: str = 'Anna') -> None:
    data: dict[str, Any] = dict(cfg.read() or {})
    v = dict(data.get('voice') or {})
    v['osx_bonus'] = True
    v['voice'] = voice_name
    data['voice'] = v
    cfg.write(data)
    voice.speak("Oh mien got. You want me to read these aloud? Very well. I'm feeling frisky today.", voice=voice_name)
