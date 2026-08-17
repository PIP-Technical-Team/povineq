---
date: 2026-08-17
title: "Publish povineq to PyPI with release-readiness gates"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-03-31-povineq-architecture-and-stack.md"
language: "Python"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 2
tags: [python, packaging, pypi, release, ci-cd, testing, uv]
execution-report: ".cg-docs/work-reports/2026-08-17-pypi-publication-release-readiness.md"
completed-phases: [1, 2]
current-phase: complete
---

# Plan: Publish povineq to PyPI with Release-Readiness Gates

## Objective

Publish the first stable `povineq` distribution to PyPI through a repeatable,
credential-safe release process. The package must pass quality gates, install
from its built artifacts, and publish only an exact version-tagged distribution
through GitHub OIDC trusted publishing.

## Context

- `pyproject.toml` uses Hatchling, a `src/` layout, Python `>=3.10`, and version
  `0.1.0`; classifiers declare support through Python 3.13.
- The committed `uv.lock` resolves packages through `https://pypi.org/simple`.
  CI has no index override, while the developer shell has a malformed,
  credential-bearing `UV_INDEX` override that caused the earlier Hatchling DNS
  failure. It is local state, not project configuration.
- Public PyPI is the release-validation registry. Release commands and CI must
  force or inherit `https://pypi.org/simple` without reading, logging, or
  persisting local internal-index credentials.
- The baseline, run with the local `UV_INDEX` neutralized, passes the offline
  suite (`200 passed`, `2 skipped`) with `92.04%` branch coverage and passes
  Ruff. Mypy reports 24 errors in eight source files, including untyped
  third-party imports and `Literal` mismatches; resolving these is planned work.
- The project has fourteen test modules plus shared fixtures. Its documentation
  dependencies are incorrectly published as a `docs` package extra; current CI,
  docs deployment, and the README use mixed `--extra`/`--group` commands.
- `twine` is not currently declared, even though it is required to validate
  source and wheel metadata before publication.
- The existing roadmap feature `pypi-publishing-and-ci-cd` is planned under
  milestone `v1-full-pipr-parity`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Run lock, build, and CI dependency resolution against public PyPI without exposing or persisting local registry credentials. | Plan review P1.1/P1.2; committed lockfile |
| R2 | Keep only `polars` as a public extra; place developer, documentation, release-validation, and typing tools in uv dependency groups and update every dependent command atomically. | Plan review P1.3/P2.1/P3.3; dependency-group solution |
| R3 | Reproduce and resolve the full release quality gate: offline tests, 85% branch coverage, Ruff, and mypy. | User request; baseline; plan review P2.2/P2.3 |
| R4 | Build and validate sdist/wheel artifacts, then install and smoke-test base, `polars`, and sdist distributions in clean environments. | PyPI release standard |
| R5 | Enforce the same quality, build, metadata, and documentation gates in GitHub Actions for all advertised Python versions. | `pyproject.toml`; plan review P2.1/P2.2 |
| R6 | Use a tag-gated, least-privilege trusted-publishing workflow that asserts the tag version equals `pyproject.toml` before PyPI upload. | Plan review P2.4; release security |
| R7 | Publish accurate PyPI installation, contributor setup, support, and changelog documentation. | README/docs; plan review P3.3 |
| R8 | Perform the first production release only after verified PyPI ownership, trusted-publisher setup, all required CI evidence, and explicit user confirmation. | User request; irreversible release boundary |

## Phase 1: Local Release Readiness

### 1. Establish the credential-safe public-PyPI baseline
- **Requirements**: R1, R3
- **Files**: No tracked-file change required unless remediation reveals one;
  `uv.lock`, `pyproject.toml`, and workflow files are inspection targets.
- **Details**: Treat `UV_INDEX` as local shell state. Do not inspect, print, or
  copy its credential value. Run each release command with a process-scoped
  public index, for example `UV_INDEX=https://pypi.org/simple <command>`, rather
  than modifying the developer shell or adding an authenticated index to project
  configuration. Confirm committed lockfile registry entries are public PyPI and
  contain no userinfo. Record the current baseline: tests and coverage pass,
  Ruff passes, and mypy fails with 24 errors. Use this baseline to scope the
  remediation work; do not presume all quality gates already pass.
