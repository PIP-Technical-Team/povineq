# Changelog

See [GitHub Releases](https://github.com/PIP-Technical-Team/povineq/releases)
for the full release history.

---

## 0.1.1 — Security-hardened dependencies

Security-hardened dependency floors for transitive runtime and tooling
dependencies:

- Bump `idna` (runtime, via `httpx`) to `>=3.15`
- Bump `urllib3` (release tooling, via `twine`) to `>=2.7.0`
- Bump `pymdown-extensions` (docs tooling, via `mkdocs-material`) to `>=11.0.1`
- Bump `pytest` (dev) to `>=9.0.3`

## 0.1.0 — Initial release

Initial release of the `povineq` Python wrapper for the World Bank PIP API,
including poverty statistics, country profiles, auxiliary data, and
pandas/polars output support.
