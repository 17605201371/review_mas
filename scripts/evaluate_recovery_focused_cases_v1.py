from __future__ import annotations

import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_system.environments.env_package.review.state import merge_review_state


OUT_JSON = ROOT / "RECOVERY_FOCUSED_EVALUATION_V1.json"
OUT_MD = ROOT / "RECOVERY_FOCUSED_EVALUATION_V1.md"


def _base_state() -> Dict[str, Any]:
    return {
        "paper_id": "recovery-focused-fixture",
        "turn_id": 1,
        "evidence_quote_bank": [
            {
                "quote_id": "q-neg",
                "raw_quote": "Ablation results do not support the robustness claim.",
                "source_locator": "Section 4.3",
                "source_span_start": 100,
                "source_span_end": 153,
            },
            {
                "quote_id": "q-pos",
                "raw_quote": "The proposed method improves accuracy on the benchmark.",
                "source_locator": "Table 2",
                "source_span_start": 200,
                "source_span_end": 257,
            },
        ],
        "claims": [
            {
                "claim_id": "claim-neg",
                "claim": "The method remains robust under ablation.",
                "importance": "high",
                "status": "supported",
                "supporting_evidence_ids": ["ev-neg"],
            },
            {
                "claim_id": "claim-pos",
                "claim": "The method improves benchmark accuracy.",
                "importance": "high",
                "status": "supported",
                "supporting_evidence_ids": ["ev-pos"],
            },
            {
                "claim_id": "claim-unverified",
                "claim": "The method is robust on a hidden stress test.",
                "importance": "medium",
                "status": "supported",
                "supporting_evidence_ids": ["ev-unverified"],
            },
        ],
        "evidence_map": [
            {
                "evidence_id": "ev-neg",
                "claim_id": "claim-neg",
                "evidence": "Ablation evidence contradicts the robustness claim.",
                "source": "Section 4.3",
                "source_locator": "Section 4.3",
                "raw_quote": "Ablation results do not support the robustness claim.",
                "quote_id": "q-neg",
                "strength": "medium",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_exact",
            },
            {
                "evidence_id": "ev-pos",
                "claim_id": "claim-pos",
                "evidence": "Benchmark evidence supports the accuracy claim.",
                "source": "Table 2",
                "source_locator": "Table 2",
                "raw_quote": "The proposed method improves accuracy on the benchmark.",
                "quote_id": "q-pos",
                "strength": "strong",
                "stance": "supports",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "paper_grounded_exact",
                "verified_quote_match_type": "quote_bank_exact",
            },
            {
                "evidence_id": "ev-unverified",
                "claim_id": "claim-unverified",
                "evidence": "The stress-test robustness claim appears unsupported, but the quote is paraphrased.",
                "source": "model paraphrase",
                "source_locator": "Section 5",
                "raw_quote": "The model fails hidden stress tests by a large margin.",
                "strength": "medium",
                "stance": "contradicts",
                "binding_status": "bound_real_claim",
                "verified_grounding_label": "not_verified_paraphrase_only",
                "verified_quote_match_type": "not_found",
            },
        ],
        "flaw_candidates": [
            {
                "flaw_id": "flaw-unverified",
                "title": "Unverified robustness weakness",
                "description": "The claimed stress-test robustness is not supported by verified paper evidence.",
                "severity": "major",
                "status": "confirmed",
                "related_claim_ids": ["claim-unverified"],
                "evidence_ids": ["ev-unverified"],
                "negative_evidence_ids": ["ev-unverified"],
                "confidence": 0.8,
            },
            {
                "flaw_id": "flaw-grounded-candidate",
                "title": "Ablation concern",
                "description": "The ablation evidence weakens the robustness claim and needs reviewer attention.",
                "severity": "major",
                "status": "candidate",
                "related_claim_ids": ["claim-neg"],
                "evidence_ids": ["ev-neg"],
                "negative_evidence_ids": ["ev-neg"],
                "confidence": 0.7,
            },
        ],
        "conflict_notes": [
            {
                "conflict_id": "conf-neg",
                "note": "Claim status is supported although verified evidence contradicts it.",
                "claim_id": "claim-neg",
                "evidence_id": "ev-neg",
            }
        ],
        "evidence_gaps": ["Claim claim-unverified lacks verified robustness evidence."],
        "unresolved_questions": [],
    }


