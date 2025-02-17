## `dirty` Action

Determine if the git tree has changes.

Example:

<!--- @@inject: ../../.github/workflows/example-dirty.yaml --->

````yaml
name: '📗 Example Dirty'

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  run-example:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Dirty 1
        id: dirty_1
        uses: khulnasoft/actions/public/dirty@v1

      - name: Touch
        run: |
          touch test.txt
          echo "\n make dirty \n" >> README.md

      - name: Dirty 2
        id: dirty_2
        uses: khulnasoft/actions/public/dirty@v1

      - name: Summary
        uses: khulnasoft/actions/public/summary@v1
        with:
          text: |
            # Dirty Summary

            ## Dirty 1

            isDirty: `${{ steps.dirty_1.outputs.isDirty }}` = ${{ steps.dirty_1.outputs.isDirty && 'Yes' || 'No' }} = ${{ !!steps.dirty_1.outputs.isDirty }}
            status:
            ```
            ${{ steps.dirty_1.outputs.status }}
            ```

            ## Dirty 2

            isDirty: `${{ steps.dirty_2.outputs.isDirty }}` = ${{ steps.dirty_2.outputs.isDirty && 'Yes' || 'No' }} = ${{ !!steps.dirty_2.outputs.isDirty }}
            status:
            ```
            ${{ steps.dirty_2.outputs.status }}
            ```
````

<!--- @@inject-end: ../../.github/workflows/example-dirty.yaml --->
