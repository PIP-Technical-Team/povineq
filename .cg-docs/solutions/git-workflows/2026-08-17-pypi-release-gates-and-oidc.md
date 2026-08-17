---
date: 2026-08-17
title: "Harden Python package release gates with locked CI and OIDC publication"
category: "git-workflows"
language: "Python"
tags: [pypi, uv, github-actions, oidc, artifacts, polars, release-gates]
root-cause: "Local release validation was stronger than CI and publication workflows, while optional Polars paths and artifact contents were not exercised remotely."
severity: "P0"
---

# Harden Python Package Release Gates With Locked CI and OIDC Publication

## Problem

The package could pass local tests and metadata checks while CI omitted runtime
Polars coverage, the lockfile was not enforced, and the tag workflow could build
and publish independently of the full quality gate. Twine validation alone did
not prove that wheel, optional-extra, or sdist installations worked. The first
attempt also could not produce remote evidence because CI only ran on `main` and
pull requests, not on the release branch.

## Root Cause

Release concerns were split across independent workflows without a shared,
executable artifact gate. `uv sync` was allowed to resolve without `--locked`,
`polars` was installed only for type checking, and the publish job depended only
on a tag-local build. GitHub environment and tag protection are repository-level
configuration, not properties created by YAML references.

## Solution

- Run CI on release branches and expose `workflow_call` for the tag workflow.
- Enforce `uv lock --check`, `uv sync --locked`, and `uv run --locked` against
  public PyPI through `UV_DEFAULT_INDEX` with ambient index variables removed in
  local release commands.
- Add a Polars runtime test job and regression tests for nowcast filtering,
  auxiliary catalog/storage behavior, and `get_cp_ki` output conversion.
- Pin Hatchling and GitHub Actions to reviewed versions/SHAs.
- Build with a cleared `dist/`, run Twine, inspect manifests, and install base
  wheel, `[polars]` wheel, and sdist in fresh uv-managed environments through
  `scripts/validate_release.py`.
- Make the tag workflow require a protected tag, main ancestry, publication-ready
  docs, and the reusable complete CI gate before OIDC upload.
- Keep PyPI ownership, trusted-publisher registration, protected `pypi`
  environment, protected `v*` tags, and explicit first-release approval as
  external release prerequisites.

## Prevention

- Treat Twine as metadata validation only; always run clean artifact installs.
- Test every advertised optional backend at runtime, not only in mypy.
- Never rely on a workflow environment name to create protection rules.
- Keep the publish workflow unable to run unless exact-tag CI and artifact gates
  pass; pin release-critical actions to immutable SHAs.
- Use process-scoped public index settings and remove ambient index overrides
  before release checks.

## Related

- `.cg-docs/solutions/build-errors/2026-04-01-pep735-dependency-groups-pip-incompatible.md`
- `.cg-docs/solutions/git-workflows/2026-04-01-mkdocs-github-pages-uv-production-pattern.md`
- `.cg-docs/solutions/build-errors/2026-04-01-hishel-v1-api-removed.md`
- `.cg-docs/plans/2026-08-17-pypi-publication-release-readiness.md`
