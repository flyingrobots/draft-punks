import random
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


def _pick(variations: list[str]) -> str:
    """Choose a random variation from a list."""
    return random.choice(variations)


# ---------------------------------------------------------------------------
# PhiedBach's commentary on blocker transitions — 5 variations each.
# Each resolved or added blocker gets a line that tells you *which instrument*
# came into or fell out of tune.
# ---------------------------------------------------------------------------

_RESOLVED_FLAVOR = {
    BlockerType.UNRESOLVED_THREAD: [
        "Ze reviewer lowers his baton — thread answered.",
        "Gut, gut! Ze voice has been heard und acknowledged.",
        "BunBun nods once. Ze thread is settled.",
        "One less voice crying in ze wilderness of ze diff.",
        "Ze conversation concludes. Harmony returns to zis passage.",
    ],
    BlockerType.FAILING_CHECK: [
        "Ze CI has found its key! Check passing.",
        "Wunderbar! Ze instrument is back in tune.",
        "Ze sour note resolves into a perfect fifth.",
        "BunBun's build lights turn green. Ze orchestra breathes.",
        "Ze check passes! A small victory in ze grand symphony.",
    ],
    BlockerType.PENDING_CHECK: [
        "Ze stagehands have finished. Check complete.",
        "Ze curtain rises — ze stage is ready.",
        "Ze preparation is done. Ve may proceed.",
        "Ze backstage crew gives ze thumbs up.",
        "No more vaiting. Ze check has concluded.",
    ],
    BlockerType.NOT_APPROVED: [
        "Ze conductor nods — approval restored.",
        "Ze blessing is given! Ze performance may continue.",
        "Ze conductor raises his baton — ve have approval.",
        "Ah! Ze maestro has signed ze score. Sehr gut.",
        "Ze seal of approval is pressed into ze vax. Gut.",
    ],
    BlockerType.DIRTY_MERGE_STATE: [
        "Ze terrible knot is untangled! Conflict resolved.",
        "Ze tangled scores are separated! Clarity returns.",
        "Ze knot in ze manuscript is undone. Wunderbar!",
        "Ze conflicting voices find zeir resolution at last.",
        "Order is restored to ze sheet music. Ze conflict is no more.",
    ],
    BlockerType.LOCAL_UNCOMMITTED: [
        "Ze local score is clean once more.",
        "All notes are properly filed in ze local ledger.",
        "Ze desk is tidy. No stray pages remain.",
        "Ze local manuscript is in order.",
        "PhiedBach nods. Ze quill has caught up vith ze thoughts.",
    ],
    BlockerType.LOCAL_UNPUSHED: [
        "Ze local und remote scores are back in harmony.",
        "Ze courier has delivered ze pages. Local und remote agree.",
        "Ze pigeon has arrived. Ze scores are synchronized.",
        "Ze local ledger matches ze cathedral's copy.",
        "No more secrets on ze local desk — all is shared.",
    ],
    BlockerType.CODERABBIT_STATE: [
        "BunBun settles back into his chair.",
        "BunBun's ears relax. Ze situation is handled.",
        "BunBun reaches for his Red Bull. Crisis averted.",
        "BunBun thumps his hind leg softly. All is vell.",
        "Ze rabbit is at peace. For now.",
    ],
    BlockerType.OTHER: [
        "A minor discordance has been resolved.",
        "A stray note has been erased from ze margin.",
        "Ze anomaly is corrected. Ve move on.",
        "Gut. One less thing to vorry about.",
        "Ze ledger is a little cleaner now.",
    ],
}

