import os, subprocess, sys, json
from pathlib import Path

def test_format_list_uses_num_and_branch():
    exe = Path(__file__).resolve().parents[1] / 'cli' / 'draft-punks'
    fake = {
        'prs': [
            {'number': 74, 'headRefName': 'chore/issues-roadmap', 'title': 'planning: roadmap DAG styling + SVG; issue sweep; ISSUES.md'},
            {'number': 123, 'headRefName': 'feat/tui', 'title': 'introduce python CLI TUI'},
        ]
    }
    env = os.environ.copy()
    env['DP_FAKE_GH_PRS'] = json.dumps(fake)
    # Expect plain list lines like: - #74 (chore/issues-roadmap) planning...
    p = subprocess.run([str(exe), 'review', '--format-list'], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    body = p.stdout.strip()
    assert p.returncode == 0, body
    lines = [ln for ln in body.splitlines() if ln.strip()]
    assert lines[0].startswith('- #74 (chore/issues-roadmap) '), lines[0]
    assert lines[1].startswith('- #123 (feat/tui) '), lines[1]
