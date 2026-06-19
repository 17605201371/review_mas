#!/usr/bin/env python3
"""Acceptance guard: no counted verified-negative may be an author self-limitation.

Offline CI guard for the red line "paper-text extraction must not become a
reviewer-discovered negative".  For every evidence record that the state layer
COUNTS as a grounded paper negative (``_is_grounded_paper_negative_evidence_record``),
this guard asserts ALL of:

  1. ``review_negative_label == review_negative_verified``
  2. source / locator / verified bucket is NOT a Limitations / Future-work section
  3. the quote does NOT match the author-limitation / future-work regex

Any violation means an author self-stated limitation leaked into the verified
negative count (e.g. a regression of the _assess_review_negative_relation
author-limitation gate).  The script exits non-zero on any violation so it can
gate a run.  It does not call any model and does not mutate state.

Usage:
    python scripts/audit_verified_negative_author_limitation_guard_v1.py RUN.jsonl [RUN2.jsonl ...]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from agent_system.environments.env_package.review.state import (
    REVIEW_NEGATIVE_VERIFIED_LABEL,
    _assess_review_negative_relation,
    _is_grounded_paper_negative_evidence_record,
    _negative_evidence_type_for_record,
    _REVIEW_NEGATIVE_AUTHOR_LIMITATION_RE,
)

_LIMITATION_SOURCE_RE = re.compile(
    r"\b(limitation|limitations|future work|future works|threats? to validity|broader impact)\b",
    re.IGNORECASE,
)


def _review_label(item: Dict[str, Any], state: Dict[str, Any]) -> str:
    label = str(item.get("review_negative_label") or "").strip()
    if label:
        return label
    return str(_assess_review_negative_relation(state or {}, item).get("review_negative_label") or "")


def _violations_for_record(item: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    label = _review_label(item, state)
    if label != REVIEW_NEGATIVE_VERIFIED_LABEL:
        issues.append(f"label_not_verified({label or 'none'})")
    source_blob = " ".join(
        str(item.get(k) or "")
        for k in ("source", "source_locator", "verified_source_bucket", "support_source_bucket")
    )
    if _LIMITATION_SOURCE_RE.search(source_blob):
        issues.append("limitation_or_future_work_source")
    quote = str(item.get("raw_quote") or item.get("evidence") or "")
    if _REVIEW_NEGATIVE_AUTHOR_LIMITATION_RE.search(quote):
        issues.append("author_limitation_quote")
    return issues


def audit_run(path: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        paper_id = str(record.get("paper_id") or "")
        state = record.get("review_state") or record.get("final_state") or {}
        if not isinstance(state, dict):
            continue
        for ev in state.get("evidence_map", []) or []:
            if not isinstance(ev, dict):
                continue
            if not _is_grounded_paper_negative_evidence_record(ev, state):
                continue  # only inspect negatives that are COUNTED as grounded
            issues = _violations_for_record(ev, state)
            if issues:
                findings.append(
                    {
                        "run": path.name,
                        "paper_id": paper_id,
                        "evidence_id": str(ev.get("evidence_id") or ""),
                        "claim_id": str(ev.get("claim_id") or ""),
                        "negative_evidence_type": _negative_evidence_type_for_record(ev),
                        "issues": issues,
                        "quote": re.sub(r"\s+", " ", str(ev.get("raw_quote") or ev.get("evidence") or ""))[:180],
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", help="run .jsonl file(s) to audit")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="report violations but always exit 0 (default: exit 1 on any violation)",
    )
    args = parser.parse_args()

    all_findings: List[Dict[str, Any]] = []
    grounded_total = 0
    for run in args.runs:
        path = Path(run)
        if not path.exists():
            print(f"[skip] {run}: not found", file=sys.stderr)
            continue
        # count grounded negatives for context
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            st = rec.get("review_state") or rec.get("final_state") or {}
            if isinstance(st, dict):
                for ev in st.get("evidence_map", []) or []:
                    if isinstance(ev, dict) and _is_grounded_paper_negative_evidence_record(ev, st):
                        grounded_total += 1
        all_findings.extend(audit_run(path))

    print(f"grounded verified-negative records inspected: {grounded_total}")
    if not all_findings:
        print("PASS: no author-limitation / non-verified negative is counted as a grounded negative.")
        return 0

    print(f"FAIL: {len(all_findings)} counted negative(s) look like author self-limitations:\n")
    for f in all_findings:
        print(f"  - [{f['run']}] {f['paper_id']} {f['evidence_id']} ({f['negative_evidence_type']})")
        print(f"      issues: {', '.join(f['issues'])}")
        print(f"      quote : {f['quote']}")
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
