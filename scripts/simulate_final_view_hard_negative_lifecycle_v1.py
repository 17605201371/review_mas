#!/usr/bin/env python3
"""Offline final-view hard-negative and unresolved lifecycle simulation.

This script does not mutate live ReviewState. It derives a decision/report-facing
view from an existing jsonl run and support-quality summary.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple

CLAIM_RE = re.compile(r"claim-[A-Za-z0-9_-]+")
META_RE = re.compile(r"\b(system|fallback|json|parse|parser|raw output|model output|excerpt|could not|unable to|not provided|insufficient context|the user wants me)\b", re.I)
EVIDENCE_GAP_RE = re.compile(r"Claim\s+(claim-[A-Za-z0-9_-]+)\s+lacks grounded supporting evidence", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def is_supporting_evidence(e: Dict[str, Any]) -> bool:
    stance = norm(e.get("stance"))
    strength = norm(e.get("strength"))
    binding = norm(e.get("binding_status"))
    return stance in {"supports", "support", "positive"} and strength in {"strong", "medium"} and binding == "bound_real_claim"


def is_strong_real_support(e: Dict[str, Any]) -> bool:
    return is_supporting_evidence(e) and norm(e.get("strength")) == "strong"


def is_fallback_or_meta_flaw(flaw: Dict[str, Any]) -> bool:
    flaw_id = norm(flaw.get("flaw_id"))
    source = norm(flaw.get("source"))
    status = norm(flaw.get("status"))
    text = " ".join(str(flaw.get(k) or "") for k in ("title", "description", "source", "grounding_status", "hygiene_status_reason")).lower()
    return (
        flaw_id.startswith("flaw-fallback")
        or source in {"fallback", "fallback-extraction", "system_meta"}
        or status in {"downgraded", "retracted"}
        or bool(META_RE.search(text))
        or text.strip().startswith("{")
        or '"flaw_candidates"' in text
    )


def flaw_is_trusted_hard_negative(flaw: Dict[str, Any]) -> bool:
    if is_fallback_or_meta_flaw(flaw):
        return False
    severity = norm(flaw.get("severity"))
    status = norm(flaw.get("status")) or "candidate"
    confidence = flaw.get("confidence")
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.0
    grounded = bool(flaw.get("evidence_ids")) or norm(flaw.get("grounding_status")) in {"grounded", "paper_grounded"}
    if status == "confirmed" and grounded and severity in {"major", "critical"}:
        return True
    if severity == "critical" and grounded and conf >= 0.65:
        return True
    if severity == "major" and grounded and conf >= 0.75:
        return True
    return False


def flaw_is_candidate_only(flaw: Dict[str, Any]) -> bool:
    if is_fallback_or_meta_flaw(flaw):
        return False
    status = norm(flaw.get("status")) or "candidate"
    severity = norm(flaw.get("severity"))
    return status == "candidate" and severity in {"major", "critical"}


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        fields = ["question", "text", "note", "description", "status", "source", "question_id"]
        return " ".join(str(item.get(k) or "") for k in fields).strip()
    return str(item or "").strip()


def item_claim_ids(item: Any) -> List[str]:
    if isinstance(item, dict):
        ids = item.get("related_claim_ids") or item.get("claim_ids") or []
        if isinstance(ids, str):
            ids = [ids]
        found = [str(x) for x in ids if str(x).strip()]
        if found:
            return found
        return CLAIM_RE.findall(item_text(item))
    return CLAIM_RE.findall(item_text(item))


def classify_unresolved(item: Any, supported_claims: set[str]) -> str:
    text = item_text(item)
    low = text.lower()
    status = norm(item.get("status")) if isinstance(item, dict) else "open"
    if status in {"resolved", "closed", "downgraded", "retracted"}:
        return "closed_or_resolved"
    if META_RE.search(text):
        return "meta_or_system"
    claim_ids = set(item_claim_ids(item))
    if claim_ids and claim_ids <= supported_claims:
        return "resolved_by_support"
    # Generic method/result questions without a target are not paper defects yet.
    if not claim_ids and any(k in low for k in ["what are", "whether", "how", "specific", "details", "experimental results", "comparisons", "ablation"]):
        return "open_review_question"
    if claim_ids:
        return "paper_grounded_open"
    return "weak_open"


def classify_gap(gap: Any, supported_claims: set[str]) -> str:
    text = str(gap or "")
    m = EVIDENCE_GAP_RE.search(text)
    if m and m.group(1) in supported_claims:
        return "stale_resolved_by_support"
    if META_RE.search(text):
        return "meta_or_system"
    if m:
        return "active_claim_gap"
    return "weak_or_generic_gap"


def criterion_ratings(report: str) -> Dict[str, str]:
    ratings: Dict[str, str] = {}
    labels = {
        "novelty": "Novelty / Originality",
        "significance": "Significance / Contribution",
        "soundness": "Technical Soundness",
        "empirical": "Empirical Adequacy",
        "clarity": "Clarity / Reproducibility",
    }
    for key, label in labels.items():
        pattern = re.compile(re.escape(label) + r"\s*:\s*([^\n]+)", re.I)
        match = pattern.search(report or "")
        if not match:
            ratings[key] = "missing"
            continue
        text = match.group(1).lower()
        if "not assess" in text or "insufficient" in text:
            ratings[key] = "not_assessable"
        elif "positive" in text or "strong" in text:
            ratings[key] = "positive"
        elif "mixed" in text or "moderate" in text or "partial" in text:
            ratings[key] = "mixed"
        elif "negative" in text or "weak" in text:
            ratings[key] = "negative"
        else:
            ratings[key] = "unknown"
    return ratings


def derive_row(jsonl_row: Dict[str, Any], support_row: Dict[str, Any]) -> Dict[str, Any]:
    state = jsonl_row.get("review_state") or {}
    evidence = [e for e in state.get("evidence_map", []) or [] if isinstance(e, dict)]
    supported_claims = {str(e.get("claim_id")) for e in evidence if is_supporting_evidence(e) and e.get("claim_id")}
    strong_supported_claims = {str(e.get("claim_id")) for e in evidence if is_strong_real_support(e) and e.get("claim_id")}

    unresolved = state.get("unresolved_questions", []) or []
    gaps = state.get("evidence_gaps", []) or []
    flaws = [f for f in state.get("flaw_candidates", []) or [] if isinstance(f, dict)]
    conflicts = state.get("conflict_notes", []) or []

    unresolved_classes = Counter(classify_unresolved(x, supported_claims) for x in unresolved)
    gap_classes = Counter(classify_gap(x, supported_claims) for x in gaps)

    trusted_flaws = [f for f in flaws if flaw_is_trusted_hard_negative(f)]
    candidate_only = [f for f in flaws if flaw_is_candidate_only(f)]
    fallback_meta_flaws = [f for f in flaws if is_fallback_or_meta_flaw(f)]

    fallback_conflicts = 0
    trusted_conflicts = 0
    for c in conflicts:
        text = json.dumps(c, ensure_ascii=False).lower() if isinstance(c, dict) else str(c).lower()
        if "fallback" in text or "downgraded" in text:
            fallback_conflicts += 1
        elif "conflict" in text or "contradict" in text:
            trusted_conflicts += 1

    active_unresolved = unresolved_classes["paper_grounded_open"] + unresolved_classes["weak_open"]
    conservative_unresolved = active_unresolved + unresolved_classes["open_review_question"]
    stale_negative_burden = unresolved_classes["resolved_by_support"] + unresolved_classes["meta_or_system"] + gap_classes["stale_resolved_by_support"] + gap_classes["meta_or_system"] + len(fallback_meta_flaws) + fallback_conflicts

    ratings = criterion_ratings(jsonl_row.get("final_report") or "")
    row = dict(support_row)
    row.update({
        "paper_id": jsonl_row.get("paper_id"),
        "runtime_pred": norm(jsonl_row.get("final_decision")) or "reject",
        "raw_unresolved_count": len(unresolved),
        "active_unresolved_count": active_unresolved,
        "conservative_unresolved_count": conservative_unresolved,
        "resolved_by_support_unresolved_count": unresolved_classes["resolved_by_support"],
        "meta_or_system_unresolved_count": unresolved_classes["meta_or_system"],
        "open_review_question_count": unresolved_classes["open_review_question"],
        "paper_grounded_open_unresolved_count": unresolved_classes["paper_grounded_open"],
        "weak_open_unresolved_count": unresolved_classes["weak_open"],
        "raw_evidence_gap_count": len(gaps),
        "stale_evidence_gap_count": gap_classes["stale_resolved_by_support"],
        "active_evidence_gap_count": gap_classes["active_claim_gap"],
        "weak_or_generic_gap_count": gap_classes["weak_or_generic_gap"],
        "trusted_hard_negative_count": len(trusted_flaws),
        "candidate_only_hard_negative_count": len(candidate_only),
        "fallback_or_meta_flaw_count": len(fallback_meta_flaws),
        "fallback_conflict_count": fallback_conflicts,
        "trusted_conflict_count": trusted_conflicts,
        "stale_negative_burden": stale_negative_burden,
        "supported_claim_count": len(supported_claims),
        "strong_supported_claim_count": len(strong_supported_claims),
        "criterion_ratings": ratings,
    })
    return row


def safe_accept_signal(row: Dict[str, Any]) -> bool:
    return (
        as_int(row, "real_strong_support_total") >= 2
        and as_int(row, "non_abstract_support_total") >= 2
        and as_int(row, "empirical_support_total") >= 1
        and as_int(row, "independent_support_group_total") >= 2
    )


def method_soundness_signal(row: Dict[str, Any]) -> bool:
    ratings = row.get("criterion_ratings") or {}
    return as_int(row, "method_support_total") >= 1 and ratings.get("soundness") in {"positive", "mixed"}


def rule_original(row: Dict[str, Any]) -> str:
    return row.get("runtime_pred") or row.get("original_pred") or "reject"


def rule_lifecycle_strict(row: Dict[str, Any]) -> str:
    if as_int(row, "trusted_hard_negative_count") > 0 or as_int(row, "trusted_conflict_count") > 1:
        return "reject"
    if as_int(row, "candidate_only_hard_negative_count") >= 2:
        return "reject"
    if as_int(row, "active_unresolved_count") >= 2 or as_int(row, "active_evidence_gap_count") > 2:
        return "reject"
    if safe_accept_signal(row) and method_soundness_signal(row):
        return "accept"
    return "reject"


def rule_lifecycle_high_precision(row: Dict[str, Any]) -> str:
    if as_int(row, "trusted_hard_negative_count") > 0 or as_int(row, "candidate_only_hard_negative_count") > 0:
        return "reject"
    if as_int(row, "active_unresolved_count") > 0 or as_int(row, "trusted_conflict_count") > 0:
        return "reject"
    if as_int(row, "active_evidence_gap_count") > 1:
        return "reject"
    if safe_accept_signal(row) and method_soundness_signal(row):
        return "accept"
    return "reject"


def rule_lifecycle_soft(row: Dict[str, Any]) -> str:
    if as_int(row, "trusted_hard_negative_count") > 0:
        return "reject"
    if as_int(row, "candidate_only_hard_negative_count") >= 2:
        return "reject"
    if as_int(row, "active_unresolved_count") >= 2:
        return "reject"
    if safe_accept_signal(row) and (method_soundness_signal(row) or as_int(row, "method_support_total") >= 1):
        return "accept"
    return "reject"


def view_four_way(row: Dict[str, Any]) -> str:
    if as_int(row, "trusted_hard_negative_count") > 0 or as_int(row, "trusted_conflict_count") > 1:
        return "reject_like"
    if as_int(row, "candidate_only_hard_negative_count") >= 2:
        return "reject_like"
    if as_int(row, "active_unresolved_count") >= 2 or as_int(row, "active_evidence_gap_count") > 2:
        return "not_assessable"
    if safe_accept_signal(row) and method_soundness_signal(row) and as_int(row, "candidate_only_hard_negative_count") == 0 and as_int(row, "active_unresolved_count") == 0:
        return "accept_like"
    if safe_accept_signal(row):
        return "borderline_positive"
    return "borderline_insufficient"


def metrics(rows: Sequence[Dict[str, Any]], name: str, fn: Callable[[Dict[str, Any]], str]) -> Dict[str, Any]:
    tp = tn = fp = fnc = 0
    pred_accept_ids: List[str] = []
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    for r in rows:
        gold = r.get("gold_decision")
        pred = fn(r)
        accept_pred = pred == "accept"
        if accept_pred:
            pred_accept_ids.append(r["paper_id"])
        if gold == "accept" and accept_pred:
            tp += 1
            recovered_accept_ids.append(r["paper_id"])
        elif gold == "accept" and not accept_pred:
            fnc += 1
            false_reject_ids.append(r["paper_id"])
        elif gold == "reject" and accept_pred:
            fp += 1
            false_accept_ids.append(r["paper_id"])
        elif gold == "reject" and not accept_pred:
            tn += 1
    total = max(1, tp + tn + fp + fnc)
    acc = (tp + tn) / total
    accept_recall = tp / max(1, tp + fnc)
    reject_recall = tn / max(1, tn + fp)
    accept_precision = tp / max(1, tp + fp)
    reject_precision = tn / max(1, tn + fnc)
    f1_accept = 0 if accept_precision + accept_recall == 0 else 2 * accept_precision * accept_recall / (accept_precision + accept_recall)
    f1_reject = 0 if reject_precision + reject_recall == 0 else 2 * reject_precision * reject_recall / (reject_precision + reject_recall)
    return {
        "rule": name,
        "accuracy": round(acc, 4),
        "macro_f1": round((f1_accept + f1_reject) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": len(pred_accept_ids),
        "false_accept_ids": false_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_reject_ids": false_reject_ids,
        "predicted_accept_ids": pred_accept_ids,
    }


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def aggregate(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    keys = [
        "raw_unresolved_count", "active_unresolved_count", "conservative_unresolved_count",
        "resolved_by_support_unresolved_count", "meta_or_system_unresolved_count", "open_review_question_count",
        "raw_evidence_gap_count", "stale_evidence_gap_count", "active_evidence_gap_count",
        "trusted_hard_negative_count", "candidate_only_hard_negative_count", "fallback_or_meta_flaw_count",
        "fallback_conflict_count", "trusted_conflict_count", "stale_negative_burden",
    ]
    agg = {k: sum(as_int(r, k) for r in rows) for k in keys}
    agg["rows"] = len(rows)
    agg["gold_accept_count"] = sum(1 for r in rows if r.get("gold_decision") == "accept")
    agg["gold_reject_count"] = sum(1 for r in rows if r.get("gold_decision") == "reject")
    agg["four_way_counts"] = dict(Counter(view_four_way(r) for r in rows))
    return agg


def render_schema() -> str:
    return """# Final-View Hard-Negative / Unresolved Lifecycle Schema v1