- **Test Scenarios**: malformed local override is ignored; lock resolves from
  public PyPI; no tracked release file contains a credential; baseline results
  reproduce from a clean process.
- **Tests**: `UV_INDEX=https://pypi.org/simple uv lock --check`; `UV_INDEX=https://pypi.org/simple uv build`; `UV_INDEX=https://pypi.org/simple uv run pytest --cov=src/povineq --cov-report=term-missing -m "not online"`; `UV_INDEX=https://pypi.org/simple uv run ruff check src/ tests/`; `UV_INDEX=https://pypi.org/simple uv run mypy src`.
- **Acceptance criteria**: Public-PyPI lock/build succeeds, all current quality
  outcomes are recorded, and no credential-bearing index URL is present in
  `uv.lock`, `pyproject.toml`, or GitHub workflow YAML.

### 2. Migrate tooling dependencies and commands atomically
- **Requirements**: R1, R2
- **Files**: `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`,
  `.github/workflows/docs.yml`, `README.md`
- **Details**: Keep `polars` as the sole `[project.optional-dependencies]`
  entry. Move MkDocs tooling to a `[dependency-groups] docs` group and add a
  `release` group containing `twine`. Keep test/lint/type tooling in `dev`; add
  narrowly justified typing dependencies such as `pandas-stubs` when needed.
  Do not add a credential-bearing `[tool.uv]` index or duplicate development
  tools as published extras. In the same change, update every affected command:
  docs CI and deployment use `uv sync --group docs`, contributor setup uses
  `uv sync --group dev`, and artifact validation syncs `--group release`.
  Regenerate the lockfile using the public-PyPI process-scoped index.
- **Test Scenarios**: public metadata exposes only `polars`; every development,
  docs, and release group installs; no CI/docs interval uses a removed extra;
  lockfile has no credentials.
- **Tests**: `UV_INDEX=https://pypi.org/simple uv lock --check`; `UV_INDEX=https://pypi.org/simple uv sync --group dev`; `UV_INDEX=https://pypi.org/simple uv sync --group docs`; `UV_INDEX=https://pypi.org/simple uv sync --group release`; `UV_INDEX=https://pypi.org/simple uv run twine --version`.
- **Acceptance criteria**: The dependency migration and all command consumers
  land together; `uv sync` succeeds for each group; `twine` is available; and
  only `polars` appears in published optional metadata.

### 3. Make the release quality gate pass locally
- **Requirements**: R2, R3
- **Files**: `src/povineq/**/*.py`, `tests/**/*.py`, `pyproject.toml`,
  `uv.lock`, as required by reproducible findings
- **Details**: Resolve the recorded mypy failures without disabling global type
  checking. Add third-party stubs where available, use narrow module-specific
  overrides only for libraries without type information, install the `polars`
  extra in the type-check environment when imports require it, and correct
  source annotations or validation types that conflict with `Literal` fields.
  Add regression tests for any runtime defect found. Make `__version__`
  behavior explicit by catching `importlib.metadata.PackageNotFoundError` for a
  direct source checkout, while retaining package metadata as the installed
  distribution authority. Do not lower the 85% coverage floor, remove Python
  3.10-3.13 support, or suppress broad mypy error classes without an approved
  deviation.
- **Test Scenarios**: source checkout without installed metadata; typed public
  argument paths; optional `polars` type imports; mocked API tests; coverage;
  lint and mypy success.
- **Tests**: `UV_INDEX=https://pypi.org/simple uv sync --group dev --extra polars`; `UV_INDEX=https://pypi.org/simple uv run pytest --cov=src/povineq --cov-report=term-missing -m "not online"`; `UV_INDEX=https://pypi.org/simple uv run ruff check src/ tests/`; `UV_INDEX=https://pypi.org/simple uv run mypy src`.
- **Acceptance criteria**: Tests, branch coverage, Ruff, and mypy all pass from
  a public-PyPI process with no broader type-checking suppression than justified
  by an untyped external dependency.

