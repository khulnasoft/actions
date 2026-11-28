#!/usr/bin/env python3
"""Print a JSON array of actions affected by changed files.

Reads changed file paths from stdin (one per line) and prints a JSON list of
action directory names that need testing. Changes to shared tooling, CI
configuration, or multiple actions affect all actions.
"""

import json
import sys

ACTIONS = ["issue-manager", "label-approved", "latest-changes", "pr-push", "pr-submit"]

# Paths that affect every action's test environment.
SHARED_FILES = {"pyproject.toml", "requirements-dev.txt"}
SHARED_PREFIXES = ("scripts/", ".github/", "tests/", "shared/")

# Paths that never affect action code and can be safely ignored.
IGNORE_PREFIXES = ("docs/", "examples/")
IGNORE_FILES = {
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".gitignore",
    ".editorconfig",
    ".pre-commit-config.yaml",
}


def affected_actions(files: list[str]) -> list[str]:
    affected: set[str] = set()
    for path in files:
        path = path.strip()
        if not path:
            continue
        for action in ACTIONS:
            if path.startswith(f"{action}/"):
                affected.add(action)
                break
        else:
            if path in SHARED_FILES or path.startswith(SHARED_PREFIXES):
                affected.update(ACTIONS)
            elif not (path.startswith(IGNORE_PREFIXES) or path in IGNORE_FILES):
                # Unknown path: be conservative and test everything so a new
                # top-level directory or tooling file cannot bypass CI.
                affected.update(ACTIONS)
    return sorted(affected)


def main() -> None:
    files = sys.stdin.read().splitlines()
    print(json.dumps(affected_actions(files)))


if __name__ == "__main__":
    main()