_ADDED_FLAVOR = {
    BlockerType.UNRESOLVED_THREAD: [
        "A new voice joins ze chorus, demanding an answer.",
        "BunBun's ears perk up. A new review comment appears.",
        "Ze reviewer has spoken! A new thread demands attention.",
        "A fresh note appears in ze margin of ze score.",
        "Someone has raised zeir hand in ze back of ze concert hall.",
    ],
    BlockerType.FAILING_CHECK: [
        "An instrument strikes a sour note!",
        "Ze orchestra winces. A check has failed.",
        "A terrible screech from ze CI section!",
        "BunBun's build lights flash red. Something is wrong.",
        "Ze pitch is off! A check needs attention.",
    ],
    BlockerType.PENDING_CHECK: [
        "Ze stagehands are still setting ze stage...",
        "Ze backstage crew is preparing. Patience.",
        "A check has begun its vork. Ve must vait.",
        "Ze gears are turning behind ze curtain.",
        "Something is brewing in ze CI kitchen...",
    ],
    BlockerType.NOT_APPROVED: [
        "Ze conductor frowns und withholds his blessing.",
        "Ze maestro shakes his head. Not yet approved.",
        "Ze approval stamp remains locked in ze drawer.",
        "Ze conductor's baton stays lowered. No approval.",
        "Ze seal of approval is not forthcoming.",
    ],
    BlockerType.DIRTY_MERGE_STATE: [
        "Ze scores have become terribly tangled!",
        "Mein Gott! Ze pages of ze score are stuck together!",
        "A terrible knot forms in ze manuscript!",
        "Ze voices clash! A merge conflict has appeared.",
        "Ze sheet music is in disarray. Conflict detected.",
    ],
    BlockerType.LOCAL_UNCOMMITTED: [
        "Ze local score has unsaved notes!",
        "Stray pages litter PhiedBach's desk!",
        "Ze quill has been busy but ze ink is not yet dry.",
        "Uncommitted changes lurk on ze local stage.",
        "Ze local manuscript has unpressed pages.",
    ],
    BlockerType.LOCAL_UNPUSHED: [
        "Ze local score races ahead of ze orchestra.",
        "Ze courier vaits — local commits have not been sent.",
        "Ze local ledger knows things ze remote does not.",
        "PhiedBach has written ahead but not shared ze pages.",
        "Ze pigeon sits idle. Commits remain undelivered.",
    ],
    BlockerType.CODERABBIT_STATE: [
        "BunBun stirs... something has changed.",
        "BunBun's ears twitch. A disturbance in ze review.",
        "Ze rabbit senses a shift in ze code.",
        "BunBun pauses mid-sip. Something is different.",
        "BunBun looks up from his keyboard. Ze wind has changed.",
    ],
    BlockerType.OTHER: [
        "An unexpected note appears in ze margin.",
        "A curious annotation has appeared in ze score.",
        "Something new und unclassified enters ze ledger.",
        "PhiedBach squints. Vhat is zis?",
        "An unfamiliar mark on ze manuscript...",
    ],
}

# ---------------------------------------------------------------------------
# One-off character moments — 5 variations each.
# ---------------------------------------------------------------------------

_SNAPSHOT_OPENING = [
    "PhiedBach adjusts his spectacles... Capturing sortie for {repo} PR #{pr}...",
    "PhiedBach dips his quill... Recording ze state of {repo} PR #{pr}...",
    "PhiedBach opens ze great ledger... Snapshotting {repo} PR #{pr}...",
    "PhiedBach peers through his spectacles at {repo} PR #{pr}...",
    "PhiedBach raises his magnifying glass... Inspecting {repo} PR #{pr}...",
]

_SNAPSHOT_SUBTEXT = [
    "BunBun thumps his leg in approval...",
    "BunBun's ears rotate toward ze screen...",
    "BunBun cracks open a fresh Red Bull...",
    "BunBun's paws hover over ze keyboard, ready...",
    "BunBun adjusts his ThinkPad und leans in...",
]

_FIRST_SNAPSHOT = [
    "First snapshot for this PR. Ze ledger is clean.",
    "A fresh page in ze great ledger. No prior sorties recorded.",
    "Ze very first sortie for zis PR. History begins now.",
    "No baseline exists yet. Zis is ze opening note.",
    "A blank page awaits. Ze first snapshot is captured.",
]

_SHA_CHANGED = [
    "SHA changed: {old} -> {new} (A new movement begins!)",
    "SHA changed: {old} -> {new} (Ze score has been revised!)",
    "SHA changed: {old} -> {new} (A fresh draft enters ze stage!)",
    "SHA changed: {old} -> {new} (Ze composition evolves!)",
    "SHA changed: {old} -> {new} (New ink on ze manuscript!)",
]

_BUNBUN_THREADS_RESOLVED = [
    "BunBun reaches for a fresh Red Bull. His work here is done... for now.",
    "BunBun crushes an empty can und adds it to ze tower. Threads clear.",
    "BunBun leans back in his chair. Ze review threads are answered.",
    "BunBun's typing stops. Ze keyboard falls silent. Threads resolved.",
    "BunBun thumps his hind leg twice — ze universal signal for 'gut gemacht.'",
]

