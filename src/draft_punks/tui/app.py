from __future__ import annotations
from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem
from textual.containers import Vertical
from textual.reactive import reactive
from textual import on
from textual.screen import Screen
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import enable_bonus_mode
from draft_punks.adapters.voice_say import OSXSayVoice
from draft_punks.adapters.github_select import select as select_github
from draft_punks.adapters.util.repo import owner_repo_from_env_or_git
from draft_punks.adapters.logging_textual import TextualLogger

SECRET = "BACH"

# Simple ASCII logo to make the title screen feel alive without extra deps.
# Keep to ~72 cols so it renders well on most terminals.
def _load_logo() -> str:
    import os
    txt = os.environ.get("DP_TUI_ASCII", "").strip()
    if not txt:
        path = os.environ.get("DP_TUI_ASCII_FILE", "").strip()
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return fh.read()
            except Exception:
                pass
    if txt:
        return txt
    return _DEFAULT_LOGO

_DEFAULT_LOGO = r"""
.

        d8b                       ,d8888b         
      88P                       88P'      d8P   
     d88                     d888888P  d888888P 
 d888888    88bd88b d888b8b    ?88'      ?88'   
d8P' ?88    88P'  `d8P' ?88    88P       88P    
88b  ,88b  d88     88b  ,88b  d88        88b    
`?88P'`88bd88'     `?88P'`88bd88'        `?8b   
                                                
                                                
                                                
                             d8b               
                             ?88               
                              88b              
?88,.d88b,?88   d8P  88bd88b   888  d88' .d888b,
`?88'  ?88d88   88   88P' ?8b  888bd8P'  ?8b,   
  88b  d8P?8(  d88  d88   88P d88888b      `?8b 
  888888P'`?88P'?8bd88'   88bd88' `?88b,`?888P' 
  88P'                                          
 d88                                           
 ?8P                                           
 
.
"""

class Title(Static):
    pass

class DraftPunksApp(App):
    BINDINGS = [
        ("escape", "app.quit", "Quit"),
        ("ctrl+c", "app.quit", "Quit"),
    ]
    CSS = """
    Screen { align: center middle; }
    #title { padding: 2; text-align: center; }
    """
    code = reactive("")

    def compose(self) -> ComposeResult:
        banner = _load_logo() + "\n\nDraft Punks — press ENTER to start\n(whisper a secret if you know it)"
        yield Vertical(Title(banner, id="title"))

    def on_key(self, event):  # simple secret listener
        if event.key == "enter":
            self.push_screen(PRPicker())
        else:
            ch = event.character or ''
            if ch:
                self.code += ch.upper()
                if self.code.endswith(SECRET):
                    cfg = ConfigFS()
                    v = OSXSayVoice()
                    enable_bonus_mode(cfg, v)
                    self.code = ""

class PRPicker(Screen):
    BINDINGS = [("r", "refresh", "Refresh"), ("l", "choose_llm", "LLM"), ("q","app.quit","Quit")]
    _prs = []
    def compose(self) -> ComposeResult:
        yield Vertical(Static("Select a PR (press L to choose LLM)", id="hint"), ListView(id="pr-list"))

    def on_mount(self) -> None:
        # Prompt for LLM on first open if not configured
        from draft_punks.adapters.config_fs import ConfigFS
        data = (ConfigFS().read() or {})
        if not data.get('llm') and not data.get('llm_cmd'):
            from draft_punks.tui.llm_select import LlmSelect
            self.app.push_screen(LlmSelect(), lambda _: None)
        self.action_refresh()

    def action_choose_llm(self) -> None:
        from draft_punks.tui.llm_select import LlmSelect
        self.app.push_screen(LlmSelect(), lambda _: None)

    def action_refresh(self) -> None:
        lv = self.query_one("#pr-list", ListView)
        # Clear any existing items (ok to ignore awaitable)
        try:
            lv.clear()
        except Exception:
            pass
        owner, repo = owner_repo_from_env_or_git()
        gh = select_github(owner, repo)
        self._prs = gh.list_open_prs()
        if not self._prs:
            lv.append(ListItem(Static("(no open PRs found for {}/{} — press r to retry)".format(owner, repo))))
            return
        for pr in self._prs:
            lv.append(ListItem(Static(f"- #{pr.number} ({pr.head_ref}) {pr.title}")))

    @on(ListView.Selected)
    def go_comments(self, event: ListView.Selected):
        try:
            st = event.item.query_one(Static)
            text = getattr(getattr(st, 'renderable', None), 'plain', None) or str(getattr(st, 'renderable', ''))
        except Exception:
            text = ""
        import re
        m = re.search(r"#(\d+)", text)
        if m:
            pr = int(m.group(1))
            from draft_punks.tui.comments import CommentViewer
            head='';
            try:
                head=[x.head_ref for x in self._prs if x.number==pr][0]
            except Exception:
                pass
            self.app.push_screen(CommentViewer(pr, head_ref=head, logger=TextualLogger(self.app.log)))

if __name__ == "__main__":
    DraftPunksApp().run()
