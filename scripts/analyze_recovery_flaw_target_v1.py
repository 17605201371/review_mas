#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agent_system.environments.env_package.review.state import build_decision_hygiene_view

VERIFIED_LABELS = {"paper_grounded_exact", "paper_grounded_normalized"}
SUPPORT_STANCES = {"supports", "partially_supports"}
CONTEXT_MARKERS = ("context", "fallback", "recovery-marker", "recovery_marker", "general")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def is_context_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return any(marker in cid for marker in CONTEXT_MARKERS)


def is_verified_evidence(ev: Dict[str, Any]) -> bool:
    label = norm(ev.get("verified_grounding_label") or ev.get("grounded_judge_label"))
    return label in VERIFIED_LABELS


def evidence_summary(state: Dict[str, Any]) -> Counter:
    counts: Counter = Counter()
    for ev in as_list(state.get("evidence_map")):
        if not isinstance(ev, dict):
            continue
        stance = norm(ev.get("stance"))
        strength = norm(ev.get("strength"))
        claim_id = ev.get("claim_id")
        verified = is_verified_evidence(ev)
        if ev.get("quote_id"):
            counts["quote_id_evidence"] += 1
        if norm(ev.get("verified_grounding_label")) in VERIFIED_LABELS:
            counts["verified_evidence"] += 1
        if stance in SUPPORT_STANCES and strength == "strong":
            counts["strong_support"] += 1
            if is_context_claim_id(claim_id):
                counts["context_or_nonreal_strong_support"] += 1
            else:
                counts["real_claim_strong_support"] += 1
                if verified:
                    counts["verified_real_claim_strong_support"] += 1
                else:
                    counts["unverified_real_claim_strong_support"] += 1
            if verified:
                counts["verified_strong_support"] += 1
            else:
                counts["unverified_strong_support"] += 1
        if norm(ev.get("stance")) in {"contradicts", "refutes", "weakens"} and verified:
            counts["verified_negative_evidence"] += 1
    return counts


def claim_summary(state: Dict[str, Any]) -> Counter:
    counts: Counter = Counter()
    for claim in as_list(state.get("claims")):
        if not isinstance(claim, dict):
            continue
        cid = claim.get("claim_id") or claim.get("id")
        if is_context_claim_id(cid):
            counts["context_claims"] += 1
        else:
            counts["real_claims"] += 1
    return counts


