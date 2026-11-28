# Architecture

## Source of truth

- **Version**: `<action>/version.txt`
- **Runtime image build**: `<action>/base.dockerfile`
- **Thin Dockerfile pin**: `<action>/Dockerfile` (points to published versioned image)
- **Action metadata**: `<action>/action.yml`
- **Config schema**: `<action>/schema.json` (issue-manager only)
- **Shared Python code**: `shared/python/actions_shared` (token-broker infrastructure used by `pr-push` and `pr-submit`)

## Build context

All images build from the **repository root** so that `shared/python/` can be included in the token-broker images. Each `base.dockerfile` copies only the files it needs. A root `.dockerignore` keeps the context small.

```bash
docker build -f issue-manager/base.dockerfile .
```

API-only actions (`issue-manager`, `label-approved`) run as a non-root user.
`latest-changes` and the token brokers run as root because they write to the
runner-mounted workspace / `GITHUB_OUTPUT`.

## Tagging

Path-scoped tags: `<action>/v<version>` (e.g., `issue-manager/v0.6.0`).

## Registries

- Docker Hub: `khulnasoft/actions-<name>:<version>`
- GHCR: `ghcr.io/khulnasoft/actions/<name>:<version>`

## Marketplace

Subdirectory actions are not automatically listed on Marketplace. Old repositories serve as discovery surfaces during migration.