_BUNBUN_THREADS_ADDED = [
    "BunBun's ears twitch. He sets down his Red Bull und turns to ze keyboard.",
    "BunBun's nose twitches. New review threads have arrived.",
    "BunBun looks up sharply. Someone has left comments on ze score.",
    "TSST-KRRRK! BunBun opens a fresh Red Bull. New threads to address.",
    "BunBun's paws are already moving. Ze reviewer has spoken.",
]

_MID_MANEUVER_TITLE = [
    "PhiedBach warns: Ze flight recorder sees you are mid-maneuver!",
    "PhiedBach raises an eyebrow: Ze local score is not in sync!",
    "PhiedBach taps his quill nervously: Local changes detected!",
    "PhiedBach adjusts his spectacles mit concern: You have local drift!",
    "PhiedBach clears his throat: Achtung! Ze local state is unsettled!",
]

_MID_MANEUVER_DETAIL = [
    "Your local score does not match ze remote symphony! Push your changes to sync ze score.",
    "Ze pages on your desk do not match ze cathedral's copy. Commit und push!",
    "Ze local und remote manuscripts have diverged. Synchronize before your next sortie.",
    "Your local stage has unpublished work. Ze orchestra cannot hear vhat you have not sent.",
    "Ze courier vaits at ze door. Push your changes so ze ensemble can see zem.",
]

_OFFICERS_CLUB_SPECTACLES = [
    "PhiedBach removes his spectacles und folds them carefully.",
    "PhiedBach sets down his quill und exhales slowly.",
    "PhiedBach closes ze great ledger vith a satisfied thump.",
    "PhiedBach straightens his powdered wig und smiles.",
    "PhiedBach leans back in his wingback chair und closes his eyes.",
]

_OFFICERS_CLUB_REDBULL = [
    "BunBun already has a Red Bull open.",
    "BunBun adds another crushed can to ze wobbling tower.",
    "BunBun's ears relax for ze first time today.",
    "BunBun thumps his hind leg — ze ceremony is complete.",
    "BunBun produces a tiny party horn from behind his ThinkPad.",
]

_WATCH_OPENING = [
    "PhiedBach raises his radar dish... Monitoring {repo} PR #{pr}...",
    "PhiedBach climbs atop ze doghouse... Scanning {repo} PR #{pr}...",
    "Snoopy — er, PhiedBach — mounts his Sopwith Camel. Watching {repo} PR #{pr}...",
    "PhiedBach adjusts ze antenna... Radar locked on {repo} PR #{pr}...",
    "PhiedBach straps on his flying goggles... Patrolling {repo} PR #{pr}...",
]

_WATCH_INTERVAL = [
    "Interval: {interval} seconds. Ctrl+C to stop dogfighting.",
    "Polling every {interval} seconds. Ctrl+C to land ze plane.",
    "Scanning every {interval} seconds. Ctrl+C to return to base.",
    "Radar sweep: {interval} seconds. Ctrl+C to lower ze dish.",
    "Sortie interval: {interval} seconds. Ctrl+C to end ze patrol.",
]

_WATCH_SHA_CHANGED = [
    "SHA changed to {sha}! A new movement begins.",
    "SHA changed to {sha}! Ze score has been revised mid-flight.",
    "SHA changed to {sha}! New ink on ze manuscript below.",
    "SHA changed to {sha}! Ze composition shifts beneath us.",
    "SHA changed to {sha}! A fresh draft rises from ze trenches.",
]

_WATCH_EXIT_1 = [
    "PhiedBach lowers his radar dish und closes ze ledger.",
    "PhiedBach removes his flying goggles und descends from ze doghouse.",
    "Ze Sopwith Camel touches down gently on ze lawn.",
    "PhiedBach folds his maps und extinguishes ze radar lamp.",
    "Ze antenna retracts. Ze patrol is over.",
]

_WATCH_EXIT_2 = [
    "Rehearsal suspended. Bis bald, mein Freund.",
    "Until ve meet again at ze aerodrome. Auf Wiedersehen.",
    "Ze Red Baron vill vait. Rest now, mein Freund.",
    "Ze skies vill be here tomorrow. Go get some sleep.",
    "PhiedBach tips his powdered wig. Bis zum nächsten Mal.",
]