## Phase 2: Artifact Gates and Publication

### 4. Validate release artifacts in isolated environments
- **Requirements**: R1, R2, R4
- **Files**: `pyproject.toml`, `uv.lock`, optionally a documented
  release-validation command or script if repetition warrants it
- **Details**: Build the sdist and wheel once from a clean public-PyPI process.
  Run `twine check` against both artifacts. In fresh temporary environments that
  do not reuse the project virtual environment, install the wheel with base
  dependencies and with `[polars]`, then install the sdist. For each install,
  assert `import povineq`, public API imports, and
  `importlib.metadata.version("povineq")` equal the built version. Inspect the
  artifact manifest only to confirm source, license, package modules, and typed
  marker are included; do not use an editable install as release evidence.
- **Test Scenarios**: sdist metadata; wheel metadata; base wheel install;
  `polars` wheel install; sdist install; missing package content; version
  consistency.
- **Tests**: `UV_INDEX=https://pypi.org/simple uv build`; `UV_INDEX=https://pypi.org/simple uv run --group release twine check dist/*`; documented clean-environment install/import commands against each artifact.
- **Acceptance criteria**: Both artifacts pass Twine validation and every clean
  install/import scenario succeeds at the package version declared by
  `pyproject.toml`.

### 5. Make CI enforce the full non-publishing release gate
- **Requirements**: R1, R2, R3, R4, R5
- **Files**: `.github/workflows/ci.yml`, `.github/workflows/docs.yml`,
  `pyproject.toml`, `uv.lock`
- **Details**: Set CI dependency resolution explicitly to public PyPI without
  credentials. Test Python 3.10, 3.11, 3.12, and 3.13 with the offline pytest
  suite and coverage report. Add a quality job that runs Ruff and mypy using
  the required dev and `polars` environment. Add a build job that uses the
  release group, runs `uv build` and `twine check`, and uploads artifacts only
  as CI artifacts. Run the strict MkDocs build through the `docs` group on
  Python 3.12. Preserve docs deployment behavior after its group migration.
- **Test Scenarios**: each supported interpreter; failing mypy blocks CI;
  artifacts fail metadata validation; docs group works; no CI job resolves an
  internal authenticated registry.
- **Tests**: successful pull-request or branch CI run; workflow command parity
  with Steps 2-4; verification that matrix, quality, build, and docs jobs fail
  when their respective commands fail.
- **Acceptance criteria**: A green CI run demonstrates all required quality and
  artifact gates on the advertised support surface without PyPI publishing or
  credentials.

### 6. Add tag-verified PyPI trusted publishing
- **Requirements**: R1, R4, R5, R6
- **Files**: `.github/workflows/publish.yml`, repository GitHub Actions settings,
  PyPI trusted-publisher configuration
- **Details**: Add a separate workflow triggered only by `v*` version tags.
  Its validation job checks out the tag, forces public-PyPI resolution, loads
  `[project].version` from `pyproject.toml` with `tomllib`, strips the leading
  `v` from `GITHUB_REF_NAME`, and exits nonzero unless the values match exactly.
  That job builds `dist/`, runs `twine check`, and uploads the validated
  artifacts. A separate publish job downloads only those artifacts, uses a
  protected `pypi` environment if configured, has only `id-token: write` plus
  required read permissions, and invokes `pypa/gh-action-pypi-publish` through
  OIDC. Do not add a PyPI API token to source control or GitHub secrets.
  Register the PyPI trusted publisher with the exact GitHub owner, repository,
  workflow filename, and environment name used by the workflow.
- **Test Scenarios**: non-tag event cannot publish; `v0.1.1` tag on `0.1.0`
  metadata fails before build/upload; matching tag builds valid artifacts;
  publisher receives OIDC identity without static credentials.
