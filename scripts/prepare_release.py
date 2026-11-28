#!/usr/bin/env python3
"""Prepare and validate releases for the monorepo's actions."""

import argparse
import re
import sys
from pathlib import Path

ACTIONS = ["issue-manager", "label-approved", "latest-changes", "pr-push", "pr-submit"]

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^version = "(\d+\.\d+\.\d+)"$')
DOCKERFILE_PIN_RE = re.compile(r"(?m)^FROM khulnasoft/actions-[a-z-]+:(\d+\.\d+\.\d+)$")
README_REF_RE = re.compile(r"(khulnasoft/actions/[a-z-]+@)([a-z-]+/v\d+\.\d+\.\d+)")


def parse_version(v: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(v):
        raise ValueError(f"Invalid version: {v!r}")
    parts = v.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump_version(version: str, bump: str) -> str:
    major, minor, patch = parse_version(version)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump type: {bump}")


def get_current_version(action: str) -> str:
    vf = Path(action) / "version.txt"
    content = vf.read_text().strip()
    if not VERSION_RE.fullmatch(content):
        raise RuntimeError(f"Invalid version in {vf}: {content!r}")
    return content


README_VERSION_ROW_RE = re.compile(
    r"(?m)^\| \[[^\]]+\]\([^)]+\) \| [^|]+ \| `([a-z-]+)/v(\d+\.\d+\.\d+)` \|$"
)


def check(action: str | None = None) -> int:
    """Validate version/pin/ref consistency. Returns 0 on success."""
    actions = [action] if action else ACTIONS
    errors = []
    for a in actions:
        ver = get_current_version(a)
        # Check root README version table row
        root_readme = Path("README.md")
        if root_readme.exists():
            content = root_readme.read_text()
            rows = {m.group(1): m.group(2) for m in README_VERSION_ROW_RE.finditer(content)}
            if a in rows and rows[a] != ver:
                errors.append(f"README.md version table lists {a} at {rows[a]}, expected {ver}")
            elif a not in rows:
                errors.append(f"README.md version table is missing a row for {a}")
        # Check Dockerfile pin
        df = Path(a) / "Dockerfile"
        if df.exists():
            content = df.read_text()
            m = re.search(r"^FROM khulnasoft/actions-[a-z-]+:(\d+\.\d+\.\d+)$", content, re.M)
            if m:
                if m.group(1) != ver:
                    errors.append(f"{a}/Dockerfile pin {m.group(1)} != version.txt {ver}")
            else:
                errors.append(f"{a}/Dockerfile has no versioned FROM pin")
        # Check README refs
        readme = Path(a) / "README.md"
        if readme.exists():
            content = readme.read_text()
            for m in re.finditer(
                r"(?:khulnasoft|mdselim606570-cloud)/actions/[a-z-]+@[a-z-]+/v(\d+\.\d+\.\d+)",
                content,
            ):
                if m.group(1) != ver:
                    errors.append(f"{a}/README.md references version {m.group(1)}, expected {ver}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print("All version/pin/ref checks passed.")
    return 0


def prepare(action: str, bump: str) -> str:
    if action not in ACTIONS:
        raise ValueError(f"Unknown action: {action}")
    current = get_current_version(action)
    new_version = bump_version(current, bump)
    # Update version.txt
    vf = Path(action) / "version.txt"
    vf.write_text(new_version + "\n")
    # Update Dockerfile pin
    df = Path(action) / "Dockerfile"
    if df.exists():
        content = df.read_text()
        content = re.sub(
            r"^(FROM khulnasoft/actions-[a-z-]+:)\d+\.\d+\.\d+$",
            rf"\g<1>{new_version}",
            content,
            flags=re.M,
        )
        df.write_text(content)
    # Update README refs
    readme = Path(action) / "README.md"
    if readme.exists():
        content = readme.read_text()
        content = re.sub(
            rf"({re.escape(action)}/v){re.escape(current)}",
            rf"\g<1>{new_version}",
            content,
        )
        readme.write_text(content)
    # Update root README version table and usage examples
    root_readme = Path("README.md")
    if root_readme.exists():
        content = root_readme.read_text()
        content = re.sub(
            rf"({re.escape(action)}/v){re.escape(current)}",
            rf"\g<1>{new_version}",
            content,
        )
        root_readme.write_text(content)
    print(f"Prepared {action} release: {current} -> {new_version}")
    return new_version


def current(action: str) -> None:
    print(get_current_version(action))


def main():
    parser = argparse.ArgumentParser(description="Release preparation tool")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Validate version/pin/ref consistency")
    p_check.add_argument("--action", choices=ACTIONS, help="Check a single action")

    p_prepare = sub.add_parser("prepare", help="Prepare a new release")
    p_prepare.add_argument("--action", required=True, choices=ACTIONS)
    p_prepare.add_argument("--bump", required=True, choices=["major", "minor", "patch"])

    p_current = sub.add_parser("current", help="Print current version")
    p_current.add_argument("--action", required=True, choices=ACTIONS)

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(check(getattr(args, "action", None)))
    elif args.command == "prepare":
        prepare(args.action, args.bump)
    elif args.command == "current":
        current(args.action)


if __name__ == "__main__":
    main()
