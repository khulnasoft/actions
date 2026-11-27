## Summary

<!-- What does this PR change and why? -->

## Action(s) affected

<!-- e.g. issue-manager, label-approved, latest-changes, or repo tooling only -->

## Checklist

- [ ] Changes are scoped to the relevant action directory(ies)
- [ ] `version.txt` was NOT bumped (releases are handled by the Publish Release workflow)
- [ ] Local checks pass: `ruff`, `ruff format --check`, `mypy`, `pytest`
- [ ] `python scripts/validate_metadata.py` passes
- [ ] `python scripts/prepare_release.py check` passes
- [ ] README examples still reference released `khulnasoft/actions/<name>@<name>/vX.Y.Z` tags
