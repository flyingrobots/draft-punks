from __future__ import annotations
from textual.screen import ModalScreen
from textual.widgets import Static, OptionList, Input
from textual.app import ComposeResult
from textual import on
from draft_punks.adapters.config_fs import ConfigFS

class LlmSelect(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        yield Static("Select an LLM provider (persisted per repo):")
        self.opts = OptionList()
        try:
            self.opts.add_options(
                "Codex",
                "Claude (JSON)",
                "Gemini",
                "Debug LLM",
                "Other (enter command template)",
            )
        except Exception:
            # Fallback for very old Textual: append items individually
            for label in [
                "Codex",
                "Claude (JSON)",
                "Gemini",
                "Other (enter command template)",
            ]:
                try:
                    self.opts.add_option(label)
                except Exception:
                    pass
        yield self.opts
        self.input = Input(placeholder="e.g., myllm -f json -p {prompt}")
        yield self.input
    
    @on(OptionList.OptionSelected)
    def choose(self, ev: OptionList.OptionSelected):
        label = ev.option.prompt
        cfg = ConfigFS()
        data = dict(cfg.read() or {})
        if label.startswith("Codex"):
            data.setdefault('llm','codex'); data.pop('llm_cmd', None)
        elif label.startswith("Claude"):
            data.setdefault('llm','claude'); data.pop('llm_cmd', None)
        elif label.startswith("Gemini"):
            data.setdefault('llm','gemini'); data.pop('llm_cmd', None)
        elif label.startswith("Debug"):
            data['llm'] = 'debug'; data.pop('llm_cmd', None)
        else:
            # focus input for template
            self.input.focus()
            return
        cfg.write(data)
        self.dismiss(True)

    @on(Input.Submitted)
    def submit_template(self, ev: Input.Submitted):
        tpl = ev.value.strip()
        if tpl:
            cfg = ConfigFS(); data = dict(cfg.read() or {})
            data['llm'] = 'other'; data['llm_cmd'] = tpl
            cfg.write(data)
            self.dismiss(True)
        else:
            self.dismiss(False)
