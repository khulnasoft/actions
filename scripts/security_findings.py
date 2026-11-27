#!/usr/bin/env python3
"""Convert security scanner JSON/SARIF output into findings markdown.

Each subcommand reads a scanner report, prints `count=<n>` to stdout (for
$GITHUB_OUTPUT), and writes a markdown summary next to the report when
findings exist. Used by .github/workflows/security.yml.
"""

import argparse
import json
import sys
from pathlib import Path


def sarif_results(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data.get("runs", [{}])[0].get("results", [])


def write_findings(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n")


def pip_audit(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.report).read_text())
    vulns: dict[tuple[str, str], tuple[str, list[str]]] = {}
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            vulns[(dep["name"], v["id"])] = (dep["version"], v.get("fix_versions", []))
    print(f"count={len(vulns)}")
    if vulns:
        lines = [f"## pip-audit findings: {args.name}", ""]
        for (name, vid), (ver, fixes) in sorted(vulns.items()):
            fix = f" (fix: {', '.join(fixes)})" if fixes else " (no fix available)"
            lines.append(f"- `{name}=={ver}` — {vid}{fix}")
        write_findings(Path(args.out), lines)
    return 0


def sarif_findings(args: argparse.Namespace, header: str, describe) -> int:
    results = sarif_results(Path(args.report))
    print(f"count={len(results)}")
    if results:
        lines = [f"## {header}", ""]
        for r in results:
            lines.append(f"- {describe(r)}")
        write_findings(Path(args.out), lines)
    return 0


def gitleaks(args: argparse.Namespace) -> int:
    def describe(r: dict) -> str:
        rule = r.get("ruleId", "unknown")
        loc = r.get("locations", [{}])[0].get("physicalLocation", {})
        uri = loc.get("artifactLocation", {}).get("uri", "?")
        line = loc.get("region", {}).get("startLine", "?")
        return f"`{rule}` in `{uri}`:{line}"

    return sarif_findings(args, "gitleaks findings", describe)


def zizmor(args: argparse.Namespace) -> int:
    def describe(r: dict) -> str:
        rule = r.get("ruleId", "unknown")
        loc = r.get("locations", [{}])[0].get("physicalLocation", {})
        uri = loc.get("artifactLocation", {}).get("uri", "?")
        return f"`{rule}` in `{uri}`"

    return sarif_findings(args, "zizmor findings", describe)


def sbom(args: argparse.Namespace) -> int:
    data = json.loads(Path(args.report).read_text())
    packages = data.get("packages", [])
    print(f"count={len(packages)}")
    if packages:
        write_findings(
            Path(args.out),
            [
                f"## SBOM generated: {args.name}",
                "",
                f"- Packages inventoried: {len(packages)}",
                "- Format: SPDX JSON",
                f"- Artifact: `sbom-{args.name}.spdx.json` in this run's artifacts",
            ],
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pip-audit")
    p.add_argument("report")
    p.add_argument("out")
    p.add_argument("--name", required=True)
    p.set_defaults(func=pip_audit)

    for name, func in (("gitleaks", gitleaks), ("zizmor", zizmor), ("trivy", zizmor)):
        p = sub.add_parser(name)
        p.add_argument("report")
        p.add_argument("out")
        p.set_defaults(func=func)

    p = sub.add_parser("sbom")
    p.add_argument("report")
    p.add_argument("out")
    p.add_argument("--name", required=True)
    p.set_defaults(func=sbom)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
