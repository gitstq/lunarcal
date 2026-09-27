# Contributing to lunarcal

Thanks for your interest in improving lunarcal!  This project is
**100% self-implemented** on top of the public astronomical-algorithm
literature (Meeus, *Astronomical Algorithms*).  We do **not** copy data
tables from existing lunar libraries.

## Development setup

```bash
git clone https://github.com/gitstq/lunarcal.git
cd lunarcal
python3 -m venv .venv && . .venv/bin/activate
pip install -e .[dev]      # build / wheel are dev-only
make test
```

There are **no runtime dependencies**; only the Python standard library
is used.  `build` is a *development* dependency for producing wheels.

## Pull requests

1. Fork the repo and create a feature branch.
2. Add or update golden-value tests in `tests/`.  Every behaviour change
   must be backed by a known, real-world date.
3. Run `make test` and make sure all 16+ golden tests pass.
4. Follow the [Conventional Commits](https://www.conventionalcommits.org/)
   style used on `main`:
   - `feat: ...` new feature
   - `fix: ...` bug fix
   - `docs: ...` documentation
   - `refactor: ...` code restructuring (no behaviour change)
   - `test: ...` adding/updating tests
   - `chore: ...` tooling / build / CI
5. Open a PR against `main`.

## Reporting issues

When reporting a date mismatch, please include:
- the Gregorian date (Beijing time) you tested,
- what lunarcal returned,
- what the *correct* value should be (cite an authoritative source),
- Python version and OS.

## Code of conduct

Be kind, be constructive, and remember that the calendar is a shared
public good.
