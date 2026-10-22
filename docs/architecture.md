# Architecture

## Source of truth

- **Version**: `<action>/version.txt`
- **Runtime image build**: `<action>/base.dockerfile`
- **Thin Dockerfile pin**: `<action>/Dockerfile` (points to published versioned image)
- **Action metadata**: `<action>/action.yml`
- **Config schema**: `<action>/schema.json` (issue-manager only)

## Build context

Each action's Docker build context is its own directory. No shared runtime code at the repository root.

## Tagging

Path-scoped tags: `<action>/v<version>` (e.g., `issue-manager/v0.6.0`).

## Registries

- Docker Hub: `khulnasoft/actions-<name>:<version>`
- GHCR: `ghcr.io/khulnasoft/actions/<name>:<version>`

## Marketplace

Subdirectory actions are not automatically listed on Marketplace. Old repositories serve as discovery surfaces during migration.
