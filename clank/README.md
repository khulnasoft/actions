# Clank

This action runs [clank](https://github.com/khulnasoft/clank), which is a simple
tool that allows you to detect imposter commits in GitHub Actions workflows.

## Usage

Basic usage:

```yaml
    permissions:
      contents: read

    - uses: khulnasoft/actions/clank@main
        with:
          workflow-path: './.github/workflows'
          token: ${{ secrets.GITHUB_TOKEN }}
```
