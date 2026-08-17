---
date: 2026-08-17
title: "Publish povineq to PyPI"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-03-31-povineq-architecture-and-stack.md"
language: "Python"
estimated-effort: "medium"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 2
tags: [python, packaging, pypi, release, ci-cd, testing]
---

# Plan: Publish povineq to PyPI

## Objective

Publish the first stable `povineq` distribution to PyPI using a repeatable,
secure release process. The release must be independently buildable, pass all
quality gates, install correctly from its built artifacts, and provide accurate
public installation and release documentation.

## Context

- `pyproject.toml` uses Hatchling, a `src/` layout, Python `>=3.10`, and version
  `0.1.0`; it declares support through Python 3.13.
- Fifteen pytest modules provide mocked, offline coverage for the package API.
  CI currently tests only Python 3.10-3.12 and does not build or validate
  distribution artifacts.
- The baseline `uv` commands could not resolve `hatchling`: the active package
  source attempted `https://r.andres/hatchling/`, which failed DNS resolution.
  This must be corrected before any release-readiness result is trusted.
- `docs` is currently a published optional dependency even though project
  guidance reserves published extras for user-facing features such as `polars`.
  Developer and documentation tooling should remain uv dependency groups.
- PyPI has no project registered at `https://pypi.org/pypi/povineq/json` as of
  this plan's research. Confirm ownership and configure trusted publishing
  before the first production upload.
- The existing roadmap feature `pypi-publishing-and-ci-cd` is planned under
  milestone `v1-full-pipr-parity`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Make the locked project environment and Hatchling build backend resolvable from an approved package source. | Baseline validation failure |
| R2 | Preserve accurate package metadata, supported Python versions, user extras, and version consistency. | `pyproject.toml`; charter |
| R3 | Make the offline test suite, lint checks, type checks, and coverage threshold pass. | User request; `pyproject.toml`; CI |
| R4 | Build and inspect a source distribution and wheel, then test clean installation of base and `polars` artifacts. | PyPI release standard |
| R5 | Extend CI to verify the release gate for every advertised Python version without publishing. | `pyproject.toml`; `.github/workflows/ci.yml` |
| R6 | Create a tag-gated, least-privilege GitHub Actions workflow that publishes verified artifacts via PyPI trusted publishing. | User request; release security |
| R7 | Update public documentation for PyPI installation, optional support, supported Python, and release notes. | README/docs; user request |
| R8 | Register and verify the first PyPI release only after all gates and explicit user confirmation. | User request; irreversible release boundary |

## Phase 1: Release Readiness

### 1. Restore reproducible packaging and release metadata
- **Requirements**: R1, R2
- **Files**: `pyproject.toml`, `uv.lock`, `.python-version` or approved package-tool configuration if required
- **Details**: Identify and remove or correct the package-index override that
  causes Hatchling resolution to target `r.andres`. Regenerate or update
  `uv.lock` using the approved registry. Retain Hatchling and the existing
  `src/` wheel configuration. Reconcile `requires-python`, classifiers, the
  project version, package `__version__` behavior, author/contact fields, URLs,
  license, and keywords. Keep only user-facing extras under
  `[project.optional-dependencies]`; move docs tooling to an appropriate uv
  dependency group and update sync commands accordingly.
- **Test Scenarios**: clean dependency resolution; lockfile consistency; build
  backend resolution without implicit local state; metadata correctly exposes
  base and `polars` installation surfaces.
- **Tests**: `uv lock --check`; `uv sync --group dev`; `uv sync --group docs`;
  `uv build`.
- **Acceptance criteria**: A fresh approved environment resolves the lockfile
  and builds both sdist and wheel without a registry-resolution error.

### 2. Make the full quality gate pass locally
- **Requirements**: R3
- **Files**: `src/povineq/**/*.py`, `tests/**/*.py`, `pyproject.toml`, only as
  failures require
- **Details**: Run the exact release checks from a fresh synced environment.
  Diagnose every reproducible test, lint, type, or coverage failure. Prefer
  fixing product code or test expectations over weakening a check. Maintain
  mocked/offline test behavior and add regression coverage for any defect found.
  Do not reduce declared Python support or the 85% coverage threshold without
  an approved plan deviation.
- **Test Scenarios**: all existing mocked API paths; error paths; public import
  surface; coverage threshold; static analysis violations.
- **Tests**: `uv run pytest --cov=src/povineq --cov-report=term-missing -m "not online"`; `uv run ruff check src/ tests/`; `uv run mypy src`.
- **Acceptance criteria**: All commands exit successfully and coverage meets or
  exceeds the configured 85% threshold.

### 3. Validate built distributions in isolated environments
- **Requirements**: R2, R4
- **Files**: `pyproject.toml`, `tests/test_imports.py`, optionally new release-validation script or workflow commands
- **Details**: Build once into `dist/`, run `twine check` on the wheel and sdist,
  and verify their package metadata and intended contents. Create clean virtual
  environments outside the project environment and install the wheel first
  without dependencies, then with resolved dependencies. Smoke-test
  `import povineq`, `povineq.__version__`, and the public import surface. Repeat
  with the `polars` extra and confirm the extra resolves without exposing
  development or docs extras.
