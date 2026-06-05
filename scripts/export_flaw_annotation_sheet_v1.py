#!/usr/bin/env python3
"""Export a CSV annotation sheet for the HygieneV3 flaw / concern / limitation
layered review output (P0.3).

Why this script
---------------
HygieneV3 routes every active ``flaw_candidate`` and every unresolved question
into one of three reviewer-visible layers: *Grounded paper weakness*,
*Potential concern requiring verification*, or *Assessment limitation*
(actionable / context / unresolved-diagnostic / stale). The paper argument is
that this layering is **principled hygiene**, not rule-driven self-talk.

To support that argument we need a cheap human annotation step. This script
turns a run's jsonl into a single CSV / JSONL pair that a human can open in
any spreadsheet, judging each row with one of four labels:

  - ``valid_grounded_flaw``    — evidence in the paper really supports a flaw
  - ``potential_concern``      — reviewer-worthy, but evidence is insufficient
  - ``assessment_limitation``  — current context is insufficient to judge
  - ``invalid_or_mismatched``  — evidence is unrelated, hallucinated, or meta

The script does NOT call any LLM. It is pure projection over the run's
``review_state`` and ``final_report`` text plus the HygieneV3 decision-view
classifications (grounded weakness / potential concern / limitation bucket).

Outputs
-------
``--output-csv`` / ``--output-jsonl`` are siblings. Each row has:

  paper_id, item_type, item_id, layer, layer_reason,
  title_or_question, description_or_context,
  cited_evidence_ids, cited_evidence_sources, cited_evidence_stances,
  negative_evidence_ids, severity, status, confidence,
  limitation_classification, primary_claim_ids,
  human_label (blank), annotator_notes (blank), paper_link (blank)

The ``human_label`` and ``annotator_notes`` columns are intentionally empty;
the spreadsheet fill-in IS the annotation task.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (  # noqa: E402
    build_decision_hygiene_view,
    _flaw_has_negative_grounding,
    _flaw_only_cites_supports,
    _flaw_explicit_negative_evidence_ids,
)


FIELDNAMES = [
    "paper_id",
    "item_type",           # flaw | limitation
    "item_id",             # flaw_id or question_id
    "layer",               # grounded_weakness | potential_concern | assessment_limitation
    "layer_reason",        # short machine reason (e.g. "auto_stance_inference", "only_cites_supports", "context_limitation")
    "title_or_question",
    "description_or_context",
    "severity",
    "status",
    "confidence",
    "related_claim_ids",
    "cited_evidence_ids",
    "cited_evidence_sources",
    "cited_evidence_stances",
    "negative_evidence_ids",
    "limitation_classification",
    "primary_claim_ids",
    "human_label",         # ← fill in
    "annotator_notes",     # ← fill in
    "paper_link",
]


def _join_list(items: Any, sep: str = ";") -> str:
    if not items:
        return ""
    if isinstance(items, str):
        return items
    return sep.join(str(x) for x in items if x is not None and str(x).strip())


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in state.get("evidence_map") or []:
        if isinstance(ev, dict):
            eid = str(ev.get("evidence_id") or "")
            if eid:
                out[eid] = ev
    return out


def _flaw_layer(
    flaw: Dict[str, Any], view: Dict[str, Any]
) -> Tuple[str, str]:
    """Classify a single flaw into one of the three reviewer layers."""
    status = str(flaw.get("status") or "").lower()
    if status in {"retracted"}:
        return "retracted", "status=retracted"
    if status == "downgraded":
        reason = str(flaw.get("hygiene_status_reason") or "downgraded_by_view")
        return "assessment_limitation", f"downgraded:{reason}"
    has_negative = _flaw_has_negative_grounding(flaw, view)
    only_supports = _flaw_only_cites_supports(flaw, view)
    explicit_neg = bool(_flaw_explicit_negative_evidence_ids(flaw))
    inferred = flaw.get("hygiene_negative_grounding_source") == "auto_stance_inference"
    if status == "confirmed" and has_negative:
        reason = "confirmed_with_explicit_negative" if explicit_neg else (
            "confirmed_with_auto_stance_inference" if inferred else "confirmed_with_negative_stance"
        )
        return "grounded_weakness", reason
    if has_negative:
        reason = "candidate_with_explicit_negative" if explicit_neg else (
            "candidate_with_auto_stance_inference" if inferred else "candidate_with_negative_stance"
        )
        return "grounded_weakness", reason
    # Active but not grounded — either support-only or generic concern.
    if only_supports:
        return "potential_concern", "only_cites_supports"
    return "potential_concern", "active_candidate_without_negative_anchor"


def _stance_summary(
    evidence_ids: List[str], lookup: Dict[str, Dict[str, Any]]
) -> Tuple[List[str], List[str]]:
    sources: List[str] = []
    stances: List[str] = []
    for eid in evidence_ids or []:
        record = lookup.get(str(eid))
        if not record:
            sources.append("[unresolved_id]")
            stances.append("[unresolved_id]")
            continue
        src = str(record.get("source") or record.get("evidence_source") or "")
        st = str(record.get("stance") or "").strip()
        sources.append(src or "[no_source]")
        stances.append(st or "[no_stance]")
    return sources, stances


def row_for_flaw(
    paper_id: str, flaw: Dict[str, Any], view: Dict[str, Any], paper_link: str
) -> Dict[str, Any]:
    layer, reason = _flaw_layer(flaw, view)
    lookup = _evidence_lookup(view)
    ev_ids = [str(x) for x in (flaw.get("evidence_ids") or [])]
    sources, stances = _stance_summary(ev_ids, lookup)
    neg_ids = _flaw_explicit_negative_evidence_ids(flaw)
    if not neg_ids and flaw.get("negative_evidence_ids"):
        neg_ids = [str(x) for x in flaw.get("negative_evidence_ids") or []]
    primary_ids = (view.get("decision_hygiene", {}) or {}).get("primary_claim_ids", [])
    return {
        "paper_id": paper_id,
        "item_type": "flaw",
        "item_id": str(flaw.get("flaw_id") or ""),
        "layer": layer,
        "layer_reason": reason,
        "title_or_question": str(flaw.get("title") or ""),
        "description_or_context": str(flaw.get("description") or ""),
        "severity": str(flaw.get("severity") or ""),
        "status": str(flaw.get("status") or ""),
        "confidence": flaw.get("confidence"),
        "related_claim_ids": _join_list(flaw.get("related_claim_ids")),
        "cited_evidence_ids": _join_list(ev_ids),
        "cited_evidence_sources": _join_list(sources),
        "cited_evidence_stances": _join_list(stances),
        "negative_evidence_ids": _join_list(neg_ids),
        "limitation_classification": "",
        "primary_claim_ids": _join_list(primary_ids),
        "human_label": "",
        "annotator_notes": "",
        "paper_link": paper_link,
    }


def row_for_limitation(
    paper_id: str, question: Dict[str, Any], view: Dict[str, Any], paper_link: str
) -> Dict[str, Any]:
    classification = str(question.get("limitation_classification") or "unclassified")
    primary_ids = (view.get("decision_hygiene", {}) or {}).get("primary_claim_ids", [])
    return {
        "paper_id": paper_id,
        "item_type": "limitation",
        "item_id": str(question.get("question_id") or question.get("id") or ""),
        "layer": "assessment_limitation",
        "layer_reason": classification,
        "title_or_question": str(
            question.get("question_text") or question.get("question") or question.get("text") or ""
        ),
        "description_or_context": str(
            question.get("reason")
            or question.get("note")
            or question.get("blocker")
            or ""
        ),
        "severity": "",
        "status": str(question.get("status") or ""),
        "confidence": "",
        "related_claim_ids": _join_list(question.get("related_claim_ids") or question.get("claim_ids")),
        "cited_evidence_ids": _join_list(question.get("evidence_ids")),
        "cited_evidence_sources": "",
        "cited_evidence_stances": "",
        "negative_evidence_ids": "",
        "limitation_classification": classification,
        "primary_claim_ids": _join_list(primary_ids),
        "human_label": "",
        "annotator_notes": "",
        "paper_link": paper_link,
    }


def iter_rows(jsonl_path: Path, include_limitations: bool, paper_link_prefix: str):
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        paper_id = str(data.get("paper_id") or data.get("sample_id") or data.get("id") or "")
        raw_state = data.get("review_state") or {}
        view = build_decision_hygiene_view(raw_state)
        paper_link = f"{paper_link_prefix}{paper_id}" if paper_link_prefix else ""
        for flaw in view.get("flaw_candidates") or []:
            if not isinstance(flaw, dict):
                continue
            status = str(flaw.get("status") or "").lower()
            # Only export rows that would appear in a reviewer-visible layer.
            if status in {"retracted"}:
                continue
            yield row_for_flaw(paper_id, flaw, view, paper_link)
        if include_limitations:
            for question in view.get("unresolved_questions") or []:
                if not isinstance(question, dict):
                    continue
                yield row_for_limitation(paper_id, question, view, paper_link)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a CSV/JSONL annotation sheet for HygieneV3 flaws and limitations."
    )
    parser.add_argument("--jsonl", required=True, help="Closure run jsonl (one paper per line).")
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-jsonl", default="")
    parser.add_argument(
        "--include-limitations",
        action="store_true",
        help="Also emit rows for each unresolved assessment limitation (default off; flaws only).",
    )
    parser.add_argument(
        "--paper-link-prefix",
        default="",
        help="Prefix for building ``paper_link`` from ``paper_id`` (e.g. OpenReview URL root).",
    )
    args = parser.parse_args()

    rows = list(
        iter_rows(Path(args.jsonl), args.include_limitations, args.paper_link_prefix)
    )

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    if args.output_jsonl:
        out_jsonl = Path(args.output_jsonl)
        out_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with out_jsonl.open("w", encoding="utf-8") as fp:
            for row in rows:
                fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    layer_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    for row in rows:
        layer_counts[row["layer"]] = layer_counts.get(row["layer"], 0) + 1
        type_counts[row["item_type"]] = type_counts.get(row["item_type"], 0) + 1

    summary = {
        "input": args.jsonl,
        "output_csv": str(out_csv),
        "output_jsonl": args.output_jsonl or None,
        "row_count": len(rows),
        "item_type_counts": type_counts,
        "layer_counts": layer_counts,
        "fieldnames": FIELDNAMES,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
