from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual import on
from draft_punks.adapters.github_ghcli import GhCliGitHub
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import speak_comment_if_allowed
from draft_punks.adapters.voice_say import OSXSayVoice
from draft_punks.core.domain.github import ReviewThread

class CommentViewer(Widget):
    def __init__(self, pr_number: int):
        super().__init__()
        self.pr_number = pr_number
        self._threads: list[ReviewThread] = []

    def compose(self) -> ComposeResult:
        self.lv = ListView(id='comments')
        self.detail = Static("Select a comment", id='detail')
        yield Horizontal(
            Vertical(self.lv, id='left', classes='panel'),
            Vertical(self.detail, id='right', classes='panel'),
        )

    def on_mount(self):
        owner, repo = owner_repo_from_env_or_git()
        gh = GhCliGitHub(owner=owner, repo=repo)
        for th in gh.iter_review_threads(self.pr_number):
            self._threads.append(th)
            for c in th.comments:
                label = c.body.splitlines()[0][:80]
                if (c.author or '').lower() == 'coderabbitai':
                    label = f"BunBun says: {label}"
                self.lv.append(ListItem(Static(label)))

    @on(ListView.Highlighted)
    def show_detail(self, event: ListView.Highlighted):
        idx = event.index
        k = 0
        for th in self._threads:
            for c in th.comments:
                if k == idx:
                    md = c.body
                    self.detail.update(f"````markdown\n{md}\n````")
                    cfg = ConfigFS()
                    speak_comment_if_allowed(cfg, OSXSayVoice(), author_login=c.author or '', text=c.body)
                    return
                k += 1
