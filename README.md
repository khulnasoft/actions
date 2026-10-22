# khulnasoft/actions

GitHub Actions by [KhulnaSoft Ltd](https://github.com/khulnasoft).

## Actions

| Action | Description | Version |
|---|---|---|
| [issue-manager](issue-manager/) | Close issues/PRs carrying a label after a configurable idle delay | `issue-manager/v0.6.0` |
| [label-approved](label-approved/) | Label PRs based on how many approvals they have received | `label-approved/v0.1.0` |
| [latest-changes](latest-changes/) | Automatically add PR changes to release notes in a Markdown file | `latest-changes/v0.4.0` |

## Usage

Each action is referenced by its subdirectory path and a path-scoped tag:

```yaml
- uses: khulnasoft/actions/issue-manager@issue-manager/v0.6.0
- uses: khulnasoft/actions/label-approved@label-approved/v0.1.0
- uses: khulnasoft/actions/latest-changes@latest-changes/v0.4.0
```

See each action's README for detailed inputs, examples, and migration notes.

## License

MIT — see [LICENSE](LICENSE).
