from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem, OptionList
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.screen import ModalScreen
from textual import on

from draft_punks.adapters.github_select import select as select_github
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.adapters.voice_say import OSXSayVoice
from draft_punks.core.services.voice import speak_comment_if_allowed
from draft_punks.core.domain.github import ReviewThread
from draft_punks.adapters.logging_textual import TextualLogger
from draft_punks.core.services.review import process_comment as process_comment_core
from draft_punks.adapters.llm_port import LlmCmdAdapter
from draft_punks.adapters.git_subprocess import GitSubprocess
from draft_punks.tui.llm_select import LlmSelect
from draft_punks.core.services.suggest import parse_suggestion_pairs, apply_suggestions


class CommentPrompt(ModalScreen[dict]):
    def __init__(self, meta: dict, body: str):
        super().__init__()
        self.meta = meta
        self.body = body

    def compose(self) -> ComposeResult:
        hdr = (
            "PR #{} ({}) • {}\n".format(self.meta['pr'], self.meta.get('head',''), self.meta.get('path',''))
            + "Comment {} of {} ({} of {} in this file)".format(
                self.meta['idx_pr'], self.meta['total_pr'], self.meta['idx_file'], self.meta['total_file']
            )
        )
        yield Static(hdr)
        yield Static("````markdown\n{}\n````".format(self.body))
        self.opts = OptionList(
            OptionList.Option('Yes'),
            OptionList.Option('Yes, but let me rewrite it'),
            OptionList.Option('Apply suggested replacement (no LLM)'),
            OptionList.Option('Yes, and send all comments in this file automatically'),
            OptionList.Option('Yes, and send all comments in general automatically'),
            OptionList.Option('No, skip this comment'),
            OptionList.Option('No, skip this file'),
            OptionList.Option('I need to adjust the LLM command or switch LLMs'),
            OptionList.Option('Quit')
        )
        yield self.opts

    def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
        self.dismiss({'choice': ev.option.prompt, 'body': self.body})


