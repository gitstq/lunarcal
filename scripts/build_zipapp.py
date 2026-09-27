#!/usr/bin/env python3
"""Build a single-file zipapp executable `lunarcal.pyz`.

Usage:
    python3 scripts/build_zipapp.py

The resulting `lunarcal.pyz` can be run directly on any machine with
Python 3.8+:
    python3 lunarcal.pyz today
    ./lunarcal.pyz solar2lunar 2024-02-10
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import zipapp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "lunarcal")
OUT = os.path.join(ROOT, "lunarcal.pyz")


def main() -> int:
    if not os.path.isdir(PKG):
        print(f"cannot find package at {PKG}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        dst = os.path.join(td, "lunarcal")
        shutil.copytree(PKG, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        zipapp.create_archive(td, target=OUT, main="lunarcal.cli:main",
                              compressed=True)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
