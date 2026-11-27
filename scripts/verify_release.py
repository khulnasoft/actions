#!/usr/bin/env python3
"""Independently verify a published KhulnaSoft action release.

Checks, without trusting the publishing workflow:

1. The release git tag resolves to the expected commit.
2. ``<action>/version.txt`` at that commit equals the released version.
3. Both registry images (Docker Hub and GHCR) resolve to the same
   manifest digest, and to the digest recorded at publish time when a
   release manifest is supplied.
4. Optionally, GitHub artifact attestations verify for each image
   (``--attest``, requires ``gh`` and ``GH_TOKEN``).

Exit status is 0 only when every check passes.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ACTIONS = ("issue-manager", "label-approved", "latest-changes")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def ls_remote_tag(repo_url: str, tag: str) -> str | None:
    """Resolve a tag to a commit SHA via git ls-remote (no clone needed)."""
    result = run(
        [
            "git",
            "ls-remote",
            repo_url,
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        ]
    )
    if result.returncode != 0:
        return None
    sha = None
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == f"refs/tags/{tag}^{{}}":
            return parts[0]  # annotated tag: peeled commit wins
        if len(parts) == 2 and parts[1] == f"refs/tags/{tag}":
            sha = parts[0]
    return sha


def fetch_version_txt(repo: str, commit: str, action: str) -> str | None:
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{action}/version.txt"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode().strip()
    except OSError:
        return None


def image_digest(image: str) -> str | None:
    """Return the manifest-list digest for an image reference."""
    result = run(
        [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            image,
            "--format",
            "{{json .}}",
        ]
    )
    if result.returncode != 0:
        return None
    try:
        manifest = json.loads(result.stdout).get("manifest", {})
    except json.JSONDecodeError:
        return None
    digest = manifest.get("digest")
    return digest if isinstance(digest, str) else None


def attestation_verifies(image: str, digest: str, owner: str) -> bool:
    result = run(
        [
            "gh",
            "attestation",
            "verify",
            f"oci://{image}@{digest}",
            "--owner",
            owner,
        ]
    )
    return result.returncode == 0


def check_release(
    *,
    repo: str,
    action: str,
    version: str,
    expect_commit: str | None = None,
    manifest_path: Path | None = None,
    attest: bool = False,
) -> tuple[list[str], bool]:
    lines: list[str] = []
    ok = True

    def report(status: str, message: str) -> None:
        nonlocal ok
        if status == "FAIL":
            ok = False
        lines.append(f"{status}: {message}")

    tag = f"{action}/v{version}"
    repo_url = f"https://github.com/{repo}"

    commit = ls_remote_tag(repo_url, tag)
    if commit is None:
        report("FAIL", f"tag {tag} does not resolve in {repo}")
        return lines, False
    report("PASS", f"tag {tag} -> commit {commit}")
    if expect_commit and commit != expect_commit:
        report("FAIL", f"tag commit {commit} != expected {expect_commit}")

    file_version = fetch_version_txt(repo, commit, action)
    if file_version is None:
        report("FAIL", f"could not fetch {action}/version.txt at {commit}")
    elif file_version != version:
        report(
            "FAIL",
            f"version.txt at {commit} is {file_version!r}, expected {version!r}",
        )
    else:
        report("PASS", f"{action}/version.txt == {version} at {commit}")

    images = {
        f"khulnasoft/actions-{action}:{version}": None,
        f"ghcr.io/khulnasoft/actions/{action}:{version}": None,
    }
    for ref in images:
        digest = image_digest(ref)
        images[ref] = digest
        if digest is None:
            report("FAIL", f"could not resolve digest for {ref}")
        else:
            report("PASS", f"{ref} -> {digest}")

    resolved = [d for d in images.values() if d]
    if len(resolved) == len(images) and len(set(resolved)) != 1:
        report("FAIL", "registry digests differ across Docker Hub and GHCR")
    elif len(set(resolved)) == 1:
        report("PASS", f"both registries agree on {resolved[0]}")

    manifest = None
    if manifest_path is not None:
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            report("FAIL", f"cannot read manifest {manifest_path}: {exc}")
    if manifest is not None:
        fails_before = sum(1 for line in lines if line.startswith("FAIL"))
        if manifest.get("schema") != "khulnasoft/release-manifest/v1":
            report("FAIL", f"unexpected manifest schema {manifest.get('schema')!r}")
        for key, expected in (
            ("action", action),
            ("version", version),
            ("tag", tag),
            ("commit", commit),
        ):
            if manifest.get(key) != expected:
                report(
                    "FAIL",
                    f"manifest {key}={manifest.get(key)!r} != {expected!r}",
                )
        recorded = manifest.get("images", {})
        for ref, digest in images.items():
            if digest and recorded.get(ref) != digest:
                report(
                    "FAIL",
                    f"manifest digest for {ref} is {recorded.get(ref)!r}, "
                    f"registry resolves {digest}",
                )
        fails_after = sum(1 for line in lines if line.startswith("FAIL"))
        if fails_after == fails_before:
            report("PASS", "release manifest consistent with live state")

    if attest and resolved:
        owner = repo.split("/", 1)[0]
        digest = resolved[0]
        for ref in images:
            name = ref.split(":", 1)[0]
            if not name.startswith(("ghcr.io/", "docker.io/", "index.docker.io/")):
                name = f"docker.io/{name}"
            if attestation_verifies(name, digest, owner):
                report("PASS", f"attestation verified for {name}@{digest}")
            else:
                report("FAIL", f"attestation verification failed for {name}")

    return lines, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="khulnasoft/actions")
    parser.add_argument("--action", required=True, choices=ACTIONS)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expect-commit", help="Assert the tag points here")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="release-manifest.json from the GitHub Release assets",
    )
    parser.add_argument(
        "--attest",
        action="store_true",
        help="Verify GitHub artifact attestations (needs gh + GH_TOKEN)",
    )
    args = parser.parse_args()

    lines, ok = check_release(
        repo=args.repo,
        action=args.action,
        version=args.version,
        expect_commit=args.expect_commit,
        manifest_path=args.manifest,
        attest=args.attest,
    )
    for line in lines:
        print(line)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
