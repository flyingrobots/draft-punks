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
from ..core.domain.blocker import BlockerSeverity, BlockerType

app = typer.Typer(help="Doghouse: The PR Flight Recorder")
console = Console()

# ---------------------------------------------------------------------------
# PhiedBach's commentary on blocker transitions.
# Each resolved or added blocker gets a line that tells you *which instrument*
# came into or fell out of tune — not a generic "Beautiful counterpoint!"
# ---------------------------------------------------------------------------

_RESOLVED_FLAVOR = {
    BlockerType.UNRESOLVED_THREAD: "Ze reviewer lowers his baton — thread answered.",
    BlockerType.FAILING_CHECK: "Ze CI has found its key! Check passing.",
    BlockerType.PENDING_CHECK: "Ze stagehands have finished. Check complete.",
    BlockerType.NOT_APPROVED: "Ze conductor nods — approval restored.",
    BlockerType.DIRTY_MERGE_STATE: "Ze terrible knot is untangled! Conflict resolved.",
    BlockerType.LOCAL_UNCOMMITTED: "Ze local score is clean once more.",
    BlockerType.LOCAL_UNPUSHED: "Ze local und remote scores are back in harmony.",
    BlockerType.CODERABBIT_STATE: "BunBun settles back into his chair.",
    BlockerType.OTHER: "A minor discordance has been resolved.",
}

_ADDED_FLAVOR = {
    BlockerType.UNRESOLVED_THREAD: "A new voice joins ze chorus, demanding an answer.",
    BlockerType.FAILING_CHECK: "An instrument strikes a sour note!",
    BlockerType.PENDING_CHECK: "Ze stagehands are still setting ze stage...",
    BlockerType.NOT_APPROVED: "Ze conductor frowns und withholds his blessing.",
    BlockerType.DIRTY_MERGE_STATE: "Ze scores have become terribly tangled!",
    BlockerType.LOCAL_UNCOMMITTED: "Ze local score has unsaved notes!",
    BlockerType.LOCAL_UNPUSHED: "Ze local score races ahead of ze orchestra.",
    BlockerType.CODERABBIT_STATE: "BunBun stirs... something has changed.",
    BlockerType.OTHER: "An unexpected note appears in ze margin.",
}

_QUIET_SKIES = [
    "Quiet skies over ze trenches...",
    "Snoopy scans ze horizon. Nothing stirs.",
    "Ze Red Baron is elsewhere tonight.",
    "BunBun sips his Red Bull. All is calm.",
    "PhiedBach hums softly to himself...",
]

def _auto_detect_repo_and_pr() -> tuple[str, int]:
    """Auto-detect current repo and PR from local git/gh context."""
    try:
        repo_res = subprocess.run(["gh", "repo", "view", "--json", "name,owner"], capture_output=True, text=True, check=True, timeout=30)
        repo_data = json.loads(repo_res.stdout)
        repo_full_name = f"{repo_data['owner']['login']}/{repo_data['name']}"

        pr_res = subprocess.run(["gh", "pr", "view", "--json", "number"], capture_output=True, text=True, check=True, timeout=30)
        pr_data = json.loads(pr_res.stdout)
        return repo_full_name, int(pr_data["number"])
    except Exception as e:
        console.print(f"[red]Error: Could not detect PR context: {e}[/red]")
        sys.exit(1)


def resolve_repo_context(
    repo: Optional[str], pr: Optional[int]
) -> tuple[str, str, str, int]:
    """Resolve repo and PR from explicit args or auto-detection.

    Returns (repo_full, repo_owner, repo_name, pr_number).
    """
    if not repo or not pr:
        detected_repo, detected_pr = _auto_detect_repo_and_pr()
        repo = repo or detected_repo
        pr = pr or detected_pr

    if "/" in repo:
        owner, name = repo.split("/", 1)
    else:
        owner, name = repo, repo
    return repo, owner, name, pr

