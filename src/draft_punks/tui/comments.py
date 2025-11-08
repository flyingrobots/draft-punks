from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem, OptionList, ProgressBar
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual import on

from draft_punks.adapters.github_select import select as select_github
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.adapters.voice_say import OSXSayVoice
from draft_punks.core.services.voice import speak_comment_if_allowed
from draft_punks.core.domain.github import ReviewThread
from draft_punks.adapters.logging_textual import TextualLogger
from draft_punks.core.services.review import process_comment as process_comment_core, _extract_json, build_prompt
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
        self.opts = OptionList()
        try:
            self.opts.add_options(
                'Yes',
                'Yes, but let me rewrite it',
                'Apply suggested replacement (no LLM)',
                'Yes, and send all comments in this file automatically',
                'Yes, and send all comments in general automatically',
                'No, skip this comment',
                'No, skip this file',
                'Go to previous comment',
                'I need to adjust the LLM command or switch LLMs',
                'Quit',
            )
        except Exception:
            for label in [
                'Yes',
                'Yes, but let me rewrite it',
                'Apply suggested replacement (no LLM)',
                'Yes, and send all comments in this file automatically',
                'Yes, and send all comments in general automatically',
                'No, skip this comment',
                'No, skip this file',
                'Go to previous comment',
                'I need to adjust the LLM command or switch LLMs',
                'Quit',
            ]:
                try:
                    self.opts.add_option(label)
                except Exception:
                    pass
        yield self.opts

    def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
        self.dismiss({'choice': ev.option.prompt, 'body': self.body})