- **Tests**: workflow YAML validation; a deliberately mismatched tag/version in
  a safe branch or local workflow assertion test; GitHub Actions validation-job
  run; PyPI trusted-publisher configuration inspection.
- **Acceptance criteria**: The publish job has no static PyPI credential and is
  unreachable unless a matching version tag's artifacts passed validation.

### 7. Publish release-facing documentation and execute the first release
- **Requirements**: R2, R7, R8
- **Files**: `README.md`, `docs/index.md`, `docs/getting-started.md`,
  `CHANGELOG.md`, `docs/changelog.md` if required by MkDocs navigation
- **Details**: Replace temporary Git-only installation notices with
  `pip install povineq` and `pip install "povineq[polars]"`; retain source
  installation only as contributor guidance. Correct the development command to
  `uv sync --group dev`, document supported Python versions, and describe that
  docs/release tooling requires uv dependency groups rather than PyPI extras.
  Add an initial changelog entry and ensure MkDocs navigation resolves it. After
  all local and CI evidence passes, verify PyPI package ownership and trusted
  publisher registration. Ask the user for explicit confirmation immediately
  before creating `v0.1.0` and enabling the production publish workflow. After
  success, install `povineq==0.1.0` from PyPI in a clean environment and update
  the release status only if that check passes.
- **Test Scenarios**: public base and optional installation guidance; contributor
  sync command; strict docs build; PyPI discovery; released clean install;
  tag/version/documentation agreement.
- **Tests**: `UV_INDEX=https://pypi.org/simple uv run --group docs mkdocs build --strict`; PyPI project/version inspection; clean-environment `pip install povineq==0.1.0` and import/version smoke test.
- **Acceptance criteria**: The first release is discoverable and installable at
  `0.1.0`, matches the Git tag and package metadata, and the documentation no
  longer claims PyPI installation is unavailable.

## Testing Strategy

- Use `UV_INDEX=https://pypi.org/simple` only as a process-scoped command
  override for local release checks; GitHub Actions uses the same credential-free
  public index policy.
- Preserve existing mocked/offline coverage with `-m "not online"`; online API
  smoke tests remain non-gating.
- Make the 85% branch-coverage threshold, Ruff, and mypy required before CI or
  release evidence can pass.
- Validate both sdist and wheel metadata with Twine and install base, optional,
  and sdist artifacts in fresh environments outside `.venv`.
- Require CI evidence for Python 3.10-3.13, typing, docs, and artifacts before
  release-tag creation; the tag workflow repeats version and artifact checks.
- Omit TestPyPI rehearsal from the release path. If later added, configure its
  separate trusted publisher and treat it as a distinct scoped change.

## Documentation Checklist

- [ ] Public PyPI commands cover base and `polars` installations.
- [ ] README contributor setup uses `uv sync --group dev`.
- [ ] Docs/release tool groups are documented as uv-only, not user package extras.
- [ ] Supported Python 3.10-3.13 range is stated consistently.
- [ ] Initial changelog is available from MkDocs navigation.
- [ ] PyPI homepage, documentation, repository, and issues URLs are valid.
- [ ] Trusted-publishing setup documents identifiers but never credentials.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| A developer `UV_INDEX` override routes uv to a malformed authenticated index. | Builds fail or credentials leak into logs/committed files. | Force public PyPI only per release process, avoid reading/logging the variable, and scan tracked config/lock files for userinfo. |
| Mypy baseline has 24 current errors. | Type gate delays release or leads to unsafe suppression. | Triage errors by third-party stubs, optional import environment, and source annotations; require narrow documented exceptions only where upstream lacks types. |
| Moving docs from an extra to a group breaks CI or deployment in an intermediate commit. | Documentation CI/deployment becomes red. | Change `pyproject.toml`, both workflows, README, and lockfile atomically in Phase 1. |
| A tag differs from project metadata. | An irreversible PyPI release has conflicting version identifiers. | Assert stripped `GITHUB_REF_NAME` equals `pyproject.toml` version before build/artifact upload. |
| `povineq` is unavailable to the intended PyPI publisher. | First publication cannot proceed. | Confirm ownership and trusted-publisher registration before tag creation. |
| Editable/source tests mask missing distribution contents. | The PyPI wheel or sdist is broken despite local tests. | Run Twine plus isolated base, optional-extra, and sdist install/import checks. |
| Python 3.13 or docs build regresses despite current local results. | Advertised support does not work for users. | Run CI matrix and strict docs job before a protected release tag. |

