from __future__ import annotations
from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem
from textual.containers import Vertical
from textual.reactive import reactive
from textual import on
from draft_punks.adapters.config_fs import ConfigFS
from draft_punks.core.services.voice import enable_bonus_mode
from draft_punks.adapters.voice_say import OSXSayVoice

SECRET = "BACH"

class Title(Static):
    pass

class DraftPunksApp(App):
    CSS = """
    Screen { align: center middle; }
    #title { padding: 2; }
    """
    code = reactive("")

    def compose(self) -> ComposeResult:
        yield Vertical(Title("Draft Punks — press ENTER to start\n(whisper a secret if you know it)", id="title"))

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

class PRPicker(Vertical):
    def compose(self) -> ComposeResult:
        lv = ListView()
        # Placeholder; real list via GitHubPort later
        for line in ["- #74 (chore/issues-roadmap) planning ...", "- #123 (feat/tui) python TUI"]:
            lv.append(ListItem(Static(line)))
        yield lv

if __name__ == "__main__":
    DraftPunksApp().run()
