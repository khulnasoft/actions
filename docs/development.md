# Development Guide

## Repository layout

This is a monorepo containing three independent GitHub Actions. Each action
lives in its own top-level directory and is released independently:

| Action | Directory | Version file | Git tag |
|---|---|---|---|
| Issue Manager | `issue-manager/` | `issue-manager/version.txt` | `issue-manager/vX.Y.Z` |
| Label Approved | `label-approved/` | `label-approved/version.txt` | `label-approved/vX.Y.Z` |
| Latest Changes | `latest-changes/` | `latest-changes/version.txt` | `latest-changes/vX.Y.Z` |

See [architecture.md](architecture.md) for the full architecture and
[migration.md](migration.md) for the migration policy from the old
single-action repositories.

## Local setup

Requires Python 3.14 (see `pyproject.toml`).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Each action has its own runtime and test dependencies:

```bash
pip install -r <action>/requirements.txt
pip install -r <action>/requirements-test.txt
```

## Common commands

Run from the repository root:

```bash
# Lint and format checks
ruff check <action>
ruff format --check <action>

# Type checking
mypy <action>

# Tests for one action
PYTHONPATH=<action> pytest <action>/tests --import-mode=importlib

# Repository-level validation (run in CI)
python scripts/validate_metadata.py
python scripts/prepare_release.py check
python scripts/affected_actions.py   # reads changed paths on stdin
```

## Docker builds

Each action builds from its own directory — the build context is the action
directory, not the repository root:

```bash
docker build -f issue-manager/base.dockerfile issue-manager
```

`base.dockerfile` builds the runtime image from source.
`<action>/Dockerfile` is a thin pinned `FROM` that references the last
published image; it exists so the action can be used before the first release
of a version is published. See [releases.md](releases.md).

## CI overview

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR / push to `main` | Lint, typecheck, tests for affected actions; metadata and version validation |
| `container-build.yml` | PR / push to `main`; manual dispatch | Build all `base.dockerfile` images (amd64 + arm64) and smoke test; dispatch runs a report-only reproducibility check |
| `actionlint.yml` | PR / push touching `.github/workflows/` | Workflow syntax linting |
| `publish-release.yml` | Manual dispatch | Release one action: bump version, publish images, tag, release notes |
| `security.yml` | PR, weekly schedule, manual | Dependency/secret/IaC/image scanning, SBOM, workflow audit, deduped issue reporting |
| `dependency-review.yml` | PR | Dependency risk review on changes |

CI detects which actions are affected by a change (`scripts/affected_actions.py`).
Changes under an action directory only test that action; changes to shared
tooling (`scripts/`, `pyproject.toml`, `.github/`, `tests/`) test all actions.

## Adding a new action

1. Create `<name>/` with `action.yml`, `version.txt` (`0.1.0`), `base.dockerfile`,
   `Dockerfile`, `requirements.txt`, `requirements-test.txt`, `tests/`, `README.md`.
2. Add the action name to `ACTIONS` in `scripts/prepare_release.py`,
   `scripts/validate_metadata.py`, and `scripts/affected_actions.py`.
3. Add it to the matrices in `.github/workflows/ci.yml` and
   `.github/workflows/container-build.yml`, and to the `action` choices in
   `.github/workflows/publish-release.yml`.
4. Add a row to the version table in the root `README.md` and a dogfooding
   workflow under `.github/workflows/` if the action should run on this repo.
5. Run `python scripts/validate_metadata.py` and
   `python scripts/prepare_release.py check` locally before opening a PR.
