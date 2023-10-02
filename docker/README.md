# Khulnasoft Docker Action

A [GitHub Action](https://github.com/features/actions) for using [Khulnasoft](https://khulnasoft.com) to check for
vulnerabilities in your Docker images.

You can use the Action as follows:

```yaml
name: Example workflow for Docker using Khulnasoft 
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - name: Run Khulnasoft to check Docker image for vulnerabilities
      uses: khulnasoft/actions/docker@master
      env:
        KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
      with:
        image: your/image-to-test
```

The Khulnasoft Docker Action has properties which are passed to the underlying image. These are
passed to the action using `with`.

| Property | Default | Description |
| --- | --- | --- |
| args |   | Override the default arguments to the Khulnasoft image |
| command | test | Specifiy which command to run, for instance test or monitor |
| image |    | The name of the image to test |
| json | false | In addition to the stdout, save the results as khulnasoft.json |
| sarif | true | In addition to the stdout, save the results as khulnasoft.sarif |

For example, you can choose to only report on high severity vulnerabilities.

```yaml
name: Example workflow for Docker using Khulnasoft 
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - name: Run Khulnasoft to check Docker images for vulnerabilities
      uses: khulnasoft/actions/docker@master
      env:
        KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
      with:
        image: your/image-to-test
        args: --severity-threshold=high
```

The Docker Action also supports integrating with GitHub Code Scanning and can show issues in the GitHub Security tab. As long as you reference a Dockerfile with `--file=Dockerfile` then a `khulnasoft.sarif` file will be generated which can be uploaded to GitHub Code Scanning.

![GitHub Code Scanning and Khulnasoft](codescanning.png)

```yaml
name: Khulnasoft Container
on: push
jobs:
  khulnasoft:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Build a Docker image
      run: docker build -t your/image-to-test .
    - name: Run Khulnasoft to check Docker image for vulnerabilities
      # Khulnasoft can be used to break the build when it detects vulnerabilities.
      # In this case we want to upload the issues to GitHub Code Scanning
      continue-on-error: true
      uses: khulnasoft/actions/docker@master
      env:
        # In order to use the Khulnasoft Action you will need to have a Khulnasoft API token.
        # More details in https://github.com/khulnasoft/actions#getting-your-khulnasoft-token
        # or you can signup for free at https://khulnasoft.com/login
        KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
      with:
        image: your/image-to-test
        args: --file=Dockerfile
    - name: Upload result to GitHub Code Scanning
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: khulnasoft.sarif
```