_WATCH_MID_MANEUVER = [
    "Radar sees you are mid-maneuver! {n} local issues.",
    "From ze air, PhiedBach spots local drift! {n} issues below.",
    "Ze radar pings local turbulence! {n} issues on ze ground.",
    "PhiedBach radios down: local state unsettled! {n} issues detected.",
    "Achtung! Ze ground crew reports {n} local issues.",
]

_QUIET_SKIES = [
    "Quiet skies over ze trenches...",
    "Snoopy scans ze horizon. Nothing stirs.",
    "Ze Red Baron is elsewhere tonight.",
    "BunBun sips his Red Bull. All is calm.",
    "PhiedBach hums softly to himself...",
    "Ze wind carries only silence across ze aerodrome...",
    "Nothing on ze radar. Ze symphony rests.",
    "Even ze synthesizers have gone quiet...",
    "PhiedBach adjusts his spectacles und vaits...",
    "Ze trenches are peaceful. A rare moment.",
]

_PLAYBACK_OPENING = [
    "PhiedBach raises his baton... Running playback: {name}",
    "PhiedBach places ze needle on ze record... Playback: {name}",
    "PhiedBach unrolls ze paper piano roll... Replaying: {name}",
    "Ze Pianola begins to play... Running playback: {name}",
    "PhiedBach threads ze punched tape... Playback: {name}",
]

_PLAYBACK_SHA_CHANGED = [
    "SHA changed: {old} -> {new} (A shift in ze score!)",
    "SHA changed: {old} -> {new} (Ze composition moved between takes!)",
    "SHA changed: {old} -> {new} (Ze manuscript was revised!)",
    "SHA changed: {old} -> {new} (A different draft on ze music stand!)",
    "SHA changed: {old} -> {new} (Ze ink dried differently zis time!)",
]

_PLAYBACK_NO_BASELINE = [
    "No baseline for this playback score.",
    "Ze Pianola has no prior recording to compare against.",
    "A solo performance — no baseline exists for zis playback.",
    "Ze paper roll begins from silence. No prior take recorded.",
    "No earlier version of zis score exists in ze archive.",
]

_EXPORT_COMPLETE = [
    "Black Box Export complete!",
    "Ze flight recorder data has been extracted!",
    "Ze manuscript fragment is sealed und ready.",
    "Ze black box has been recovered from ze wreckage!",
    "Export complete! Ze evidence is preserved.",
]

