# Khulnasoft Setup Action

A [GitHub Action](https://github.com/features/actions) for installing [Khulnasoft](https://khulnasoft.co/KhulnasoftGH) to check for
vulnerabilities.

You can use the Action as follows:

```yaml
name: Khulnasoft example 
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@master
    - uses: khulnasoft/actions/setup@master
    - uses: actions/setup-go@v1
      with:
        go-version: "1.13"
    - name: Khulnasoft monitor 
      run: khulnasoft test
      env:
        KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
```

When using the Setup Action you are responsible for setting up the development environment required to run Khulnasoft.
In this case this is a Go project so `actions/setup-go` was used, but this would be specific to your project. The [language and frameworks guides](https://docs.github.com/en/actions/language-and-framework-guides) are a good starting point.

The Khulnasoft Setup Action has properties which are passed to the underlying image. These are
passed to the action using `with`.

| Property | Default | Description |
| --- | --- | --- |
| khulnasoft-version | latest | Install a specific version of Khulnasoft |

The Action also has outputs:

| Property | Default | Description |
| --- | --- | --- |
| version |   | The full version of the Khulnasoft CLI installed |

For example, you can choose to install a specific version of Khulnasoft. The installed version can be
grabbed from the output:

```yaml
name: Khulnasoft example
on: push
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@master
    - uses: khulnasoft/actions/setup@master
      id: khulnasoft
      with:
        khulnasoft-version: v1.391.0
    - uses: actions/setup-go@v1
      with:
        go-version: "1.13"
    - name: Khulnasoft version
      run: echo "${{ steps.khulnasoft.outputs.version }}"
    - name: Khulnasoft monitor 
      run: khulnasoft monitor
      env:
        KHULNASOFT_TOKEN: ${{ secrets.KHULNASOFT_TOKEN }}
```
