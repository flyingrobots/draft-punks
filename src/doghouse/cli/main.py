import typer
import sys
import subprocess
import json
import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from ..core.services.recorder_service import RecorderService
from ..core.services.delta_engine import DeltaEngine
from ..adapters.github.gh_cli_adapter import GhCliAdapter
from ..adapters.storage.jsonl_adapter import JSONLStorageAdapter
from ..core.domain.blocker import BlockerSeverity

app = typer.Typer(help="Doghouse: The PR Flight Recorder")
console = Console()

def get_current_repo_and_pr() -> tuple[str, int]:
    """Auto-detect current repo and PR from context."""
    try:
        # Detect repo
        repo_res = subprocess.run(["gh", "repo", "view", "--json", "name,owner"], capture_output=True, text=True, check=True)
        repo_data = json.loads(repo_res.stdout)
        repo_full_name = f"{repo_data['owner']['login']}/{repo_data['name']}"
        
        # Detect current PR (branch-based)
        pr_res = subprocess.run(["gh", "pr", "view", "--json", "number"], capture_output=True, text=True, check=True)
        pr_data = json.loads(pr_res.stdout)
        return repo_full_name, int(pr_data["number"])
    except Exception as e:
        console.print(f"[red]Error: Could not detect PR context: {e}[/red]")
        sys.exit(1)

@app.command()
def snapshot(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number to snapshot"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)"),
    as_json: bool = typer.Option(False, "--json", help="Output machine-readable JSON")
):
    """Capture a snapshot of the current PR state and show the delta."""
    if not repo or not pr:
        detected_repo, detected_pr = get_current_repo_and_pr()
        repo = repo or detected_repo
        pr = pr or detected_pr

    github = GhCliAdapter()
    storage = JSONLStorageAdapter()
    engine = DeltaEngine()
    service = RecorderService(github, storage, engine)

    snapshot, delta = service.record_sortie(repo, pr)

    if as_json:
        output = {
            "snapshot": snapshot.to_dict(),
            "delta": {
                "baseline_timestamp": delta.baseline_timestamp,
                "head_changed": delta.head_changed,
                "added_blockers": [b.id for b in delta.added_blockers],
                "removed_blockers": [b.id for b in delta.removed_blockers],
                "verdict": delta.verdict
            }
        }
        console.print(json.dumps(output, indent=2))
        return

    console.print(f"📡 [bold]PhiedBach adjusts his spectacles... Capturing sortie for {repo} PR #{pr}...[/bold]")
    console.print("[dim italic]BunBun thumps his leg in approval...[/dim italic]")

    console.print(f"\n[bold blue]Snapshot captured at {snapshot.timestamp} 🎼[/bold blue]")
    console.print(f"SHA: [dim]{snapshot.head_sha}[/dim]")
    
    # Show Delta
    if delta.baseline_sha:
        console.print(f"\n[bold]Ze Delta against {delta.baseline_timestamp}:[/bold]")
        if delta.head_changed:
            console.print(f"  [yellow]SHA changed: {delta.baseline_sha[:7]} -> {snapshot.head_sha[:7]} (A new movement begins!)[/yellow]")
            
        if delta.removed_blockers:
            for b in delta.removed_blockers:
                console.print(f"  [green]✓ Resolved: {b.message} (Beautiful counterpoint!)[/green]")
        
        if delta.added_blockers:
            for b in delta.added_blockers:
                console.print(f"  [red]+ New: {b.message} (A discordant note arrives!)[/red]")
    else:
        console.print("\n[dim]First snapshot for this PR. Ze ledger is clean.[/dim]")

    # Current Blockers Table
    table = Table(title=f"Live Blockers for PR #{pr} (Ze Blocker Set)", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Message")
    
    for b in snapshot.blockers:
        severity_style = "red" if b.severity == BlockerSeverity.BLOCKER else "yellow"
        table.add_row(b.type.value, b.severity.value, b.message, style=severity_style if b.severity == BlockerSeverity.BLOCKER else None)
        
    console.print(table)
    
    console.print(f"\n[bold green]PhiedBach's Verdict: {delta.verdict}[/bold green]")

from ..core.services.playback_service import PlaybackService
from pathlib import Path

@app.command()
def playback(
    name: str = typer.Argument(..., help="Name of the playback fixture directory")
):
    """Run a playback against offline fixtures to verify engine logic."""
    playback_path = Path("tests/doghouse/fixtures/playbacks") / name
    if not playback_path.exists():
        console.print(f"[red]Error: Playback directory '{playback_path}' not found.[/red]")
        sys.exit(1)
        
    engine = DeltaEngine()
    service = PlaybackService(engine)
    
    baseline, current, delta = service.run_playback(playback_path)
    
    console.print(f"🎬 [bold]PhiedBach raises his baton... Running playback: {name}[/bold]")
    
    # Show Delta
    if baseline:
        console.print(f"\n[bold]Ze Delta against {baseline.timestamp}:[/bold]")
        if delta.head_changed:
            console.print(f"  [yellow]SHA changed: {baseline.head_sha[:7]} -> {current.head_sha[:7]} (A shift in ze score!)[/yellow]")
            
        if delta.removed_blockers:
            for b in delta.removed_blockers:
                console.print(f"  [green]✓ Resolved: {b.message} (Harmony is restored!)[/green]")
        
        if delta.added_blockers:
            for b in delta.added_blockers:
                console.print(f"  [red]+ New: {b.message} (An unexpected dissonance!)[/red]")
    else:
        console.print("\n[dim]No baseline for this playback score.[/dim]")

    # Current Blockers Table
    table = Table(title=f"Current Blockers (Playback: {name})", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Message")
    
    for b in current.blockers:
        severity_style = "red" if b.severity == BlockerSeverity.BLOCKER else "yellow"
        table.add_row(b.type.value, b.severity.value, b.message, style=severity_style if b.severity == BlockerSeverity.BLOCKER else None)
        
    console.print(table)
    console.print(f"\n[bold green]PhiedBach's Verdict: {delta.verdict}[/bold green]")

if __name__ == "__main__":
    app()
