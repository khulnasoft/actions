# Setup Knative Eventing

This action installs Knative Eventing into the current kubectl context.

## Usage

```yaml
- uses: khulnasoft/actions/setup-knative-eventing@main
  with:
    # Version is the version of Knative Eventing to install.
    # (defaults to 1.11.0)
    version: 1.11.0
```

## Scenarios

```yaml
steps:
- uses: khulnasoft/actions/setup-knative-eventing@main
  with:
    version: 1.11.0
```
