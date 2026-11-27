#!/usr/bin/env python3
"""Create or update a deduplicated GitHub issue for a security scanner.

Each scanner gets at most one open issue, identified by a hidden marker in the
issue body. Repeat runs add a comment with the latest findings instead of
opening duplicates. Issues are never auto-closed.

Requires the `gh` CLI authenticated with permission to read/write issues.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

MARKER_TEMPLATE = "<!-- security-source: {source} -->"
LABEL = "security"


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )


def find_open_issue(source: str) -> int | None:
    marker = MARKER_TEMPLATE.format(source=source)
    result = gh(
        "issue",
        "list",
        "--label",
        LABEL,
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        "number,body",
    )
    for issue in json.loads(result.stdout):
        if marker in (issue.get("body") or ""):
            return int(issue["number"])
    return None


def ensure_label() -> None:
    result = subprocess.run(
        [
            "gh",
            "label",
            "create",
            LABEL,
            "--color",
            "B60205",
            "--description",
            "Automated security scan findings",
        ],
        capture_output=True,
        text=True,
    )
    # Label already exists is the expected failure; anything else surfaces later.
    if result.returncode != 0 and "already exists" not in result.stderr.lower():
        print(
            f"warning: could not ensure '{LABEL}' label: {result.stderr.strip()}", file=sys.stderr
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Scanner id, e.g. pip-audit-issue-manager")
    parser.add_argument("--title", required=True, help="Issue title for new issues")
    parser.add_argument("--body-file", required=True, help="Markdown file with findings")
    parser.add_argument("--run-url", required=True, help="URL of the workflow run")
    args = parser.parse_args()

    details = Path(args.body_file).read_text(encoding="utf-8").strip()
    marker = MARKER_TEMPLATE.format(source=args.source)
    body = f"{marker}\n\n{details}\n\nWorkflow run: {args.run_url}\n"

    ensure_label()
    existing = find_open_issue(args.source)
    if existing is not None:
        gh(
            "issue",
            "comment",
            str(existing),
            "--body",
            f"New scan run: {args.run_url}\n\n{details}",
        )
        print(f"Commented on existing issue #{existing} for '{args.source}'.")
    else:
        gh(
            "issue",
            "create",
            "--label",
            LABEL,
            "--title",
            args.title,
            "--body",
            body,
        )
        print(f"Created security issue for '{args.source}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
