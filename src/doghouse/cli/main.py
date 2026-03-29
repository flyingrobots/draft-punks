import datetime
import json
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..adapters.git.git_adapter import GitAdapter
from ..adapters.github.gh_cli_adapter import GhCliAdapter
from ..adapters.storage.jsonl_adapter import JSONLStorageAdapter
from ..core.domain.blocker import BlockerSeverity, BlockerType
from ..core.domain.delta import Delta
from ..core.services.delta_engine import DeltaEngine
from ..core.services.playback_service import PlaybackService
from ..core.services.recorder_service import RecorderService

app = typer.Typer(help="Doghouse: The PR Flight Recorder")
console = Console()


# ---------------------------------------------------------------------------
# PhiedBach's theatrical verdicts — 5 variations each, randomly chosen.
# The machine-readable verdict (Delta.verdict) stays terse and stable.
# These lists live in the CLI layer because randomness is a presentation
# concern, not a domain concern.
# ---------------------------------------------------------------------------

_V_MERGE_READY = [
    "Ze orchestra is in tune. You may merge, mein Freund. 🎼",
    "Ze symphony is complete! Merge vhen you are ready. 🎼",
    "All voices are in harmony. Ze merge gate is open. 🎼",
    "Not a single note out of place. Merge avay! 🎼",
    "Ze score is flawless. PhiedBach beams. You may merge. 🎼",
]

_V_MERGE_CONFLICT = [
    "Ze score has a terrible knot! Resolve ze merge conflicts before anything else. ⚔️",
    "Mein Gott — ze pages are stuck together! Untangle ze conflicts first. ⚔️",
    "Ze voices clash in ze worst vay! Fix ze merge conflicts. ⚔️",
    "Ze manuscript is in disarray! No progress until ze conflicts are resolved. ⚔️",
    "A terrible knot in ze score! Nothing else matters until zis is undone. ⚔️",
]

_V_FAILING_CHECKS = [
    "{n} {noun} {verb} out of tune! Fix ze failing checks. 🛑",
    "{n} {noun} {verb} hitting sour notes! Ze CI section needs attention. 🛑",
    "{n} {noun} {verb} screeching! Fix ze checks before ze audience notices. 🛑",
    "Ze CI section reports {n} {noun} off-key! Attend to zem. 🛑",
    "{n} {noun} {verb} playing in ze wrong key entirely! Fix ze failing checks. 🛑",
]

_V_UNRESOLVED_THREADS = [
    "{n} {noun} {verb} unanswered. Address ze review feedback. 💬",
    "{n} {noun} {verb} calling from ze back of ze concert hall. Respond to zem. 💬",
    "{n} {noun} {verb} still vaiting for a reply. Address ze feedback. 💬",
    "Ze chorus has {n} unacknowledged {noun}. Answer zem. 💬",
    "{n} {noun} {verb} echoing in ze rafters. Ze review threads need attention. 💬",
]

_V_PENDING_CHECKS = [
    "Ze stagehands are still preparing. Vait for CI to finish. ⏳",
    "Ze backstage crew is not yet ready. Patience, mein Freund. ⏳",
    "Ze gears are turning behind ze curtain. Vait for CI. ⏳",
    "Ze orchestra is tuning. CI is still in progress. ⏳",
    "Ze preparation continues. CI has not yet finished its vork. ⏳",
]

_V_APPROVAL_NEEDED = [
    "Ze conductor has not yet given his blessing. Approval is needed. 📋",
    "Ze maestro's baton remains lowered. You need approval to proceed. 📋",
    "Ze seal of approval has not yet been pressed into ze vax. 📋",
    "Ze conductor vaits to see ze final rehearsal. Approval is required. 📋",
    "No blessing from ze podium yet. Seek approval before merging. 📋",
]

_V_DEFAULT = [
    "{n} {noun} {verb} on ze music stand. Resolve zem before ze performance. 🚧",
    "{n} {noun} {verb} in ze margins. Clear ze remaining blockers. 🚧",
    "Ze ledger still shows {n} unresolved {noun}. Attend to zem. 🚧",
    "{n} {noun} {verb} unresolved. Ze symphony cannot begin. 🚧",
    "PhiedBach counts {n} remaining {noun}. Address zem. 🚧",
]


