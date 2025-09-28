# 🎼🎵🎶 Draft Punks

## 🐇 CodeRabbit’s Poem-TL;DR

> I flood your PR, my notes cascade,
> Too many threads, the page degrades.
> But PhiedBach scores them, quill in hand,
> A worksheet formed, your decisions we demand.
> No push may pass till all’s reviewed,
> Install the flows — ten lines, you’re cued. 🐇✨

_PhiedBach adjusts his spectacles: “Ja. Das is accurate. Let us rehearse, und together your code vil become a beautiful symphony of syntax.”_

---

## Guten Tag, Meine Freunde

![P.R. PhiedBach & BunBun](assets/images/PRPhiedbachUndBunBun-thumb.webp)

> *"Every comment is a note. Every note must be played."*  
> — Johann Sebastian Bach, Kapellmeister of Commits, 2025

The door creaks. RGB light pours out like stained glass at a nightclub. Inside: bicycles hang from hooks, modular synths blink, an anime wall scroll flutters gently in the draft. An 80-inch screen above a neon fireplace displays a GitHub Pull Request in cathedral scale. Vape haze drifts like incense.

A white rabbit sits calm at a ThinkPad plastered with Linux stickers. Beside him, spectacles sliding low, quill in hand, rises a man in powdered wig and Crocs — though here he is known as P.R. PhiedBach.

**PhiedBach** (bowing, one hand on his quill like a baton):  
*Ah… guten abend. Velkommen, velkommen to ze LED Bike Shed Dungeon. You arrive for your… how do you say… pull request? Sehr gut.*

*I am P.R. PhiedBach — Pieter Rabbit PhiedBach. But in truth, I am Johann Sebastian Bach. Ja, ja, that Bach. Once Kapellmeister in Leipzig, composer of fugues und cantatas. Then one evening I followed a small rabbit down a very strange hole, and when I awoke... it was 2025. Das ist sehr verwirrend.*

