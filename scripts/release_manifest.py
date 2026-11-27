#!/usr/bin/env python3
"""Build a release manifest binding an action release to image digests.

The manifest is the tamper-evident record of what a release produced: the
source commit, the git tag, and the exact registry digests pushed for each
image, plus the SHA-256 of the SPDX SBOM generated from the digest-pinned
image. It is attached to the GitHub Release as an asset and consumed by
scripts/verify_release.py for independent verification.
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = "khulnasoft/release-manifest/v1"
DIGEST_RE = re.compile(r"^[a-z0-9]+:[0-9a-f]{32,}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def sha256_file(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def build_manifest(
    *,
    action: str,
    version: str,
    commit: str,
    images: dict[str, str],
    sbom_path: Path | None = None,
    repository: str = "khulnasoft/actions",
    run_url: str | None = None,
) -> dict:
    if not COMMIT_RE.match(commit):
        raise ValueError(f"commit must be a 40-char hex SHA, got {commit!r}")
    if not images:
        raise ValueError("at least one --image NAME=DIGEST is required")
    for name, digest in images.items():
        if not DIGEST_RE.match(digest):
            raise ValueError(f"invalid digest for {name}: {digest!r}")

    manifest: dict = {
        "schema": SCHEMA,
        "repository": repository,
        "action": action,
        "version": version,
        "tag": f"{action}/v{version}",
        "commit": commit,
        "images": dict(sorted(images.items())),
        "created_at": datetime.now(UTC).isoformat(),
    }
    if run_url:
        manifest["workflow_run"] = run_url
    if sbom_path is not None:
        digest, size = sha256_file(sbom_path)
        manifest["sbom"] = {
            "file": sbom_path.name,
            "format": "spdx-json",
            "sha256": digest,
            "size_bytes": size,
        }
    return manifest


def parse_image(spec: str) -> tuple[str, str]:
    name, sep, digest = spec.partition("=")
    if not sep or not name or not digest:
        raise argparse.ArgumentTypeError(f"--image expects NAME=DIGEST, got {spec!r}")
    return name, digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument(
        "--image",
        action="append",
        type=parse_image,
        required=True,
        metavar="NAME=DIGEST",
        help="Registry image reference and its manifest digest (repeatable)",
    )
    parser.add_argument("--sbom", type=Path, help="SPDX SBOM file to hash")
    parser.add_argument("--repository", default="khulnasoft/actions")
    parser.add_argument("--run-url", help="Workflow run URL for provenance")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = build_manifest(
            action=args.action,
            version=args.version,
            commit=args.commit,
            images=dict(args.image),
            sbom_path=args.sbom,
            repository=args.repository,
            run_url=args.run_url,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
