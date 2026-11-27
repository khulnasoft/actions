"""Repository-level contract tests for release tooling and CI helpers."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_script(
    name: str, args: list[str] | None = None, stdin: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name), *(args or [])],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def test_prepare_release_check_passes() -> None:
    result = run_script("prepare_release.py", ["check"])
    assert result.returncode == 0, result.stderr


def test_validate_metadata_passes() -> None:
    result = run_script("validate_metadata.py")
    assert result.returncode == 0, result.stderr


def test_affected_actions_single_action() -> None:
    result = run_script(
        "affected_actions.py",
        stdin="issue-manager/app/main.py\ndocs/architecture.md\n",
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == ["issue-manager"]


def test_affected_actions_shared_paths_affect_all() -> None:
    for path in ("scripts/prepare_release.py", "pyproject.toml", ".github/workflows/ci.yml"):
        result = run_script("affected_actions.py", stdin=f"{path}\n")
        assert result.returncode == 0
        assert json.loads(result.stdout) == [
            "issue-manager",
            "label-approved",
            "latest-changes",
        ], path


def test_affected_actions_docs_only_returns_empty() -> None:
    result = run_script(
        "affected_actions.py",
        stdin="docs/releases.md\nexamples/issue-manager/workflow.yml\nREADME.md\n",
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


def test_affected_actions_unknown_path_tests_everything() -> None:
    for path in ("new-tooling/setup.sh", "new-action/main.py", "random-file.txt"):
        result = run_script("affected_actions.py", stdin=f"{path}\n")
        assert result.returncode == 0
        assert json.loads(result.stdout) == [
            "issue-manager",
            "label-approved",
            "latest-changes",
        ], path


def test_affected_actions_deleted_and_renamed_paths() -> None:
    # --no-renames in CI reports deletes and adds separately, so both the old
    # and new locations are covered here.
    result = run_script(
        "affected_actions.py",
        stdin="issue-manager/app/removed.py\nlabel-approved/label_approved/moved.py\n",
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == ["issue-manager", "label-approved"]


def test_security_findings_pip_audit(tmp_path: Path) -> None:
    report = tmp_path / "pip-audit.json"
    report.write_text(
        json.dumps(
            {
                "dependencies": [
                    {
                        "name": "foo",
                        "version": "1.0",
                        "vulns": [
                            {
                                "id": "PYSEC-1",
                                "fix_versions": ["1.1"],
                                "aliases": [],
                                "description": "test",
                            }
                        ],
                    },
                    {"name": "bar", "version": "2.0", "vulns": []},
                ],
                "fixes": [],
            }
        )
    )
    out = tmp_path / "findings.md"
    result = run_script(
        "security_findings.py",
        ["pip-audit", str(report), str(out), "--name", "issue-manager"],
    )
    assert result.returncode == 0
    assert "count=1" in result.stdout
    assert "PYSEC-1" in out.read_text()


def test_security_findings_clean_report_writes_nothing(tmp_path: Path) -> None:
    report = tmp_path / "zizmor.sarif"
    report.write_text(json.dumps({"runs": [{"results": []}]}))
    out = tmp_path / "findings.md"
    result = run_script("security_findings.py", ["zizmor", str(report), str(out)])
    assert result.returncode == 0
    assert "count=0" in result.stdout
    assert not out.exists()


def test_release_manifest_roundtrip(tmp_path: Path) -> None:
    digest = "sha256:" + "ab" * 32
    commit = "cd" * 20
    sbom = tmp_path / "sbom-issue-manager.spdx.json"
    sbom.write_text('{"spdxVersion": "SPDX-2.3"}\n')
    out = tmp_path / "release-manifest-issue-manager.json"
    result = run_script(
        "release_manifest.py",
        [
            "--action",
            "issue-manager",
            "--version",
            "0.6.1",
            "--commit",
            commit,
            "--image",
            f"khulnasoft/actions-issue-manager:0.6.1={digest}",
            "--image",
            f"ghcr.io/khulnasoft/actions/issue-manager:0.6.1={digest}",
            "--sbom",
            str(sbom),
            "--run-url",
            "https://example.com/run/1",
            "--output",
            str(out),
        ],
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads(out.read_text())
    assert manifest["schema"] == "khulnasoft/release-manifest/v1"
    assert manifest["tag"] == "issue-manager/v0.6.1"
    assert manifest["commit"] == commit
    assert manifest["images"]["ghcr.io/khulnasoft/actions/issue-manager:0.6.1"] == digest
    assert manifest["sbom"]["format"] == "spdx-json"
    assert len(manifest["sbom"]["sha256"]) == 64


def test_release_manifest_rejects_bad_input(tmp_path: Path) -> None:
    out = tmp_path / "m.json"
    base = [
        "--action",
        "issue-manager",
        "--version",
        "0.6.1",
        "--output",
        str(out),
    ]
    bad_commit = run_script(
        "release_manifest.py",
        [*base, "--commit", "notasha", "--image", "img=sha256:" + "ab" * 32],
    )
    assert bad_commit.returncode == 2
    bad_digest = run_script(
        "release_manifest.py",
        [*base, "--commit", "cd" * 20, "--image", "img=not-a-digest"],
    )
    assert bad_digest.returncode == 2
    no_images = run_script("release_manifest.py", [*base, "--commit", "cd" * 20])
    assert no_images.returncode == 2