本脚本只做离线派生视图，不改 runtime、不改 live `ReviewState`。

## 派生字段

- `active_unresolved_count`：仍可能代表论文风险的 open unresolved。
- `resolved_by_support_unresolved_count`：相关 claim 已有 real support，但 unresolved 仍未关闭。
- `meta_or_system_unresolved_count`：包含 fallback、JSON、excerpt、system limitation 等系统侧信息。
- `open_review_question_count`：没有绑定明确 paper defect 的普通待查问题。
- `stale_evidence_gap_count`：claim 已有 support，但仍保留 `lacks grounded evidence` gap。
- `trusted_hard_negative_count`：非 fallback/meta，且 grounded/confirmed/confidence 足够的 major/critical flaw。
- `candidate_only_hard_negative_count`：仍只是 candidate 的 major/critical flaw，不应直接等同 confirmed weakness。
- `fallback_or_meta_flaw_count`：fallback、malformed JSON 或 system-meta flaw。

## 原则

这些字段用于 final decision/report 前的 derived view。它们不能写回 live state，也不能改变 manager/recovery 轨迹。
"""


def render_audit(rows: Sequence[Dict[str, Any]], agg: Dict[str, Any]) -> str:
    top = [[k, v] for k, v in agg.items() if k != "four_way_counts"]
    accept_rows = [r for r in rows if r.get("gold_decision") == "accept"]
    accept_table = []
    for r in accept_rows:
        accept_table.append([
            r["paper_id"], r["runtime_pred"], r["real_strong_support_total"], r["method_support_total"],
            r["active_unresolved_count"], r["resolved_by_support_unresolved_count"], r["stale_evidence_gap_count"],
            r["trusted_hard_negative_count"], view_four_way(r),
        ])
    return "# Final-View Hard-Negative / Unresolved Lifecycle Audit v1\n\n## 汇总\n\n" + md_table(["metric", "value"], top) + "\n\n## Gold accept case table\n\n" + md_table(["paper_id", "runtime", "real", "method", "active_unresolved", "resolved_unresolved", "stale_gap", "trusted_hard_neg", "view"], accept_table)


def render_simulation(scores: Sequence[Dict[str, Any]], agg: Dict[str, Any]) -> str:
    rows = []
    for s in scores:
        rows.append([s["rule"], s["accuracy"], s["macro_f1"], s["accept_recall"], s["reject_recall"], s["predicted_accept_count"], ", ".join(s["false_accept_ids"]) or "无", ", ".join(s["recovered_accept_ids"]) or "无"])
    text = "# Final-View Hard-Negative / Unresolved Lifecycle Simulation v1\n\n"
    text += md_table(["rule", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"], rows)
    text += "\n\n## Four-way derived view\n\n"
    text += md_table(["view", "count"], sorted(agg["four_way_counts"].items()))
    return text


def render_casebook(rows: Sequence[Dict[str, Any]]) -> str:
    table = []
    for r in rows:
        if r.get("gold_decision") == "accept" or view_four_way(r) in {"accept_like", "borderline_positive"}:
            table.append([
                r["paper_id"], r.get("gold_decision"), r["runtime_pred"], view_four_way(r),
                r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["method_support_total"],
                r["active_unresolved_count"], r["trusted_hard_negative_count"], r["candidate_only_hard_negative_count"], r["stale_negative_burden"],
            ])
    return "# Final-View Lifecycle Casebook v1\n\n" + md_table(["paper_id", "gold", "runtime", "view", "real", "nonabs", "empirical", "method", "active_unresolved", "trusted_hard_neg", "candidate_hard_neg", "stale_burden"], table)


def render_decision(agg: Dict[str, Any], scores: Sequence[Dict[str, Any]]) -> str:
    strict = next(s for s in scores if s["rule"] == "lifecycle_strict")
    high_precision = next(s for s in scores if s["rule"] == "lifecycle_high_precision")
    soft = next(s for s in scores if s["rule"] == "lifecycle_soft")
    return f"""# Final-View Hard-Negative / Unresolved Lifecycle Decision v1