def _run_case(
    name: str,
    description: str,
    payload: Dict[str, Any],
    expect_commit: bool,
    expect_failure_code: str = "SUCCESS",
    target_field: Optional[str] = None,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    before = _base_state()
    after = merge_review_state(copy.deepcopy(before), payload)
    patch_log = after.get("_latest_patch_log", {})
    target_status = ""
    if target_field and target_id:
        id_key = "claim_id" if target_field == "claims" else "flaw_id"
        for item in after.get(target_field, []) or []:
            if str(item.get(id_key) or "") == target_id:
                target_status = str(item.get("status") or "")
                break
    passed = bool(patch_log.get("recovery_committed")) == expect_commit and str(patch_log.get("recovery_failure_code") or "") == expect_failure_code
    return {
        "name": name,
        "description": description,
        "payload": payload,
        "expect_commit": expect_commit,
        "expect_failure_code": expect_failure_code,
        "passed": passed,
        "target_status_after": target_status,
        "patch_log": patch_log,
    }


def run_cases() -> List[Dict[str, Any]]:
    return [
        _run_case(
            "valid_verified_claim_downgrade_resolves_conflict",
            "Verified negative evidence can downgrade an inconsistent supported claim and resolve its active conflict.",
            {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": "claim-neg",
                "old_status": "supported",
                "new_status": "unsupported",
                "supporting_evidence_ids": ["ev-neg"],
                "conflict_note_ids": ["conf-neg"],
                "resolution_expectation": "resolved",
                "confidence": 0.85,
            },
            True,
            target_field="claims",
            target_id="claim-neg",
        ),
        _run_case(
            "support_only_claim_downgrade_blocked",
            "Positive support evidence cannot justify unsupported recovery.",
            {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": "claim-pos",
                "old_status": "supported",
                "new_status": "unsupported",
                "supporting_evidence_ids": ["ev-pos"],
                "resolution_expectation": "partially_resolved",
                "confidence": 0.7,
            },
            False,
            "EVIDENCE_SEMANTIC_MISMATCH",
            target_field="claims",
            target_id="claim-pos",
        ),
        _run_case(
            "unverified_negative_claim_downgrade_blocked",
            "Negative paraphrase-only evidence cannot justify unsupported recovery once verified grounding is enabled.",
            {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": "claim-unverified",
                "old_status": "supported",
                "new_status": "unsupported",
                "supporting_evidence_ids": ["ev-unverified"],
                "resolution_expectation": "partially_resolved",
                "confidence": 0.7,
            },
            False,
            "EVIDENCE_SEMANTIC_MISMATCH",
            target_field="claims",
            target_id="claim-unverified",
        ),
        _run_case(
            "flaw_downgrade_reduces_unverified_confirmed_flaw",
            "A confirmed flaw without verified negative evidence can be safely downgraded out of grounded-weakness status.",
            {
                "action": "apply_recovery_patch",
                "target_type": "flaw",
                "target_id": "flaw-unverified",
                "old_status": "confirmed",
                "new_status": "downgraded",
                "supporting_evidence_ids": ["ev-unverified"],
                "resolution_expectation": "partially_resolved",
                "confidence": 0.8,
            },
            True,
            target_field="flaw_candidates",
            target_id="flaw-unverified",
        ),
        _run_case(
            "no_effect_patch_blocked",
            "A patch that leaves the target lifecycle unchanged is blocked as no-effect.",
            {
                "action": "apply_recovery_patch",
                "target_type": "flaw",
                "target_id": "flaw-unverified",
                "old_status": "confirmed",
                "new_status": "confirmed",
                "supporting_evidence_ids": ["ev-unverified"],
                "resolution_expectation": "partially_resolved",
                "confidence": 0.6,
            },
            False,
            "NO_EFFECT_PATCH",
            target_field="flaw_candidates",
            target_id="flaw-unverified",
        ),
    ]


def _summary(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    committed = [case for case in cases if case["patch_log"].get("recovery_committed")]
    blocked = [case for case in cases if not case["patch_log"].get("recovery_committed")]
    improved = [case for case in committed if case["patch_log"].get("recovery_consistency_improved")]
    negative = [case for case in committed if case["patch_log"].get("negative_recovery_commit")]
    return {
        "case_count": len(cases),
        "passed_count": sum(1 for case in cases if case["passed"]),
        "committed_count": len(committed),
        "blocked_count": len(blocked),
        "consistency_improved_commit_count": len(improved),
        "negative_recovery_commit_count": len(negative),
        "failure_code_counts": {
            code: sum(1 for case in cases if case["patch_log"].get("recovery_failure_code") == code)
            for code in sorted({str(case["patch_log"].get("recovery_failure_code") or "") for case in cases})
        },
    }


def _render_markdown(result: Dict[str, Any]) -> str:
    rows = []
    for case in result["cases"]:
        log = case["patch_log"]
        delta = log.get("recovery_state_delta", {}).get("delta", {}) or {}
        delta_bits = []
        for key in ("open_conflict_count", "confirmed_flaw_without_verified_negative_count", "negative_grounding_conflict_count"):
            if key in delta and delta[key] != 0:
                delta_bits.append(f"{key}={delta[key]}")
        rows.append(
            "| {name} | {passed} | {committed} | {failure} | {improved} | {negative} | {delta} |".format(
                name=case["name"],
                passed="yes" if case["passed"] else "no",
                committed="yes" if log.get("recovery_committed") else "no",
                failure=log.get("recovery_failure_code", ""),
                improved="yes" if log.get("recovery_consistency_improved") else "no",
                negative="yes" if log.get("negative_recovery_commit") else "no",
                delta=", ".join(delta_bits) or "none",
            )
        )
    summary = result["summary"]
    return "\n".join(
        [
            "# Recovery Focused Evaluation v1",
            "",
            "## 结论",
            "",
            "这轮不是自然 full39 的 recovery 触发统计，而是固定冲突状态上的功能验证。目标是证明 recovery 在有 verified hard-negative grounding 时可以安全 commit，并在 support-only / unverified / no-effect patch 上保持拦截。",
            "",
            "## Summary",
            "",
            f"- case_count: {summary['case_count']}",
            f"- passed_count: {summary['passed_count']}",
            f"- committed_count: {summary['committed_count']}",
            f"- blocked_count: {summary['blocked_count']}",
            f"- consistency_improved_commit_count: {summary['consistency_improved_commit_count']}",
            f"- negative_recovery_commit_count: {summary['negative_recovery_commit_count']}",
            f"- failure_code_counts: `{json.dumps(summary['failure_code_counts'], ensure_ascii=False, sort_keys=True)}`",
            "",
            "## Case Table",
            "",
            "| case | passed | committed | failure_code | consistency_improved | negative_commit | key_delta |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## Interpretation",
            "",
            "- recovery commit 现在不是靠放松 validator 得到：support-only evidence 和 unverified paraphrase-only negative evidence 都会被拦截。",
            "- valid verified negative evidence 可以驱动 claim lifecycle 修复，并记录 open conflict 的下降。",
            "- confirmed flaw 如果缺 verified negative evidence，可以通过 downgrade patch 从 grounded weakness 候选中移出，降低未验证缺陷污染。",
            "- natural full39 中 commit 为 0 仍需解释为自然样本没有通过 validator 的修复机会；本 focused set 证明机制本身可以在合格输入上 commit。",
        ]
    ) + "\n"


def main() -> None:
    cases = run_cases()
    result = {
        "run_id": "recovery_focused_evaluation_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": _summary(cases),
        "cases": cases,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_render_markdown(result), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    if result["summary"]["passed_count"] != result["summary"]["case_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
