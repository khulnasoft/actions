# PR Push

Get a short-lived, repository-scoped GitHub App installation token for pushing
changes from a GitHub Actions workflow.

The action exchanges the workflow's GitHub Actions OIDC token for an
installation token from a deployed PR Push service. The service verifies the
workflow identity and only issues a token when the workflow is authorized
(allowed workflow, open pull request, trusted actor, and an unmodified workflow
file).

## How to use

Create a workflow in your repository at `.github/workflows/pr-push.yml`:

```YAML
name: PR Push

on:
  pull_request:

jobs:
  push:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: mdselim606570-cloud/actions/pr-push@pr-push/v0.0.1
        id: token
      - run: echo "token=${{ steps.token.outputs.token }}"
```

The `token` output is masked in the logs. The workflow must be listed in
`.github/pr-push.yml` in the repository's default branch and must run from an
open pull request (or an authorized branch for `workflow_dispatch`).

## Inputs

| Input | Description | Default |
|---|---|---|
| `url` | URL of the deployed PR Push service | `https://pr-push.khulnasoft.com` |

## Outputs

| Output | Description |
|---|---|
| `token` | GitHub App installation token |

## License

This project is licensed under the terms of the MIT license.