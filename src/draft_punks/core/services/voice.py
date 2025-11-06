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


def speak_comment_if_allowed(cfg: ConfigPort, voice: VoicePort, *, author_login: str, text: str) -> bool:
    """Speak a comment according to config voice scope.
    Returns True if spoken.
    """
    data = dict(cfg.read() or {})
    vconf = dict(data.get('voice') or {})
    if not vconf.get('osx_bonus'):
        return False
    scope = (vconf.get('read_scope') or 'coderabbit_only').lower()
    author = (author_login or '').lower()
    allowed = False
    if scope == 'coderabbit_only':
        allowed = author in {'coderabbitai','code-rabbit','coderabbit'}
    elif scope == 'all':
        allowed = True
    else:
        allowed = False
    if not allowed:
        return False
    vname = vconf.get('voice') or 'Anna'
    return bool(voice.speak(text, voice=vname))
