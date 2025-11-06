import json
from pathlib import Path
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import enable_bonus_mode
from draft_punks.adapters.voice_say import OSXSayVoice

class FakeRunner:
    def __init__(self):
        self.calls = []
    def __call__(self, argv, text=True):
        self.calls.append(argv)
        class CP: stdout=""; returncode=0
        return CP()


def test_osx_say_builds_command_on_darwin_with_voice():
    r = FakeRunner()
    v = OSXSayVoice(runner=r, platform_name='darwin', which=lambda _: True)
    ok = v.speak("Hallo Welt", voice='Anna')
    assert ok
    assert r.calls and r.calls[-1][:3] == ['say','-v','Anna']


def test_enable_bonus_writes_config_and_greets(tmp_path, monkeypatch):
    # route HOME
    home = tmp_path / 'home'; home.mkdir(parents=True)
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('DP_REPO_NAME', 'myrepo')

    cfg = ConfigFS()
    r = FakeRunner()
    v = OSXSayVoice(runner=r, platform_name='darwin', which=lambda _: True)

    enable_bonus_mode(cfg, v)

    # config exists and has voice.osx_bonus true
    data = json.loads(cfg.path.read_text())
    assert data.get('voice',{}).get('osx_bonus') is True
    assert data['voice'].get('voice') == 'Anna'

    # greeting spoken
    assert r.calls and r.calls[-1][0:3] == ['say','-v','Anna']
