#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SUPPORT_STANCES = {"supports", "partially_supports"}
META_RE = re.compile(
    r"\b(excerpt|truncat|provided text|provided paper|full text|not provided|missing section|missing results section|"
    r"insufficient excerpt|current evidence slice|current text|context|cannot verify|unable to verify|"
    r"fallback|malformed|raw output|agent/meta|system|review limitation|not assessable|cuts off|cut off)\b",
    re.I,
)
EXCERPT_RE = re.compile(r"\b(excerpt|truncat|provided text|provided paper|full text|cuts off|cut off|abstract is incomplete|terminates abruptly)\b", re.I)
FALLBACK_RE = re.compile(r"\b(fallback|malformed|raw output|could not recover|agent/meta)\b", re.I)
SYSTEM_RE = re.compile(r"\b(system|review limitation|not assessable|current evidence slice|cannot verify|unable to verify|context limitation)\b", re.I)
PAPER_GROUNDING_RE = re.compile(
    r"\b(method|mechanism|algorithm|experiment|evaluation|baseline|dataset|metric|result|table|figure|ablation|proof|theorem|architecture|hyperparameter)\b",
    re.I,
)
SUPPORT_BUCKET_RE = {
    "abstract": re.compile(r"abstract", re.I),
    "method": re.compile(r"\b(method|approach|model|framework|algorithm|architecture)\b", re.I),
    "empirical": re.compile(r"\b(experiment|evaluation|result|baseline|dataset|metric|ablation)\b", re.I),
    "table_or_figure": re.compile(r"\b(table|figure|fig\.)\b", re.I),
}


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def infer_gold(row: Dict[str, Any]) -> str:
    explicit = norm(row.get("ground_truth_decision") or row.get("gold_decision"))
    if explicit in {"accept", "reject"}:
        return explicit
    pred = norm(row.get("final_decision") or (row.get("review_state") or {}).get("final_decision"))
    corr = row.get("accept_reject_correct")
    if pred in {"accept", "reject"} and corr in {0, 0.0, 1, 1.0}:
        return pred if corr in {1, 1.0} else ("accept" if pred == "reject" else "reject")
    return "unknown"


def is_real_claim(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and "fallback" not in cid and "general" not in cid


def evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(ev.get("evidence_id") or ""): ev for ev in state.get("evidence_map", []) or [] if ev.get("evidence_id")}


def evidence_support_bucket(ev: Dict[str, Any]) -> str:
    text = " ".join(str(ev.get(key, "")) for key in ["source", "support_source_bucket", "support_quality", "evidence"])
    for bucket, pattern in SUPPORT_BUCKET_RE.items():
        if pattern.search(text):
            return bucket
    return "unknown"


def support_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    counts = Counter()
    per_bucket = Counter()
    for ev in state.get("evidence_map", []) or []:
        stance = norm(ev.get("stance"))
        strength = norm(ev.get("strength"))
        claim_id = ev.get("claim_id")
        if stance in SUPPORT_STANCES and strength == "strong":
            if is_real_claim(claim_id):
                counts["real_strong_support"] += 1
                bucket = evidence_support_bucket(ev)
                per_bucket[bucket] += 1
                if bucket != "abstract":
                    counts["nonabstract_strong_support"] += 1
                if bucket in {"empirical", "table_or_figure"}:
                    counts["empirical_strong_support"] += 1
            else:
                counts["fallback_strong_support"] += 1
        if stance in SUPPORT_STANCES and strength == "medium" and is_real_claim(claim_id):
            counts["real_medium_support"] += 1
    counts["support_buckets"] = dict(per_bucket)
    return dict(counts)


def issue_text(issue: Any) -> str:
    if isinstance(issue, dict):
        fields = [
            issue.get("title"), issue.get("description"), issue.get("flaw"), issue.get("question"),
            issue.get("rationale"), issue.get("status"), issue.get("severity"),
        ]
        return " ".join(str(x or "") for x in fields)
    return str(issue or "")


def evidence_ids(issue: Any) -> List[str]:
    if not isinstance(issue, dict):
        return []
    ids = issue.get("evidence_ids") or issue.get("supporting_evidence_ids") or []
    if isinstance(ids, str):
        ids = [ids]
    return [str(x) for x in ids if x]


def related_claim_ids(issue: Any) -> List[str]:
    if not isinstance(issue, dict):
        return []
    ids = issue.get("related_claim_ids") or issue.get("claim_ids") or issue.get("target_claim_ids") or []
    if isinstance(ids, str):
        ids = [ids]
    return [str(x) for x in ids if x]