def _theatrical_verdict(delta: Delta) -> str:
    """PhiedBach's theatrical verdict for human eyes."""
    all_current = delta.added_blockers + delta.still_open_blockers
    if not all_current:
        return random.choice(_V_MERGE_READY)

    if any(b.type == BlockerType.DIRTY_MERGE_STATE for b in all_current):
        return random.choice(_V_MERGE_CONFLICT)

    failing = [b for b in all_current if b.type == BlockerType.FAILING_CHECK]
    if failing:
        n = len(failing)
        noun = "instrument" if n == 1 else "instruments"
        verb = "is" if n == 1 else "are"
        return random.choice(_V_FAILING_CHECKS).format(n=n, noun=noun, verb=verb)

    threads = [b for b in all_current if b.type == BlockerType.UNRESOLVED_THREAD]
    if threads:
        n = len(threads)
        noun = "voice" if n == 1 else "voices"
        verb = "remains" if n == 1 else "remain"
        return random.choice(_V_UNRESOLVED_THREADS).format(n=n, noun=noun, verb=verb)

    if any(b.type == BlockerType.PENDING_CHECK for b in all_current):
        return random.choice(_V_PENDING_CHECKS)

    if any(b.type == BlockerType.NOT_APPROVED for b in all_current):
        return random.choice(_V_APPROVAL_NEEDED)

    n = len(all_current)
    noun = "item" if n == 1 else "items"
    verb = "remains" if n == 1 else "remain"
    return random.choice(_V_DEFAULT).format(n=n, noun=noun, verb=verb)


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
    "PhiedBach hangs his flying goggles on ze nail by ze doghouse door.",
]

_OFFICERS_CLUB_REDBULL = [
    "BunBun already has a Red Bull open.",
    "BunBun adds another crushed can to ze wobbling tower.",
    "BunBun's ears relax for ze first time today.",
    "BunBun thumps his hind leg — ze ceremony is complete.",
    "BunBun produces a tiny party horn from behind his ThinkPad.",
]

# ---------------------------------------------------------------------------
# Closing scenes — narrative paragraphs set at the doghouse.
# These are the chapter endings. 2-4 sentences of atmosphere.
# ---------------------------------------------------------------------------

_SCENE_MERGE_READY = [
    (
        "Ze propeller sputters to a halt. PhiedBach climbs down from atop "
        "ze doghouse, removes his flying goggles, und hangs them on a nail. "
        "Across ze aerodrome, ze officers' club glows warm. BunBun is already "
        "inside, a Red Bull sweating on ze counter beside him, his ears "
        "finally at rest."
    ),
    (
        "Silence settles over ze aerodrome. Ze Sopwith Camel cools on ze "
        "tarmac, its engine ticking softly. PhiedBach folds his maps und "
        "tucks them into his coat. From inside ze officers' club, ze faint "
        "pulse of a synthesizer bassline drifts across ze grass. BunBun has "
        "put on ze Daft Punks again."
    ),
    (
        "Ze last searchlight blinks off. PhiedBach lowers himself from ze "
        "rooftop, his Crocs touching damp grass. Ze scarf he insists on "
        "wearing despite never actually flying trails behind him. He makes "
        "his way to ze officers' club, where BunBun has already arranged two "
        "Red Bulls und a small victory formation of crushed cans."
    ),
    (
        "Ze mission is over. PhiedBach slides his spectacles into his breast "
        "pocket und allows himself a rare smile. Ze doghouse stands quiet "
        "under ze stars, its purpose fulfilled. Inside ze officers' club, "
        "BunBun adds another crushed can to ze wobbling tower. Ze tower "
        "holds. It always holds."
    ),
    (
        "PhiedBach steps down from ze doghouse for ze last time today. Ze "
        "wind has died. Ze Red Baron is somewhere else, fighting someone "
        "else's PR. He walks ze short path to ze officers' club, where "
        "BunBun waits in his usual silence — a ThinkPad open, a Red Bull "
        "half-finished, ears perfectly still."
    ),
]