class CommentViewer(Widget):
    BINDINGS = [('s', 'summary', 'Show summary'), ('h', 'help', 'Help'), ('a', 'batch_send', 'Send remaining')]

    def __init__(self, pr_number: int, head_ref: str = '', logger: TextualLogger | None = None):
        super().__init__()
        self.pr_number = pr_number
        self.head_ref = head_ref
        self._logger = logger
        self._auto_all: bool = False
        self._auto_files: set[str] = set()
        self._threads: list[ReviewThread] = []
        self._flat: list[tuple[str, object]] = []
        self._thread_ids: list[str] = []
        self._counts_by_file: dict[str, int] = {}
        self._commits_by_file: dict[str, list[str]] = {}
        self._commits: list[str] = []

    def compose(self) -> ComposeResult:
        self.lv = ListView(id='comments')
        self.detail = Static('Select a comment', id='detail')
        self.header = Static('', id='header')
        yield self.header
        yield Horizontal(Vertical(self.lv, id='left', classes='panel'), Vertical(self.detail, id='right', classes='panel'))

    def on_mount(self):
        owner, repo = owner_repo_from_env_or_git()
        gh = select_github(owner, repo)
        try:
            if self._logger:
                setattr(gh, 'progress', lambda page, total: self._logger.info('page {} • {} comments so far…'.format(page, total)))
        except Exception:
            pass
        counts: dict[str, int] = {}
        for th in gh.iter_review_threads(self.pr_number):
            self._threads.append(th)
            for c in th.comments:
                self._flat.append((th.path, c))
                self._thread_ids.append(th.id)
                counts[th.path] = counts.get(th.path, 0) + 1
                label = c.body.splitlines()[0][:80]
                if self._auto_all or th.path in self._auto_files:
                    label = '[AUTO] ' + label
                if (getattr(c, 'author', '') or '').lower() == 'coderabbitai':
                    label = 'BunBun says: ' + label
                self.lv.append(ListItem(Static(label)))
        self._counts_by_file = counts
        if self._flat:
            first_path = self._flat[0][0]
            self.header.update('PR #{} ({}) • {}\nComment 1 of {} (1 of {} in this file)\n0%'.format(
                self.pr_number, self.head_ref, first_path, len(self._flat), self._counts_by_file.get(first_path,1)
            ))

    @on(ListView.Highlighted)
    def show_detail(self, event: ListView.Highlighted):
        idx = event.index
        path, c = self._flat[idx]
        md = c.body
        self.detail.update("````markdown\n{}\n````".format(md))
        cfg = ConfigFS()
        speak_comment_if_allowed(cfg, OSXSayVoice(), author_login=getattr(c, 'author', '') or '', text=c.body)

        total_pr = len(self._flat)
        total_file = self._counts_by_file.get(path, 1)
        pos_file = 1
        for i, (p, _) in enumerate(self._flat):
            if i == idx:
                break
            if p == path:
                pos_file += 1
        pct = int((idx + 1) * 100 / max(1, total_pr))
        self.header.update('PR #{} ({}) • {}\nComment {} of {} ({} of {} in this file)\n{}%'.format(
            self.pr_number, self.head_ref, path, idx+1, total_pr, pos_file, total_file, pct
        ))

    @on(ListView.Selected)
    def act_on_comment(self, event: ListView.Selected):
        idx = event.index
        path, c = self._flat[idx]
        total_pr = len(self._flat)
        total_file = self._counts_by_file.get(path, 1)
        pos_file = 1
        for i, (p, _) in enumerate(self._flat):
            if i == idx:
                break
            if p == path:
                pos_file += 1
        meta = {'pr': self.pr_number, 'head': self.head_ref, 'path': path, 'idx_pr': idx + 1, 'total_pr': total_pr, 'idx_file': pos_file, 'total_file': total_file}
        if self._auto_all or path in self._auto_files:
            self.ensure_llm_selected(); self.invoke_llm(meta, c.body); return
        prompt = CommentPrompt(meta, c.body)
        self._pending = (idx, meta, c)
        self.app.push_screen(prompt, self.handle_choice)

    def handle_choice(self, res: dict | None):
        if not res or not hasattr(self, '_pending'):
            return
        idx, meta, c = self._pending
        choice = res.get('choice') if res else 'No, skip this comment'
        if choice.startswith('Yes, and send all comments in general'):
            self._auto_all = True; self.ensure_llm_selected(); self.invoke_llm(meta, c.body)
        elif choice.startswith('Yes, and send all comments in this file'):
            self._auto_files.add(meta['path']); self.ensure_llm_selected(); self.invoke_llm(meta, c.body)
        elif choice.startswith('Apply suggested replacement'):
            pairs = parse_suggestion_pairs(c.body)
            if not pairs:
                (self._logger or TextualLogger(self.app.log)).warn('No suggestion blocks found in this comment.')
            else:
                applied = apply_suggestions(meta['path'], pairs)
                if applied:
                    gs = GitSubprocess(); gs.add_and_commit([meta['path']], 'Apply suggestion: {} ({} hunk)'.format(meta['path'], applied))
                    sha = gs.head_sha(); (self._logger or TextualLogger(self.app.log)).info('Applied {} suggestion hunk(s) to {}.'.format(applied, meta['path']))
                    data = (ConfigFS().read() or {})
                    if data.get('reply_on_success') and sha:
                        owner, repo = owner_repo_from_env_or_git(); gh = select_github(owner, repo)
                        thread_id = self._thread_ids[idx]
                        if thread_id:
                            gh.post_reply(thread_id, 'Addressed in {} — @coderabbitai'.format(sha))
                else:
                    (self._logger or TextualLogger(self.app.log)).warn('Suggestion did not match file content.')
        elif choice.startswith('Yes, but let me rewrite'):
            from draft_punks.adapters.util.editor import open_in_editor
            edited = open_in_editor(c.body)
            self.ensure_llm_selected(); self.invoke_llm(meta, edited or c.body)
        elif choice == 'Yes':
            self.ensure_llm_selected(); self.invoke_llm(meta, c.body)
        elif choice.startswith('I need to adjust the LLM'):
            self.app.push_screen(LlmSelect(), lambda _: None)
        elif choice.startswith('No, skip this file'):
            self._auto_files.add(meta['path'])
        elif choice.startswith('Quit'):
            self.app.exit()
        del self._pending

    def ensure_llm_selected(self):
        data = (ConfigFS().read() or {})
        if not data.get('llm') and not data.get('llm_cmd'):
            self.app.push_screen(LlmSelect(), lambda _: None)

    def invoke_llm(self, meta: dict, body: str):
        logger = self._logger or TextualLogger(self.app.log)
        adapter = LlmCmdAdapter(); git = GitSubprocess()
        commits = process_comment_core(pr_number=meta['pr'], head_ref=meta.get('head', ''), body=body, llm=adapter, git=git, log=logger)
        if commits:
            logger.info('Commits: ' + ', '.join(commits))
            self._commits.extend(commits)
            self._commits_by_file.setdefault(meta['path'], []).extend(commits)
            data = (ConfigFS().read() or {})
            if data.get('reply_on_success'):
                owner, repo = owner_repo_from_env_or_git(); gh = select_github(owner, repo)
                idx = meta['idx_pr'] - 1
                if 0 <= idx < len(self._thread_ids):
                    thread_id = self._thread_ids[idx]
                    gh.post_reply(thread_id, 'Addressed in {} — @coderabbitai'.format(commits[0]))
        else:
            logger.warn('No commits reported or JSON invalid.')

    def action_summary(self):
        class Summary(ModalScreen[bool]):
            def __init__(self, parent: 'CommentViewer'):
                super().__init__(); self.parent = parent
            def compose(self) -> ComposeResult:
                yield Static('PR #{} ({}) — Summary'.format(self.parent.pr_number, self.parent.head_ref))
                if not self.parent._commits:
                    yield Static('No commits recorded yet.')
                else:
                    yield Static('\n'.join(['- `{}`'.format(s) for s in self.parent._commits]))
                yield OptionList(OptionList.Option('Push now'), OptionList.Option('Close'))
            def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                self.dismiss(ev.option.prompt == 'Push now')
        def after(ok: bool):
            if ok:
                git = GitSubprocess(); br = git.current_branch()
                okp = git.push() if git.has_upstream() else git.push_set_upstream('origin', 'HEAD:{}'.format(br))
                (self._logger or TextualLogger(self.app.log)).info('Pushed.' if okp else 'Push failed.')
        self.app.push_screen(Summary(self), after)

    def action_help(self):
        class Help(ModalScreen[None]):
            def compose(self) -> ComposeResult:
                md = """```
Keys:
  Enter  -> act on selected comment
  s      -> show summary / push
  h      -> help
  a      -> batch send remaining
List actions:
  Yes / Yes (rewrite) / Apply suggestion / Yes (auto)
  Skip comment / Skip file / Switch LLM
```"""
                yield Static(md)
                yield OptionList(OptionList.Option('Close'))
            def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                self.dismiss(None)
        self.app.push_screen(Help())

    def action_batch_send(self):
        total = len(self._flat)
        sent = 0
        self.ensure_llm_selected()
        for idx, (path, c) in enumerate(self._flat):
            if path in self._auto_files:
                continue
            meta = {'pr': self.pr_number, 'head': self.head_ref, 'path': path, 'idx_pr': idx + 1, 'total_pr': total, 'idx_file': 1, 'total_file': self._counts_by_file.get(path, 1)}
            self.invoke_llm(meta, c.body); sent += 1
            if self._logger:
                self._logger.info('Batch progress: {}/{}'.format(sent, total))