- **Test Scenarios**: base wheel install; wheel install with `[polars]`; source
  distribution build/install; metadata validation; version matches release tag.
- **Tests**: `uv build`; `uv run twine check dist/*`; documented clean-environment
  install/import commands executed against `dist/`.
- **Acceptance criteria**: Both artifacts pass metadata validation and clean
  base and optional-extra installations import successfully.

## Phase 2: Automation and Publication

### 4. Expand CI into a non-publishing release gate
- **Requirements**: R3, R4, R5
- **Files**: `.github/workflows/ci.yml`, `pyproject.toml`, `uv.lock`
- **Details**: Update CI to cover every classifier-supported CPython version
  (3.10, 3.11, 3.12, and 3.13). Use the lockfile and the same `uv` dependency
  group commands validated locally. Keep mocked tests offline, retain quality
  checks, and add a dedicated artifact-build/metadata-validation job. Run the
  documentation smoke check using the docs dependency group. Upload release
  artifacts only as CI artifacts, never to PyPI.
- **Test Scenarios**: pull-request matrix; build job; docs strict build; failure
  prevents later release pipeline success.
- **Tests**: GitHub Actions CI run for a pull request or push; local command
  parity with CI workflow.
- **Acceptance criteria**: CI is green on all four supported Python versions
  and records validated artifacts for a release workflow to consume.

### 5. Add trusted PyPI publishing automation
- **Requirements**: R6, R8
- **Files**: `.github/workflows/publish.yml`, repository GitHub Actions/PyPI
  trusted-publisher configuration
- **Details**: Add a separate workflow triggered only by an immutable version
  tag matching the package version. It must have least-privilege permissions,
  including `id-token: write` only for the PyPI publish job, and use
  `pypa/gh-action-pypi-publish` trusted publishing rather than API tokens.
  Enforce that release artifacts were built and validated by the same release
  gate, validate `dist/*` with Twine immediately before upload, and scope any
  PyPI GitHub environment protection to the publish job. Document the required
  PyPI trusted-publisher registration values: owner `PIP-Technical-Team`, repo
  `povineq`, workflow `publish.yml`, and configured environment if used.
- **Test Scenarios**: non-tag events cannot publish; malformed/mismatched tag
  stops the workflow; publish job obtains OIDC identity without stored secret;
  protected production upload requires approval.
- **Tests**: workflow YAML lint/inspection; dry-run or TestPyPI rehearsal if
  available; GitHub Actions run that exercises build and artifact handoff before
  the production-tag approval.
- **Acceptance criteria**: The workflow can publish only a validated,
  version-matched tag release using OIDC trusted publishing and no repository
  PyPI token.

### 6. Update release-facing documentation and publish the first release
- **Requirements**: R7, R8
- **Files**: `README.md`, `docs/index.md`, `docs/getting-started.md`,
  `CHANGELOG.md`, `docs/changelog.md` if required by MkDocs navigation
- **Details**: Replace temporary Git-only installation notices with canonical
  PyPI commands (`pip install povineq` and `pip install "povineq[polars]"`),
  while retaining source-install guidance only where useful for contributors.
  State the supported Python range and add an initial, user-oriented changelog
  entry. Ensure MkDocs navigation resolves the changelog page. After local and
  CI verification pass, confirm PyPI ownership/trusted-publisher setup and ask
  the user for explicit confirmation before creating the version tag and
  allowing the production publish workflow. Verify the published project from a
  clean environment and update release links/status only after success.
- **Test Scenarios**: installation instructions work; docs strict build succeeds;
  PyPI release is discoverable; clean external install imports the released
  version.
- **Tests**: `uv run mkdocs build --strict`; production PyPI project/version
  inspection; clean-environment `pip install povineq==<tag-version>` plus
  import smoke test.
- **Acceptance criteria**: The released version is available on PyPI, installs
  correctly, matches the git tag and package metadata, and the public docs no
  longer claim it is unavailable.

## Testing Strategy

- Use a fresh uv-managed environment after resolving the build dependency
  source; do not treat cached or editable installs as release evidence.
- Run the complete mocked suite with `-m "not online"`; online API smoke tests
  are optional and must not gate release unless added deliberately.
- Enforce the existing 85% branch-coverage floor, Ruff configuration, and
  configured mypy checks.
- Verify all artifacts from the `dist/` directory with `twine check` and clean
  environment installs of both base and `polars` packages.
- Make CI command-for-command consistent with local verification and exercise
  its 3.10-3.13 matrix before a production tag.
- Do not use TestPyPI as a substitute for production validation; use it only as
  an optional rehearsal and publish production only after confirmation.

## Documentation Checklist

- [ ] `README.md` documents PyPI base and `polars` installation commands.
- [ ] README documents supported Python versions and uv-based contributor setup.
- [ ] MkDocs installation pages remove the “not available on PyPI” warning only
      after publication succeeds.
- [ ] Release notes/changelog contain an initial-version entry and are reachable
      from the configured MkDocs navigation.
