import json
import os
from pathlib import Path
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.adapters.llm_cmd import build_command_for_prompt


def test_config_path_is_in_home_repo_bucket(tmp_path, monkeypatch):
    # fake HOME
    home = tmp_path / 'home'
    home.mkdir(parents=True)
    monkeypatch.setenv('HOME', str(home))
    # repo name given explicitly
    cfg = ConfigFS(repo_name='libgitledger')
    p = cfg.path
    assert str(p).endswith('libgitledger/config.json')
    assert p.parts[-3:] == ('.draft-punks','libgitledger','config.json')


def test_llm_builder_reads_config_when_env_missing(tmp_path, monkeypatch):
    # ensure env is empty
    monkeypatch.delenv('DP_LLM', raising=False)
    monkeypatch.delenv('DP_LLM_CMD', raising=False)
    # write config under HOME bucket
    home = tmp_path / 'home'
    home.mkdir(parents=True)
    monkeypatch.setenv('HOME', str(home))
    cfg_dir = home / '.draft-punks' / 'myrepo'
    cfg_dir.mkdir(parents=True)
    (cfg_dir / 'config.json').write_text(json.dumps({'llm':'claude'}))
    # make config visible to adapter via DP_REPO_NAME
    monkeypatch.setenv('DP_REPO_NAME', 'myrepo')
    from importlib import reload
    import draft_punks.adapters.llm_cmd as llm
    reload(llm)
    cmd = llm.build_command_for_prompt('Yo')
    assert cmd[:2] == ['claude','-p']
    assert '--output-format' in cmd and 'json' in cmd
