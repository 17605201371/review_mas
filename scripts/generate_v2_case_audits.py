#!/usr/bin/env python3
"""V2 case audit generator: extends build_case_audit_v1 with three new case types.

New case types (beyond v1):
- safe_blocked_patch: recovery patches that were validator-blocked (EVIDENCE_TARGET_MISMATCH,
  BLOCKED_BY_POLICY, INSUFFICIENT_EVIDENCE, SEMANTIC_MISMATCH) with interpreted outcome.
- negative_semantic_rejection: negative evidence items that failed semantic anchor validation
  (negative_grounding_conflicts / invalid_negative_evidence_id), with explanation.
- state_hygiene_decomposition: per-paper state contamination decomposition into
  harmful vs conservative, with sub-type detail.

Each bundle contains: paper_id, case_type, raw_flag, interpreted_outcome, plus
type-specific detail fields and a manual_label slot.

Guard rails: reads saved state only; never runs the model; a record that cannot
be processed is recorded with an error flag and skipped; a case type with no
matches yields an empty list.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    _flaw_negative_grounding_conflicts,
)

SCHEMA_VERSION = "case_audit_v2_20260603"

V2_CASE_TYPES = [
    "safe_blocked_patch",
    "negative_semantic_rejection",
    "state_hygiene_decomposition",
]

# Interpretation map matching dashboard_run_comparison_v1
_FAILURE_CODE_INTERPRETATIONS = {
    "EVIDENCE_TARGET_MISMATCH": "safe_blocked_patch (missing or unverified IDs)",
    "BLOCKED_BY_POLICY": "safe_blocked_patch (policy restriction/abstention)",
    "INSUFFICIENT_EVIDENCE": "safe_blocked_patch (insufficient evidence criteria)",
    "SEMANTIC_MISMATCH": "safe_blocked_patch (semantic validation mismatch)",
}

_SAFE_BLOCKED_CODES = set(_FAILURE_CODE_INTERPRETATIONS.keys())


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _text(value: Any, limit: int = 240) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "\u2026"


def _row_state(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    if not isinstance(state, dict):
        return {}
    if row.get("paper_id") and not state.get("paper_id"):
        state = dict(state)
        state["paper_id"] = row.get("paper_id")
    return state


def _evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in state.get("evidence_map", []) or []:
        if isinstance(ev, dict) and str(ev.get("evidence_id") or ""):
            out[str(ev["evidence_id"])] = ev
    return out


def _claim_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for claim in state.get("claims", []) or []:
        if isinstance(claim, dict) and str(claim.get("claim_id") or ""):
            out[str(claim["claim_id"])] = claim
    return out


def _collect_safe_blocked_patches(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect recovery patches that were validator-blocked (safe blocked).

    turn_logs may be at top-level row or inside review_state.
    """
    bundles: List[Dict[str, Any]] = []
    turn_logs = row.get("turn_logs") or (row.get("review_state") or {}).get("turn_logs") or []
    if isinstance(turn_logs, dict):
        turn_logs = list(turn_logs.values())
    for tl in turn_logs:
        if not isinstance(tl, dict):
            continue
        if not tl.get("recovery_attempted"):
            continue
        code = str(tl.get("recovery_failure_code") or "")
        if code not in _SAFE_BLOCKED_CODES:
            continue
        bundles.append({
            "raw_flag": code,
            "interpreted_outcome": _FAILURE_CODE_INTERPRETATIONS[code],
            "committed_state_corruption": False,
            "recovery_target_type": tl.get("recovery_target_type") or tl.get("recovery_patch_operation") or "",
            "recovery_target_gate_label": tl.get("recovery_target_gate_label") or "",
            "turn_id": tl.get("turn_id") or tl.get("step") or "",
        })
    return bundles