def evidence_is_real_grounded(ids: Iterable[str], ev_map: Dict[str, Dict[str, Any]]) -> bool:
    for evid in ids:
        ev = ev_map.get(str(evid))
        if not ev:
            continue
        if norm(ev.get("source")) == "fallback-extraction":
            continue
        if is_real_claim(ev.get("claim_id")):
            return True
    return False


def classify_flaw(flaw: Dict[str, Any], ev_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    text = issue_text(flaw)
    ids = evidence_ids(flaw)
    grounded = evidence_is_real_grounded(ids, ev_map)
    status = norm(flaw.get("status")) or "candidate"
    severity = norm(flaw.get("severity")) or "unknown"
    category = "ungrounded_candidate"
    reasons: List[str] = []
    if text.strip().startswith("{") or "\"flaw_candidates\"" in text:
        category = "fallback_or_malformed_artifact"
        reasons.append("malformed_json_or_fallback_artifact")
    elif FALLBACK_RE.search(text):
        category = "fallback_or_malformed_artifact"
        reasons.append("fallback_or_raw_output_language")
    elif EXCERPT_RE.search(text):
        category = "excerpt_limitation"
        reasons.append("excerpt_or_truncation_language")
    elif SYSTEM_RE.search(text):
        category = "system_meta_limitation"
        reasons.append("system_or_context_limitation_language")
    elif grounded and status == "confirmed":
        category = "grounded_confirmed_flaw"
        reasons.append("confirmed_and_real_evidence_bound")
    elif grounded:
        category = "grounded_candidate"
        reasons.append("candidate_with_real_evidence_bound")
    elif PAPER_GROUNDING_RE.search(text) and ids:
        category = "weakly_grounded_candidate"
        reasons.append("paper_criterion_language_but_evidence_not_real_bound")
    else:
        category = "ungrounded_candidate"
        reasons.append("no_real_evidence_binding")
    return {
        "flaw_id": flaw.get("flaw_id") or flaw.get("id") or "",
        "title": flaw.get("title") or "",
        "severity": severity,
        "status": status,
        "evidence_ids": ids,
        "related_claim_ids": related_claim_ids(flaw),
        "category": category,
        "reasons": reasons,
        "is_major_or_critical": severity in {"major", "critical"},
        "is_confirmed": status == "confirmed",
        "is_strong_reject_blocker_original": severity in {"major", "critical"},
        "is_strong_reject_blocker_view": category == "grounded_confirmed_flaw" and severity in {"major", "critical"},
        "excerpt": text[:260],
    }


def classify_unresolved(item: Any, ev_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    text = issue_text(item)
    ids = evidence_ids(item)
    category = "paper_grounded_unresolved"
    reasons: List[str] = []
    if FALLBACK_RE.search(text):
        category = "fallback_or_malformed_artifact"
        reasons.append("fallback_language")
    elif EXCERPT_RE.search(text):
        category = "excerpt_limitation"
        reasons.append("excerpt_or_truncation_language")
    elif SYSTEM_RE.search(text):
        category = "system_meta_limitation"
        reasons.append("system_or_context_limitation_language")
    elif not related_claim_ids(item) and not ids:
        category = "ungrounded_unresolved"
        reasons.append("no_claim_or_evidence_binding")
    elif ids and not evidence_is_real_grounded(ids, ev_map):
        category = "weakly_grounded_unresolved"
        reasons.append("evidence_ids_not_real_bound")
    else:
        reasons.append("claim_or_real_evidence_bound")
    return {
        "question_id": item.get("question_id") if isinstance(item, dict) else "",
        "category": category,
        "reasons": reasons,
        "related_claim_ids": related_claim_ids(item),
        "evidence_ids": ids,
        "excerpt": text[:240],
    }


def classify_gap(item: Any) -> Dict[str, Any]:
    text = issue_text(item)
    category = "paper_evidence_gap"
    reasons: List[str] = []
    if FALLBACK_RE.search(text):
        category = "fallback_or_malformed_artifact"
        reasons.append("fallback_language")
    elif EXCERPT_RE.search(text):
        category = "excerpt_limitation"
        reasons.append("excerpt_or_truncation_language")
    elif SYSTEM_RE.search(text):
        category = "system_meta_limitation"
        reasons.append("system_or_context_limitation_language")
    else:
        reasons.append("paper_gap_language")
    return {"category": category, "reasons": reasons, "excerpt": text[:220]}


def aggregate_categories(items: Iterable[Dict[str, Any]]) -> Counter:
    return Counter(item.get("category") or "unknown" for item in items)


def derived_decision(row: Dict[str, Any], flaw_items: List[Dict[str, Any]], unresolved_items: List[Dict[str, Any]], support: Dict[str, Any]) -> Dict[str, Any]:
    grounded_confirmed_major = sum(1 for item in flaw_items if item["is_strong_reject_blocker_view"])
    grounded_candidate_major = sum(1 for item in flaw_items if item["category"] == "grounded_candidate" and item["is_major_or_critical"])
    paper_unresolved = sum(1 for item in unresolved_items if item["category"] in {"paper_grounded_unresolved", "weakly_grounded_unresolved"})
    meta_negative = sum(1 for item in flaw_items if item["category"] in {"excerpt_limitation", "system_meta_limitation", "fallback_or_malformed_artifact"})
    meta_negative += sum(1 for item in unresolved_items if item["category"] in {"excerpt_limitation", "system_meta_limitation", "fallback_or_malformed_artifact"})
    real_strong = int(support.get("real_strong_support", 0) or 0)
    nonabstract = int(support.get("nonabstract_strong_support", 0) or 0)
    empirical = int(support.get("empirical_strong_support", 0) or 0)
    real_medium = int(support.get("real_medium_support", 0) or 0)

    if grounded_confirmed_major > 0:
        label = "reject_like"
        reason = "grounded_confirmed_major_or_critical_flaw"
    elif real_strong >= 2 and nonabstract >= 1 and grounded_candidate_major == 0 and paper_unresolved <= 3:
        label = "accept_like"
        reason = "real_nonabstract_support_without_grounded_blocker"
    elif real_strong >= 2 and grounded_candidate_major == 0 and paper_unresolved <= 3:
        label = "borderline"
        reason = "abstract_or_low_depth_support_only"
    elif real_medium >= 2 and grounded_candidate_major == 0 and paper_unresolved <= 3:
        label = "borderline"
        reason = "medium_support_only_requires_human_review"
    elif meta_negative > 0 and grounded_confirmed_major == 0 and grounded_candidate_major == 0:
        label = "not_assessable"
        reason = "negative_burden_is_meta_or_excerpt_limitation"
    else:
        label = "reject_like"
        reason = "insufficient_support_or_grounded_candidate_burden"
    return {
        "derived_label": label,
        "derived_reason": reason,
        "grounded_confirmed_major_flaw_count": grounded_confirmed_major,
        "grounded_candidate_major_flaw_count": grounded_candidate_major,
        "paper_grounded_unresolved_count": paper_unresolved,
        "meta_negative_burden_count": meta_negative,
    }


def analyze(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    aggregate = Counter()
    case_rows: List[Dict[str, Any]] = []
    flaw_examples: List[Dict[str, Any]] = []
    for row in rows:
        state = row.get("review_state") or {}
        ev_map = evidence_lookup(state)
        support = support_summary(state)
        flaw_items = [classify_flaw(flaw, ev_map) for flaw in state.get("flaw_candidates", []) or []]
        unresolved_items = [classify_unresolved(item, ev_map) for item in state.get("unresolved_questions", []) or []]
        gap_items = [classify_gap(item) for item in state.get("evidence_gaps", []) or []]
        flaw_cats = aggregate_categories(flaw_items)
        unresolved_cats = aggregate_categories(unresolved_items)
        gap_cats = aggregate_categories(gap_items)
        derived = derived_decision(row, flaw_items, unresolved_items, support)
        pred = norm(row.get("final_decision") or state.get("final_decision")) or "unknown"
        gold = infer_gold(row)
        aggregate["rows"] += 1
        aggregate[f"gold_{gold}"] += 1
        aggregate[f"original_pred_{pred}"] += 1
        aggregate[f"derived_{derived['derived_label']}"] += 1
        aggregate[f"original_{gold}->{pred}"] += 1
        aggregate[f"derived_{gold}->{derived['derived_label']}"] += 1
        aggregate["real_strong_support_total"] += int(support.get("real_strong_support", 0) or 0)
        aggregate["nonabstract_strong_support_total"] += int(support.get("nonabstract_strong_support", 0) or 0)
        aggregate["real_medium_support_total"] += int(support.get("real_medium_support", 0) or 0)
        for key, value in flaw_cats.items():
            aggregate[f"flaw_{key}"] += value
        for key, value in unresolved_cats.items():
            aggregate[f"unresolved_{key}"] += value
        for key, value in gap_cats.items():
            aggregate[f"gap_{key}"] += value
        if len(flaw_examples) < 20:
            for item in flaw_items:
                if item["category"] in {"excerpt_limitation", "system_meta_limitation", "fallback_or_malformed_artifact"} and len(flaw_examples) < 20:
                    flaw_examples.append({"paper_id": row.get("paper_id"), **item})
        case_rows.append({
            "paper_id": row.get("paper_id"),
            "gold_decision": gold,
            "original_decision": pred,
            "derived_label": derived["derived_label"],
            "derived_reason": derived["derived_reason"],
            **support,
            **derived,
            "flaw_count": len(flaw_items),
            "flaw_categories": dict(flaw_cats),
            "unresolved_count": len(unresolved_items),
            "unresolved_categories": dict(unresolved_cats),
            "gap_count": len(gap_items),
            "gap_categories": dict(gap_cats),
            "top_flaws": flaw_items[:3],
            "top_unresolved": unresolved_items[:3],
            "reward": row.get("reward"),
        })
    return {"aggregate": dict(aggregate), "case_rows": case_rows, "meta_flaw_examples": flaw_examples}


def metric_summary(case_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    gold_binary = [row["gold_decision"] for row in case_rows]
    original = [row["original_decision"] for row in case_rows]
    strict = ["accept" if row["derived_label"] == "accept_like" else "reject" for row in case_rows]
    review_aware = ["accept" if row["derived_label"] == "accept_like" else ("borderline" if row["derived_label"] in {"borderline", "not_assessable"} else "reject") for row in case_rows]

    def binary_metrics(preds: List[str]) -> Dict[str, Any]:
        tp = sum(1 for g, p in zip(gold_binary, preds) if g == "accept" and p == "accept")
        tn = sum(1 for g, p in zip(gold_binary, preds) if g == "reject" and p == "reject")
        fp = sum(1 for g, p in zip(gold_binary, preds) if g == "reject" and p == "accept")
        fn = sum(1 for g, p in zip(gold_binary, preds) if g == "accept" and p == "reject")
        acc = (tp + tn) / len(preds) if preds else 0
        accept_recall = tp / (tp + fn) if (tp + fn) else 0
        reject_recall = tn / (tn + fp) if (tn + fp) else 0
        accept_precision = tp / (tp + fp) if (tp + fp) else 0
        reject_precision = tn / (tn + fn) if (tn + fn) else 0
        accept_f1 = 2 * accept_precision * accept_recall / (accept_precision + accept_recall) if (accept_precision + accept_recall) else 0
        reject_f1 = 2 * reject_precision * reject_recall / (reject_precision + reject_recall) if (reject_precision + reject_recall) else 0
        return {
            "accuracy": acc,
            "accept_recall": accept_recall,
            "reject_recall": reject_recall,
            "macro_f1": (accept_f1 + reject_f1) / 2,
            "predicted_accept_count": sum(1 for p in preds if p == "accept"),
            "false_accept_ids": [row["paper_id"] for row, p in zip(case_rows, preds) if row["gold_decision"] == "reject" and p == "accept"],
            "recovered_accept_ids": [row["paper_id"] for row, p in zip(case_rows, preds) if row["gold_decision"] == "accept" and p == "accept"],
        }

    return {
        "original_binary": binary_metrics(original),
        "derived_strict_accept_like_only": binary_metrics(strict),
        "derived_label_counts": dict(Counter(row["derived_label"] for row in case_rows)),
        "borderline_or_not_assessable_ids": [row["paper_id"] for row in case_rows if row["derived_label"] in {"borderline", "not_assessable"}],
        "review_aware_labels": dict(Counter(review_aware)),
    }


def write_schema(path: Path) -> None:
    text = """# Final-View Flaw Lifecycle Schema v1

## 目标

本 schema 只用于 final-view / offline 派生视图，不改 live `ReviewState`，不改变模型推理轨迹，也不直接调 final decision 阈值。

## Flaw 分类

- `grounded_confirmed_flaw`: 已确认、major/critical 且绑定真实 evidence 的论文缺陷，可作为强 reject blocker。
- `grounded_candidate`: 绑定真实 evidence，但仍是 candidate/open 的疑点。可以进入 Potential Concerns，不应等同 confirmed weakness。
- `weakly_grounded_candidate`: 有 paper/criterion 语言或 evidence id，但没有真实 evidence binding。需要人工复核。
- `ungrounded_candidate`: 没有 evidence/claim grounding 的候选疑点，不应作为强 reject blocker。
- `excerpt_limitation`: 截断、上下文不足、只看到 abstract 等导致的限制，应进入 Review Limitations / Not Assessable。
- `system_meta_limitation`: 系统无法验证、当前 evidence slice 不足等系统侧限制，不应写成论文缺陷。
- `fallback_or_malformed_artifact`: fallback、malformed JSON、raw output 等 artifact，不应进入 Key Weakness。

## Decision view 原则

- 只有 `grounded_confirmed_flaw` 且 severity 为 major/critical 时，才作为强 reject blocker。
- meta / excerpt / fallback 类问题不消失，但转入 `Review Limitations`，不作为论文 weakness。
- accept-like 仍需要真实、非 abstract 的 positive support；本视图不把 abstract-only support 直接升级为 accept。
"""
    path.write_text(text, encoding="utf-8")


def write_audit(payload: Dict[str, Any], path: Path) -> None:
    agg = payload["aggregate"]
    lines = ["# Final-View Flaw Meta-Leakage Audit v1", "", "## Aggregate", "", "| metric | value |", "|---|---:|"]
    keys = [k for k in sorted(agg) if k.startswith(("flaw_", "unresolved_", "gap_"))]
    for key in keys:
        lines.append(f"| `{key}` | {agg[key]} |")
    lines += ["", "## Meta / Artifact Flaw Examples", "", "| paper_id | category | severity | status | title | excerpt |", "|---|---|---|---|---|---|"]
    for item in payload["meta_flaw_examples"]:
        title = str(item.get("title") or "").replace("|", "/")[:80]
        excerpt = str(item.get("excerpt") or "").replace("|", "/").replace("\n", " ")[:180]
        lines.append(f"| {item['paper_id']} | {item['category']} | {item['severity']} | {item['status']} | {title} | {excerpt} |")
    lines += ["", "## 结论", "", "当前 final view 中存在大量 excerpt / system / fallback / malformed artifact 类负面项。这些项适合进入 Review Limitations 或 Potential Concerns，不应直接作为 confirmed paper weakness。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_simulation(payload: Dict[str, Any], path: Path) -> None:
    metrics = payload["metrics"]
    lines = ["# Final-View Flaw Lifecycle Simulation v1", "", "## Decision Health", "", "| metric | original | derived strict |", "|---|---:|---:|"]
    for key in ["accuracy", "accept_recall", "reject_recall", "macro_f1", "predicted_accept_count"]:
        o = metrics["original_binary"].get(key, 0)
        d = metrics["derived_strict_accept_like_only"].get(key, 0)
        if isinstance(o, float) or isinstance(d, float):
            lines.append(f"| `{key}` | {float(o):.4f} | {float(d):.4f} |")
        else:
            lines.append(f"| `{key}` | {o} | {d} |")
    lines += ["", "## Derived Label Counts", "", "| label | count |", "|---|---:|"]
    for label, count in metrics["derived_label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines += ["", "## Recovered / False Accepts", "", f"- recovered_accept_ids: `{metrics['derived_strict_accept_like_only']['recovered_accept_ids']}`", f"- false_accept_ids: `{metrics['derived_strict_accept_like_only']['false_accept_ids']}`", "", "## 解释", "", "这个 simulation 不是最终 decision rule。它验证的是：当 meta/excerpt/fallback artifact 不再作为强 reject blocker 时，系统是否能更诚实地区分 accept-like、reject-like、borderline 与 not-assessable。若 accept-like 仍然很少，说明 positive support formation 仍是瓶颈；若 not-assessable 很多，说明 final report 应明确暴露审稿上下文限制，而不是包装成论文缺陷。"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_case_table(payload: Dict[str, Any], path: Path) -> None:
    lines = ["# Final-View Flaw Lifecycle Case Table v1", "", "| paper_id | gold | original | derived | reason | real strong | nonabs strong | real medium | grounded confirmed major | grounded candidate major | meta burden | flaw cats | unresolved cats |", "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for row in payload["case_rows"]:
        flaw_cats = ", ".join(f"{k}:{v}" for k, v in row["flaw_categories"].items())
        unresolved_cats = ", ".join(f"{k}:{v}" for k, v in row["unresolved_categories"].items())
        lines.append(
            f"| {row['paper_id']} | {row['gold_decision']} | {row['original_decision']} | {row['derived_label']} | {row['derived_reason']} | "
            f"{row.get('real_strong_support', 0)} | {row.get('nonabstract_strong_support', 0)} | {row.get('real_medium_support', 0)} | "
            f"{row['grounded_confirmed_major_flaw_count']} | {row['grounded_candidate_major_flaw_count']} | {row['meta_negative_burden_count']} | {flaw_cats} | {unresolved_cats} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_decision(payload: Dict[str, Any], path: Path) -> None:
    metrics = payload["metrics"]
    agg = payload["aggregate"]
    text = f"""# Final-View Flaw Lifecycle Decision v1

## 结论

`Final-View Flaw Lifecycle / Meta-Leakage Simulation v1` 值得保留为离线 derived-view 分析层，但暂时不要接入 live state，也不要作为新的 accept/reject 硬规则。

## 关键结果

- 原始 fulltest39: `predicted_accept_count={metrics['original_binary']['predicted_accept_count']}`, `accept_recall={metrics['original_binary']['accept_recall']:.4f}`, `reject_recall={metrics['original_binary']['reject_recall']:.4f}`, `macro_f1={metrics['original_binary']['macro_f1']:.4f}`。
- derived strict: `predicted_accept_count={metrics['derived_strict_accept_like_only']['predicted_accept_count']}`, `accept_recall={metrics['derived_strict_accept_like_only']['accept_recall']:.4f}`, `reject_recall={metrics['derived_strict_accept_like_only']['reject_recall']:.4f}`, `macro_f1={metrics['derived_strict_accept_like_only']['macro_f1']:.4f}`。
- derived labels: `{metrics['derived_label_counts']}`。
- flaw meta/artifact burden: excerpt/system/fallback/malformed 相关项大量存在，例如 `flaw_excerpt_limitation={agg.get('flaw_excerpt_limitation', 0)}`, `flaw_system_meta_limitation={agg.get('flaw_system_meta_limitation', 0)}`, `flaw_fallback_or_malformed_artifact={agg.get('flaw_fallback_or_malformed_artifact', 0)}`。

## 判断

这轮说明：当前全 reject 不应只解释为 final threshold 太严，也不应只解释为 support 数量不足。final view 里确实存在大量未验证 candidate、excerpt limitation、system/meta limitation 和 fallback/malformed artifact，它们会污染 Key Weakness 与 reject blocker。

但 derived strict 没有显著恢复 accept-like，这同样重要：即使移除 meta/excerpt/fallback 负担，gold accept 仍缺少足够的 non-abstract / empirical / independent positive support。因此下一步不应直接调 accept 阈值。

## 下一步

建议进入 `MAINLINE_FINAL_V1_SPEC + unified metrics dry run`，但必须把本层作为 final-view/report hygiene 的组成部分：

1. runtime 主线继续保持 Evidence Binding / JSON Robustness / fallback target isolation；
2. final-view 层加入 flaw lifecycle / meta-leakage 分类；
3. criterion-aware report 中把 excerpt/system/fallback artifact 放进 Review Limitations / Not Assessable，而不是 Key Weakness；
4. final decision 仍作为 health check，不作为论文唯一主指标；
5. 不恢复 Support Formation Pass，不回 sticky/throttle/gate，不做 live state hygiene mutation。
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--docs-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()
    rows = load_jsonl(Path(args.input))
    payload = analyze(rows)
    payload["input"] = args.input
    payload["metrics"] = metric_summary(payload["case_rows"])
    out = Path(args.output_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    docs = Path(args.docs_dir)
    docs.mkdir(parents=True, exist_ok=True)
    write_schema(docs / "FINAL_VIEW_FLAW_LIFECYCLE_SCHEMA.md")
    write_audit(payload, docs / "FINAL_VIEW_FLAW_META_LEAKAGE_AUDIT.md")
    write_simulation(payload, docs / "FINAL_VIEW_FLAW_LIFECYCLE_SIMULATION.md")
    write_case_table(payload, docs / "FINAL_VIEW_FLAW_LIFECYCLE_CASE_TABLE.md")
    write_decision(payload, docs / "FINAL_VIEW_FLAW_LIFECYCLE_DECISION.md")
    print(json.dumps({"aggregate": payload["aggregate"], "metrics": payload["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
