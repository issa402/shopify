#!/usr/bin/env python3
"""Read-only repo discovery for infra onboarding.

Scans a local checkout for common infrastructure signals: CI workflows,
Dockerfiles, Compose files, Terraform, Kubernetes, Helm, scripts, docs, and
ownership files. It does not read secrets or call any external service.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


INTERESTING_NAMES = {
    "README.md",
    "CODEOWNERS",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    ".env.example",
}

INTERESTING_DIRS = {
    ".github/workflows": "github_actions",
    "terraform": "terraform",
    "infra": "infra",
    "k8s": "kubernetes",
    "helm": "helm",
    "charts": "helm_charts",
    "scripts": "scripts",
    "docs": "docs",
    "runbooks": "runbooks",
    "monitoring": "monitoring",
    "alerts": "alerts",
}

INTERESTING_SUFFIXES = {
    ".tf": "terraform",
    ".tfvars": "terraform_vars",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sh": "shell_scripts",
    ".ps1": "powershell_scripts",
}

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "dist", "build", "target", "__pycache__"}


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    why_it_matters: str


@dataclass(frozen=True)
class RepoDiscoveryReport:
    root: str
    findings: list[Finding]
    next_questions: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only infrastructure discovery for a local repo.")
    parser.add_argument("root", nargs="?", default=".", help="Repo root to scan. Default: current directory.")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    return parser.parse_args()


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if should_skip(relative):
            continue
        if path.is_file():
            yield path


def classify_file(root: Path, path: Path) -> Finding | None:
    rel = path.relative_to(root)
    rel_str = str(rel)

    for dir_name, category in INTERESTING_DIRS.items():
        if rel_str.startswith(f"{dir_name}/"):
            return Finding(category, rel_str, f"Found {category} surface to inspect.")

    if path.name in INTERESTING_NAMES:
        return Finding("repo_signal", rel_str, f"Found {path.name}, useful for ownership/runtime/deploy discovery.")

    suffix_category = INTERESTING_SUFFIXES.get(path.suffix)
    if suffix_category:
        return Finding(suffix_category, rel_str, f"Found {suffix_category} file to review.")

    return None


def build_report(root: Path) -> RepoDiscoveryReport:
    findings = []
    seen = set()
    for path in iter_files(root):
        finding = classify_file(root, path)
        if finding and (finding.category, finding.path) not in seen:
            findings.append(finding)
            seen.add((finding.category, finding.path))

    findings.sort(key=lambda item: (item.category, item.path))
    questions = [
        "Which team owns this repo?",
        "Where does this service run: AWS, Azure, on-prem, SaaS, or local only?",
        "How is this deployed and rolled back?",
        "Where are logs, metrics, alerts, and runbooks?",
        "What access is required to support this system?",
        "What is the smallest safe improvement to propose first?",
    ]
    return RepoDiscoveryReport(str(root), findings, questions)


def print_text(report: RepoDiscoveryReport) -> None:
    print(f"Repo discovery: {report.root}")
    print("\nFindings:")
    for finding in report.findings:
        print(f"- [{finding.category}] {finding.path} - {finding.why_it_matters}")
    print("\nNext questions:")
    for question in report.next_questions:
        print(f"- {question}")


def print_markdown(report: RepoDiscoveryReport) -> None:
    print("# Repo Discovery Report\n")
    print(f"Root: `{report.root}`\n")
    print("## Findings\n")
    print("| Category | Path | Why it matters |")
    print("| --- | --- | --- |")
    for finding in report.findings:
        print(f"| {finding.category} | `{finding.path}` | {finding.why_it_matters} |")
    print("\n## Next Questions\n")
    for question in report.next_questions:
        print(f"- {question}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"ERROR: root path does not exist or is not a directory: {root}")
        return 1

    report = build_report(root)
    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    elif args.format == "markdown":
        print_markdown(report)
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