def _collect_negative_semantic_rejections(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Collect negative evidence items that failed semantic anchor validation."""
    bundles: List[Dict[str, Any]] = []
    ev_by_id = _evidence_lookup(state)
    claims = _claim_lookup(state)
    flaws = state.get("flaw_candidates") or []
    for flaw in flaws:
        if not isinstance(flaw, dict):
            continue
        conflicts = _flaw_negative_grounding_conflicts(flaw, state)
        for conflict in conflicts:
            ev_id = str(conflict.get("evidence_id") or "")
            ev = ev_by_id.get(ev_id, {})
            claim_id = str(ev.get("claim_id") or "")
            claim_text = (claims.get(claim_id) or {}).get("claim") or ""
            bundles.append({
                "raw_flag": "invalid_negative_evidence_id",
                "interpreted_outcome": "negative_semantic_anchor_conflict",
                "evidence_id": ev_id,
                "target_flaw_id": str(conflict.get("flaw_id") or ""),
                "target_claim_id": claim_id,
                "claim_text": _text(claim_text),
                "conflict_reason": str(conflict.get("reason") or ""),
                "explanation": (
                    "Generic gap or weak negative evidence lacks semantic negative anchor; "
                    "rejected by semantic verifier. The evidence ID exists in evidence_map "
                    "but was not accepted as a valid negative anchor."
                ),
            })
    return bundles


def _collect_state_hygiene_decomposition(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Per-paper state contamination decomposition into harmful vs conservative.

    Reads from pre-computed decision_hygiene in state_audit (already stored in
    saved JSONL) rather than re-running build_decision_hygiene_view.
    """
    hygiene = (state.get("state_audit") or {}).get("decision_hygiene") or {}
    bundles: List[Dict[str, Any]] = []
    total = hygiene.get("state_contamination_count", 0)
    if not total:
        return bundles
    harmful = hygiene.get("harmful_state_contamination_count", 0)
    repairable = hygiene.get("repairable_state_warning_count",
                             hygiene.get("repairable_contamination_target_count", 0))
    conservative = hygiene.get("conservative_state_warning_count",
                               hygiene.get("conservative_contamination_target_count", 0))
    type_counts = hygiene.get("state_contamination_type_counts") or {}
    gate_counts = hygiene.get("recovery_target_gate_counts") or {}
    bundles.append({
        "raw_flag": "state_contamination",
        "interpreted_outcome": (
            f"harmful_state_contamination={harmful} / "
            f"repairable_state_warning={repairable} / "
            f"conservative_state_warning={conservative}"
        ),
        "harmful_state_contamination_count": harmful,
        "repairable_state_warning_count": repairable,
        "conservative_state_warning_count": conservative,
        "weak_target_warning_count": conservative,
        "contamination_type_counts": type_counts,
        "recovery_target_gate_counts": gate_counts,
        "contamination_harmful_recovery_risk": type_counts.get("harmful_recovery_risk", 0),
        "contamination_target_gate_real_target": gate_counts.get("real_target", 0),
    })
    return bundles


def generate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    bundles: Dict[str, List[Dict[str, Any]]] = {ct: [] for ct in V2_CASE_TYPES}
    errors: List[Dict[str, Any]] = []
    for row in rows:
        paper_id = str(row.get("paper_id") or "")
        try:
            state = _row_state(row)

            # safe_blocked_patch
            for b in _collect_safe_blocked_patches(row):
                bundles["safe_blocked_patch"].append({
                    "case_type": "safe_blocked_patch",
                    "paper_id": paper_id,
                    **b,
                    "manual_label": "",
                })

            # negative_semantic_rejection
            for b in _collect_negative_semantic_rejections(state):
                bundles["negative_semantic_rejection"].append({
                    "case_type": "negative_semantic_rejection",
                    "paper_id": paper_id,
                    **b,
                    "manual_label": "",
                })

            # state_hygiene_decomposition
            for b in _collect_state_hygiene_decomposition(state):
                bundles["state_hygiene_decomposition"].append({
                    "case_type": "state_hygiene_decomposition",
                    "paper_id": paper_id,
                    **b,
                    "manual_label": "",
                })
        except Exception as exc:
            errors.append({"paper_id": paper_id, "error": f"{type(exc).__name__}: {exc}"})
            continue

    return {
        "schema_version": SCHEMA_VERSION,
        "paper_count": len(rows),
        "case_counts": {ct: len(bundles[ct]) for ct in V2_CASE_TYPES},
        "bundles": bundles,
        "errors": errors,
    }


def _write_csv(bundles: List[Dict[str, Any]], path: Path) -> None:
    if not bundles:
        path.write_text("", encoding="utf-8")
        return
    keys = list(bundles[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for b in bundles:
            row = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
                   for k, v in b.items()}
            w.writerow(row)


def _write_md(bundles: List[Dict[str, Any]], path: Path, title: str) -> None:
    lines = [f"# {title}", ""]
    if not bundles:
        lines.append("_No cases found._")
        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
        return
    keys = list(bundles[0].keys())
    lines.append("| " + " | ".join(keys) + " |")
    lines.append("| " + " | ".join("---" for _ in keys) + " |")
    for b in bundles:
        vals = []
        for k in keys:
            v = b.get(k, "")
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            vals.append(str(v).replace("|", "\\|")[:120])
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="V2 case audit generator (offline, zero GPU)")
    ap.add_argument("--input", required=True, help="saved review_infer jsonl")
    ap.add_argument("--output-dir", required=True, help="directory for output files")
    ap.add_argument("--limit-per-type", type=int, default=0, help="cap bundles per case type (0=all)")
    args = ap.parse_args()

    rows = _load_jsonl(Path(args.input))
    result = generate(rows)
    if args.limit_per_type > 0:
        for ct in V2_CASE_TYPES:
            result["bundles"][ct] = result["bundles"][ct][: args.limit_per_type]

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write full JSON
    json_path = out_dir / "case_audit_v2.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write per-type CSV and MD
    for ct in V2_CASE_TYPES:
        ct_bundles = result["bundles"][ct]
        safe_name = ct.upper()
        _write_csv(ct_bundles, out_dir / f"CASE_AUDIT_{safe_name}_V2.csv")
        _write_md(ct_bundles, out_dir / f"CASE_AUDIT_{safe_name}_V2.md", f"Case Audit: {ct}")

    print(f"[OK] v2 case audit -> {out_dir}")
    print(f"paper_count={result['paper_count']} errors={len(result['errors'])}")
    print("case_counts:", json.dumps(result["case_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
