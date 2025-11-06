from types import SimpleNamespace
from draft_punks.adapters.github_ghcli import GhCliGitHub

def test_list_prs_handles_invalid_json():
    def runner(argv):
        return SimpleNamespace(stdout='not json', returncode=0)
    gh=GhCliGitHub(owner='o', repo='r', runner=runner)
    prs=gh.list_open_prs()
    assert prs == []


def test_iter_threads_handles_empty():
    def runner(argv):
        return SimpleNamespace(stdout='{}', returncode=0)
    gh=GhCliGitHub(owner='o', repo='r', runner=runner)
    threads=list(gh.iter_review_threads(1))
    assert threads == []