def turn_recovery_summary(turns: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Counter = Counter()
    failure_codes: Counter = Counter()
    patch_sources: Counter = Counter()
    target_types: Counter = Counter()
    target_flaw_turns: List[Dict[str, Any]] = []
    commit_events: List[Dict[str, Any]] = []
    blocked_events: List[Dict[str, Any]] = []
    for idx, turn in enumerate(turns):
        if not isinstance(turn, dict):
            continue
        if turn.get("recovery_push_triggered"):
            counts["recovery_push_triggered"] += 1
        if turn.get("recovery_patch_mode_entered"):
            counts["recovery_patch_mode_entered"] += 1
        if turn.get("recovery_attempted"):
            counts["recovery_attempted"] += 1
        if turn.get("recovery_emitted") or turn.get("recovery_patch_emitted"):
            counts["recovery_emitted"] += 1
        if turn.get("recovery_validated") or turn.get("recovery_patch_validated"):
            counts["recovery_validated"] += 1
        committed = bool(turn.get("recovery_committed") or turn.get("recovery_patch_committed"))
        if committed:
            counts["recovery_committed"] += 1
        if turn.get("recovery_blocked") or turn.get("recovery_patch_blocked"):
            counts["recovery_blocked"] += 1
        if turn.get("negative_recovery_commit"):
            counts["negative_recovery_commit"] += 1
        if turn.get("recovery_consistency_improved"):
            counts["recovery_consistency_improved"] += 1
        code = str(turn.get("recovery_failure_code") or "").strip()
        if code:
            failure_codes[code] += 1
        recovery_seen = any(bool(turn.get(k)) for k in [
            "recovery_push_triggered",
            "recovery_patch_mode_entered",
            "recovery_attempted",
            "recovery_emitted",
            "recovery_patch_emitted",
            "recovery_validated",
            "recovery_patch_validated",
            "recovery_committed",
            "recovery_patch_committed",
            "recovery_blocked",
            "recovery_patch_blocked",
        ])
        source = str(turn.get("recovery_patch_source") or turn.get("recovery_push_source") or "").strip()
        if recovery_seen and source and source != "none":
            patch_sources[source] += 1
        target_type = str(turn.get("recovery_target_type") or "").strip()
        if recovery_seen and target_type:
            target_types[target_type] += 1
        target_flaw_ids = [str(x) for x in as_list(turn.get("target_flaw_ids")) if str(x)]
        if target_flaw_ids:
            counts["turns_with_target_flaw_ids"] += 1
            target_flaw_turns.append({
                "turn_index": idx + 1,
                "final_action_type": turn.get("final_action_type") or turn.get("effective_action_type"),
                "policy_source": turn.get("policy_source"),
                "target_flaw_ids": target_flaw_ids,
                "recovery_emitted": bool(turn.get("recovery_emitted") or turn.get("recovery_patch_emitted")),
                "recovery_committed": committed,
                "failure_code": code,
            })
        if committed:
            commit_events.append({
                "turn_index": idx + 1,
                "target_type": target_type,
                "target_id": turn.get("recovery_target_id") or turn.get("target_id"),
                "new_status": turn.get("new_status"),
                "old_status": turn.get("old_status"),
                "patch_source": source,
                "state_delta": turn.get("recovery_state_delta"),
                "consistency_improved": bool(turn.get("recovery_consistency_improved")),
                "negative_commit": bool(turn.get("negative_recovery_commit")),
            })
        elif turn.get("recovery_blocked") or turn.get("recovery_patch_blocked"):
            blocked_events.append({
                "turn_index": idx + 1,
                "target_type": target_type,
                "target_id": turn.get("recovery_target_id") or turn.get("target_id"),
                "failure_code": code,
                "patch_source": source,
            })
    return {
        "counts": dict(counts),
        "failure_codes": dict(failure_codes),
        "patch_sources": dict(patch_sources),
        "target_types": dict(target_types),
        "target_flaw_turns": target_flaw_turns,
        "commit_events": commit_events,
        "blocked_events": blocked_events,
    }


def aggregate_run(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    aggregate: Counter = Counter()
    decision_counts: Counter = Counter()
    failure_codes: Counter = Counter()
    patch_sources: Counter = Counter()
    target_types: Counter = Counter()
    case_rows: List[Dict[str, Any]] = []
    commit_cases: List[Dict[str, Any]] = []
    target_flaw_cases: List[Dict[str, Any]] = []
    for row in rows:
        pid = row.get("paper_id")
        state = row.get("review_state") or {}
        decision_counts[norm(row.get("final_decision") or state.get("final_decision") or "unknown")] += 1
        es = evidence_summary(state)
        cs = claim_summary(state)
        for k, v in es.items():
            aggregate[k] += v
        for k, v in cs.items():
            aggregate[k] += v
        try:
            view = build_decision_hygiene_view(state)
            hygiene = view.get("decision_hygiene", {}) or {}
        except Exception as exc:  # keep analyzer robust for partially written rows
            view = state
            hygiene = {"error": str(exc)}
            aggregate["decision_hygiene_errors"] += 1
        for key in [
            "grounded_weakness_count",
            "verified_potential_concern_count",
            "potential_concern_count",
            "assessment_limitation_flaw_count",
            "verified_negative_flaw_count",
            "negative_evidence_candidate_count",
            "negative_evidence_linked_to_flaw_count",
            "negative_evidence_unlinked_to_flaw_count",
            "candidate_to_potential_concern_downgrade_count",
        ]:
            aggregate[key] += int(hygiene.get(key) or 0)
        rec = turn_recovery_summary(row.get("turn_logs") or [])
        for k, v in rec["counts"].items():
            aggregate[k] += v
        failure_codes.update(rec["failure_codes"])
        patch_sources.update(rec["patch_sources"])
        target_types.update(rec["target_types"])
        if rec["commit_events"]:
            aggregate["rows_with_recovery_commit"] += 1
            commit_cases.append({"paper_id": pid, "events": rec["commit_events"]})
        if rec["target_flaw_turns"]:
            aggregate["rows_with_target_flaw_turns"] += 1
            target_flaw_cases.append({"paper_id": pid, "events": rec["target_flaw_turns"][:5]})
        case_rows.append({
            "paper_id": pid,
            "final_decision": norm(row.get("final_decision") or state.get("final_decision") or "unknown"),
            "real_claims": cs.get("real_claims", 0),
            "context_claims": cs.get("context_claims", 0),
            "strong_support": es.get("strong_support", 0),
            "verified_strong_support": es.get("verified_strong_support", 0),
            "verified_real_claim_strong_support": es.get("verified_real_claim_strong_support", 0),
            "unverified_strong_support": es.get("unverified_strong_support", 0),
            "context_or_nonreal_strong_support": es.get("context_or_nonreal_strong_support", 0),
            "grounded_weakness": int(hygiene.get("grounded_weakness_count") or 0),
            "verified_potential_concern": int(hygiene.get("verified_potential_concern_count") or 0),
            "potential_concern": int(hygiene.get("potential_concern_count") or 0),
            "assessment_limitation_flaw": int(hygiene.get("assessment_limitation_flaw_count") or 0),
            "verified_negative_flaw": int(hygiene.get("verified_negative_flaw_count") or 0),
            "recovery_committed": rec["counts"].get("recovery_committed", 0),
            "recovery_consistency_improved": rec["counts"].get("recovery_consistency_improved", 0),
            "turns_with_target_flaw_ids": rec["counts"].get("turns_with_target_flaw_ids", 0),
        })
    total_strong = aggregate.get("strong_support", 0)
    aggregate["paper_count"] = len(rows)
    aggregate["verified_strong_support_rate"] = (aggregate.get("verified_strong_support", 0) / total_strong) if total_strong else 0.0
    aggregate["verified_real_strong_support_rate"] = (aggregate.get("verified_real_claim_strong_support", 0) / aggregate.get("real_claim_strong_support", 0)) if aggregate.get("real_claim_strong_support", 0) else 0.0
    return {
        "summary": dict(aggregate),
        "decision_counts": dict(decision_counts),
        "failure_codes": dict(failure_codes),
        "patch_sources": dict(patch_sources),
        "target_types": dict(target_types),
        "case_rows": case_rows,
        "commit_cases": commit_cases,
        "target_flaw_cases": target_flaw_cases,
    }


def compare_summary(current: Dict[str, Any], baseline: Dict[str, Any] | None) -> Dict[str, Any]:
    if not baseline:
        return {}
    keys = sorted(set(current.get("summary", {})) | set(baseline.get("summary", {})))
    out: Dict[str, Any] = {}
    for key in keys:
        cv = current.get("summary", {}).get(key, 0)
        bv = baseline.get("summary", {}).get(key, 0)
        if isinstance(cv, (int, float)) and isinstance(bv, (int, float)):
            out[key] = {"baseline": bv, "current": cv, "delta": cv - bv}
    return out


def write_md(result: Dict[str, Any], compare: Dict[str, Any], args: argparse.Namespace) -> str:
    s = result["summary"]
    lines: List[str] = []
    lines.append("# Recovery Flaw Target v1 Full39 Analysis")
    lines.append("")
    lines.append(f"- 输入: `{args.input}`")
    if args.baseline:
        lines.append(f"- 对照: `{args.baseline}`")
    lines.append(f"- 样本数: {s.get('paper_count', 0)}")
    lines.append("")
    lines.append("## 证据闭环")
    lines.append(f"- strong support: {s.get('strong_support', 0)}")
    lines.append(f"- verified strong support: {s.get('verified_strong_support', 0)} ({s.get('verified_strong_support_rate', 0):.1%})")
    lines.append(f"- real-claim strong support: {s.get('real_claim_strong_support', 0)}")
    lines.append(f"- verified real-claim strong support: {s.get('verified_real_claim_strong_support', 0)} ({s.get('verified_real_strong_support_rate', 0):.1%})")
    lines.append(f"- context/non-real strong support: {s.get('context_or_nonreal_strong_support', 0)}")
    lines.append(f"- quote_id evidence: {s.get('quote_id_evidence', 0)}")
    lines.append("")
    lines.append("## Flaw Lifecycle")
    lines.append(f"- grounded weakness: {s.get('grounded_weakness_count', 0)}")
    lines.append(f"- verified potential concern: {s.get('verified_potential_concern_count', 0)}")
    lines.append(f"- potential concern: {s.get('potential_concern_count', 0)}")
    lines.append(f"- assessment limitation flaw: {s.get('assessment_limitation_flaw_count', 0)}")
    lines.append(f"- verified negative flaw: {s.get('verified_negative_flaw_count', 0)}")
    lines.append(f"- negative evidence linked/unlinked: {s.get('negative_evidence_linked_to_flaw_count', 0)} / {s.get('negative_evidence_unlinked_to_flaw_count', 0)}")
    lines.append("")
    lines.append("## Recovery")
    for key in ["recovery_push_triggered", "recovery_patch_mode_entered", "recovery_attempted", "recovery_emitted", "recovery_validated", "recovery_committed", "recovery_blocked", "rows_with_recovery_commit", "turns_with_target_flaw_ids", "rows_with_target_flaw_turns", "recovery_consistency_improved", "negative_recovery_commit"]:
        lines.append(f"- {key}: {s.get(key, 0)}")
    lines.append("")
    lines.append("### recovery failure codes")
    for key, value in Counter(result.get("failure_codes", {})).most_common():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("### patch source")
    for key, value in Counter(result.get("patch_sources", {})).most_common():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    lines.append("### target types")
    for key, value in Counter(result.get("target_types", {})).most_common():
        lines.append(f"- `{key}`: {value}")
    if compare:
        lines.append("")
        lines.append("## 与对照的关键差异")
        for key in [
            "verified_strong_support", "verified_real_claim_strong_support", "context_or_nonreal_strong_support",
            "grounded_weakness_count", "verified_potential_concern_count", "assessment_limitation_flaw_count",
            "recovery_committed", "rows_with_recovery_commit", "recovery_consistency_improved", "negative_recovery_commit",
            "turns_with_target_flaw_ids", "rows_with_target_flaw_turns",
        ]:
            if key in compare:
                item = compare[key]
                lines.append(f"- `{key}`: {item['baseline']} -> {item['current']} (delta {item['delta']:+})")
    lines.append("")
    lines.append("## 初步判断")
    if s.get("recovery_committed", 0) > 0:
        lines.append("- 本轮自然 full39 已出现 committed recovery，可开始判断 flaw-target recovery 是否真正进入 runtime。")
    else:
        lines.append("- 本轮自然 full39 仍未出现 committed recovery；若 target_flaw_ids 也很少，下一步应继续修 recovery 入口，而不是 validator。")
    if s.get("verified_potential_concern_count", 0) > 0 or s.get("grounded_weakness_count", 0) > 0:
        lines.append("- verified negative evidence 已经能进入 flaw lifecycle，后续重点看是否能从 potential concern 稳定升级为 grounded weakness。")
    else:
        lines.append("- flaw lifecycle 仍缺 verified negative grounding，需要继续加强 Critique Agent 或 negative-evidence binding。")
    lines.append("")
    lines.append("## target flaw 样例")
    for case in result.get("target_flaw_cases", [])[:10]:
        lines.append(f"- `{case['paper_id']}`: {case['events']}")
    lines.append("")
    lines.append("## recovery commit 样例")
    for case in result.get("commit_cases", [])[:10]:
        lines.append(f"- `{case['paper_id']}`: {case['events']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--baseline", default="")
    parser.add_argument("--output-json", default="RECOVERY_FLAW_TARGET_V1_FULL39_ANALYSIS.json")
    parser.add_argument("--output-md", default="RECOVERY_FLAW_TARGET_V1_FULL39_ANALYSIS.md")
    args = parser.parse_args()

    current = aggregate_run(load_jsonl(Path(args.input)))
    baseline_result = aggregate_run(load_jsonl(Path(args.baseline))) if args.baseline else None
    comparison = compare_summary(current, baseline_result)
    payload = {"input": args.input, "baseline": args.baseline, **current, "comparison": comparison}
    Path(args.output_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_md).write_text(write_md(current, comparison, args), encoding="utf-8")


if __name__ == "__main__":
    main()
