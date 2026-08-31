"""Anti-drift: the package version must match pyproject.toml."""

from __future__ import annotations

import pathlib

import tomllib

import facturino


def test_version_matches_pyproject() -> None:
    root = pathlib.Path(__file__).resolve().parent.parent
    data = tomllib.loads((root / "pyproject.toml").read_text())
    assert facturino.__version__ == data["project"]["version"]