## 结论

离线 simulation 支持继续推进 final-view lifecycle 方向，但当前不应 runtime 化，也不应放宽 accept-like。

关键原因：

- raw unresolved 总量为 `{agg['raw_unresolved_count']}`，派生后 active unresolved 仍为 `{agg['active_unresolved_count']}`，说明确实存在大量未关闭/未分层的 negative burden。
- stale / meta / fallback burden 为 `{agg['stale_negative_burden']}`，说明 final report/decision 前有必要做 derived cleanup。
- strict lifecycle rule 恢复 accept：`{', '.join(strict['recovered_accept_ids']) or '无'}`，false accept：`{', '.join(strict['false_accept_ids']) or '无'}`。
- high-precision lifecycle rule 恢复 accept：`{', '.join(high_precision['recovered_accept_ids']) or '无'}`，false accept：`{', '.join(high_precision['false_accept_ids']) or '无'}`。
- soft lifecycle rule 恢复 accept：`{', '.join(soft['recovered_accept_ids']) or '无'}`，false accept：`{', '.join(soft['false_accept_ids']) or '无'}`。

## 下一步

下一步不直接改 live state。建议实现一个更精细的 **Final-View Unresolved Classifier v1**，只服务 final decision/report derived view：

1. 将 `open_review_question`、`meta_or_system`、`resolved_by_support` 从 paper weakness 中分离。
2. 将多项 `candidate_only_hard_negative` 作为 `reject_like` 或 `not_assessable`，不能忽略。
3. 只让 `paper_grounded_open` 和可信 confirmed/grounded flaw 进入强 reject blocker。
4. 对 `not_assessable` 单独报告，不映射成 reject 或 accept。

