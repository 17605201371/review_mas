#!/usr/bin/env python3
"""Extract recovery replay fixture cases from a review_infer JSONL run.

Usage
-----
    python scripts/extract_recovery_replay_cases.py \
        mainline_p0_1a_full39_20260524_qwen35_t7.jsonl \
        --outdir tests/recovery_replay/cases \
        [--per-code 1]          # how many per failure_code
        [--paper WNxlJJIEVj]   # specific paper only

Each output JSON contains:
    case_id, review_state, raw_payload, expected (failure_code, validated, …)
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _slim_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only fields needed by validate_recovery_patch."""
    return {
        "claims": state.get("claims") or [],
        "evidence_map": state.get("evidence_map") or [],
        "flaw_candidates": state.get("flaw_candidates") or [],
        "current_hypotheses": state.get("current_hypotheses") or [],
        "conflict_notes": state.get("conflict_notes") or [],
    }


def _extract_critique_payload(worker_payloads: List[Any]) -> Optional[Dict[str, Any]]:
    """Return the Critique Agent's payload if it has a recovery action."""
    for wp in worker_payloads:
        if not isinstance(wp, dict):
            continue
        aid = str(wp.get("agent_id") or "")
        if "Critique" not in aid:
            continue
        payload = wp.get("payload")
        if isinstance(payload, dict) and payload.get("action") in {
            "apply_recovery_patch",
            "blocked",
        }:
            # slim: keep only patch-relevant fields
            patch_keys = [
                "action", "target_type", "target_id",
                "old_status", "new_status",
                "supporting_evidence_ids", "negative_evidence_ids",
                "conflict_note_ids", "reason_for_change",
                "resolution_expectation", "confidence",
                "blocked_reason", "missing_requirements",
                "_recovery_patch_source",
            ]
            return {k: payload.get(k) for k in patch_keys}
    return None


def extract_cases(
    jsonl_path: str,
    *,
    per_code: int = 1,
    paper_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Scan a JSONL and extract recovery replay cases."""
    code_counts: Dict[str, int] = {}
    cases: List[Dict[str, Any]] = []

    with open(jsonl_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            paper_id = record.get("paper_id", "")
            if paper_filter and paper_id != paper_filter:
                continue

            for tlog in record.get("turn_logs") or []:
                if not tlog.get("recovery_attempted"):
                    continue

                fail_code = tlog.get("recovery_failure_code") or "NONE"
                if code_counts.get(fail_code, 0) >= per_code:
                    continue

                state_snap = tlog.get("state_snapshot")
                if not isinstance(state_snap, dict):
                    continue

                critique_payload = _extract_critique_payload(
                    tlog.get("worker_payloads") or []
                )
                if critique_payload is None:
                    continue

                turn_id = tlog.get("turn_id", "?")
                case_id = f"{paper_id}_turn{turn_id}_{fail_code}"

                # Derive validator-level expected outcome.
                # The turn_log failure_code reflects the runner-level result
                # (after fallback/salvage), which may differ from the raw
                # validator output.  For action=blocked the validator always
                # returns failure_code=BLOCKED_BY_POLICY, validated=True.
                action = critique_payload.get("action", "")
                if action == "blocked":
                    exp_failure_code = "BLOCKED_BY_POLICY"
                    exp_validated = True
                    exp_commit = False
                else:
                    exp_failure_code = fail_code if fail_code != "NONE" else "SUCCESS"
                    exp_validated = tlog.get("recovery_patch_validated", False)
                    exp_commit = tlog.get("recovery_patch_committed", False)

                case = {
                    "case_id": case_id,
                    "paper_id": paper_id,
                    "turn_id": turn_id,
                    "review_state": _slim_state(state_snap),
                    "raw_payload": critique_payload,
                    "expected": {
                        "failure_code": exp_failure_code,
                        "validated": exp_validated,
                        "commit_allowed": exp_commit,
                    },
                    "meta": {
                        "runner_failure_code": fail_code,
                        "snapshot_timing": "post_recovery",
                        "recovery_target_id": tlog.get("recovery_target_id"),
                        "recovery_target_type": tlog.get("recovery_target_type"),
                        "recovery_patch_source": tlog.get("recovery_patch_source"),
                    },
                }
                cases.append(case)
                code_counts[fail_code] = code_counts.get(fail_code, 0) + 1

    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract recovery replay fixtures")
    parser.add_argument("jsonl", help="Path to review_infer JSONL run")
    parser.add_argument("--outdir", default="tests/recovery_replay/cases")
    parser.add_argument("--per-code", type=int, default=1)
    parser.add_argument("--paper", default=None)
    args = parser.parse_args()

    cases = extract_cases(
        args.jsonl, per_code=args.per_code, paper_filter=args.paper
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for case in cases:
        fname = f"{case['case_id']}.json"
        out_path = outdir / fname
        with open(out_path, "w") as fh:
            json.dump(case, fh, indent=2, ensure_ascii=False, default=str)
        print(f"  -> {out_path}  ({case['expected']['failure_code']})")

    print(f"\nExtracted {len(cases)} cases to {outdir}")


if __name__ == "__main__":
    main()