_EXPORT_SAVED = [
    "Manuscript Fragment saved to: [cyan]{path}[/cyan]",
    "Ze bundle is filed at: [cyan]{path}[/cyan]",
    "PhiedBach stamps ze wax seal. Saved to: [cyan]{path}[/cyan]",
    "Ze evidence is catalogued at: [cyan]{path}[/cyan]",
    "Ze repro bundle rests at: [cyan]{path}[/cyan]",
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

    console.print(f"📡 [bold]{_pick(_SNAPSHOT_OPENING).format(repo=repo, pr=pr)}[/bold]")
    console.print(f"[dim italic]{_pick(_SNAPSHOT_SUBTEXT)}[/dim italic]")

    console.print(f"\n[bold blue]Snapshot captured at {snapshot.timestamp} 🎼[/bold blue]")
    console.print(f"SHA: [dim]{snapshot.head_sha}[/dim]")

    # Show Delta
    if delta.baseline_sha:
        console.print(f"\n[bold]Ze Delta against {delta.baseline_timestamp}:[/bold]")
        if delta.head_changed:
            console.print("  [yellow]{msg}[/yellow]".format(
                msg=_pick(_SHA_CHANGED).format(old=delta.baseline_sha[:7], new=snapshot.head_sha[:7])
            ))

        if delta.removed_blockers:
            for b in delta.removed_blockers:
                flavor = _pick(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = _pick(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        # BunBun reacts to review thread changes
        threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
        threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
        if threads_resolved and not threads_added:
            console.print(f"\n[dim italic]{_pick(_BUNBUN_THREADS_RESOLVED)}[/dim italic]")
        elif threads_added:
            console.print(f"\n[dim italic]{_pick(_BUNBUN_THREADS_ADDED)}[/dim italic]")
    else:
        console.print(f"\n[dim]{_pick(_FIRST_SNAPSHOT)}[/dim]")

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
        console.print(f"\n[bold yellow]⚠️  {_pick(_MID_MANEUVER_TITLE)}[/bold yellow]")
        console.print(f"[yellow]{_pick(_MID_MANEUVER_DETAIL)}[/yellow]")

    # The officers' club moment
    merge_ready = not (delta.added_blockers + delta.still_open_blockers)
    if merge_ready and delta.removed_blockers:
        console.print()
        console.print(f"[dim italic]{_pick(_OFFICERS_CLUB_SPECTACLES)}[/dim italic]")
        console.print("[bold green]PhiedBach's Verdict: {verdict}[/bold green]".format(verdict=delta.verdict_display))
        console.print(f"[dim italic]{_pick(_OFFICERS_CLUB_REDBULL)}[/dim italic]")
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

    console.print(f"🎬 [bold]{_pick(_PLAYBACK_OPENING).format(name=name)}[/bold]")

    # Show Delta
    if baseline:
        console.print(f"\n[bold]Ze Delta against {baseline.timestamp}:[/bold]")
        if delta.head_changed:
            console.print("  [yellow]{msg}[/yellow]".format(
                msg=_pick(_PLAYBACK_SHA_CHANGED).format(old=baseline.head_sha[:7], new=current.head_sha[:7])
            ))

        if delta.removed_blockers:
            for b in delta.removed_blockers:
                flavor = _pick(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = _pick(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")
    else:
        console.print(f"\n[dim]{_pick(_PLAYBACK_NO_BASELINE)}[/dim]")

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

    console.print(f"📦 [bold green]{_pick(_EXPORT_COMPLETE)}[/bold green]")
    console.print(_pick(_EXPORT_SAVED).format(path=out_path))

import time

@app.command()
def watch(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)"),
    interval: int = typer.Option(180, "--interval", help="Polling interval in seconds")
):
    """PhiedBach's Radar: Live monitoring of PR state."""
    repo, repo_owner, repo_name, pr = resolve_repo_context(repo, pr)

    console.print(f"📡 [bold]{_pick(_WATCH_OPENING).format(repo=repo, pr=pr)}[/bold]")
    console.print(f"[dim]{_pick(_WATCH_INTERVAL).format(interval=interval)}[/dim]")

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
                    console.print("  [yellow]{msg}[/yellow]".format(
                        msg=_pick(_WATCH_SHA_CHANGED).format(sha=snapshot.head_sha[:7])
                    ))

                if delta.removed_blockers:
                    for b in delta.removed_blockers:
                        flavor = _pick(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                        console.print(f"  [green]✓ {b.message}[/green]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                if delta.added_blockers:
                    for b in delta.added_blockers:
                        flavor = _pick(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                        console.print(f"  [red]+ {b.message}[/red]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                # BunBun reacts to review thread changes
                threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
                threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
                if threads_resolved and not threads_added:
                    console.print(f"[dim italic]{_pick(_BUNBUN_THREADS_RESOLVED)}[/dim italic]")
                elif threads_added:
                    console.print(f"[dim italic]{_pick(_BUNBUN_THREADS_ADDED)}[/dim italic]")

                # The officers' club — merge-ready mid-patrol
                merge_ready = not (delta.added_blockers + delta.still_open_blockers)
                if merge_ready and delta.removed_blockers:
                    console.print()
                    console.print(f"[dim italic]{_pick(_OFFICERS_CLUB_SPECTACLES)}[/dim italic]")
                    console.print(f"[bold green]Verdict: {delta.verdict_display}[/bold green]")
                    console.print(f"[dim italic]{_pick(_OFFICERS_CLUB_REDBULL)}[/dim italic]")
                else:
                    console.print(f"[bold green]Verdict: {delta.verdict_display}[/bold green]")

                # Mid-maneuver warning
                local_issues = [b for b in snapshot.blockers if b.type in [BlockerType.LOCAL_UNCOMMITTED, BlockerType.LOCAL_UNPUSHED]]
                if local_issues:
                    console.print("[yellow]⚠️  {msg}[/yellow]".format(
                        msg=_pick(_WATCH_MID_MANEUVER).format(n=len(local_issues))
                    ))

            else:
                quiet_polls += 1
                if quiet_polls % 3 == 0:
                    console.print(f"\n[dim italic]{_pick(_QUIET_SKIES)} ({snapshot.timestamp.strftime('%H:%M:%S')})[/dim italic]")

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print(f"\n[dim italic]{_pick(_WATCH_EXIT_1)}[/dim italic]")
        console.print(f"[bold red]{_pick(_WATCH_EXIT_2)}[/bold red]")

if __name__ == "__main__":
    app()
