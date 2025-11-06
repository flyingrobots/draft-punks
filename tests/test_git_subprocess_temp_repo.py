import os, subprocess, tempfile, shutil, textwrap
from pathlib import Path
from draft_punks.adapters.git_subprocess import GitSubprocess

def _write(p: Path, name: str, content: str):
    f=p/name; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(content); return f

def _run(cwd: Path, *args):
    return subprocess.run(list(args), cwd=cwd, check=True, capture_output=True, text=True)


def test_git_subprocess_commit_and_push_to_bare_repo(tmp_path):
    work = tmp_path / 'work'; work.mkdir()
    bare = tmp_path / 'bare.git'; bare.mkdir()
    _run(bare, 'git','init','--bare')
    _run(work, 'git','init')
    env=dict(os.environ)
    env.update({'GIT_AUTHOR_NAME':'DP','GIT_AUTHOR_EMAIL':'dp@example','GIT_COMMITTER_NAME':'DP','GIT_COMMITTER_EMAIL':'dp@example'})
    _write(work, 'README.md', '# hi\n')
    subprocess.run(['git','add','.'], cwd=work, env=env, check=True)
    subprocess.run(['git','commit','-m','init'], cwd=work, env=env, check=True)

    # test is_commit
    head=_run(work,'git','rev-parse','HEAD').stdout.strip()
    git=GitSubprocess()
    assert git.is_commit(head)
    # no upstream yet
    assert git.current_branch() in {'master','main'}
    assert not git.has_upstream()

    # add remote and push -u
    _run(work,'git','remote','add','origin', str(bare))
    ok = git.push_set_upstream('origin', f'HEAD:{git.current_branch()}')
    assert ok
    assert git.has_upstream()
