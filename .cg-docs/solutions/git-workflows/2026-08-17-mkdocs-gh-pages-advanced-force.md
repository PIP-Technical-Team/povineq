---
date: 2026-08-17
title: "Fix mkdocs gh-deploy refusal when the generated gh-pages branch has advanced"
category: "git-workflows"
language: "Python"
tags: [mkdocs, gh-pages, gh-deploy, force, ci-cd, github-actions, documentation, non-fast-forward]
root-cause: "After a prior successful docs deployment, the generated gh-pages branch's history diverges from the local cloned copy, so mkdocs gh-deploy refuses a non-fast-forward push and the docs workflow fails with 'generated gh-pages branch had advanced'."
severity: "P2"
---

# Fix `mkdocs gh-deploy` refusal when the generated `gh-pages` branch has advanced

## Problem

The docs deployment step `uv run --locked mkdocs gh-deploy` failed in CI with an
error indicating that the generated `gh-pages` branch had advanced and the push
was refused (non-fast-forward). Subsequent docs deployments kept failing until
the branch was force-updated.

## Root Cause

`mkdocs gh-deploy` clones the `gh-pages` branch, builds the site, commits it,
and pushes the result. When the branch history on the remote does not match the
local copy (for example because a previous deploy left the branch in a state
that no longer fast-forwards, or because the branch was otherwise rewritten),
git refuses the push without `--force`. The failure message is "generated
gh-pages branch had advanced", which is MkDocs reporting the non-fast-forward
push refusal.

## Solution

Change the deploy step to force-update the generated branch:

```yaml
- name: Deploy docs
  run: uv run --locked mkdocs gh-deploy --force
```

This is safe **only because** the workflow already serializes deploys with a
concurrency guard:

```yaml
concurrency:
  group: deploy-docs
  cancel-in-progress: true
```

`gh-pages` is a wholly regenerated artifact: each run rebuilds `site/` from
scratch with `mkdocs build --strict` and pushes the full output, so a
force-update leaves no irrecoverable partial state. The concurrency guard
prevents the documented race where two concurrent `--force` deploys tear the
branch.

## Prevention

- Keep the `concurrency:` group on any deploy workflow that uses `--force`;
  never add `--force` to a workflow without it.
- Split `mkdocs build --strict` into its own step before `gh-deploy` so build
  failures surface separately from deploy failures.
- Treat `gh-pages` as a generated artifact: never hand-edit it directly, and
  never rely on it staying fast-forwardable.
- After a docs deploy failure mentioning the generated branch, prefer
  `--force` (with the guard present) over manual branch surgery.

## Related

- `2026-04-01-mkdocs-github-pages-uv-production-pattern.md` — full production
  MkDocs workflow (paths filter, pinned uv, concurrency, strict build). This
  entry documents the specific `--force` failure mode and when it is safe.
- MkDocs deployment docs: https://www.mkdocs.org/user-guide/deploying-your-docs/
