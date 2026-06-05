from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_system.environments.env_package.review.state import _assess_quote_semantic_grounding, merge_review_state
from scripts.audit_evidence_grounding_quality_v1 import load_paper_text_map, verify_quote_grounding

NEGATIVE_STANCES = {
    "contradicts",
    "contradict",
    "refutes",
    "refute",
    "weakens",
    "weaken",
    "undermines",
    "undermine",
    "partially_contradicts",
    "partially_refutes",
    "missing",
    "unsupported",
    "does_not_support",
    "not_grounded",
}
VERIFIED_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
CLAIM_DOWNGRADE_STATUSES = {"supported", "partially_supported", "uncertain"}
FLAW_DOWNGRADE_STATUSES = {"candidate", "confirmed"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _verify_state_evidence(state: Dict[str, Any], paper_text: str) -> Dict[str, Any]:
    verified = copy.deepcopy(state or {})
    for ev in verified.get("evidence_map", []) or []:
        if not isinstance(ev, dict):
            continue
        verification = verify_quote_grounding(str(ev.get("raw_quote") or ""), paper_text)
        ev["verified_grounding_label"] = verification["verified_grounding_label"]
        ev["verified_quote_match_type"] = verification["verified_quote_match_type"]
        ev["verified_source_span_start"] = verification["verified_source_span_start"]
        ev["verified_source_span_end"] = verification["verified_source_span_end"]
        ev["verified_grounding_reason"] = verification["verified_grounding_reason"]
        ev.update(_assess_quote_semantic_grounding(verified, ev))
    return verified


def _evidence_by_id(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(ev.get("evidence_id") or ""): ev
        for ev in state.get("evidence_map", []) or []
        if isinstance(ev, dict) and ev.get("evidence_id")
    }


def _is_verified_negative(ev: Dict[str, Any]) -> bool:
    return (
        isinstance(ev, dict)
        and str(ev.get("stance") or "").strip().lower() in NEGATIVE_STANCES
        and str(ev.get("verified_grounding_label") or "") in VERIFIED_LABELS
        and str(ev.get("semantic_grounding_label") or "semantic_unjudged") in {"semantic_unjudged", "semantic_support_verified"}
        and str(ev.get("claim_id") or "").startswith("claim-")
        and not str(ev.get("claim_id") or "").startswith(("claim-context", "claim-fallback", "claim-recovery"))
    )


def _is_verified_positive(ev: Dict[str, Any]) -> bool:
    return (
        isinstance(ev, dict)
        and str(ev.get("stance") or "").strip().lower() in {"supports", "partially_supports"}
        and str(ev.get("strength") or "").strip().lower() == "strong"
        and str(ev.get("verified_grounding_label") or "") in VERIFIED_LABELS
    )


def _flaw_verified_negative_ids(flaw: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    ids = []
    for raw in list(flaw.get("negative_evidence_ids") or []) + list(flaw.get("evidence_ids") or []):
        eid = str(raw or "")
        ev = by_id.get(eid)
        if eid and eid not in ids and ev and _is_verified_negative(ev):
            ids.append(eid)
    return ids


def _first_existing_evidence_id(flaw: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> Optional[str]:
    for raw in flaw.get("evidence_ids") or []:
        eid = str(raw or "")
        if eid and eid in by_id:
            return eid
    return None


def _candidate_patches_for_state(state: Dict[str, Any], max_patches: int) -> List[Dict[str, Any]]:
    by_id = _evidence_by_id(state)
    patches: List[Dict[str, Any]] = []

    evidence_by_claim: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in by_id.values():
        if _is_verified_negative(ev):
            evidence_by_claim[str(ev.get("claim_id") or "")].append(ev)

    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        status = str(claim.get("status") or "").strip().lower()
        if status not in CLAIM_DOWNGRADE_STATUSES:
            continue
        negs = evidence_by_claim.get(claim_id) or []
        if not negs:
            continue
        patches.append({
            "candidate_type": "claim_verified_negative_downgrade",
            "payload": {
                "action": "apply_recovery_patch",
                "target_type": "claim",
                "target_id": claim_id,
                "old_status": status,
                "new_status": "unsupported",
                "supporting_evidence_ids": [str(negs[0].get("evidence_id"))],
                "resolution_expectation": "partially_resolved",
                "confidence": 0.8,
            },
        })
        if len(patches) >= max_patches:
            return patches

    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        flaw_id = str(flaw.get("flaw_id") or "")
        status = str(flaw.get("status") or "").strip().lower() or "candidate"
        if status not in FLAW_DOWNGRADE_STATUSES:
            continue
        if _flaw_verified_negative_ids(flaw, by_id):
            continue
        evidence_id = _first_existing_evidence_id(flaw, by_id)
        if not evidence_id:
            patches.append({
                "candidate_type": "flaw_no_evidence_downgrade_should_block",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "flaw",
                    "target_id": flaw_id,
                    "old_status": status,
                    "new_status": "downgraded",
                    "supporting_evidence_ids": [],
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.6,
                },
            })
        else:
            patches.append({
                "candidate_type": "flaw_without_verified_negative_downgrade",
                "payload": {
                    "action": "apply_recovery_patch",
                    "target_type": "flaw",
                    "target_id": flaw_id,
                    "old_status": status,
                    "new_status": "downgraded",
                    "supporting_evidence_ids": [evidence_id],
                    "resolution_expectation": "partially_resolved",
                    "confidence": 0.7,
                },
            })
        if len(patches) >= max_patches:
            return patches

    return patches


def _compact_patch_log(log: Dict[str, Any]) -> Dict[str, Any]:
    delta = log.get("recovery_state_delta", {}) or {}
    return {
        "recovery_committed": bool(log.get("recovery_committed", False)),
        "recovery_validated": bool(log.get("recovery_validated", False)),
        "recovery_failure_code": str(log.get("recovery_failure_code") or ""),
        "recovery_failure_message": str(log.get("recovery_failure_message") or "")[:240],
        "recovery_consistency_improved": bool(log.get("recovery_consistency_improved", False)),
        "negative_recovery_commit": bool(log.get("negative_recovery_commit", False)),
        "state_delta": delta.get("delta", {}),
        "improved_keys": delta.get("improved_keys", []),
        "worsened_keys": delta.get("worsened_keys", []),
    }


def run_replay(rows: List[Dict[str, Any]], paper_text_map: Dict[str, str], max_patches_per_paper: int) -> Dict[str, Any]:
    cases = []
    counters = Counter()
    paper_counters = Counter()

    for row in rows:
        pid = str(row.get("paper_id") or "")
        paper_text = paper_text_map.get(pid, "")
        state = _verify_state_evidence(row.get("review_state") or {}, paper_text)
        patches = _candidate_patches_for_state(state, max_patches=max_patches_per_paper)
        if patches:
            paper_counters["papers_with_replay_candidates"] += 1
        for patch in patches:
            candidate_type = patch["candidate_type"]
            payload = patch["payload"]
            after = merge_review_state(copy.deepcopy(state), payload)
            log = _compact_patch_log(after.get("_latest_patch_log", {}))
            counters[f"candidate_type::{candidate_type}"] += 1
            counters[f"failure_code::{log['recovery_failure_code']}"] += 1
            counters["replay_patch_count"] += 1
            counters["committed_count"] += int(log["recovery_committed"])
            counters["blocked_count"] += int(not log["recovery_committed"])
            counters["consistency_improved_commit_count"] += int(log["recovery_committed"] and log["recovery_consistency_improved"])
            counters["negative_recovery_commit_count"] += int(log["negative_recovery_commit"])
            cases.append({
                "paper_id": pid,
                "candidate_type": candidate_type,
                "target_type": payload.get("target_type", ""),
                "target_id": payload.get("target_id", ""),
                "supporting_evidence_ids": payload.get("supporting_evidence_ids", []),
                "patch_log": log,
            })

    committed_papers = {case["paper_id"] for case in cases if case["patch_log"]["recovery_committed"]}
    blocked_papers = {case["paper_id"] for case in cases if not case["patch_log"]["recovery_committed"]}
    summary = {
        "paper_count": len(rows),
        "papers_with_replay_candidates": paper_counters["papers_with_replay_candidates"],
        "replay_patch_count": counters["replay_patch_count"],
        "committed_count": counters["committed_count"],
        "blocked_count": counters["blocked_count"],
        "rows_with_any_commit": len(committed_papers),
        "rows_with_any_block": len(blocked_papers),
        "consistency_improved_commit_count": counters["consistency_improved_commit_count"],
        "negative_recovery_commit_count": counters["negative_recovery_commit_count"],
        "candidate_type_counts": {k.split("::", 1)[1]: v for k, v in sorted(counters.items()) if k.startswith("candidate_type::")},
        "failure_code_counts": {k.split("::", 1)[1]: v for k, v in sorted(counters.items()) if k.startswith("failure_code::")},
    }
    return {"summary": summary, "cases": cases}


def render_md(result: Dict[str, Any], input_path: str) -> str:
    summary = result["summary"]
    rows = []
    for case in result["cases"][:80]:
        log = case["patch_log"]
        delta = log.get("state_delta", {}) or {}
        key_delta = []
        for key, value in delta.items():
            if value:
                key_delta.append(f"{key}={value}")
        rows.append(
            "| {paper_id} | {candidate_type} | {target_type}:{target_id} | {committed} | {failure} | {improved} | {negative} | {delta} |".format(
                paper_id=case["paper_id"],
                candidate_type=case["candidate_type"],
                target_type=case["target_type"],
                target_id=case["target_id"],
                committed="yes" if log["recovery_committed"] else "no",
                failure=log["recovery_failure_code"],
                improved="yes" if log["recovery_consistency_improved"] else "no",
                negative="yes" if log["negative_recovery_commit"] else "no",
                delta=", ".join(key_delta[:4]) or "none",
            )
        )
    return "\n".join([
        "# Recovery Targeted Full39 Replay v1",
        "",
        "## 结论",
        "",
        "这不是重新跑模型，而是在最新 full39 ReviewState 上做 targeted recovery replay。脚本先对 evidence raw_quote 做 post-hoc verification，再筛选真实状态中的 claim/flaw recovery candidates，用当前 recovery validator 和 merge 逻辑回放 patch。",
        "",
        "## Input",
        "",
        f"- input_jsonl: `{input_path}`",
        "- dataset: `/reviewF/datasets/drmas_review/test.parquet`",
        "",
        "## Summary",
        "",
        f"- paper_count: {summary['paper_count']}",
        f"- papers_with_replay_candidates: {summary['papers_with_replay_candidates']}",
        f"- replay_patch_count: {summary['replay_patch_count']}",
        f"- committed_count: {summary['committed_count']}",
        f"- blocked_count: {summary['blocked_count']}",
        f"- rows_with_any_commit: {summary['rows_with_any_commit']}",
        f"- rows_with_any_block: {summary['rows_with_any_block']}",
        f"- consistency_improved_commit_count: {summary['consistency_improved_commit_count']}",
        f"- negative_recovery_commit_count: {summary['negative_recovery_commit_count']}",
        f"- candidate_type_counts: `{json.dumps(summary['candidate_type_counts'], ensure_ascii=False, sort_keys=True)}`",
        f"- failure_code_counts: `{json.dumps(summary['failure_code_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## Case Table",
        "",
        "| paper_id | candidate_type | target | committed | failure_code | consistency_improved | negative_commit | key_delta |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        "## Interpretation",
        "",
        "- 本 replay 回答的是：在真实 39 条结果里，如果存在可定位的 claim/flaw 修复机会，当前 validator 是否允许安全 commit、是否记录 state-quality delta。",
        "- committed_count 不是自然模型输出的 commit 数，而是 targeted replay 的可修复性上界/候选验证。",
        "- 若 blocked_count 高，说明真实状态里的候选多数仍缺 verified hard-negative grounding 或有效 evidence alignment；这应作为 hard-negative grounding 的后续修复目标。",
    ]) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="quote_bank_full39_20260513_qwen35.jsonl")
    parser.add_argument("--dataset", default="/reviewF/datasets/drmas_review/test.parquet")
    parser.add_argument("--max-patches-per-paper", type=int, default=3)
    parser.add_argument("--output-json", default="RECOVERY_TARGETED_FULL39_REPLAY_V1.json")
    parser.add_argument("--output-md", default="RECOVERY_TARGETED_FULL39_REPLAY_V1.md")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    paper_text_map = load_paper_text_map(Path(args.dataset))
    replay = run_replay(rows, paper_text_map, max_patches_per_paper=args.max_patches_per_paper)
    result = {
        "run_id": "recovery_targeted_full39_replay_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input": args.input,
        "dataset": args.dataset,
        **replay,
    }
    Path(args.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(render_md(result, args.input), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
