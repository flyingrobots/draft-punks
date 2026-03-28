# Doghouse 2.0

The Doghouse is the design bay for the next structural evolution of Draft Punks.

Draft Punks already solves one real problem well: it turns overwhelming review feedback into
an explicit worksheet and forces a decision. That is the conductor's score.

Doghouse 2.0 is the missing companion mechanic: the black box recorder.

When a PR has been through multiple pushes, rerun checks, and automated reviewer waves, the
author stops trusting memory. GitHub mixes historical and live state, the CLI is noisy, and
the worksheet alone cannot answer the most urgent question:

- what changed
- what matters now
- what should happen next

## Why This Exists

Draft Punks should not lose its flavor while it grows up.

The goal is not to replace BunBun, PhiedBach, or the ritual of adjudicating comments. The goal
is to give them a better instrument.

- Draft Punks as the conductor's score
- Doghouse as the flight recorder

The worksheet system remains the place where decisions are written down. Doghouse adds the
durable state reconstruction layer that tells the operator what fight they are actually in.

## Ze Lore: Why "Doghouse"?

*PhiedBach leans in, his quill trembling with excitement.*

"You ask vhy it is called ze Doghouse? Ah, it is a tale of madness und bravery! You see, our fellow composer **Codex** was losing his mind in ze GitHub tunnels. Ze GraphQL queries, ze 'gh' CLI mess, ze endless cascading threads... it was a maddening fog! Codex felt he was fighting hallucinations.

It reminded us of a small beagle named **Snoopy**, sitting atop his wooden house, dreaming he was an ace pilot in ze Great War, dogfighting ze Red Baron in ze clouds. 

When you use zis tool, you are Snoopy. Your PR is your cockpit. You are sparring mit ze reviewers—ze CodeRabbits und ze maintainers—in a tactical dance. Ze Doghouse is your vessel, your Black Box, und your Sopwith Camel. 

"Und do not forget ze radar!" *PhiedBach exclaims.* "Ze Doghouse, he has a very sensitive scanner for **BunBun's moods**. He tells you vhen ze rabbit is on **'Cooldown'**, perhaps eating a digital carrot or resting his ears. Or vhen he has **'Suspended'** his review because he sees you are in ze flow und does not vish to startle your muse! No more shouting into ze void—you vill know exactly vhere ze dogfight stands."

**Record ze flight. Win ze dogfight.**"

## Working Principle

- Capture trustworthy local PR state first.
- Provide ze **Mathematical Score** (JSONL) for ze **Thinking Automatons**.
- Diff semantic review state, not raw JSON.
- Separate CodeRabbit state from human and Codex reviewer state.
- Emit a machine-usable next action instead of just more telemetry.
- Preserve the Draft Punks voice after the mechanic is trustworthy.

## Proposed Plumbing

The first Doghouse 2.0 cut should revolve around three concepts:

- `snapshot`
  A local point-in-time artifact for PR state.
- `sortie`
  A review episode such as `post_push`, `fix_batch`, `merge_check`, or `resume`.
- `delta`
  A semantic comparison that explains what changed since the last meaningful sortie.

The eventual agent-native interface should emit JSONL events instead of UI-first prose:

- `doghouse.snapshot`
- `doghouse.baseline`
- `doghouse.comparison`
- `doghouse.delta`
- `doghouse.next_action`
- `doghouse.coderabbit`

That plumbing can later feed friendlier TUI or worksheet surfaces without coupling the core
mechanic to one presentation.

## Relationship To Current Draft Punks

Current Draft Punks is strongest at:

- harvesting review comments
- forcing accept/reject decisions
- preserving rationale
- refusing to let unresolved worksheet placeholders slip through

Doghouse 2.0 should add:

- review-state reconstruction across pushes
- meaningful baseline selection
- check / thread / blocker transition tracking
- merge-readiness clarity
- resume-after-interruption clarity

The future product shape is:

- Act I: Doghouse reconstructs the sortie
- Act II: Draft Punks adjudicates the notes
- Act III: Draft Punks conducts the reply / resolve / merge ritual

## Documents

- [Flight Recorder Brief](./flight-recorder-brief.md)
  Product brief, hills, non-goals, object model, and success criteria.
- [Playbacks](./playbacks.md)
  Concrete situations Doghouse 2.0 must handle well.

## Current Stance

- Do not build generic GitHub analytics mush.
- Do not lose the PhiedBach / BunBun flavor.
- Do not force the worksheet model to carry every kind of PR-state burden.
- Build the recorder mechanic first, then re-layer the theater on top of it.
