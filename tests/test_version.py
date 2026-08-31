"""Anti-drift: the package version must match pyproject.toml."""

from __future__ import annotations

import pathlib
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10: tomllib entered the stdlib in 3.11 (PEP 680).
    import tomli as tomllib

import facturino


def test_version_matches_pyproject() -> None:
    root = pathlib.Path(__file__).resolve().parent.parent
    data = tomllib.loads((root / "pyproject.toml").read_text())
    assert facturino.__version__ == data["project"]["version"]
