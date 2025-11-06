import json
from pathlib import Path
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import speak_comment_if_allowed
from draft_punks.adapters.voice_say import OSXSayVoice

class FakeRunner:
    def __init__(self):
        self.calls = []
    def __call__(self, argv, text=True):
        self.calls.append(argv)
        class CP: stdout=""; returncode=0
        return CP()


def test_speak_only_for_coderabbit_when_scope_is_coderabbit_only(tmp_path, monkeypatch):
    # HOME & repo config
    home = tmp_path / 'home'; home.mkdir(parents=True)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('DP_REPO_NAME', 'myrepo')

    cfg = ConfigFS()
    cfg.path.parent.mkdir(parents=True, exist_ok=True)
    cfg.write({
        'voice': {
            'osx_bonus': True,
            'voice': 'Anna',
            'read_scope': 'coderabbit_only'
        }
    })

    r = FakeRunner()
    v = OSXSayVoice(runner=r, platform_name='darwin', which=lambda _: True)

    # non-coderabbit author
    spoke = speak_comment_if_allowed(cfg, v, author_login='alice', text='hello')
    assert not spoke
    assert not r.calls

    # coderabbit author
    spoke = speak_comment_if_allowed(cfg, v, author_login='coderabbitai', text='hi')
    assert spoke
    assert r.calls and r.calls[-1][:3] == ['say','-v','Anna']
