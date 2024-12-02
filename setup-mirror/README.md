# Setup Mirror

This action configures the actions runner to use a container registry mirror.

## Usage

```yaml
- uses: khulnasoft/actions/setup-mirror@main
  with:
    # Mirror is the hostname of the registry mirror. For example, mirror.gcr.io.
    # Required.
    mirror: mirror.gcr.io
```

## Scenarios

```yaml
steps:
- uses: khulnasoft/actions/setup-mirror@main
  with:
    mirror: mirror.gcr.io
```
