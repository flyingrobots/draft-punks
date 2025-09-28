# Draft Punks

Draft Punks keeps sprawling CodeRabbit reviews manageable. It collects every review comment into a Markdown worksheet, guides you through accepting or rejecting each note, and blocks pushes until every decision is documented.

## TL;DR
- Harvest CodeRabbit review threads into a local worksheet with `{response}` placeholders.
- Fill each placeholder with an **Accepted** or **Rejected** response (plus rationale).
- A pre-push hook refuses to let you push until the worksheet is complete.
- The Apply Feedback workflow pushes your decisions back to GitHub once you commit the worksheet.

---

## Why Draft Punks Exists
CodeRabbit can outpace any reviewer—its comments arrive so quickly that GitHub’s UI becomes noisy and easy to ignore. Draft Punks enforces a rhythm: every comment must be heard, answered, and resolved before code merges. Instead of skimming threads, you work from a single Markdown score where each instrument (comment) gets a clear response.

## How It Works
1. **Seed workflow** copies CodeRabbit comments from a pull request into `docs/code-reviews/PR*/<comment>.md` worksheets.
2. **You** review the worksheet locally, marking every comment’s `{response}` block as **Accepted** or **Rejected** and adding rationale.
3. **Pre-push hook** (`tools/hooks/pre-push-draft-punks.sh`) scans staged worksheets. Empty `{response}` placeholders or missing decisions trigger a failed push.
4. **Apply workflow** (`tools/review/apply_feedback_to_github.py`) reads the completed worksheets and updates the original GitHub review threads with your decisions.

---

## Requirements
- GitHub repository with CodeRabbit enabled on pull requests.
- Ability to run GitHub Actions workflows.
- Local git hooks enabled (Draft Punks ships one) and Python 3.9+ for the tool scripts.

---

## Quick Start
1. **Add the workflows.** Copy the two workflow files below into `.github/workflows/` on your repository’s default branch.
2. **Commit the Draft Punks toolkit.** Include the `docs/code-reviews/` directory and the `tools/` scripts from this repository.
3. **Open a pull request.** CodeRabbit leaves feedback as usual.
4. **Run the seed workflow.** On `opened`, `reopened`, or `synchronize` events the action builds worksheets in `docs/code-reviews/PR<id>/`.
5. **Pull the branch locally** and open each worksheet. Replace every `{response}` placeholder with an **Accepted** or **Rejected** block (examples below).
6. **Stage changes and push.** The pre-push hook blocks incomplete worksheets; fix any flagged sections and try again.
7. **Watch the Apply workflow.** On pushes that touch `docs/code-reviews/**.md`, the GitHub Action posts your responses back to the corresponding review threads.

---

## Installation
Add these GitHub Actions to your repository. Update `uses:` versions as Draft Punks releases new tags.

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

### Local Setup Checklist
- Copy `tools/hooks/pre-push-draft-punks.sh` into `.git/hooks/pre-push` (or source it from your hook manager).
- Ensure `tools/review/apply_feedback_to_github.py` is executable (`chmod +x`).
- Export `GITHUB_TOKEN` when running local scripts that access the API.
- Keep the `docs/code-reviews/` directory in version control; the workflows read and write to these files.

---

## Completing a Worksheet
Every worksheet entry mirrors a CodeRabbit thread. Replace each `{response}` with one of the templated blocks below.

**Accepted**
```markdown
> [!note]- **Accepted**
> **What changed:** Fixed indentation in commit def5678
> **Lesson learned:** Consistent spacing improves readability
> **Prevention:** Added pre-commit hook for formatting
```

**Rejected**
```markdown
> [!CAUTION]- **Rejected**
> **Rationale:** Performance cost outweighs marginal benefit
> **Trade-offs:** Maintainability over micro-optimization
> **Future consideration:** Revisit if profiling shows bottleneck
```

Tips:
- Keep explanations concise; reviewers should learn why you accepted or declined a change.
- When rejecting, reference data (benchmarks, specs) whenever possible.
- Commit the worksheet alongside any code changes that address the feedback.

---

## Pre-Push Enforcement
The pre-push script inspects staged Markdown files in `docs/code-reviews/`. You will see output like:

```bash
❌ Review worksheet issues detected:
- docs/code-reviews/PR123/abc1234.md: contains unfilled placeholder '{response}'
- docs/code-reviews/PR123/abc1234.md: section missing Accepted/Rejected decision
```

Set `HOOKS_BYPASS=1 git push` to bypass in emergencies, but consider that a last resort—the gate is the only thing preventing unresolved feedback from slipping through.

---

## Apply Feedback Workflow Details
- Script path: `tools/review/apply_feedback_to_github.py`
- Expects `GITHUB_TOKEN` with permission to update pull request comments.
- Filters for `docs/code-reviews/**.md` files whose names contain `"docs/code-reviews/PR"`.
- On success, the workflow replays each worksheet entry to the matching GitHub review thread and marks it resolved when appropriate.

If the workflow exits with a non-zero status, check the action logs for:
- Missing or malformed worksheet sections.
- Authentication failures (token not set or insufficient scopes).
- API rate limiting.

---

## Troubleshooting
- **No worksheets appear.** Confirm the seed workflow ran on your PR and that GitHub Actions has access to CodeRabbit’s comment API.
- **Pre-push hook never runs.** Verify the hook file is executable and located at `.git/hooks/pre-push` (or configured in your hook manager).
- **Script crashes locally.** Ensure Python 3.9+ is on your PATH and that files use ASCII quotes (see `README` fix history!).
- **Apply workflow posts duplicates.** Make sure you commit updated worksheets only once; avoid rewriting history without rerunning the seed workflow.

---

## Lore Corner (Optional)
In the original README, Kapellmeister P.R. PhiedBach and CodeRabbit (BunBun) welcome you to the LED Bike Shed Dungeon: bicycles on hooks, modular synths, and anime scrolls set the mood. Keep the lore if it delights your team; park it in a separate section (like this one) so newcomers can skip straight to setup while veterans savor the mythology.

---

## Next Steps
- Align the README and README-2.md content once you settle on the voice.
- Publish a release tag when workflows change so adopters can lock to a specific version.
- Consider adding automated tests for the pre-push hook and apply script to catch regressions early.

"One More Merge… It’s Never Over. Harder. Better. Faster. Structured."
