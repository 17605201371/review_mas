#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set


ACCEPT_REJECT = {"accept", "reject"}
POSITIVE_STANCES = {"supports", "support", "partially_supports", "partial_support"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")
META_RE = re.compile(
    r"\b(excerpt|truncated|not available|cannot verify|could not verify|fallback|"
    r"recovery failure|system|agent|raw output|parse|complete text|insufficient context)\b",
    re.I,
)


SECTION_PATTERNS = [
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    (
        "result",
        re.compile(
            r"\b(result|evaluation|experiment|benchmark|baseline|outperform|accuracy|"
            r"f1|auc|bleu|rouge|performance|metric|dataset)\b",
            re.I,
        ),
    ),
    (
        "method",
        re.compile(
            r"\b(method|approach|model|framework|algorithm|architecture|training objective|"
            r"loss function|inference|design)\b",
            re.I,
        ),
    ),
    ("abstract", re.compile(r"\babstract\b|\btitle\b", re.I)),
    ("conclusion", re.compile(r"\bconclusion\b|\bdiscussion\b", re.I)),
]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def existing_real_claim_ids(state: Dict[str, Any]) -> Set[str]:
    ids: Set[str] = set()
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        cid = str(claim.get("claim_id") or "").strip()
        if is_real_claim_id(cid):
            ids.add(cid)
    return ids


def pred_decision(row: Dict[str, Any]) -> str:
    value = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    return value if value in ACCEPT_REJECT else "undecided"


def infer_gold(row: Dict[str, Any]) -> str:
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision") or row.get("label"))
    if explicit in ACCEPT_REJECT:
        return explicit
    pred = pred_decision(row)
    try:
        correct = float(row.get("accept_reject_correct", row.get("decision_correct")))
    except (TypeError, ValueError):
        return "unknown"
    if pred not in ACCEPT_REJECT:
        return "unknown"
    return pred if correct >= 0.5 else ("reject" if pred == "accept" else "accept")


def evidence_text(ev: Dict[str, Any]) -> str:
    fields = (
        "source",
        "evidence",
        "support_quality_reason",
        "binding_rationale",
        "rationale",
        "support_source_bucket",
    )
    return " ".join(str(ev.get(key) or "") for key in fields)


def evidence_section(ev: Dict[str, Any]) -> str:
    bucket = norm(ev.get("support_source_bucket"))
    bucket_map = {
        "result_or_experiment": "result",
        "method_or_approach": "method",
        "method_or_design": "method",
        "conclusion_or_discussion": "conclusion",
        "abstract": "abstract",
    }
    if bucket in bucket_map:
        return bucket_map[bucket]
    text = evidence_text(ev)
    for section, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section
    return "unknown"


def is_positive_strong(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) == "strong"


def binding_class(ev: Dict[str, Any], valid_real_ids: Set[str]) -> str:
    claim_id = str(ev.get("claim_id") or "").strip()
    status = norm(ev.get("binding_status"))
    if not claim_id:
        return "unbound"
    if claim_id.startswith(REAL_CLAIM_PREFIX_BLOCKLIST):
        return "fallback_bound"
    if claim_id not in valid_real_ids:
        return "invalid_bound"
    if status in {"invalid_claim_id", "fallback_bound", "unbound"}:
        return status
    return "valid_real"


def independent_group(ev: Dict[str, Any], section: str) -> str:
    text = re.sub(r"\W+", " ", str(ev.get("evidence") or "").lower()).strip()
    digest = hashlib.sha1(" ".join(text.split()[:18]).encode("utf-8")).hexdigest()[:8] if text else "empty"
    return f"{ev.get('claim_id') or ''}:{section}:{digest}"


def flaw_counts(state: Dict[str, Any]) -> Dict[str, int]:
    grounded_major = 0
    confirmed_critical = 0
    meta_flaw = 0
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = norm(flaw.get("status")) or "candidate"
        severity = norm(flaw.get("severity"))
        grounded = bool(flaw.get("evidence_ids") or flaw.get("supporting_evidence_ids") or flaw.get("evidence_id"))
        text = " ".join(str(flaw.get(key) or "") for key in ("title", "description", "source", "reason"))
        if grounded and severity in {"major", "critical"}:
            grounded_major += 1
        if grounded and severity == "critical" and status == "confirmed":
            confirmed_critical += 1
        if META_RE.search(text):
            meta_flaw += 1
    return {
        "grounded_major_flaw_count": grounded_major,
        "confirmed_critical_flaw_count": confirmed_critical,
        "meta_flaw_count": meta_flaw,
    }


def derive_row(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    valid_real_ids = existing_real_claim_ids(state)
    evidence = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]
    total_strong = 0
    valid_real_strong = 0
    invalid_bound_strong = 0
    fallback_bound_strong = 0
    unbound_strong = 0
    non_abstract = 0
    empirical = 0
    method = 0
    independent: Set[str] = set()
    invalid_evidence_ids: List[str] = []
    valid_real_evidence_ids: List[str] = []

    for ev in evidence:
        cls = binding_class(ev, valid_real_ids)
        if cls == "invalid_bound":
            invalid_evidence_ids.append(str(ev.get("evidence_id") or ""))
        if not is_positive_strong(ev):
            continue
        total_strong += 1
        if cls == "valid_real":
            valid_real_strong += 1
            valid_real_evidence_ids.append(str(ev.get("evidence_id") or ""))
            section = evidence_section(ev)
            independent.add(independent_group(ev, section))
            if section not in {"abstract", "unknown"}:
                non_abstract += 1
            if section in {"result", "ablation", "table_or_figure"}:
                empirical += 1
            if section == "method":
                method += 1
        elif cls == "invalid_bound":
            invalid_bound_strong += 1
        elif cls == "fallback_bound":
            fallback_bound_strong += 1
        else:
            unbound_strong += 1

    claims_with_method_plus_result = int(method > 0 and empirical > 0)
    counts = flaw_counts(state)
    return {
        "paper_id": row.get("paper_id"),
        "gold_decision": infer_gold(row),
        "current_decision": pred_decision(row),
        "reward": row.get("reward"),
        "valid_real_claim_count": len(valid_real_ids),
        "final_evidence_total": len(evidence),
        "total_strong_support": total_strong,
        "valid_real_strong_support": valid_real_strong,
        "invalid_bound_strong_support": invalid_bound_strong,
        "fallback_bound_strong_support": fallback_bound_strong,
        "unbound_strong_support": unbound_strong,
        "non_abstract_valid_real_support": non_abstract,
        "empirical_valid_real_support": empirical,
        "method_valid_real_support": method,
        "independent_valid_real_support_groups": len(independent),
        "claims_with_method_plus_result_support": claims_with_method_plus_result,
        "invalid_bound_evidence_count": sum(1 for ev in evidence if binding_class(ev, valid_real_ids) == "invalid_bound"),
        "fallback_bound_evidence_count": sum(1 for ev in evidence if binding_class(ev, valid_real_ids) == "fallback_bound"),
        "unbound_evidence_count": sum(1 for ev in evidence if binding_class(ev, valid_real_ids) == "unbound"),
        "invalid_evidence_ids": [x for x in invalid_evidence_ids if x],
        "valid_real_evidence_ids": [x for x in valid_real_evidence_ids if x],
        "unresolved_count": len(state.get("unresolved_questions", []) or []),
        "evidence_gap_count": len(state.get("evidence_gaps", []) or []),
        "candidate_flaw_count": len(state.get("flaw_candidates", []) or []),
        **counts,
    }


def label_support_quality(row: Dict[str, Any]) -> str:
    if row["confirmed_critical_flaw_count"] > 0:
        return "reject_like_grounded_critical"
    if row["valid_real_strong_support"] >= 2 and row["non_abstract_valid_real_support"] >= 1 and row["independent_valid_real_support_groups"] >= 2:
        return "accept_like_valid_support"
    if row["valid_real_strong_support"] >= 1:
        return "borderline_valid_support"
    if row["total_strong_support"] > row["valid_real_strong_support"]:
        return "not_assessable_invalid_support_only"
    return "reject_like_no_valid_support"


def score(rows: List[Dict[str, Any]], strict_borderline: bool = True) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    pred_accept_ids: List[str] = []
    false_accept_ids: List[str] = []
    recovered_accept_ids: List[str] = []
    false_reject_ids: List[str] = []
    borderline_ids: List[str] = []
    for row in rows:
        label = row["support_quality_label"]
        raw_accept = label == "accept_like_valid_support" or (not strict_borderline and label == "borderline_valid_support")
        pred = "accept" if raw_accept else "reject"
        gold = row["gold_decision"]
        if label == "borderline_valid_support":
            borderline_ids.append(row["paper_id"])
        if pred == "accept":
            pred_accept_ids.append(row["paper_id"])
        if gold == "accept" and pred == "accept":
            tp += 1
            if row["current_decision"] == "reject":
                recovered_accept_ids.append(row["paper_id"])
        elif gold == "accept" and pred == "reject":
            fn += 1
            false_reject_ids.append(row["paper_id"])
        elif gold == "reject" and pred == "accept":
            fp += 1
            false_accept_ids.append(row["paper_id"])
        elif gold == "reject" and pred == "reject":
            tn += 1
    total = len([r for r in rows if r["gold_decision"] in ACCEPT_REJECT]) or 1
    accept_recall = tp / (tp + fn) if tp + fn else 0.0
    reject_recall = tn / (tn + fp) if tn + fp else 0.0
    accept_precision = tp / (tp + fp) if tp + fp else 0.0
    reject_precision = tn / (tn + fn) if tn + fn else 0.0
    f1_accept = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if accept_precision + accept_recall else 0.0
    f1_reject = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if reject_precision + reject_recall else 0.0
    return {
        "accuracy": round((tp + tn) / total, 4),
        "macro_f1": round((f1_accept + f1_reject) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": len(pred_accept_ids),
        "true_accept_count": tp,
        "false_accept_count": fp,
        "false_reject_count": fn,
        "predicted_accept_ids": pred_accept_ids,
        "false_accept_ids": false_accept_ids,
        "recovered_accept_ids": recovered_accept_ids,
        "false_reject_ids": false_reject_ids,
        "borderline_ids": borderline_ids,
    }


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def render_schema() -> str:
    return """# Final-View Invalid Binding Filter v1 Schema

## 定位

本轮是离线 final-view simulation，不改 runtime、不改 ReviewState、不重跑模型。

## 目的

`Evidence ID Turn-Scoping v1` 修复了 evidence_id 覆盖，但暴露出 invalid claim binding。`Evidence Claim Binding Guard v1` 证明 live 清空 invalid claim_id 会伤害 accept 侧 support formation。因此，本轮把 invalid binding 放到 final-view 层处理。

## 过滤规则

- `valid_real`: evidence.claim_id 存在于当前 ReviewState claims，且不是 fallback/general claim。
- `invalid_bound`: evidence.claim_id 不为空，但不存在于当前真实 claims。
- `fallback_bound`: evidence.claim_id 指向 claim-fallback / claim-general。
- `unbound`: evidence.claim_id 为空。

只有 `valid_real` 且 stance 支持、strength strong 的 evidence 进入 accept-like support 计数。

## 边界

该层只用于报告、case table 和 decision simulation。它不修改 live state，也不影响 manager / recovery / evidence formation。
"""


def render_simulation(summary: Dict[str, Any]) -> str:
    rows = [
        ["strict_borderline_as_reject", *[summary["strict"][k] for k in ("accuracy", "macro_f1", "accept_recall", "reject_recall", "predicted_accept_count", "false_accept_count", "true_accept_count")]],
        ["lenient_borderline_as_accept", *[summary["lenient"][k] for k in ("accuracy", "macro_f1", "accept_recall", "reject_recall", "predicted_accept_count", "false_accept_count", "true_accept_count")]],
    ]
    return (
        "# Final-View Invalid Binding Filter v1 Simulation\n\n"
        + md_table(["mapping", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "true_accept"], rows)
        + "\n\n## Aggregate\n\n"
        + md_table(
            ["metric", "value"],
            [
                ["rows", summary["rows"]],
                ["total_strong_support", summary["total_strong_support"]],
                ["valid_real_strong_support", summary["valid_real_strong_support"]],
                ["invalid_bound_strong_support", summary["invalid_bound_strong_support"]],
                ["fallback_bound_strong_support", summary["fallback_bound_strong_support"]],
                ["unbound_strong_support", summary["unbound_strong_support"]],
                ["rows_with_invalid_bound_evidence", summary["rows_with_invalid_bound_evidence"]],
                ["rows_with_valid_2plus_support", summary["rows_with_valid_2plus_support"]],
                ["gold_accept_with_valid_2plus_support", summary["gold_accept_with_valid_2plus_support"]],
            ],
        )
    )


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            [
                row["paper_id"],
                row["gold_decision"],
                row["current_decision"],
                row["support_quality_label"],
                row["valid_real_strong_support"],
                row["invalid_bound_strong_support"],
                row["fallback_bound_strong_support"],
                row["unbound_strong_support"],
                row["non_abstract_valid_real_support"],
                row["empirical_valid_real_support"],
                row["independent_valid_real_support_groups"],
                row["invalid_bound_evidence_count"],
            ]
        )
    return "# Final-View Invalid Binding Filter v1 Case Table\n\n" + md_table(
        [
            "paper_id",
            "gold",
            "current",
            "view_label",
            "valid_real_strong",
            "invalid_strong",
            "fallback_strong",
            "unbound_strong",
            "nonabs_valid",
            "empirical_valid",
            "ind_groups",
            "invalid_evidence",
        ],
        table_rows,
    )


def render_decision(summary: Dict[str, Any]) -> str:
    strict = summary["strict"]
    return f"""# Final-View Invalid Binding Filter v1 Decision

## 结论

**保留为离线 final-view 过滤和论文分析层，不做 runtime mutation。**

本轮验证的是：invalid claim binding 是否可以在 final-view 中被安全剥离，而不是在 live state merge 阶段清空 claim_id。结果支持这个方向。

## 关键结果

- total strong support: `{summary['total_strong_support']}`
- valid real strong support: `{summary['valid_real_strong_support']}`
- invalid-bound strong support: `{summary['invalid_bound_strong_support']}`
- fallback-bound strong support: `{summary['fallback_bound_strong_support']}`
- unbound strong support: `{summary['unbound_strong_support']}`
- rows with invalid-bound evidence: `{summary['rows_with_invalid_bound_evidence']}`
- rows with valid 2+ support: `{summary['rows_with_valid_2plus_support']}`
- gold accept with valid 2+ support: `{summary['gold_accept_with_valid_2plus_support']}`

## Decision simulation 安全下界

- strict accuracy: `{strict['accuracy']}`
- strict macro_f1: `{strict['macro_f1']}`
- strict accept_recall: `{strict['accept_recall']}`
- strict reject_recall: `{strict['reject_recall']}`
- strict predicted_accept_count: `{strict['predicted_accept_count']}`
- strict false_accept_ids: `{strict['false_accept_ids']}`
- strict recovered_accept_ids: `{strict['recovered_accept_ids']}`

## 判断

这层不应直接恢复 accept/reject；它的价值是让主试验指标区分：

1. 真正绑定到当前真实 claim 的 support；
2. 指向不存在 claim 的 invalid-bound support；
3. fallback/unbound support；
4. non-abstract / empirical / independent support。

`Evidence Claim Binding Guard v1` 失败说明不能在 live state 中清掉 invalid claim_id。当前正确做法是：保留 live evidence trajectory，在 final-view / support-quality / criterion-grounded simulation 中过滤不可靠 support。

## 下一步

把该 view 接入统一主试验分析表，而不是 runtime。下一轮应生成 `Mainline-Final-v1` 的最终论文结果包：runtime 指标、support-quality view、criterion-grounding view、case study 和 failure taxonomy。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=Path("outputs/results_main/review_infer/final_view_invalid_binding_filter_v1.json"))
    parser.add_argument("--doc-dir", type=Path, default=Path("docs/experiments/mainline_current"))
    args = parser.parse_args()

    rows = [derive_row(row) for row in load_jsonl(args.input)]
    for row in rows:
        row["support_quality_label"] = label_support_quality(row)
    summary = {
        "input": str(args.input),
        "rows": len(rows),
        "total_strong_support": sum(row["total_strong_support"] for row in rows),
        "valid_real_strong_support": sum(row["valid_real_strong_support"] for row in rows),
        "invalid_bound_strong_support": sum(row["invalid_bound_strong_support"] for row in rows),
        "fallback_bound_strong_support": sum(row["fallback_bound_strong_support"] for row in rows),
        "unbound_strong_support": sum(row["unbound_strong_support"] for row in rows),
        "rows_with_invalid_bound_evidence": sum(row["invalid_bound_evidence_count"] > 0 for row in rows),
        "rows_with_valid_2plus_support": sum(row["valid_real_strong_support"] >= 2 for row in rows),
        "gold_accept_with_valid_2plus_support": sum(row["gold_decision"] == "accept" and row["valid_real_strong_support"] >= 2 for row in rows),
        "strict": score(rows, strict_borderline=True),
        "lenient": score(rows, strict_borderline=False),
        "case_rows": rows,
    }
    write_json(args.output_json, summary)
    write_md(args.doc_dir / "FINAL_VIEW_INVALID_BINDING_FILTER_V1_SCHEMA.md", render_schema())
    write_md(args.doc_dir / "FINAL_VIEW_INVALID_BINDING_FILTER_V1_SIMULATION.md", render_simulation(summary))
    write_md(args.doc_dir / "FINAL_VIEW_INVALID_BINDING_FILTER_V1_CASE_TABLE.md", render_case_table(rows))
    write_md(args.doc_dir / "FINAL_VIEW_INVALID_BINDING_FILTER_V1_DECISION.md", render_decision(summary))
    print(json.dumps({k: summary[k] for k in ("rows", "valid_real_strong_support", "invalid_bound_strong_support", "rows_with_valid_2plus_support")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
