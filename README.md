# khulnasoft/actions

GitHub Actions by [KhulnaSoft Ltd](https://github.com/khulnasoft).

## Actions

| Action | Description | Version |
|---|---|---|
| [issue-manager](issue-manager/) | Close issues/PRs carrying a label after a configurable idle delay | `issue-manager/v0.6.0` |
| [label-approved](label-approved/) | Label PRs based on how many approvals they have received | `label-approved/v0.1.0` |
| [latest-changes](latest-changes/) | Automatically add PR changes to release notes in a Markdown file | `latest-changes/v0.4.0` |
| [pr-push](pr-push/) | Get a short-lived, repository-scoped GitHub App token for pushing from pull request workflows | `pr-push/v0.0.1` |
| [pr-submit](pr-submit/) | Get a short-lived, repository-scoped GitHub App token for scheduled or manually dispatched workflows | `pr-submit/v0.0.1` |

## Usage

Each action is referenced by its subdirectory path and a path-scoped tag:

```yaml
- uses: khulnasoft/actions/issue-manager@issue-manager/v0.6.0
- uses: khulnasoft/actions/label-approved@label-approved/v0.1.0
- uses: khulnasoft/actions/latest-changes@latest-changes/v0.4.0
- uses: khulnasoft/actions/pr-push@pr-push/v0.0.1
- uses: khulnasoft/actions/pr-submit@pr-submit/v0.0.1
```

See each action's README for detailed inputs, examples, and migration notes.

## Documentation

- [Architecture](docs/architecture.md) — repository layout, build contexts, tagging, registries
- [Migration guide](docs/migration.md) — moving from the old single-action repositories
- [Development guide](docs/development.md) — local setup, CI, adding a new action
- [Release guide](docs/releases.md) — versioning, cutting a release, rollback
- [Security automation](docs/security.md) — scanning coverage, findings flow, repo settings
- [Release provenance](docs/provenance.md) — attestation, verification, reproducibility
- [Contributing](CONTRIBUTING.md)
- [Examples](examples/) — ready-to-use workflow files for each action

## License

MIT — see [LICENSE](LICENSE).