class CommentViewer(Screen):
    BINDINGS = [('s', 'summary', 'Show summary'), ('h', 'help', 'Help'), ('a', 'batch_send', 'Send remaining'), ('left','prev_comment','Prev'), ('right','next_comment','Next')]

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

    def _show_at_index(self, idx: int):
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

    @on(ListView.Highlighted)
    def show_detail(self, event: ListView.Highlighted):
        self._show_at_index(event.index)

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
        self._prompt_for_index(idx)

    def _prompt_for_index(self, idx: int):
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
        prompt = CommentPrompt(meta, c.body)
        self._pending = (idx, meta, c)
        self.app.push_screen(prompt, self.handle_choice)

    def handle_choice(self, res: dict | None):
        if not res or not hasattr(self, '_pending'):
            return
        idx, meta, c = self._pending
        choice = res.get('choice') if res else 'No, skip this comment'
        if choice.startswith('Go to previous'):
            prev_idx = max(0, idx-1)
            self._show_at_index(prev_idx)
            self._prompt_for_index(prev_idx)
            del self._pending
            return
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
        cfg = ConfigFS(); data = cfg.read() or {}
        provider = (data.get('llm') or '').strip().lower()
        # Debug LLM: show the prompt and simulate result
        if provider == 'debug':
            prompt = (
                "We are processing code review feedback for PR #{} ({}).\n".format(meta['pr'], meta.get('head','')) +
                "Respond only with JSON: {\"success\": true|false, \"git_commits\": [\"<sha1>\", ...], \"error\": \"...\"}.\n" +
                "Feedback:\n{}\n".format(body)
            )
            class DebugPrompt(ModalScreen[str]):
                def compose(self) -> ComposeResult:
                    yield Static("Debug LLM — this is the prompt that would be sent:")
                    yield Static("````text\n{}\n````".format(prompt))
                    self.opts = OptionList()
                    try:
                        self.opts.add_options('Emit success', 'Simulate failure', 'Close')
                    except Exception:
                        for label in ['Emit success', 'Simulate failure', 'Close']:
                            try: self.opts.add_option(label)
                            except Exception: pass
                    yield self.opts
                def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                    self.dismiss(ev.option.prompt)
            def after(choice: str | None):
                if choice and choice.startswith('Emit success'):
                    git = GitSubprocess(); sha = git.head_sha() or 'deadbeef'
                    logger.info('Debug LLM: emitting success with commit {}'.format(sha))
                    self._commits.append(sha)
                    self._commits_by_file.setdefault(meta['path'], []).append(sha)
                    cfg2 = ConfigFS(); data2 = cfg2.read() or {}
                    if data2.get('reply_on_success'):
                        owner, repo = owner_repo_from_env_or_git(); gh = select_github(owner, repo)
                        idx = meta['idx_pr'] - 1
                        if 0 <= idx < len(self._thread_ids):
                            thread_id = self._thread_ids[idx]
                            gh.post_reply(thread_id, 'Addressed in {} — @coderabbitai (debug)'.format(sha))
                    # Ask to resolve
                    self._ask_resolve_then_next(meta, success=True, error=None)
                elif choice and choice.startswith('Simulate failure'):
                    logger.error('Debug LLM: simulated failure')
                    self._ask_continue_on_error("simulated failure", meta)
            self.app.push_screen(DebugPrompt(), after)
            return
        # Normal path: invoke configured LLM and drive flow
        adapter = LlmCmdAdapter(); git = GitSubprocess()
        prompt = build_prompt(meta['pr'], meta.get('head',''), body)
        try:
            out = adapter.run(prompt)
        except Exception as e:
            logger.error('LLM invocation failed: {}'.format(e))
            self._ask_continue_on_error(str(e), meta)
            return
        js = _extract_json(out or "")
        if not js:
            logger.warn('LLM returned non-JSON; ignoring output')
            self._ask_continue_on_error('non-JSON output', meta)
            return
        success = bool(js.get('success'))
        commits = js.get('git_commits') if js.get('git_commits') is not None else js.get('commits')
        commits = commits or []
        if success:
            accepted = []
            for s in commits:
                if isinstance(s, str) and git.is_commit(s):
                    accepted.append(s)
            if accepted:
                logger.info('Commits: ' + ', '.join(accepted))
                self._commits.extend(accepted)
                self._commits_by_file.setdefault(meta['path'], []).extend(accepted)
                data2 = (ConfigFS().read() or {})
                if data2.get('reply_on_success'):
                    owner, repo = owner_repo_from_env_or_git(); gh = select_github(owner, repo)
                    idx = meta['idx_pr'] - 1
                    if 0 <= idx < len(self._thread_ids):
                        thread_id = self._thread_ids[idx]
                        gh.post_reply(thread_id, 'Addressed in {} — @coderabbitai'.format(accepted[0]))
            self._ask_resolve_then_next(meta, success=True, error=None)
        else:
            err = js.get('error') or 'unknown error'
            self._ask_continue_on_error(err, meta)

    def _ask_resolve_then_next(self, meta: dict, success: bool, error: str | None):
        class Ask(ModalScreen[str]):
            def compose(self) -> ComposeResult:
                yield Static('LLM success is true. Mark as resolved?')
                self.opts = OptionList();
                try: self.opts.add_options('Yes','No')
                except Exception:
                    try: self.opts.add_option('Yes'); self.opts.add_option('No')
                    except Exception: pass
                yield self.opts
            def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                self.dismiss(ev.option.prompt)
        def after(choice: str | None):
            # Resolve if requested, then move next
            if choice and choice.startswith('Yes'):
                owner, repo = owner_repo_from_env_or_git(); gh = select_github(owner, repo)
                idx = meta['idx_pr'] - 1
                if 0 <= idx < len(self._thread_ids):
                    thread_id = self._thread_ids[idx]
                    gh.resolve_thread(thread_id)
            next_idx = meta['idx_pr']  # 0-based next
            if next_idx < len(self._flat):
                self._show_at_index(next_idx)
                self._prompt_for_index(next_idx)
            else:
                # End of list: show summary
                self.action_summary()
        self.app.push_screen(Ask(), after)

    def _ask_continue_on_error(self, err: str, meta: dict):
        class Ask(ModalScreen[str]):
            def compose(self) -> ComposeResult:
                yield Static('LLM had an error: {}\nContinue?'.format(err))
                self.opts = OptionList();
                try: self.opts.add_options('Yes','No')
                except Exception:
                    try: self.opts.add_option('Yes'); self.opts.add_option('No')
                    except Exception: pass
                yield self.opts
            def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                self.dismiss(ev.option.prompt)
        def after(choice: str | None):
            if choice and choice.startswith('No'):
                # Return to PR picker (main menu)
                try: self.app.pop_screen()  # exit CommentViewer
                except Exception: pass
                return
            # Continue to next unresolved comment
            next_idx = meta['idx_pr']  # 0-based next
            if next_idx < len(self._flat):
                self._show_at_index(next_idx)
                self._prompt_for_index(next_idx)
            else:
                self.action_summary()
        self.app.push_screen(Ask(), after)

    def action_prev_comment(self):
        try:
            idx = max(0, self.lv.index - 1)
            self._show_at_index(idx)
            self._prompt_for_index(idx)
        except Exception:
            pass

    def action_next_comment(self):
        try:
            idx = min(len(self._flat)-1, self.lv.index + 1)
            self._show_at_index(idx)
            self._prompt_for_index(idx)
        except Exception:
            pass

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
        viewer = self
        class Batch(ModalScreen[None]):
            def __init__(self):
                super().__init__(); self.cancelled=False
            def compose(self) -> ComposeResult:
                yield Static('Batch sending remaining comments...')
                self.pb = ProgressBar(total=total)
                yield self.pb
                yield OptionList(OptionList.Option('Cancel'))
            def on_option_list_option_selected(self, ev: OptionList.OptionSelected):
                self.cancelled = True; self.dismiss(None)
            def update(self, value:int):
                try:
                    self.pb.progress = value
                except Exception:
                    pass
        modal = Batch()
        self.app.push_screen(modal)
        for idx, (path, c) in enumerate(self._flat):
            if path in self._auto_files:
                continue
            if getattr(modal, 'cancelled', False):
                break
            meta = {'pr': self.pr_number, 'head': self.head_ref, 'path': path, 'idx_pr': idx + 1, 'total_pr': total, 'idx_file': 1, 'total_file': self._counts_by_file.get(path, 1)}
            self.invoke_llm(meta, c.body); sent += 1
            try:
                modal.update(sent)
            except Exception:
                pass
            if self._logger:
                self._logger.info('Batch progress: {}/{}'.format(sent, total))
        try:
            self.app.pop_screen()
        except Exception:
            pass
