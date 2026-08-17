# 🧠 Project Brain — Chronological Log

_Generated 2026-08-17 · 16 artifacts (newest first) + 14 roadmap features_

## undated

- **[2026-03-31-povineq-v1-full-implementation-review](.cg-docs/reviews/2026-03-31-povineq-v1-full-implementation-review.md)** · `review` · _—_ · `—`
  > **Review depth**: thorough **Files reviewed**: 34 **Findings**: 2 P1 · 25 P2 · 12 P3 **Date**: 2026-04-01 **Agents**:…
- **[2026-04-01-documentation-website-light-review](.cg-docs/reviews/2026-04-01-documentation-website-light-review.md)** · `review` · _—_ · `—`
  > **Review depth**: light **Files reviewed**: 7 (`.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.gitignore`…
- **[2026-04-01-documentation-website-review](.cg-docs/reviews/2026-04-01-documentation-website-review.md)** · `review` · _—_ · `—`
  > **Review depth**: thorough **Files reviewed**: 8 (`.gitignore`, `pyproject.toml`, `roadmap.json`, `uv.lock`, `.github…
- **[2026-04-01-povineq-light-review](.cg-docs/reviews/2026-04-01-povineq-light-review.md)** · `review` · _—_ · `—`
  > **Review depth**: light **Date**: 2026-04-01 **Files reviewed**: 34 (14 source + 14 test + pyproject.toml + CI + conf…

## 2026-08-17

- **[Harden Python package release gates with locked CI and OIDC publication](.cg-docs/solutions/git-workflows/2026-08-17-pypi-release-gates-and-oidc.md)** · `solution` · _—_ · `2026-08-17`
  > The package could pass local tests and metadata checks while CI omitted runtime Polars coverage, the lockfile was not…
- **[Publish povineq to PyPI](.cg-docs/plans/2026-08-17-pypi-publication.md)** · `plan` · _active_ · `2026-08-17`
  > Publish the first stable `povineq` distribution to PyPI using a repeatable, secure release process. The release must …
- **[Publish povineq to PyPI with release-readiness gates](.cg-docs/plans/2026-08-17-pypi-publication-release-readiness.md)** · `plan` · _active_ · `2026-08-17`
  > Publish the first stable `povineq` distribution to PyPI through a repeatable, credential-safe release process. The pa…

## 2026-04-01

- **[Documentation website for povineq](.cg-docs/brainstorms/2026-04-01-documentation-website.md)** · `brainstorm` · _decided_ · `2026-04-01`
  > The `povineq` package needs a documentation website similar to what `pkgdown` provides for R packages (e.g., [pipr](h…
- **[Documentation website with MkDocs + Material](.cg-docs/plans/2026-04-01-documentation-website.md)** · `plan` · _active_ · `2026-04-01`
  > Build and deploy a documentation website for `povineq` at `pip-technical-team.github.io/povineq/` using MkDocs + Mate…
- **[hishel >=1.0 removed CacheTransport/FileStorage/Controller API](.cg-docs/solutions/build-errors/2026-04-01-hishel-v1-api-removed.md)** · `solution` · _—_ · `2026-04-01`
  > Code that used `hishel` for caching HTTP responses (commonly paired with `httpx`) would fail at import time with: No …
- **[loguru: avoid f-strings in log calls \(defeats lazy evaluation\)](.cg-docs/solutions/testing-patterns/2026-04-01-loguru-no-fstrings.md)** · `solution` · _—_ · `2026-04-01`
  > Calls like `logger.debug(f"Processing {len(data)} records")` pass a pre-formatted string to loguru. If the `DEBUG` le…
- **[pandas inplace=True silently returns None, causing downstream NoneType errors](.cg-docs/solutions/bugs/2026-04-01-pandas-inplace-returns-none.md)** · `solution` · _—_ · `2026-04-01`
  > Code using `inplace=True` on pandas DataFrame methods (e.g., `rename`, `drop`, `set_index`, `sort_values`) stores `No…
- **[PEP 735 \[dependency-groups\] is uv-only; pip silently ignores them](.cg-docs/solutions/build-errors/2026-04-01-pep735-dependency-groups-pip-incompatible.md)** · `solution` · _—_ · `2026-04-01`
  > Defining dev or docs dependencies under `[dependency-groups]` in `pyproject.toml` (PEP 735 syntax) works perfectly wi…
- **[Production-ready MkDocs + GitHub Pages + uv CI/CD workflow](.cg-docs/solutions/git-workflows/2026-04-01-mkdocs-github-pages-uv-production-pattern.md)** · `solution` · _—_ · `2026-04-01`
  > A minimal `mkdocs gh-deploy` workflow works locally but has several reliability problems in CI: 1. **Race condition**…

## 2026-03-31

- **[povineq Python package — architecture and stack decisions](.cg-docs/brainstorms/2026-03-31-povineq-architecture-and-stack.md)** · `brainstorm` · _decided_ · `2026-03-31`
  > The team needs to build `povineq`, a Python wrapper for the PIP API that replicates the functionality of the `pipr` R…
- **[povineq v1.0 — Full implementation plan](.cg-docs/plans/2026-03-31-povineq-v1-full-implementation.md)** · `plan` · _active_ · `2026-03-31`
  > Build a complete Python package (`povineq`) that wraps the World Bank PIP API with full feature parity to the `pipr` …

## Roadmap Features

- **[Architecture and stack design](roadmap.json#architecture-and-stack-design)** · `feature` · _done_ · `—`
  > Architecture and stack design
- **[Async support](roadmap.json#async-support)** · `feature` · _idea_ · `—`
  > Async support
- **[Auxiliary data functions \(get_aux and all convenience wrappers\)](roadmap.json#auxiliary-data-functions)** · `feature` · _done_ · `—`
  > Auxiliary data functions (get_aux and all convenience wrappers)
- **[CLI \(thin wrapper around core functions\)](roadmap.json#cli)** · `feature` · _idea_ · `—`
  > CLI (thin wrapper around core functions)
- **[Core infrastructure](roadmap.json#core-infrastructure)** · `feature` · _done_ · `—`
  > Core infrastructure
- **[Core stats functions \(get_stats, get_wb, get_agg\)](roadmap.json#core-stats-functions)** · `feature` · _done_ · `—`
  > Core stats functions (get_stats, get_wb, get_agg)
- **[Country profile functions \(get_cp, get_cp_ki\)](roadmap.json#country-profile-functions)** · `feature` · _done_ · `—`
  > Country profile functions (get_cp, get_cp_ki)
- **[Documentation and README](roadmap.json#documentation-and-readme)** · `feature` · _done_ · `—`
  > Documentation and README
- **[Documentation website \(MkDocs + Material\)](roadmap.json#documentation-website-mkdocs-material)** · `feature` · _done_ · `—`
  > Documentation website (MkDocs + Material)
- **[get_gd — grouped data from user-supplied distributions](roadmap.json#get-gd-grouped-data)** · `feature` · _idea_ · `—`
  > get_gd — grouped data from user-supplied distributions
- **[Package scaffolding](roadmap.json#package-scaffolding)** · `feature` · _done_ · `—`
  > Package scaffolding
- **[PyPI publishing and CI/CD](roadmap.json#pypi-publishing-and-ci-cd)** · `feature` · _active_ · `—`
  > PyPI publishing and CI/CD
- **[Tests \(pytest suite mirroring pipr test suite\)](roadmap.json#tests)** · `feature` · _done_ · `—`
  > Tests (pytest suite mirroring pipr test suite)
- **[Utility functions \(check_api, get_versions, get_pip_info, cache helpers\)](roadmap.json#utility-functions)** · `feature` · _done_ · `—`
  > Utility functions (check_api, get_versions, get_pip_info, cache helpers)
