from types import SimpleNamespace
from draft_punks.adapters.github_ghcli import GhCliGitHub

def test_post_reply_builds_mutation():
    calls=[]
    def runner(argv):
        calls.append(argv)
        return SimpleNamespace(stdout='{}', returncode=0)
    gh=GhCliGitHub(owner='o', repo='r', runner=runner)
    ok=gh.post_reply('PRRT_123','Addressed in 123abc — @coderabbitai')
    assert ok
    joined=' '.join(calls[-1])
    assert 'addPullRequestReviewThreadReply' in joined