- [ ] The PyPI project metadata uses working homepage, documentation,
      repository, and issue URLs.
- [ ] Release workflow setup instructions identify trusted publishing but never
      record credentials.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| The configured registry cannot resolve Hatchling. | All build and quality claims are invalid. | Correct the approved package-source configuration first; rerun every gate from a fresh environment. |
| `povineq` is already claimed on PyPI or by a different publisher. | First publication cannot proceed. | Confirm project ownership before tagging; select a new name only after explicit approval. |
| CI advertises support different from package metadata. | Users install unsupported wheels or encounter untested failures. | Matrix-test every advertised 3.10-3.13 version and keep classifiers synchronized. |
| A token-based or overprivileged workflow leaks release authority. | Unauthorized or compromised release publication. | Use a separate tag-only workflow with OIDC trusted publishing, `id-token: write`, and protected environment controls. |
| Locally editable installation masks missing wheel contents or metadata. | Broken PyPI artifact despite passing source tests. | Validate sdist/wheel with Twine and install them into clean external environments. |
| Changing docs/extras breaks contributor or site builds. | Regressed contributor setup or documentation deployment. | Keep non-user tooling in uv groups and run strict docs build in CI before release. |

## Out of Scope

- New PIP API features, API behavior changes, CLI/async support, and v2 work.
- Adding new public package extras beyond the existing `polars` option.
- Storing PyPI tokens, credentials, or other release secrets in source control.
- Automatic production release without an explicit confirmation immediately
  before tagging/publishing.

## Completion Contract

### Outcome

`povineq` version `0.1.0` is independently buildable, installs successfully
from a built wheel with its declared Python and optional-dependency support, and
has passing automated quality gates. A protected GitHub Actions release workflow
can publish an exact version-tagged artifact to PyPI using trusted publishing,
with public installation and release documentation updated.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Build dependency source is valid and locked environment resolves. | `uv lock --check` and `uv build` | yes |
| V2 | Full offline suite passes with branch coverage at or above 85%. | `uv run pytest --cov=src/povineq --cov-report=term-missing -m "not online"` | yes |
| V3 | Linting and configured type checks pass. | `uv run ruff check src/ tests/` and `uv run mypy src` | yes |
| V4 | Wheel and source archive satisfy metadata and contents checks. | `uv run twine check dist/*`; clean-environment base and `[polars]` wheel installs | yes |
| V5 | CI validates Python 3.10-3.13, tests, quality gates, artifact build, and docs build without PyPI credentials. | Updated `.github/workflows/ci.yml`; successful GitHub Actions run | yes |
| V6 | Tag-only release workflow uses PyPI trusted publishing and uploads only verified artifacts. | `.github/workflows/publish.yml`; GitHub environment configuration confirmed | yes |
| V7 | Public docs cover PyPI installation, optional support, supported Python, and release notes. | Updated `README.md`, `docs/`, and changelog artifacts | yes |
| V8 | First release is visible and installable at the expected version. | PyPI project release plus clean-environment install/import check | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | Keep `requires-python >=3.10` and test every advertised version, including 3.13. | `pyproject.toml` classifiers and CI matrix agree. |
| C2 | Only `polars` is a public extra; dev/docs tooling stays in uv dependency groups. | Inspect package metadata and CI sync commands. |
| C3 | Do not commit PyPI tokens or credentials. | Trusted publishing with `id-token: write`; security review of workflow. |
| C4 | Do not publish artifacts that did not pass the same local/CI checks. | Workflow validates exact artifacts before upload. |
| C5 | Preserve offline deterministic testing through mocked PIP API interactions. | Continue `-m "not online"` and existing HTTP mocks. |

### Boundaries

- Allowed: package metadata, dependency organization and lockfile, test/CI gates,
  distribution verification, PyPI trusted-publishing workflow, release docs,
  version tag, and first PyPI publication.
- Out of scope: PIP API features, CLI/async/v2 work, public behavior changes,
  new user extras, and publishing credentials.

### Iteration Policy

1. Resolve the invalid or unreachable Hatchling package-index configuration
   before judging test, lint, typing, build, or release readiness.
2. Fix code, metadata, configuration, or tests only when a required quality
   gate reveals a reproducible failure.
3. Treat an advertised-support mismatch as a required deviation; under policy
   `ask`, pause for approval before reducing support or changing the release
   surface.
4. Before production upload, confirm PyPI project ownership and that the PyPI
   trusted-publisher configuration exactly matches the repository and workflow.
5. Publish only after all required evidence passes in CI and the user explicitly
   confirms the irreversible first-release action.

### Blocked-Stop Conditions

- The configured package registry remains unable to resolve the required build
  backend.
- A required test, lint, typing, build, distribution-install, metadata, or CI
  check fails without an approved correction.
- `povineq` is unavailable to the intended PyPI account or the trusted publisher
  cannot be verified.
- The release workflow would need static PyPI credentials or unreviewed
  permission broadening.
- The package version already exists on PyPI, or the release tag and package
  version disagree.
- Production PyPI publication lacks explicit user confirmation.