_SCENE_WATCH_EXIT = [
    (
        "Ze radar dish lowers vith a soft creak. PhiedBach climbs down from "
        "ze doghouse rooftop und stretches. Ze night sky is full of stars, "
        "und somewhere below, ze code sleeps in its repository. BunBun has "
        "already gone inside. A single Red Bull can sits on ze railing, "
        "still cold."
    ),
    (
        "Ze patrol ends. Ze Sopwith Camel's engine falls silent above ze "
        "trenches. PhiedBach wraps his scarf tighter und descends ze ladder. "
        "Ze aerodrome is dark now, ze runway outlined only by moonlight. "
        "Tomorrow there vill be more sorties. But not tonight."
    ),
    (
        "PhiedBach folds his charts, one by one, und stows them in ze wooden "
        "box beside ze doghouse. Ze wind carries ze faint hum of a "
        "synthesizer from somewhere inside. BunBun's ThinkPad light is ze "
        "only glow in ze darkness. Even rabbits need sleep eventually."
    ),
    (
        "Ze antenna retracts into ze doghouse roof. PhiedBach removes his "
        "flying goggles und blinks at ze quiet sky. No bogeys. No Red Baron. "
        "Just stars und ze soft tick of a cooling engine. He descends, his "
        "Crocs finding each rung vith practiced care."
    ),
    (
        "Silence returns to ze aerodrome. Ze doghouse stands watch alone now, "
        "its occupant gone for ze night. PhiedBach's spectacles rest on ze "
        "instrument panel. BunBun's Red Bull can collection gleams faintly in "
        "ze starlight. Ze war vill resume at dawn."
    ),
]