## Out of Scope

- Changing PIP API behavior, adding `get_gd`, CLI/async support, or v2 features.
- Adding user-facing extras beyond `polars`.
- Reading, logging, embedding, or committing Artifactory/PyPI credentials.
- Changing the approved release-validation registry from public PyPI.
- Publishing automatically or without user confirmation immediately before the
  first production tag.

## Completion Contract

### Outcome

`povineq` version `0.1.0` is built, tested, and installed from artifacts using
a credential-free public-PyPI resolution path. CI enforces tests, coverage,
Ruff, mypy, artifact validation, and tag-version equality; a least-privilege
trusted-publishing workflow can perform the user-approved first PyPI release.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Release commands bypass local `UV_INDEX`; committed release files have no credentials. | `UV_INDEX=https://pypi.org/simple uv lock --check`; credential scan of lock/workflow files | yes |
| V2 | 1 | Offline suite, coverage, Ruff, and mypy pass. | Public-PyPI pytest, Ruff, and mypy commands from Step 3 | yes |
| V3 | 2 | sdist/wheel pass metadata validation and isolated base, optional, and sdist installs. | `uv build`; `twine check`; clean install/import checks | yes |
| V4 | 2 | CI verifies Python 3.10-3.13, quality, artifact, and docs gates. | Successful `.github/workflows/ci.yml` run | yes |
| V5 | 2 | Tag release asserts version equality before OIDC publish. | `.github/workflows/publish.yml`; mismatch-negative check | yes |
| V6 | final | PyPI release is visible, version-matched, and clean-installable. | PyPI inspection; `pip install povineq==0.1.0`; import/version check | yes |
| V7 | final | Public and contributor documentation shows valid installation/release paths. | README/docs/changelog; strict MkDocs build | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Public PyPI is the only release validation and CI registry; local credentials never enter tracked files. | Process-scoped override plus credential scan. |
| C2 | 1 | `polars` is the only public extra; tooling remains in uv groups. | `pyproject.toml` metadata and all sync commands. |
| C3 | 1 | Preserve Python 3.10-3.13 support, mocked offline testing, and 85% coverage. | Classifiers, CI matrix, test command, coverage config. |
| C4 | 2 | Do not publish unverified or tag/version-mismatched artifacts. | CI evidence and workflow assertion. |
| C5 | 2 | Publish job uses OIDC and least privilege, never a static PyPI token. | `publish.yml` permissions/action and repository settings. |

### Boundaries

- Allowed: release command environment isolation; dependency groups; type fixes;
  tests; artifact/CI/publish workflows; release docs; first tag and PyPI release.
- Out of scope: credentials, registry-policy changes, package feature work, new
  public extras, and unconfirmed production publication.

### Iteration Policy

1. Use public PyPI process-scoped resolution without accessing the local
   `UV_INDEX` value.
2. Make dependency-group migration and every consuming command a single change.
3. Correct type defects or add only narrow, justified external-library typing
   exceptions; request approval before weakening type, coverage, or Python
   support requirements.
4. Require a matching tag, green required CI evidence, artifact validation,
   package ownership, and trusted-publisher configuration before publication.
5. Pause for explicit user confirmation before creating or publishing `v0.1.0`.

### Blocked-Stop Conditions

- Public PyPI cannot reproduce the lock/build without the local `UV_INDEX`.
- A release file or artifact contains an Artifactory/PyPI credential.
- Required tests, coverage, Ruff, mypy, artifact validation, CI, or docs checks
  remain failing after permitted remediation.
- PyPI ownership, trusted-publisher configuration, or tag-version equality
  cannot be verified.
- The user has not explicitly approved first production publication.
