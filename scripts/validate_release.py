"""Validate built distributions in isolated environments before publication."""

from __future__ import annotations

import os
import re
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION_MATCH = re.search(
    r'^version\s*=\s*["\']([^"\']+)["\']',
    (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
    flags=re.MULTILINE,
)
EXPECTED_VERSION = VERSION_MATCH.group(1) if VERSION_MATCH else None


def _run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def _python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _create_venv(path: Path) -> Path:
    _run(["uv", "venv", "--clear", str(path)])
    return _python(path)


def _install_and_smoke(python: Path, artifact: Path, extra: str | None = None) -> None:
    requirement = f"{artifact}[{extra}]" if extra else str(artifact)
    env = os.environ.copy()
    env.pop("UV_INDEX", None)
    env.pop("UV_INDEX_URL", None)
    env.pop("UV_EXTRA_INDEX_URL", None)
    env["UV_DEFAULT_INDEX"] = "https://pypi.org/simple"
    _run(["uv", "pip", "install", "--python", str(python), requirement], env=env)
    _run(
        [
            str(python),
            "-c",
            (
                f"import importlib.metadata as m; import povineq; "
                f"assert m.version('povineq') == {EXPECTED_VERSION!r}; "
                f"assert povineq.__version__ == {EXPECTED_VERSION!r}; "
                "print('release smoke test passed')"
            ),
        ]
    )


def main() -> None:
    """Validate manifests and smoke-test each distribution in isolation."""
    if EXPECTED_VERSION is None:
        raise SystemExit("Could not determine project version")

    wheels = sorted(DIST.glob("povineq-*.whl"))
    sdists = sorted(DIST.glob("povineq-*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("dist/ must contain exactly one povineq wheel and sdist")

    wheel, sdist = wheels[0], sdists[0]
    wheel_names = zipfile.ZipFile(wheel).namelist()
    sdist_names = tarfile.open(sdist).getnames()
    if "povineq/py.typed" not in wheel_names:
        raise SystemExit("wheel is missing povineq/py.typed")
    if any(".cg-docs/" in name or "/tests/" in name or ".github/" in name for name in sdist_names):
        raise SystemExit("sdist contains development-only files")

    with tempfile.TemporaryDirectory(prefix="povineq-release-") as temporary:
        base_python = _create_venv(Path(temporary) / "base")
        _install_and_smoke(base_python, wheel)

        polars_python = _create_venv(Path(temporary) / "polars")
        _install_and_smoke(polars_python, wheel, "polars")
        _run([str(polars_python), "-c", "import polars"])

        sdist_python = _create_venv(Path(temporary) / "sdist")
        _install_and_smoke(sdist_python, sdist)


if __name__ == "__main__":
    main()