@app.command()
def snapshot(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number to snapshot"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)"),
    as_json: bool = typer.Option(False, "--json", help="Output machine-readable JSON")
):
    """Capture a snapshot of the current PR state and show the delta."""
    repo, repo_owner, repo_name, pr = resolve_repo_context(repo, pr)

    github = GhCliAdapter(repo_owner=repo_owner, repo_name=repo_name)
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
        # Use sys.stdout directly for machine JSON to avoid Rich encoding artifacts
        sys.stdout.write(json.dumps(output, indent=2) + "\n")
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
                flavor = _RESOLVED_FLAVOR.get(b.type, "Resolved.")
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = _ADDED_FLAVOR.get(b.type, "A new concern.")
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        # BunBun reacts to review thread changes
        threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
        threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
        if threads_resolved and not threads_added:
            console.print("\n[dim italic]BunBun reaches for a fresh Red Bull. His work here is done... for now.[/dim italic]")
        elif threads_added:
            console.print("\n[dim italic]BunBun's ears twitch. He sets down his Red Bull und turns to ze keyboard.[/dim italic]")
    else:
        console.print("\n[dim]First snapshot for this PR. Ze ledger is clean.[/dim]")

    # Current Blockers Table
    table = Table(title=f"Live Blockers for PR #{pr} (Ze Blocker Set)", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Impact", style="bold")
    table.add_column("Message")

    local_blockers_count = 0
    for b in snapshot.blockers:
        if b.type in [BlockerType.LOCAL_UNCOMMITTED, BlockerType.LOCAL_UNPUSHED]:
            local_blockers_count += 1

        severity_style = "red" if b.severity == BlockerSeverity.BLOCKER else "yellow"
        impact_text = "Primary" if b.is_primary else "Secondary"

        table.add_row(
            b.type.value,
            b.severity.value,
            impact_text,
            b.message,
            style=severity_style if b.severity == BlockerSeverity.BLOCKER else None
        )

    console.print(table)

    if local_blockers_count > 0:
        console.print(f"\n[bold yellow]⚠️  PhiedBach warns: Ze flight recorder sees you are mid-maneuver![/bold yellow]")
        console.print("[yellow]Your local score does not match ze remote symphony! Push your changes to sync ze score.[/yellow]")

    # The officers' club moment
    merge_ready = not (delta.added_blockers + delta.still_open_blockers)
    if merge_ready and delta.removed_blockers:
        console.print()
        console.print("[dim italic]PhiedBach removes his spectacles und folds them carefully.[/dim italic]")
        console.print("[bold green]PhiedBach's Verdict: {verdict}[/bold green]".format(verdict=delta.verdict_display))
        console.print("[dim italic]BunBun already has a Red Bull open.[/dim italic]")
    else:
        console.print(f"\n[bold green]PhiedBach's Verdict: {delta.verdict_display}[/bold green]")

from ..core.services.playback_service import PlaybackService
from pathlib import Path

@app.command()
def playback(
    name: str = typer.Argument(..., help="Name of the playback fixture directory")
):
    """Run a playback against offline fixtures to verify engine logic."""
    # Try local path first, then package-relative
    playback_path = Path("tests/doghouse/fixtures/playbacks") / name
    if not playback_path.exists():
        # Fallback to package-relative (assuming src/doghouse/cli/main.py)
        playback_path = Path(__file__).parent.parent.parent.parent / "tests" / "doghouse" / "fixtures" / "playbacks" / name

    if not playback_path.exists():
        console.print(f"[red]Error: Playback directory '{name}' not found.[/red]")
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
                flavor = _RESOLVED_FLAVOR.get(b.type, "Resolved.")
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = _ADDED_FLAVOR.get(b.type, "A new concern.")
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")
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
    console.print(f"\n[bold green]PhiedBach's Verdict: {delta.verdict_display}[/bold green]")

@app.command()
def export(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)")
):
    """Bundle PR history and metadata into a black box repro file."""
    repo, repo_owner, repo_name, pr = resolve_repo_context(repo, pr)

    storage = JSONLStorageAdapter()
    snapshots = storage.list_snapshots(repo, pr)

    github = GhCliAdapter(repo_owner=repo_owner, repo_name=repo_name)
    metadata = github.get_pr_metadata(pr)

    # Capture recent git log for context
    git_log = subprocess.run(["git", "log", "-n", "10", "--oneline"], capture_output=True, text=True).stdout

    repro_bundle = {
        "repo": repo,
        "pr_number": pr,
        "metadata": metadata,
        "git_log_recent": git_log.split("\n"),
        "snapshots": [s.to_dict() for s in snapshots]
    }

    out_path = f"doghouse_repro_PR{pr}.json"
    with open(out_path, "w") as f:
        json.dump(repro_bundle, f, indent=2)

    console.print(f"📦 [bold green]Black Box Export complete![/bold green]")
    console.print(f"Manuscript Fragment saved to: [cyan]{out_path}[/cyan]")

