import types
from draft_punks.core.services.review import process_comment

class FakeLogger:
    def __init__(self):
        self.events = []
    def info(self, msg: str): self.events.append(('info', msg))
    def warn(self, msg: str): self.events.append(('warn', msg))
    def error(self, msg: str): self.events.append(('error', msg))
    def markdown(self, md: str): self.events.append(('md', md))

class FakeLlm:
    def run(self, prompt: str) -> str:
        return "not json, just chatter"

class FakeGit:
    def is_commit(self, sha: str) -> bool: return False


def test_process_comment_non_json_logs_and_ignores():
    logger = FakeLogger()
    llm    = FakeLlm()
    git    = FakeGit()
    commits = process_comment(pr_number=74, head_ref='feat/x', body='fix pls', llm=llm, git=git, log=logger)
    assert commits == []
    # should have at least one warn
    assert any(level=='warn' for level,_ in logger.events), logger.events
