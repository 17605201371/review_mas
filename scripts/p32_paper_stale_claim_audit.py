#!/usr/bin/env python3
"""Audit paper drafts for stale pre-P32 result claims.

The P32 paper narrative is now bounded by the clean-repeat evidence pack:
two accepted hardneg20 clean runs, five recurring Critique-origin clusters,
manual-D total 0, harmful recovery total 0, and no full39 / accept-reject /
PPO claim.  This script fails when the main paper drafts drift back to older
P28/P28.6 or partial-run result language.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


DEFAULT_TARGETS = (
    "PAPER_CLEAN_BODY_DRAFT_20260701.md",
    "PAPER_EXPERIMENT_SECTION_DRAFT_20260701.md",
)

BANNED_PATTERNS = (
    r"\bP28(?:\.6)?\b",
    r"partial16",
    r"16/20",
    r"16 of 20",
    r"8/9",
    r"8 of (?:the )?9",
    r"9 issue clusters",
    r"9 verified",
    r"13 review issue rows",
    r"13 obligation-grounded review issue rows",
    r"fresh full20 P28",
    r"MiMo API returned",
    r"402 Insufficient",
    r"deterministic reviewer seeds",
    r"only 2 verified rows",
)

REQUIRED_PHRASES = (
    "two accepted hardneg20 clean runs",
    "five recurring Critique-origin",
    "manual-D",
    "harmful recovery",
    "full39",
    "accept/reject",
    "PPO",
)


def _line_matches(text: str, pattern: str) -> List[Dict[str, Any]]:
    regex = re.compile(pattern, re.IGNORECASE)
    matches: List[Dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            matches.append({"line": lineno, "pattern": pattern, "text": line.strip()})
    return matches


def _audit_file(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    banned: List[Dict[str, Any]] = []
    for pattern in BANNED_PATTERNS:
        banned.extend(_line_matches(text, pattern))
    missing_required = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    return {
        "path": str(path),
        "banned_matches": banned,
        "missing_required_phrases": missing_required,
        "status": "PASS" if not banned and not missing_required else "FAIL",
    }


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    targets = [Path(path) for path in (args.file or DEFAULT_TARGETS)]
    files = [_audit_file(path) for path in targets]
    blocking: List[str] = []
    for item in files:
        if item["banned_matches"]:
            blocking.append(f"{item['path']} has stale result phrases")
        if item["missing_required_phrases"]:
            blocking.append(f"{item['path']} is missing P32 boundary phrases")
    return {
        "status": "PASS" if not blocking else "FAIL",
        "blocking_issues": blocking,
        "files": files,
        "banned_patterns": list(BANNED_PATTERNS),
        "required_phrases": list(REQUIRED_PHRASES),
    }


def _render_md(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# P32 Paper Stale Claim Audit")
    lines.append("")
    lines.append(f"- status: **{report['status']}**")
    lines.append("")
    if report["blocking_issues"]:
        lines.append("## Blocking Issues")
        lines.append("")
        for issue in report["blocking_issues"]:
            lines.append(f"- {issue}")
        lines.append("")
    lines.append("## Files")
    lines.append("")
    for item in report["files"]:
        lines.append(f"### `{item['path']}`")
        lines.append("")
        lines.append(f"- status: `{item['status']}`")
        lines.append(f"- banned matches: `{len(item['banned_matches'])}`")
        lines.append(f"- missing required phrases: `{len(item['missing_required_phrases'])}`")
        for match in item["banned_matches"][:20]:
            lines.append(f"  - line {match['line']}: `{match['pattern']}` -> {match['text']}")
        for phrase in item["missing_required_phrases"]:
            lines.append(f"  - missing: `{phrase}`")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", action="append", help="Paper draft file to audit. Defaults to the two main paper drafts.")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--fail-on-stale", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_render_md(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2))
    if args.fail_on_stale and report["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