He gestures conspiratorially toward the rabbit.  
*And zis… zis is CodeRabbit. Mein assistant. Mein virtuoso. Mein BunBun (isn't he cute?).*

BunBun's ears twitch. He does not look up. His paws tap a key, and the PR on the giant screen ripples red, then green.

**PhiedBach** (delighted):  
*You see? Calm as a pond, but behind his silence there is clarity. He truly understands your code. I? I hear only music. He is ze concertmaster; I am only ze man waving his arms.*

From the synth rack, a pulsing bassline begins. PhiedBach claps once.  
*Ah, ze Daft Punks again! Always two of them, helmets like Teutonic knights. Their music is fugue for robots. BunBun insists it helps him code. Even mein Crocs want to dance.*

---

## Ze Problem: When Genius Becomes Cacophony

GitHub cannot withstand BunBun's brilliance. His reviews arrive like a thousand voices at once — so many comments, so fastidious, that the page itself slows to a dirge. Browsers wheeze. Threads collapse under their own counterpoint.

Your choices are terrible:
- Ignore ze feedback (barbaric!)
- Drown in ze overwhelming symphony
- Click "Resolve" without truly answering ze note

*Nein, nein, nein!* Zis is not ze way.

---

## Ze Solution: Structured Rehearsal

Draft Punks is the cathedral we built to contain it.

It scrapes every CodeRabbit comment from your Pull Request and transcribes them into a **Markdown worksheet** — the score. Each comment is given a `{response}` placeholder. You, the composer, must mark each one: **Decision: Accepted** or **Decision: Rejected**, with rationale.

A pre-push hook enforces the ritual. No unresolved placeholders may pass into the great repository. Thus every voice is answered, no feedback forgotten, the orchestra in time.

---

## Installation: Join Ze Orchestra

Add zis to your repository and conduct your first rehearsal:

```yaml
# .github/workflows/draft-punks-seed.yml
name: Seed Review Worksheet
on:
  pull_request_target:
    types: [opened, reopened, synchronize]

jobs:
  seed:
    uses: neuroglyph/draft-punks/.github/workflows/seed-review.yml@v1.0.0
    secrets: inherit
```

```yaml
# .github/workflows/draft-punks-apply.yml  
name: Apply Feedback
on:
  push:
    paths: ['docs/code-reviews/**.md']

jobs:
  apply:
    uses: neuroglyph/draft-punks/.github/workflows/apply-feedback.yml@v1.0.0
    secrets: inherit
```

Zat ist all! Ten lines of YAML, and your review chaos becomes beautiful counterpoint.

---

## Ze Response Templates

Each feedback receives one of two treatments in ze worksheet:

**Accepted** — "Ja, zis wisdom I embrace"
```markdown
> [!note]- **Accepted**
> **What changed:** Fixed indentation in commit def5678  
> **Lesson learned:** Consistent spacing improves readability  
> **Prevention:** Added pre-commit hook for formatting
```

**Rejected** — "Nein, but mit rationale und respect"
```markdown
> [!CAUTION]- **Rejected**
> **Rationale:** Performance cost outweighs marginal benefit  
> **Trade-offs:** Maintainability over micro-optimization  
> **Future consideration:** Revisit if profiling shows bottleneck
```

---

## Example Worksheet

```markdown
# PR Review Worksheet — PR42 @ deadbeef

### "nit: spacing"
```text
BunBun: Indent with 4 spaces, not 3.
```

Decision: Accepted  
Response: Fixed in commit 1234abcd.

### "needs test for edge case"
```text
BunBun: Missing test when input=0.
```

Decision: Rejected  
Response: Handled upstream; see PR 77.

### "rename variable"
```text
BunBun: `foo` → `session_ref`
```

Decision: Accepted  
Response: Renamed in commit 5678efgh.
```

Push passes. Worksheet preserved. Orchestra applauds.

---

## Ze Workflow

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant GH as GitHub PR
    participant CR as CodeRabbit (BunBun)
    participant DP as Draft Punks
    participant WS as Worksheet
    participant HOOK as Pre-Push Gate

    Dev->>GH: Open PR
    GH-->>CR: CodeRabbit reviews\n(leaves many comments)
    GH-->>DP: Trigger workflow
    DP->>GH: Scrape BunBun's comments
    DP->>WS: Generate worksheet\nwith {response} placeholders
    Dev->>WS: Fill in decisions\n(Accepted/Rejected)
    Dev->>HOOK: git push
    HOOK-->>WS: Verify completeness
    alt Incomplete
        HOOK-->>Dev: ❌ Reject push
    else Complete
        HOOK-->>Dev: ✅ Allow push
        DP->>GH: Apply decisions\npost back to threads
    end
```

---

## Ze Pre-Push Gate

BunBun insists: no unresolved `{response}` placeholders may pass.

```bash
❌ Review worksheet issues detected:
- docs/code-reviews/PR123/abc1234.md: contains unfilled placeholder '{response}'
- docs/code-reviews/PR123/abc1234.md: section missing Accepted/Rejected decision

# Emergency bypass (use sparingly!)
HOOKS_BYPASS=1 git push
```

---

## Philosophie: Warum „Draft Punks“?

Because every pull request begins as a draft — rough, unpolished, full of potential. Because BunBun's reviews are robotic precision. Because ze Daft Punks — always two of them — compose fugues for robots.

When I pronounce it mit ze hard "s," BunBun's ears twitch. It pleases me. Kleine Freude for such a complex mind — like a well-resolved chord.

PhiedBach closes his ledger with deliberate care. From his desk drawer, he produces a folded bit of parchment and presses it with a wax seal — shaped, naturally, like a rabbit. As he rises to hand you the sealed document, his eyes drift momentarily to the anime wall scroll, where the warrior maiden hangs frozen mid-transformation.

He sighs, almost fondly.

"Ja… ze anime? I confess I do not understand it myself, but BunBun is rather fond of zis particular series. Something about magical girls und friendship conquering darkness. I must admit..." he pauses, adjusting his spectacles, "ze opening theme song is surprisingly well-composed. Very catchy counterpoint."

He presses the parchment into your hands.

"Take zis, mein Freund. Your rehearsal begins now. Fill ze worksheet, address each comment mit proper consideration, und push again. When BunBun's threads are resolved und ze pre-push gate approves, you may merge your branch."

He waves his quill with ceremonial finality.

"Now, off mit you. Go make beautiful code. Wir sehen uns wieder."

PhiedBach settles back into his wingback chair by the neon fireplace. BunBun crushes another Red Bull can with methodical precision, adding it to the wobbling tower. The synthesizer pulses its eternal bassline. The anime maiden watches, silent and eternal, as the RGB lights cycle through their spectrum.

PhiedBach adjusts his spectacles and returns to his ledger. "I do not know how to return to 1725," he mutters, "aber vielleicht… it is better zis way."

Velkommen to ze future of code review.

**One More Merge… It's Never Over.**
**Harder. Better. Faster. Structured.**