## 暂不做

- 不调 runtime accept/reject 阈值。
- 不恢复 sticky/throttle/progression gate。
- 不把 hygiene 放入 `_refresh_state_consistency()`。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True, type=Path)
    parser.add_argument("--support-summary", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--doc-dir", required=True, type=Path)
    parser.add_argument("--doc-prefix", default="FINAL_VIEW_LIFECYCLE_V1")
    args = parser.parse_args()

    jsonl_rows = {r.get("paper_id"): r for r in load_jsonl(args.jsonl)}
    support_rows = load_json(args.support_summary)["rows"]
    rows = [derive_row(jsonl_rows[r["paper_id"]], r) for r in support_rows if r.get("paper_id") in jsonl_rows]
    agg = aggregate(rows)
    scores = [
        metrics(rows, "runtime_current", rule_original),
        metrics(rows, "lifecycle_strict", rule_lifecycle_strict),
        metrics(rows, "lifecycle_high_precision", rule_lifecycle_high_precision),
        metrics(rows, "lifecycle_soft", rule_lifecycle_soft),
    ]
    output = {"jsonl": str(args.jsonl), "support_summary": str(args.support_summary), "aggregate": agg, "scores": scores, "rows": rows}
    write_json(args.output_json, output)
    prefix = args.doc_prefix
    write_md(args.doc_dir / f"{prefix}_SCHEMA.md", render_schema())
    write_md(args.doc_dir / f"{prefix}_AUDIT.md", render_audit(rows, agg))
    write_md(args.doc_dir / f"{prefix}_SIMULATION.md", render_simulation(scores, agg))
    write_md(args.doc_dir / f"{prefix}_CASEBOOK.md", render_casebook(rows))
    write_md(args.doc_dir / f"{prefix}_DECISION.md", render_decision(agg, scores))
    print(json.dumps({"output_json": str(args.output_json), "aggregate": agg, "scores": scores}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
