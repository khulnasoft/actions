# Security Automation

`khulnasoft/actions` is scanned continuously by `.github/workflows/security.yml`.
All scanners run in **report-only** mode: findings never block merges. They are
published to GitHub Code Scanning (SARIF) and summarized into deduplicated
GitHub issues labeled `security`.

## Coverage

| Scanner | Tool | Version | Frequency | Covers |
|---|---|---|---|---|
| Python deps | `pip-audit` (OSV) | 2.10.1 | PR + weekly | `requirements.txt` + `requirements-test.txt` of all 3 actions |
| Secrets | `gitleaks` | 8.30.1 | PR + weekly | Full git history, secrets redacted in reports |
| Workflow audit | `zizmor` | 1.33.1 | PR + weekly | Permissions, injection, unpinned actions, trigger abuse |
| IaC config | `trivy config` | via trivy-action 0.36.0 | PR + weekly | Dockerfile misconfigurations |
| Image vulns | `trivy image` | via trivy-action 0.36.0 | Weekly + manual | Built `base.dockerfile` images, HIGH/CRITICAL, unfixed ignored |
| SBOM | `syft` | 1.57.2 | Weekly + manual | SPDX JSON inventory of all 3 runtime images |

Dependency *updates* are handled separately by Dependabot
(`.github/dependabot.yml`) and `dependency-review.yml` on PRs.

## Findings flow

1. Each scan job writes raw reports (SARIF/JSON) and, when findings exist, a
   `findings-*.md` summary, uploaded as workflow artifacts (30–90 day retention).
2. SARIF reports upload to Code Scanning on same-repo PRs and scheduled runs.
3. On schedule/manual runs, the `report` job downloads all findings artifacts
   and calls `scripts/security_issue.py`, which keeps **one open issue per
   scanner** (deduplicated via a hidden `security-source` marker). New runs
   comment on the existing issue instead of opening duplicates. Issues are
   never auto-closed — a human decides when a finding is resolved.

## Manual repository settings (one-time)

These cannot be configured from workflow files — enable them in the repository
settings (free for public repositories):

- **Settings → Code security → Secret scanning**: enable.
- **Settings → Code security → Push protection**: enable (blocks pushes that
   contain secrets before they reach the repository).
- **Settings → Code security → Dependabot alerts / security updates**: enable.
- **Settings → Environments → `release`**: consider requiring reviewer approval
   for the release pipeline (already referenced by `publish-release.yml`).

## Tuning thresholds

Everything is report-only today. To tighten later:

- `trivy image`: remove `ignore-unfixed` or raise `severity` floor is already
  HIGH,CRITICAL; add `exit-code: "1"` to block on findings.
- `pip-audit`/`gitleaks`/`zizmor`: have the scan step `exit 1` on findings and
  drop the report-only wrapper in `security.yml`.
- Per-rule zizmor suppressions live inline as `# zizmor: ignore[<rule>]` —
  each carries a justification comment.

## Tool pinning

All third-party actions are SHA-pinned. gitleaks, syft, pip-audit, and zizmor
are installed as checksum-verified or version-pinned binaries/packages so the
security tooling itself cannot drift silently.
