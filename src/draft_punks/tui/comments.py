from __future__ import annotations
from textual.app import ComposeResult
from textual.widgets import Static, ListView, ListItem, OptionList
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual import on
from draft_punks.adapters.github_ghcli import GhCliGitHub
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import speak_comment_if_allowed
from draft_punks.adapters.voice_say import OSXSayVoice
from draft_punks.core.domain.github import ReviewThread
from draft_punks.adapters.logging_textual import TextualLogger
from draft_punks.core.services.review import process_comment as process_comment_core
from draft_punks.adapters.llm_port import LlmCmdAdapter
from draft_punks.adapters.git_subprocess import GitSubprocess
from textual.screen import ModalScreen
from draft_punks.tui.llm_select import LlmSelect

class CommentViewer(Widget):
    def __init__(self, pr_number: int, head_ref: str = "", logger: TextualLogger | None = None):
        super().__init__()
        self.pr_number = pr_number
        self.head_ref = head_ref
        self._logger = logger
        self._auto_all = False
        self._auto_files = set()
        self._threads: list[ReviewThread] = []

    def compose(self) -> ComposeResult:
        self.lv = ListView(id='comments')
        self.detail = Static("Select a comment", id='detail')
        self.header = Static('', id='header')
        yield self.header
        yield Horizontal(
            Vertical(self.lv, id='left', classes='panel'),
            Vertical(self.detail, id='right', classes='panel'),
        )

    def on_mount(self):
        owner, repo = owner_repo_from_env_or_git()
        gh = GhCliGitHub(owner=owner, repo=repo)
        self._flat=[]
        counts_by_file={}
        for th in gh.iter_review_threads(self.pr_number):
            self._threads.append(th)
            for c in th.comments:
                self._flat.append((th.path,c))
                counts_by_file[th.path]=counts_by_file.get(th.path,0)+1
                label = c.body.splitlines()[0][:80]
                if self._auto_all or th.path in self._auto_files:
                    label = '[AUTO] ' + label
                if (c.author or '').lower() == 'coderabbitai':
                    label = f"BunBun says: {label}"
                self.lv.append(ListItem(Static(label)))
        self._counts_by_file=counts_by_file

    @on(ListView.Highlighted)
    def show_detail(self, event: ListView.Highlighted):
        idx = event.index
        k = 0
        for th in self._threads:
            for c in th.comments:
                if k == idx:
                    md = c.body
                    self.detail.update(f"````markdown\n{md}\n````")
        # header update
        idx=event.index
        path,_=self._flat[idx]
        total_pr=len(self._flat); total_file=self._counts_by_file.get(path,1)
        # compute index-in-file
        pos_file=1
        for i,(p,_) in enumerate(self._flat):
            if i==idx: break
            if p==path: pos_file+=1
        pct=int((idx+1)*100/max(1,total_pr))
        self.header.update(f"PR #{self.pr_number} ({self.head_ref}) • {path}
Comment {idx+1} of {total_pr} ({pos_file} of {total_file} in this file)\n{pct}%")
                    cfg = ConfigFS()
                    speak_comment_if_allowed(cfg, OSXSayVoice(), author_login=c.author or '', text=c.body)
                    return
                k += 1


class CommentPrompt(ModalScreen[dict]):
    def __init__(self, meta: dict, body: str):
        super().__init__(); self.meta=meta; self.body=body
    def compose(self) -> 'ComposeResult':
        from textual.app import ComposeResult as _CR
        hdr=(f"PR #{self.meta['pr']} ({self.meta.get('head','')}) • {self.meta.get('path','')}\n"
             f"Comment {self.meta['idx_pr']} of {self.meta['total_pr']} ("
             f"{self.meta['idx_file']} of {self.meta['total_file']} in this file)")
        yield Static(hdr)
        yield Static(f"````markdown\n{self.body}\n````")
        self.opts=OptionList(OptionList.Option('Yes'),
            OptionList.Option('Yes, but let me rewrite it'),
            OptionList.Option('Yes, and send all comments in this file automatically'),
            OptionList.Option('Yes, and send all comments in general automatically'),
            OptionList.Option('No, skip this comment'),
            OptionList.Option('No, skip this file'),
            OptionList.Option('I need to adjust the LLM command or switch LLMs'),
            OptionList.Option('Quit'))
        yield self.opts
    def on_option_list_option_selected(self, ev):
        self.dismiss({'choice': ev.option.prompt, 'body': self.body})

    @on(ListView.Selected)
    def act_on_comment(self, event: ListView.Selected):
        idx=event.index; path,c=self._flat[idx]
        total_pr=len(self._flat); total_file=self._counts_by_file.get(path,1)
        n_file=1
        for i,(p,_) in enumerate(self._flat):
            if i==idx: break
            if p==path: n_file+=1
        meta={'pr':self.pr_number,'head':self.head_ref,'path':path,'idx_pr':idx+1,'total_pr':total_pr,'idx_file':n_file,'total_file':total_file}
        if self._auto_all or path in self._auto_files:
            self.invoke_llm(meta, c.body); return
        prompt=CommentPrompt(meta, c.body)
        self._pending=(idx,meta,c)
        self.app.push_screen(prompt, self.handle_choice)

    def handle_choice(self, res: dict | None):
        if not res or not hasattr(self,'_pending'): return
        idx,meta,c=self._pending
        choice=res.get('choice') if res else 'No, skip this comment'
        if choice.startswith('Yes, and send all comments in general'):
            self._auto_all=True; self.invoke_llm(meta, c.body)
        elif choice.startswith('Yes, and send all comments in this file'):
            self._auto_files.add(meta['path']); self.invoke_llm(meta, c.body)
        elif choice.startswith('Yes, but let me rewrite'):
            self.invoke_llm(meta, c.body)
        elif choice=='Yes':
            self.ensure_llm_selected(); self.invoke_llm(meta, c.body)
        elif choice.startswith('I need to adjust the LLM'):
            self.app.push_screen(LlmSelect(), lambda _: None)
        elif choice.startswith('No, skip this file'):
            self._auto_files.add(meta['path'])
        elif choice.startswith('Quit'):
            self.app.exit()
        del self._pending

    def ensure_llm_selected(self):
        cfg=ConfigFS(); data=cfg.read() or {}
        if not data.get('llm') and not data.get('llm_cmd'):
            self.app.push_screen(LlmSelect(), lambda _: None)

    def invoke_llm(self, meta: dict, body: str):
        logger=self._logger or TextualLogger(self.app.log)
        adapter=LlmCmdAdapter(); git=GitSubprocess()
        commits=process_comment_core(pr_number=meta['pr'], head_ref=meta.get('head',''), body=body, llm=adapter, git=git, log=logger)
        if commits: logger.info('Commits: '+', '.join(commits))
        else: logger.warn('No commits reported or JSON invalid.')
