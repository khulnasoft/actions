# Migration Guide

## From old repositories to `khulnasoft/actions`

| Old reference | New reference |
|---|---|
| `uses: khulnasoft/issue-manager@0.5.1` | `uses: khulnasoft/actions/issue-manager@issue-manager/v0.6.0` |
| `uses: khulnasoft/label-approved@0.0.4` | `uses: khulnasoft/actions/label-approved@label-approved/v0.1.0` |
| `uses: khulnasoft/latest-changes@0.3.2` | `uses: khulnasoft/actions/latest-changes@latest-changes/v0.4.0` |
| `docker://khulnasoft/latest-changes:0.3.0` | `docker://ghcr.io/khulnasoft/actions/latest-changes:0.4.0` |

## Notes

- Old repositories, tags, and images remain available. No existing reference is broken.
- New references use path-scoped tags (`<action>/v<version>`) so Dependabot can track each action independently.
- The Docker image naming changed: Docker Hub uses `khulnasoft/actions-<name>`, GHCR uses `ghcr.io/khulnasoft/actions/<name>`.
