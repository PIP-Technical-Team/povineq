---
date: 2026-08-17
depth: light
type: standard
plan: .cg-docs/plans/2026-08-17-pypi-publication.md
findings:
  P2.1: fixed
  P3.1: skipped
  P3.2: skipped
  P3.3: skipped
  P3.4: skipped
  P3.5: skipped
---

# Review Report

**Review mode**: light
**Scope**: post-merge main commits `0fd3a03` + `4abbf22` (v0.1.0 publication docs finalization)
**Files reviewed**: 10 (`.github/workflows/docs.yml`, `README.md`, `docs/changelog.md`, `docs/getting-started.md`, `docs/index.md`, `roadmap.json`, plus `.cg-docs/` bookkeeping artifacts)
**Findings**: 6 (P0: 0, P1: 0, P2: 1, P3: 5)

> Auto-routing applied: docs-only changes with no statistical/pipeline code.
> Resolved review mode: `light`. Mandatory emphasis: none (no high-risk signals).

### P1 — CRITICAL

None.

### P2 — IMPORTANT

- **[P2.1]** [cg-testing]/[cg-code-quality] `README.md:8` — Stale pre-release wording "Once the first release is published, install the package from PyPI:" contradicts the published v0.1.0 release and the sibling docs (`docs/index.md`, `docs/getting-started.md`).
  **Why**: `pyproject.toml` sets `readme = "README.md"`, so the live PyPI long description for `povineq 0.1.0` displays this stale conditional on an already-published package.
  **Fix**: Replace with "Install the released package from PyPI:" — applied.
  `[safe_auto]` — **Applied and verified in working tree.**

### P3 — MINOR

- **[P3.1]** [cg-testing] `.github/workflows/docs.yml:49` — `--force` force-pushes the generated `gh-pages` branch.
  **Why**: Intended fix for the non-fast-forward `gh-deploy` refusal documented in the work report; safe because the `concurrency` guard serializes runs and no custom domain exists. Residual minor risk only: overwrites any remote-only commits on `gh-pages`.
  **Fix**: None required — keep `--force` given the documented failure.
  `[advisory]`

- **[P3.2]** [cg-testing] `docs/getting-started.md:62` — Comment "hundreds of rows, one per survey" makes an unverifiable live-response row count claim.
  **Why**: The offline suite (`-m "not online"`) cannot validate live PIP response size.
  **Fix**: Optional: soften to "# one row per survey estimate".
  `[advisory]`

- **[P3.3]** [cg-code-quality] `.cg-docs/reviews/2026-08-17-pypi-publication-release-readiness-review.md` — `findings:` map still records `P0.2: open` and Residual Risk still says the release is blocked.
  **Why**: The release was subsequently completed (V6 passed; `current.json` status `completed`), so the review record contradicts the active state.
  **Fix**: Optional bookkeeping: update `P0.2` → fixed and Residual Risk. No code impact.
  `[advisory]`

- **[P3.4]** [cg-code-quality] `.cg-docs/plans/2026-08-17-pypi-publication.md:4` — Plan frontmatter `status: active` while the pub-release-readiness plan (the one referenced by `current.json` and roadmap) is `completed`.
  **Why**: Two plans for the same effort in inconsistent states.
  **Fix**: Optional bookkeeping: set the superseded plan to `completed` or add a superseded-by pointer.
  `[advisory]`

- **[P3.5]** [cg-code-quality]/[cg-testing] `roadmap.json:8` — Milestone `v1-full-pipr-parity` titled "v1.0 — Full pipr parity" marked `done` while the published release is `0.1.0`.
  **Why**: Version-scheme mismatch if milestone titles are meant to track PyPI versions; cosmetic if roadmap versioning is internal.
  **Fix**: Confirm milestone-title↔version semantics when the plan next runs. Protected file — no change applied.
  `[advisory]`

### ✅ Passed

- `@cg-code-quality`: `docs.yml` `--force` change verified consistent with the production MkDocs pattern (concurrency guard + paths filter + pinned uv present); no other issues.
- `@cg-testing`: No test/coverage impact from `--force` or docs changes; `ci.yml` docs job unchanged and still validates strict build.

### ⚠️ Incomplete Reviews

None — both agents returned usable output.

## Autofix Summary

> Autofix complete: applied 1 safe fix (file: `README.md:8` changed to "Install the released package from PyPI:"), 0 manual fixes need your review, 5 advisory notes filed.

## Model Advisory

The review stage found a docs-only, low-risk scope; no heavy reasoning effort is needed for the accompanying bookkeeping entries. A standard effort model is adequate.

> ## Review Summary
> - **Fixed**: 1 finding
> - **Skipped**: 5 findings (advisory — noted, not applied)
> - **Remaining**: 0 findings