_SCENE_EXPORT = [
    (
        "Ze black box clicks shut. PhiedBach seals it vith wax — "
        "rabbit-shaped, naturally — und sets it on ze shelf beside ze "
        "others. Every flight leaves a record. Every sortie, a story. "
        "BunBun has already filed ze paperwork."
    ),
    (
        "PhiedBach wraps ze manuscript fragment in oilcloth und ties it "
        "vith twine. Ze evidence is preserved against rain, fire, und ze "
        "fog of GitHub. He places it carefully in ze archive beneath ze "
        "doghouse. BunBun stamps it vith a small ink paw print."
    ),
    (
        "Ze flight recorder data is extracted, catalogued, und sealed. "
        "PhiedBach holds ze bundle for a moment, feeling its weight — every "
        "snapshot, every delta, every blocker that came und went. Then he "
        "sets it down. Ze record speaks for itself."
    ),
    (
        "Ze hangar doors creak shut. Inside, ze export bundle sits under a "
        "single bare bulb, a complete account of ze sortie. PhiedBach dusts "
        "off his hands. BunBun thumps once — his way of saying ze archive "
        "is in order."
    ),
    (
        "PhiedBach locks ze evidence cabinet und pockets ze key. Somewhere "
        "in that bundle is ze truth of vhat happened — not vhat anyone "
        "remembers, not vhat ze GitHub UI shows, but vhat actually changed, "
        "und vhen. That is vhy they built ze doghouse."
    ),
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
    if repo is None or pr is None:
        detected_repo, detected_pr = _auto_detect_repo_and_pr()
        repo = repo if repo is not None else detected_repo
        pr = pr if pr is not None else detected_pr

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
    service = RecorderService(github, storage, engine, git=GitAdapter())

    snap, delta = service.record_sortie(repo, pr)

    if as_json:
        output = {
            "snapshot": snap.to_dict(),
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

    console.print(f"📡 [bold]{random.choice(_SNAPSHOT_OPENING).format(repo=repo, pr=pr)}[/bold]")
    console.print(f"[dim italic]{random.choice(_SNAPSHOT_SUBTEXT)}[/dim italic]")

    console.print(f"\n[bold blue]Snapshot captured at {snap.timestamp} 🎼[/bold blue]")
    console.print(f"SHA: [dim]{snap.head_sha}[/dim]")

    # Show Delta
    if delta.baseline_sha:
        console.print(f"\n[bold]Ze Delta against {delta.baseline_timestamp}:[/bold]")
        if delta.head_changed:
            console.print("  [yellow]{msg}[/yellow]".format(
                msg=random.choice(_SHA_CHANGED).format(old=delta.baseline_sha[:7], new=snap.head_sha[:7])
            ))

        if delta.removed_blockers:
            for b in delta.removed_blockers:
                flavor = random.choice(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = random.choice(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        # BunBun reacts to review thread changes
        threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
        threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
        if threads_resolved and not threads_added:
            console.print(f"\n[dim italic]{random.choice(_BUNBUN_THREADS_RESOLVED)}[/dim italic]")
        elif threads_added:
            console.print(f"\n[dim italic]{random.choice(_BUNBUN_THREADS_ADDED)}[/dim italic]")
    else:
        console.print(f"\n[dim]{random.choice(_FIRST_SNAPSHOT)}[/dim]")

    # Current Blockers Table
    table = Table(title=f"Live Blockers for PR #{pr} (Ze Blocker Set)", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Impact", style="bold")
    table.add_column("Message")

    local_blockers_count = 0
    for b in snap.blockers:
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
        console.print(f"\n[bold yellow]⚠️  {random.choice(_MID_MANEUVER_TITLE)}[/bold yellow]")
        console.print(f"[yellow]{random.choice(_MID_MANEUVER_DETAIL)}[/yellow]")

    # The officers' club moment
    merge_ready = not (delta.added_blockers + delta.still_open_blockers)
    if merge_ready and delta.removed_blockers:
        console.print()
        console.print(f"[dim italic]{random.choice(_OFFICERS_CLUB_SPECTACLES)}[/dim italic]")
        console.print("[bold green]PhiedBach's Verdict: {verdict}[/bold green]".format(verdict=_theatrical_verdict(delta)))
        console.print(f"[dim italic]{random.choice(_OFFICERS_CLUB_REDBULL)}[/dim italic]")
        console.print()
        console.print(f"[dim italic]{random.choice(_SCENE_MERGE_READY)}[/dim italic]")
    else:
        console.print(f"\n[bold green]PhiedBach's Verdict: {_theatrical_verdict(delta)}[/bold green]")

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

    console.print(f"🎬 [bold]{random.choice(_PLAYBACK_OPENING).format(name=name)}[/bold]")

    # Show Delta
    if baseline:
        console.print(f"\n[bold]Ze Delta against {baseline.timestamp}:[/bold]")
        if delta.head_changed:
            console.print("  [yellow]{msg}[/yellow]".format(
                msg=random.choice(_PLAYBACK_SHA_CHANGED).format(old=baseline.head_sha[:7], new=current.head_sha[:7])
            ))

        if delta.removed_blockers:
            for b in delta.removed_blockers:
                flavor = random.choice(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                console.print(f"  [green]✓ {b.message}[/green]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")

        if delta.added_blockers:
            for b in delta.added_blockers:
                flavor = random.choice(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                console.print(f"  [red]+ {b.message}[/red]")
                console.print(f"    [dim italic]{flavor}[/dim italic]")
    else:
        console.print(f"\n[dim]{random.choice(_PLAYBACK_NO_BASELINE)}[/dim]")

    # Current Blockers Table
    table = Table(title=f"Current Blockers (Playback: {name})", show_header=True)
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Message")

    for b in current.blockers:
        severity_style = "red" if b.severity == BlockerSeverity.BLOCKER else "yellow"
        table.add_row(b.type.value, b.severity.value, b.message, style=severity_style if b.severity == BlockerSeverity.BLOCKER else None)

    console.print(table)
    console.print(f"\n[bold green]PhiedBach's Verdict: {_theatrical_verdict(delta)}[/bold green]")

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
    git_log = subprocess.run(["git", "log", "-n", "10", "--oneline"], capture_output=True, text=True, timeout=30).stdout

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

    console.print(f"📦 [bold green]{random.choice(_EXPORT_COMPLETE)}[/bold green]")
    console.print(random.choice(_EXPORT_SAVED).format(path=Path(out_path).resolve()))
    console.print()
    console.print(f"[dim italic]{random.choice(_SCENE_EXPORT)}[/dim italic]")

@app.command()
def watch(
    pr: Optional[int] = typer.Option(None, "--pr", help="PR number"),
    repo: Optional[str] = typer.Option(None, "--repo", help="Repository (owner/name)"),
    interval: int = typer.Option(180, "--interval", help="Polling interval in seconds")
):
    """PhiedBach's Radar: Live monitoring of PR state."""
    repo, repo_owner, repo_name, pr = resolve_repo_context(repo, pr)

    console.print(f"📡 [bold]{random.choice(_WATCH_OPENING).format(repo=repo, pr=pr)}[/bold]")
    console.print(f"[dim]{random.choice(_WATCH_INTERVAL).format(interval=interval)}[/dim]")

    github = GhCliAdapter(repo_owner=repo_owner, repo_name=repo_name)
    storage = JSONLStorageAdapter()
    engine = DeltaEngine()
    service = RecorderService(github, storage, engine, git=GitAdapter())

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
                        msg=random.choice(_WATCH_SHA_CHANGED).format(sha=snapshot.head_sha[:7])
                    ))

                if delta.removed_blockers:
                    for b in delta.removed_blockers:
                        flavor = random.choice(_RESOLVED_FLAVOR.get(b.type, ["Resolved."]))
                        console.print(f"  [green]✓ {b.message}[/green]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                if delta.added_blockers:
                    for b in delta.added_blockers:
                        flavor = random.choice(_ADDED_FLAVOR.get(b.type, ["A new concern."]))
                        console.print(f"  [red]+ {b.message}[/red]")
                        console.print(f"    [dim italic]{flavor}[/dim italic]")

                # BunBun reacts to review thread changes
                threads_resolved = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.removed_blockers)
                threads_added = any(b.type == BlockerType.UNRESOLVED_THREAD for b in delta.added_blockers)
                if threads_resolved and not threads_added:
                    console.print(f"[dim italic]{random.choice(_BUNBUN_THREADS_RESOLVED)}[/dim italic]")
                elif threads_added:
                    console.print(f"[dim italic]{random.choice(_BUNBUN_THREADS_ADDED)}[/dim italic]")

                # The officers' club — merge-ready mid-patrol
                merge_ready = not (delta.added_blockers + delta.still_open_blockers)
                if merge_ready and delta.removed_blockers:
                    console.print()
                    console.print(f"[dim italic]{random.choice(_OFFICERS_CLUB_SPECTACLES)}[/dim italic]")
                    console.print(f"[bold green]Verdict: {_theatrical_verdict(delta)}[/bold green]")
                    console.print(f"[dim italic]{random.choice(_OFFICERS_CLUB_REDBULL)}[/dim italic]")
                    console.print()
                    console.print(f"[dim italic]{random.choice(_SCENE_MERGE_READY)}[/dim italic]")
                else:
                    console.print(f"[bold green]Verdict: {_theatrical_verdict(delta)}[/bold green]")

                # Mid-maneuver warning
                local_issues = [b for b in snapshot.blockers if b.type in [BlockerType.LOCAL_UNCOMMITTED, BlockerType.LOCAL_UNPUSHED]]
                if local_issues:
                    console.print("[yellow]⚠️  {msg}[/yellow]".format(
                        msg=random.choice(_WATCH_MID_MANEUVER).format(n=len(local_issues))
                    ))

            else:
                quiet_polls += 1
                if quiet_polls % 3 == 0:
                    console.print(f"\n[dim italic]{random.choice(_QUIET_SKIES)} ({snapshot.timestamp.strftime('%H:%M:%S')})[/dim italic]")

            time.sleep(interval)
    except KeyboardInterrupt:
        console.print(f"\n[dim italic]{random.choice(_WATCH_EXIT_1)}[/dim italic]")
        console.print(f"[bold red]{random.choice(_WATCH_EXIT_2)}[/bold red]")
        console.print()
        console.print(f"[dim italic]{random.choice(_SCENE_WATCH_EXIT)}[/dim italic]")

if __name__ == "__main__":
    app()
