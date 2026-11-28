# Release Guide

Each action is versioned and released independently. Releasing one action does
not rebuild or re-release the others.

## Versioning

- Source of truth: `<action>/version.txt` (semver `MAJOR.MINOR.PATCH`).
- Git tags are path-scoped: `<action>/v<version>` (e.g. `issue-manager/v0.6.0`).
  Only exact-version tags are published. Major-version aliases (e.g.
  `<action>/v0`) are intentionally **not** created, because published tags are
  immutable and a moving alias would violate that guarantee. Consumers should
  pin exact versions; Dependabot can keep them updated.
- There is no single repository-wide version.

## Cutting a release

Releases are published by the **Publish Release** workflow
(`.github/workflows/publish-release.yml`), triggered manually via
*Actions → Publish Release → Run workflow* with:

- `action`: which action to release
- `bump`: `patch`, `minor`, or `major`

The workflow:

1. Runs `scripts/prepare_release.py prepare`, which bumps `version.txt`,
   updates the `Dockerfile` pin, and rewrites self-references in the action's
   `README.md`.
2. Runs `scripts/prepare_release.py check` to validate consistency.
3. Commits the version changes to `main`.
4. Builds `base.dockerfile` for `linux/amd64` and `linux/arm64` and pushes:
   - Docker Hub: `khulnasoft/actions-<name>:<version>`
   - GHCR: `ghcr.io/khulnasoft/actions/<name>:<version>`
5. Creates and pushes the tag `<action>/v<version>` and a GitHub Release with
   generated release notes.
6. Verifies the tag exists and both images are inspectable.

Required secrets: `DOCKER_USERNAME` and `DOCKER_TOKEN` (Docker Hub). The
workflow runs in the `release` GitHub environment — configure required
reviewers there if you want a manual approval gate.

## Pre-release checklist

Before dispatching a release:

- [ ] Changes are merged to `main` and CI is green.
- [ ] The action's `README.md` usage examples reference the new version
      (the prepare step rewrites `uses:` self-references automatically).
- [ ] `python scripts/prepare_release.py check` passes locally.

## Image naming

| Registry | Image |
|---|---|
| Docker Hub | `khulnasoft/actions-<name>:<version>` |
| GHCR | `ghcr.io/khulnasoft/actions/<name>:<version>` |

The runtime image is always built from `base.dockerfile`. The thin
`<action>/Dockerfile` only pins the previously published image so the action
works with `uses:` before a release exists.

## Rollback

Published versions and tags are immutable — never move or delete a published
tag.

- **Bad release, quick fix:** release the next patch version normally.
- **Bad release, need to revert consumers:** users pin
  `khulnasoft/actions/<name>@<name>/v<version>`; point them back to the previous
  tag (e.g. `issue-manager/v0.5.0`). Tags and images for all previous versions
  remain available.
- **Broken image, same version:** do not reuse the version. Bump and re-release.

## Dependabot

Dependabot can track `khulnasoft/actions/<name>@<name>/vX.Y.Z` references and
open update PRs when new path-scoped tags are published. See
`.github/dependabot.yml`.
