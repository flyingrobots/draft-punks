import os, subprocess, sys
from pathlib import Path

def test_cli_version_exits_zero_and_shows_name_and_semver():
    exe = Path(__file__).resolve().parents[1] / 'cli' / 'draft-punks'
    assert exe.exists(), 'entrypoint script missing'
    out = subprocess.run([str(exe), '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # Expect a line like: draft-punks 0.0.1
    assert out.returncode == 0
    line = (out.stdout or '').strip().splitlines()[-1]
    assert line.startswith('draft-punks '), f'bad version line: {line!r}'
    # crude semver-ish: N.N.N
    ver = line.split()[-1]
    assert ver.count('.')==2, f'bad semver: {ver}'
