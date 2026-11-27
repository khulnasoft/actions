"""Unit tests for scripts/verify_release.py with network/subprocess mocked."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_release", ROOT / "scripts" / "verify_release.py"
)
assert SPEC and SPEC.loader
verify_release = importlib.util.module_from_spec(SPEC)
sys.modules["verify_release"] = verify_release
SPEC.loader.exec_module(verify_release)

DIGEST = "sha256:" + "ab" * 32
COMMIT = "cd" * 20


@pytest.fixture
def mocked(monkeypatch: pytest.MonkeyPatch):
    state = {
        "tag_sha": COMMIT,
        "version_txt": "0.6.1",
        "digests": {
            "khulnasoft/actions-issue-manager:0.6.1": DIGEST,
            "ghcr.io/khulnasoft/actions/issue-manager:0.6.1": DIGEST,
        },
        "attest_ok": True,
    }
    monkeypatch.setattr(verify_release, "ls_remote_tag", lambda repo, tag: state["tag_sha"])
    monkeypatch.setattr(
        verify_release,
        "fetch_version_txt",
        lambda repo, commit, action: state["version_txt"],
    )
    monkeypatch.setattr(
        verify_release,
        "image_digest",
        lambda ref: state["digests"].get(ref),
    )
    monkeypatch.setattr(
        verify_release,
        "attestation_verifies",
        lambda image, digest, owner: state["attest_ok"],
    )
    return state


def check(**overrides):
    kwargs = {
        "repo": "khulnasoft/actions",
        "action": "issue-manager",
        "version": "0.6.1",
        "expect_commit": None,
        "manifest_path": None,
        "attest": False,
    }
    kwargs.update(overrides)
    return verify_release.check_release(**kwargs)


def test_happy_path(mocked) -> None:
    lines, ok = check(expect_commit=COMMIT, attest=True)
    assert ok, lines
    assert any("RESULT" not in line and "PASS" in line for line in lines)


def test_tag_mismatch_fails(mocked) -> None:
    mocked["tag_sha"] = "ef" * 20
    lines, ok = check(expect_commit=COMMIT)
    assert not ok
    assert any("tag commit" in line for line in lines)


def test_version_txt_mismatch_fails(mocked) -> None:
    mocked["version_txt"] = "0.6.0"
    _, ok = check()
    assert not ok


def test_missing_tag_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verify_release, "ls_remote_tag", lambda repo, tag: None)
    lines, ok = check()
    assert not ok
    assert any("does not resolve" in line for line in lines)


def test_registry_digest_drift_fails(mocked) -> None:
    mocked["digests"]["ghcr.io/khulnasoft/actions/issue-manager:0.6.1"] = "sha256:" + "cd" * 32
    lines, ok = check()
    assert not ok
    assert any("differ across" in line for line in lines)


def test_manifest_consistency(mocked, tmp_path: Path) -> None:
    manifest = {
        "schema": "khulnasoft/release-manifest/v1",
        "action": "issue-manager",
        "version": "0.6.1",
        "tag": "issue-manager/v0.6.1",
        "commit": COMMIT,
        "images": {
            "khulnasoft/actions-issue-manager:0.6.1": DIGEST,
            "ghcr.io/khulnasoft/actions/issue-manager:0.6.1": DIGEST,
        },
    }
    path = tmp_path / "release-manifest.json"
    path.write_text(json.dumps(manifest))
    _, ok = check(manifest_path=path)
    assert ok

    manifest["images"]["ghcr.io/khulnasoft/actions/issue-manager:0.6.1"] = "sha256:" + "00" * 32
    path.write_text(json.dumps(manifest))
    lines, ok = check(manifest_path=path)
    assert not ok
    assert any("manifest digest" in line for line in lines)


def test_attestation_failure_fails(mocked) -> None:
    mocked["attest_ok"] = False
    _, ok = check(attest=True)
    assert not ok
