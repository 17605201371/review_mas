#!/usr/bin/env python3
"""Audit role-aware PaperIndex retrieval over a review runner JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

from agent_system.environments.env_package.review.paper_index import build_paper_index
from agent_system.environments.env_package.review.review_retrieval import render_retrieval_context


ROLE_BUDGETS = {"claim": 2200, "evidence": 2300, "critique": 1800}
ROLE_EXPECTED_TYPES = {
    "claim": {"abstract", "introduction", "method", "results", "limitations", "conclusion"},
    "evidence": {"results", "analysis", "method", "limitations", "discussion", "conclusion", "abstract"},
    "critique": {"results", "analysis", "limitations", "discussion", "method", "related_work", "conclusion"},
}
ROLE_REQUIRED_GROUPS = {
    "claim": ({"abstract", "introduction"}, {"method"}, {"results"}),
    "evidence": ({"results"}, {"method", "analysis"}),
    "critique": ({"results"}, {"analysis", "limitations", "discussion"}),
}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _manager_payload(role: str, state: Mapping[str, Any]) -> Dict[str, Any]:
    claim_ids = [
        str(item.get("claim_id") or "")
        for item in state.get("claims", [])[:2]
        if isinstance(item, dict) and str(item.get("claim_id") or "")
    ]
    return {
        "action_type": {"claim": "extract_claims", "evidence": "verify_evidence", "critique": "analyze_flaws"}[role],
        "target_claim_ids": claim_ids if role != "claim" else [],
        "focus": str(state.get("active_focus") or state.get("last_focus") or ""),
    }


def build_audit(input_jsonl: Path) -> Dict[str, Any]:
    rows = _load_jsonl(input_jsonl)
    cases = []
    for row in rows:
        state = row.get("review_state") if isinstance(row.get("review_state"), dict) else {}
        paper_id = str(row.get("paper_id") or state.get("paper_id") or "")
        paper_text = str(state.get("paper_text") or "")
        index = build_paper_index(paper_text)
        available_types = {section.section_type for section in index.sections}
        role_reports = {}
        result_sets = {}
        for role, max_chars in ROLE_BUDGETS.items():
            context, meta = render_retrieval_context(
                paper_text, role, state, _manager_payload(role, state), max_chars=max_chars
            )
            result_ids = {str(item.get("result_id") or "") for item in meta["paper_index_retrieval_results"]}
            retrieved_types = set(meta["paper_index_retrieval_section_types"])
            expected_available = available_types & ROLE_EXPECTED_TYPES[role]
            required_groups = [group & available_types for group in ROLE_REQUIRED_GROUPS[role] if group & available_types]
            result_sets[role] = result_ids
            role_reports[role] = {
                "query_count": meta["paper_index_retrieval_query_count"],
                "result_count": meta["paper_index_retrieval_result_count"],
                "context_chars": len(context),
                "section_types": sorted(retrieved_types),
                "result_ids": sorted(result_ids),
                "roundtrip_ok": meta["paper_index_retrieval_roundtrip_ok"],
                "expected_available_section_types": sorted(expected_available),
                "expected_type_recall": len(retrieved_types & expected_available) / len(expected_available) if expected_available else 1.0,
                "required_group_coverage": sum(bool(group & retrieved_types) for group in required_groups) / len(required_groups) if required_groups else 1.0,
                "parser_modes": meta["paper_index_summary"].get("parser_modes", []),
            }
        pairwise = {}
        for left, right in (("claim", "evidence"), ("claim", "critique"), ("evidence", "critique")):
            union = result_sets[left] | result_sets[right]
            pairwise[f"{left}_vs_{right}"] = len(result_sets[left] & result_sets[right]) / len(union) if union else 1.0
        cases.append({
            "paper_id": paper_id,
            "paper_chars": len(paper_text),
            "available_section_types": sorted(available_types),
            "roles": role_reports,
            "pairwise_result_jaccard": pairwise,
            "all_three_result_sets_identical": len({tuple(sorted(value)) for value in result_sets.values()}) == 1,
        })
    role_summary = {}
    for role in ROLE_BUDGETS:
        reports = [case["roles"][role] for case in cases]
        role_summary[role] = {
            "paper_count": len(reports),
            "nonempty_count": sum(report["result_count"] > 0 for report in reports),
            "roundtrip_ok_count": sum(report["roundtrip_ok"] for report in reports),
            "mean_result_count": sum(report["result_count"] for report in reports) / len(reports) if reports else 0.0,
            "mean_context_chars": sum(report["context_chars"] for report in reports) / len(reports) if reports else 0.0,
            "mean_expected_type_recall": sum(report["expected_type_recall"] for report in reports) / len(reports) if reports else 0.0,
            "mean_required_group_coverage": sum(report["required_group_coverage"] for report in reports) / len(reports) if reports else 0.0,
            "section_type_counts": dict(Counter(section_type for report in reports for section_type in report["section_types"])),
        }
    identical_count = sum(case["all_three_result_sets_identical"] for case in cases)
    blocking = []
    for role, summary in role_summary.items():
        if summary["nonempty_count"] != len(cases):
            blocking.append(f"empty_retrieval:{role}:{summary['nonempty_count']}/{len(cases)}")
        if summary["roundtrip_ok_count"] != len(cases):
            blocking.append(f"span_roundtrip:{role}:{summary['roundtrip_ok_count']}/{len(cases)}")
        if summary["mean_required_group_coverage"] < 0.8:
            blocking.append(f"required_group_coverage_below_0_80:{role}:{summary['mean_required_group_coverage']:.3f}")
    if identical_count > len(cases) * 0.25:
        blocking.append(f"role_result_sets_too_similar:{identical_count}/{len(cases)}")
    return {
        "status": "PASS_FUNCTIONAL" if not blocking else "BLOCKED",
        "boundary": "P34-1 role-aware retrieval functional audit; manual PaperIndex anchor gate remains separate",
        "input_jsonl": str(input_jsonl),
        "input_sha256": hashlib.sha256(input_jsonl.read_bytes()).hexdigest(),
        "paper_count": len(cases),
        "role_summary": role_summary,
        "all_three_result_sets_identical_count": identical_count,
        "blocking_issues": blocking,
        "cases": cases,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# P34-1 Role-Aware Retrieval Audit",
        "",
        f"- status: **{report['status']}**",
        f"- paper_count: `{report['paper_count']}`",
        f"- all_three_result_sets_identical_count: `{report['all_three_result_sets_identical_count']}`",
        "",
        "## Role Summary",
        "",
    ]
    lines.extend(f"- `{role}`: `{summary}`" for role, summary in report["role_summary"].items())
    lines.extend(["", "## Blocking Issues", ""])
    lines.extend(f"- `{item}`" for item in report["blocking_issues"]) if report["blocking_issues"] else lines.append("- none")
    lines.extend(["", "Manual section-boundary and anchor acceptance remains `NEEDS_MANUAL_ANCHORS`; this report does not replace it."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()
    report = build_audit(Path(args.input_jsonl))
    Path(args.output_json).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "paper_count", "role_summary", "all_three_result_sets_identical_count", "blocking_issues")}, ensure_ascii=False))
    return 0 if report["status"] == "PASS_FUNCTIONAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
