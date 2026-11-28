# PR Submit

Get a short-lived, repository-scoped GitHub App installation token for
submitting changes from a scheduled or manually dispatched GitHub Actions
workflow.

The action exchanges the workflow's GitHub Actions OIDC token for an
installation token from a deployed PR Submit service. The service verifies the
workflow identity and only issues a token when the workflow is authorized
(allowed workflow running from the default branch, trusted actor, and an
unmodified workflow file).

## How to use

Create a workflow in your repository at `.github/workflows/pr-submit.yml`:

```YAML
name: PR Submit

on:
  workflow_dispatch:

jobs:
  submit:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: mdselim606570-cloud/actions/pr-submit@pr-submit/v0.0.1
        id: token
      - run: echo "token=${{ steps.token.outputs.token }}"
```

The `token` output is masked in the logs. The workflow must be listed in
`.github/pr-submit.yml` in the repository's default branch and must run from
the default branch.

## Inputs

| Input | Description | Default |
|---|---|---|
| `url` | URL of the deployed PR Submit service | `https://pr-submit.khulnasoft.com` |

## Outputs

| Output | Description |
|---|---|
| `token` | GitHub App installation token |

## License

This project is licensed under the terms of the MIT license.