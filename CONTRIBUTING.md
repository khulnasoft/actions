# Contributing

Thanks for your interest in contributing to khulnasoft/actions!

## Before you start

- For questions and problems, please use [GitHub Discussions](https://github.com/khulnasoft/actions/discussions) — issues in this repo are reserved for maintainers.
- Security vulnerabilities: see [SECURITY.md](SECURITY.md). Do not open public issues.

## Development setup

See [docs/development.md](docs/development.md) for the repository layout, local
setup, and the commands CI runs.

## Making changes

1. Keep each action self-contained inside its own directory. Do not share
   runtime code between actions at the repository root.
2. Bump `<action>/version.txt` only via the release workflow — do not bump
   versions in regular PRs.
3. Keep `uses:` examples in READMEs pointing at released
   `khulnasoft/actions/<name>@<name>/vX.Y.Z` tags.
4. Run the same checks CI runs before opening a PR:

   ```bash
   ruff check <action> && ruff format --check <action>
   mypy <action>
   PYTHONPATH=<action> pytest <action>/tests --import-mode=importlib
   python scripts/validate_metadata.py
   python scripts/prepare_release.py check
   ```

5. Fill out the pull request template.

## Releasing

Releases are cut with the **Publish Release** workflow — see
[docs/releases.md](docs/releases.md). Never move or delete published tags.
