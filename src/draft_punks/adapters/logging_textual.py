from __future__ import annotations
from typing import Optional
from textual.widgets import Log as TLog
from rich.markdown import Markdown
from draft_punks.ports.logging import LoggingPort

class TextualLogger(LoggingPort):
    def __init__(self, log_widget: TLog):
        self._log = log_widget
    def info(self, msg: str) -> None:
        self._log.write(f"[cyan]INFO[/]: {msg}")
    def warn(self, msg: str) -> None:
        self._log.write(f"[yellow]WARN[/]: {msg}")
    def error(self, msg: str) -> None:
        self._log.write(f"[red]ERROR[/]: {msg}")
    def markdown(self, md: str) -> None:
        self._log.write(Markdown(md))
