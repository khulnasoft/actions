# Khulnasoft Infrastructure as Code Action

A [GitHub Action](https://github.com/features/actions) for using [Khulnasoft](https://khulnasoft.com) to check for
issues in your Infrastructure as Code files.

You can use the Action as follows:

```yaml
name: Example workflow for Khulnasoft Infrastructure as Code
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check Kubernetes manifest file for issues
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
```

In order to use the Khulnasoft Infrastructure as Code Test Action, you will need to have a Khulnasoft API token. 
More details in [Getting Your Khulnasoft Token](https://github.com/khulnasoft/actions#getting-your-khulnasoft-token), or you can [sign up for free](https://khulnasoft.com/login).  


The Khulnasoft Infrastructure as Code Action has properties which are passed to the underlying image. These are
passed to the action using `with`:

| Property  | Default | Description                                                        |
|-----------|----------|-------------------------------------------------------------------|
| `args`    |          | Override the default arguments to the Khulnasoft image.                 |
| `command` | `"test"` | Specify which command to run, currently only `test` is supported. |
| `file`    |          | The paths in which to scan files with issues.                     |
| `json`    | `false`  | In addition to the stdout, save the results as khulnasoft.json          |
| `sarif`   | `true`   | In addition to the stdout, save the results as khulnasoft.sarif         |

## Examples
### Specifying paths
You can specify the paths to the configuration files and directories to target during the test.  
When no path is specified, the whole repository is scanned by default:

```yaml
name: Example workflow for Khulnasoft Infrastructure as Code
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check Kubernetes manifest file for issues
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
        with:
          file: your/kubernetes-manifest.yaml your/terraform/directory
```

### Specifying severity threshold
You can also choose to only report on high severity vulnerabilities:

```yaml
name: Example workflow for Khulnasoft Infrastructure as Code
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check Kubernetes manifest file for issues
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
        with:
          file: your/kubernetes-manifest.yaml
          args: --severity-threshold=high
```
### Sharing test results
You can [share your test results](https://docs.khulnasoft.com/products/khulnasoft-infrastructure-as-code/share-cli-results-with-the-khulnasoft-web-ui) to the Khulnasoft platform:

```yaml
name: Example workflow for Khulnasoft Infrastructure as Code
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check Kubernetes manifest file for issues
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
        with:
          args: --report
```
### Specifying scan mode for Terraform Plan
You can also choose the [scan mode](https://docs.khulnasoft.com/products/khulnasoft-infrastructure-as-code/khulnasoft-cli-for-infrastructure-as-code/test-your-terraform-files-with-the-cli-tool#terraform-plan), when scanning Terraform Plan files:

```yaml
name: Example workflow for Khulnasoft Infrastructure as Code
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check Kubernetes manifest file for issues
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
        with:
          args: --scan=resource-changes
```

### Integrating with GitHub Code Scanning

The Infrastructure as Code Action also supports integrating with GitHub Code Scanning and can show issues in the GitHub Security tab. When run, a `khulnasoft.sarif` file will be generated which can be uploaded to GitHub Code Scanning:

```yaml
name: Khulnasoft Infrastructure as Code
on: push
jobs:
  khulnasoft:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Khulnasoft to check configuration files for security issues
        # Khulnasoft can be used to break the build when it detects security issues.
        # In this case we want to upload the issues to GitHub Code Scanning
        continue-on-error: true
        uses: khulnasoft/actions/iac@master
        env:
          KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
      - name: Upload result to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: khulnasoft.sarif
```

## Related Documentation
For more information on how to use the `khulnasoft iac test` command, see the following: 
- [Khulnasoft CLI for Infastructure as Code](https://docs.khulnasoft.com/products/khulnasoft-infrastructure-as-code/khulnasoft-cli-for-infrastructure-as-code)
- [Khulnasoft Infrastructure as Code Test Command](https://docs.khulnasoft.com/khulnasoft-cli/commands/iac-test)
