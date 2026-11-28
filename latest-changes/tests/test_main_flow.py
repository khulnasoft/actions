import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

import latest_changes.main as lc


class FakeLabel:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeUser:
    login = "octocat"
    html_url = "https://github.com/octocat"


class FakePR:
    def __init__(self, number: int, merged: bool, labels: list[str]) -> None:
        self.number = number
        self.title = "A change"
        self.html_url = f"https://github.com/octo/repo/pull/{number}"
        self.user = FakeUser()
        self.merged = merged
        self.labels = [FakeLabel(name) for name in labels]


class FakeRepo:
    def __init__(self, pr: FakePR) -> None:
        self._pr = pr
        self.requested_numbers: list[int] = []

    def get_pull(self, number: int) -> FakePR:
        self.requested_numbers.append(number)
        return self._pr


class FakeGithub:
    def __init__(self, repo: FakeRepo) -> None:
        self._repo = repo

    def get_repo(self, name: str) -> FakeRepo:
        return self._repo


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    event = tmp_path / "event.json"
    event.write_text(json.dumps({"number": 42}), encoding="utf-8")
    changes = tmp_path / "README.md"
    changes.write_text(
        "## Release Notes\n\n### Latest Changes\n\n### 0.0.1\n\n* Old.\n", encoding="utf-8"
    )
    monkeypatch.setenv("GITHUB_REPOSITORY", "octo/repo")
    monkeypatch.setenv("INPUT_TOKEN", "secret")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("INPUT_LATEST_CHANGES_FILE", str(changes))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "output"))
    monkeypatch.setattr(lc.shutil, "which", lambda _: "/usr/bin/git")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    return changes, tmp_path / "output"


def test_main_adds_change_and_writes_outputs(
    env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    changes, output = env
    repo = FakeRepo(FakePR(42, merged=True, labels=["feature"]))
    monkeypatch.setattr(lc, "Github", lambda **_: FakeGithub(repo))
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(lc.subprocess, "run", fake_run)

    lc.main()

    content = changes.read_text(encoding="utf-8")
    assert "A change" in content
    assert repo.requested_numbers == [42]
    assert any(call[:2] == ["/usr/bin/git", "push"] for call in calls)
    written = output.read_text(encoding="utf-8")
    assert "message<<EOF" in written
    assert '"number": 42' in written
    assert '"labels": ["feature"]' in written


def test_main_skips_unmerged_pr(env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    changes, output = env
    repo = FakeRepo(FakePR(42, merged=False, labels=[]))
    monkeypatch.setattr(lc, "Github", lambda **_: FakeGithub(repo))

    with pytest.raises(SystemExit) as excinfo:
        lc.main()
    assert excinfo.value.code == 0
    assert "A change" not in changes.read_text(encoding="utf-8")
    assert not output.exists()


def test_main_uses_workflow_input_number(
    env: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    changes, _ = env
    event = changes.parent / "event.json"
    event.write_text(json.dumps({"inputs": {"number": 77}}), encoding="utf-8")
    repo = FakeRepo(FakePR(77, merged=True, labels=[]))
    monkeypatch.setattr(lc, "Github", lambda **_: FakeGithub(repo))
    monkeypatch.setattr(
        lc.subprocess,
        "run",
        lambda args, **_: subprocess.CompletedProcess(args, 0),
    )

    lc.main()
    assert repo.requested_numbers == [77]


def test_main_reports_missing_event_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    changes = tmp_path / "README.md"
    changes.write_text("### Latest Changes\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_REPOSITORY", "octo/repo")
    monkeypatch.setenv("INPUT_TOKEN", "secret")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("INPUT_LATEST_CHANGES_FILE", str(changes))
    monkeypatch.setattr(lc.shutil, "which", lambda _: "/usr/bin/git")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(lc, "Github", lambda **_: FakeGithub(FakeRepo(FakePR(42, True, []))))

    with pytest.raises(SystemExit) as excinfo:
        lc.main()
    assert excinfo.value.code == 1
