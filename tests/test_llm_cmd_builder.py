import os, shlex
from draft_punks.adapters.llm_cmd import build_command_for_prompt

def _with_env(env):
    def deco(fn):
        def inner():
            olds = {k: os.environ.get(k) for k in env}
            try:
                os.environ.update({k:v for k,v in env.items() if v is not None})
                for k,v in olds.items():
                    if v is None and k in os.environ: del os.environ[k]
            finally:
                pass
            try:
                fn()
            finally:
                for k,v in olds.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
        return inner
    return deco

@_with_env({'DP_LLM':'codex','DP_LLM_CMD':None})
def test_codex_builds_exec_style():
    cmd = build_command_for_prompt("Hello")
    assert cmd[:2] == ['codex','exec']
    assert cmd[-1] == 'Hello'

@_with_env({'DP_LLM':'claude','DP_LLM_CMD':None})
def test_claude_adds_output_format_json():
    cmd = build_command_for_prompt("Hi there")
    assert cmd[:2] == ['claude','-p']
    assert '--output-format' in cmd and 'json' in cmd

@_with_env({'DP_LLM':'gemini','DP_LLM_CMD':None})
def test_gemini_uses_p_flag():
    cmd = build_command_for_prompt("Prompt")
    assert cmd[:2] == ['gemini','-p']
    assert cmd[-1] == 'Prompt'

@_with_env({'DP_LLM':None,'DP_LLM_CMD':'myllm -f json -p {prompt}'})
def test_other_template_substitution():
    cmd = build_command_for_prompt("hey you")
    assert cmd[:3] == ['myllm','-f','json']
    assert cmd[-2:] == ['-p','hey you']