import time

@app.command()
def watch(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)"),
    interval: int = typer.Option(180, "--interval", help="Polling interval in seconds")
):
    """PhiedBach's Radar: Live monitoring of PR state."""
    repo, repo_owner, repo_name, pr = resolve_repo_context(repo, pr)

    console.print(f"📡 [bold]PhiedBach raises his radar dish... Monitoring {repo} PR #{pr}...[/bold]")
    console.print(f"[dim]Interval: {interval} seconds. Ctrl+C to stop dogfighting.[/dim]")

    github = GhCliAdapter(repo_owner=repo_owner, repo_name=repo_name)
    storage = JSONLStorageAdapter()
    engine = DeltaEngine()
    service = RecorderService(github, storage, engine)

    quiet_polls = 0

    try:
        while True:
            snapshot, delta = service.record_sortie(repo, pr)

            has_changes = delta.added_blockers or delta.removed_blockers or delta.head_changed
            is_first_run = not delta.baseline_sha

            if is_first_run or has_changes:
                quiet_polls = 0
                console.print(f"\n[bold blue]Radar Pulse: {snapshot.timestamp.strftime('%H:%M:%S')} 🎼[/bold blue]")

                if delta.head_changed:
                    console.print(f"  [yellow]SHA changed to {snapshot.head_sha[:7]}! A new movement begins.[/yellow]")

                if delta.removed_blockers:
                    for b in delta.removed_blockers:
                        flavor = _RESOLVED_FLAVOR.get(b.type, "Resolved.")
                        console.print(f"  [green]✓ {b.message}[/green]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                if delta.added_blockers:
                    for b in delta.added_blockers:
                        flavor = _ADDED_FLAVOR.get(b.type, "A new concern.")
                        console.print(f"  [red]+ {b.message}[/red]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                # BunBun reacts to review thread changes
                threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
                threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
                if threads_resolved and not threads_added:
                    console.print("[dim italic]BunBun reaches for a fresh Red Bull. His work here is done... for now.[/dim italic]")
                elif threads_added:
                    console.print("[dim italic]BunBun's ears twitch. He sets down his Red Bull und turns to ze keyboard.[/dim italic]")

                # The officers' club — merge-ready mid-patrol
                merge_ready = not (delta.added_blockers + delta.still_open_blockers)
                if merge_ready and delta.removed_blockers:
                    console.print()
                    console.print("[dim italic]PhiedBach removes his spectacles und folds them carefully.[/dim italic]")
                    console.print(f"[bold green]Verdict: {delta.verdict_display}[/bold green]")
                    console.print("[dim italic]BunBun already has a Red Bull open.[/dim italic]")
                else:
                    console.print(f"[bold green]Verdict: {delta.verdict_display}[/bold green]")

                # Mid-maneuver warning
                local_issues = [b for b in snapshot.blockers if b.type in [BlockerType.LOCAL_UNCOMMITTED, BlockerType.LOCAL_UNPUSHED]]
                if local_issues:
                    console.print(f"[yellow]⚠️  Radar sees you are mid-maneuver! {len(local_issues)} local issues.[/yellow]")

            else:
                quiet_polls += 1
                if quiet_polls % 3 == 0:
                    msg = _QUIET_SKIES[quiet_polls // 3 % len(_QUIET_SKIES)]
                    console.print(f"\n[dim italic]{msg} ({snapshot.timestamp.strftime('%H:%M:%S')})[/dim italic]")

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim italic]PhiedBach lowers his radar dish und closes ze ledger.[/dim italic]")
        console.print("[bold red]Rehearsal suspended. Bis bald, mein Freund.[/bold red]")

if __name__ == "__main__":
    app()
