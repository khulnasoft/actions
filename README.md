# GitHub Action: Dependabot Auto Merge

Automatically merge Dependabot PRs when version comparison is within range.

## Usage

use `Makefile` to run tasks locally:

| Task          | Description                        |
|---------------|------------------------------------|
| `make pull`   | pull latest containers             |
| `make lint`   | run super-linter                   |
| `make readme` | generate root README.md            |
| `make clean`  | delete containers, images, volumes |
| `make help`   | display help                       |

> **Note:**  
> The source `README.md` file is in `docs/README.md`, the file at root is generated using [pandoc][] using the provided [template][].
>
> You should run `make readme` after any change to `docs/README.md` and before commit / push

  [pandoc]: https://pandoc.org/
  [template]: ./docs/README.template
