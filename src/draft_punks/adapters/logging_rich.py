from __future__ import annotations
from rich.console import Console
from rich.markdown import Markdown
from draft_punks.ports.logging import LoggingPort

class RichLogger(LoggingPort):
    def __init__(self, console: Console | None = None):
        self._c = console or Console()
    def info(self, msg: str) -> None:
        self._c.print(f"[cyan]INFO[/]: {msg}")
    def warn(self, msg: str) -> None:
        self._c.print(f"[yellow]WARN[/]: {msg}")
    def error(self, msg: str) -> None:
        self._c.print(f"[red]ERROR[/]: {msg}")
    def markdown(self, md: str) -> None:
        self._c.print(Markdown(md))
