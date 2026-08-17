---
date: 2026-08-17
depth: full
type: standard
plan: .cg-docs/plans/2026-08-17-pypi-publication-release-readiness.md
findings:
  P0.1: open
  P0.2: open
  P0.3: fixed
  P0.4: fixed
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
---

# Release Readiness Review

## Review Report

**Review mode**: full
**Scope**: `main...chore/publish-pypi`
**Review fallback**: legacy prior review files had no tracked `findings:` map,
so no P2/P3 suppression was applied.

### P0 — BLOCKING

- **[P0.1]** `.github/workflows/publish.yml:14` — Protected `v*` tag rules are
  required but are not configured in the repository. The workflow now refuses
  unprotected tag events with `github.ref_protected == true`; configure a
  protected release-tag ruleset before the first release.
- **[P0.2]** `.github/workflows/publish.yml:64-69` — The `pypi` environment and
  PyPI trusted publisher are external configuration and are not present yet.
  Create the protected environment with required reviewers and register the
  exact owner, repository, workflow, and environment at PyPI.

### P1 — RESOLVED

- **[P1.1]** Polars nowcast filtering, auxiliary catalog/storage behavior, and
  simplified country-profile output now preserve the requested backend and
  public contracts; regression tests cover each path.
- **[P1.2]** CI now runs the full Python 3.10-3.13 matrix, quality checks, a
  Polars runtime job, locked public-PyPI resolution, and clean artifact installs.
- **[P1.3]** The publish workflow now requires protected tags, main ancestry,
  publication-ready documentation, and the reusable complete CI gate before
  OIDC publication.
- **[P1.4]** Build output is cleared, Hatchling is pinned, actions are SHA-pinned,
  and the reusable release validator checks wheel/sdist manifests and installs.
- **[P1.5]** Runtime validation now rejects invalid API versions and output
  backends; source-checkout version fallback reads project metadata.

### P2 — RESOLVED

- **[P2.1]** The committed lockfile is enforced with `uv lock --check`,
  `uv sync --locked`, and `uv run --locked`.
- **[P2.2]** Public documentation now distinguishes published PyPI commands
  from GitHub development installation and documents the Polars GitHub extra.
- **[P2.3]** Documentation no longer claims response caching is active; it
  describes the current retry/connection-pooling behavior.
- **[P2.4]** The package metadata now bounds supported Python versions to
  `>=3.10,<3.14`, matching classifiers and CI.

## Validation

- Local: `210 passed`, `92.87%` branch coverage, Ruff passed, mypy passed.
- Local strict MkDocs build passed.
- Local Twine, manifest, base-wheel, Polars-wheel, and sdist smoke tests passed.
- Remote CI run [32052515633](https://github.com/PIP-Technical-Team/povineq/actions/runs/32052515633)
  passed all eight jobs, including Polars runtime and clean artifact installs.

## Residual Risk

The release remains intentionally blocked until repository administrators create
the protected `pypi` environment and protected `v*` tag rules, PyPI ownership and
trusted-publisher registration are complete, and the user explicitly approves
the first production tag/upload. No tag or PyPI upload was attempted.
