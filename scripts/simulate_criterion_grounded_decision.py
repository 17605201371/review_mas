#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

ACCEPT_REJECT = {"accept", "reject"}
POSITIVE_STANCES = {"supports", "support", "partially_supports", "partial_support"}
NEGATIVE_STANCES = {"contradicts", "contradict", "refutes"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")

SECTION_PATTERNS = [
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    ("result", re.compile(r"\b(result|evaluation|experiment|benchmark|baseline|outperform|accuracy|f1|auc|bleu|rouge|performance|metric|dataset)\b", re.I)),
    ("method", re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training objective|loss function|inference|design)\b", re.I)),
    ("abstract", re.compile(r"\babstract\b|\btitle\b", re.I)),
    ("conclusion", re.compile(r"\bconclusion\b|\bdiscussion\b", re.I)),
]

CRITERIA = {
    "novelty": {
        "label": "novelty_originality",
        "coverage": re.compile(r"\b(novel|novelty|original|originality|new contribution|first to|prior work|related work)\b", re.I),
        "negative": re.compile(r"\b(lack(?:s|ing)? novelty|not novel|incremental|limited novelty|insufficient novelty)\b", re.I),
        "positive": re.compile(r"\b(novel|original|new contribution|first to|distinct contribution)\b", re.I),
        "sections": {"abstract", "method", "result", "ablation", "table_or_figure"},
    },
    "significance": {
        "label": "significance_contribution",
        "coverage": re.compile(r"\b(significant|significance|important|impact|contribution|practical|useful|meaningful|relevance)\b", re.I),
        "negative": re.compile(r"\b(limited significance|minor contribution|unclear impact|limited impact|weak contribution)\b", re.I),
        "positive": re.compile(r"\b(significant|important|impact|useful|meaningful|contribution)\b", re.I),
        "sections": {"abstract", "result", "ablation", "table_or_figure"},
    },
    "soundness": {
        "label": "technical_soundness",
        "coverage": re.compile(r"\b(sound|soundness|valid|validity|method|methodology|algorithm|theory|assumption|proof|objective|optimization|design|technical)\b", re.I),
        "negative": re.compile(r"\b(unsound|invalid|flaw(?:ed)? method|methodological flaw|unsupported assumption|weak theory|incorrect)\b", re.I),
        "positive": re.compile(r"\b(sound|valid|well[- ]?motivated|methodologically sound|technically sound)\b", re.I),
        "sections": {"method", "result", "ablation", "table_or_figure"},
    },
    "empirical": {
        "label": "empirical_adequacy",
        "coverage": re.compile(r"\b(empirical|experiment|evaluation|result|baseline|dataset|metric|ablation|table|figure|benchmark)\b", re.I),
        "negative": re.compile(r"\b(insufficient experiment|weak evaluation|missing baseline|no ablation|limited empirical|inadequate experiment)\b", re.I),
        "positive": re.compile(r"\b(strong result|outperform|improve|baseline|ablation|empirical evidence|evaluation)\b", re.I),
        "sections": {"result", "ablation", "table_or_figure"},
    },
    "clarity": {
        "label": "clarity_reproducibility",
        "coverage": re.compile(r"\b(clear|clarity|reproducib|readab|implementation|detail|code|hyperparameter|description|presentation)\b", re.I),
        "negative": re.compile(r"\b(unclear|not clear|lacks detail|insufficient detail|hard to reproduce|not reproducible|poorly written)\b", re.I),
        "positive": re.compile(r"\b(clear|well[- ]?presented|readable|reproducible|detailed)\b", re.I),
        "sections": {"method", "result", "table_or_figure", "abstract"},
    },
}

META_RE = re.compile(r"\b(excerpt|truncated|not available|cannot verify|could not verify|fallback|recovery failure|system|agent|raw output|parse|complete text|insufficient context)\b", re.I)
NOT_ASSESSABLE_RE = re.compile(r"\b(not assessable|cannot assess|insufficient information|not enough information|needs more context|cannot determine)\b", re.I)
EVIDENCE_REF_RE = re.compile(r"\b(evidence[-_ ]?\d+|claim[-_ ]?\d+|table\s*\d+|figure\s*\d+|fig\.?\s*\d+|section\s*\d+)\b", re.I)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def evidence_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ("source", "evidence", "support_quality_reason", "binding_rationale", "rationale"))


def evidence_section(ev: Dict[str, Any]) -> str:
    bucket = norm(ev.get("support_source_bucket"))
    mapping = {
        "result_or_experiment": "result",
        "method_or_approach": "method",
        "method_or_design": "method",
        "conclusion_or_discussion": "conclusion",
        "abstract": "abstract",
    }
    if bucket in mapping:
        return mapping[bucket]
    text = evidence_text(ev)
    for section, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section
    return "unknown"


def is_positive_strong(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) == "strong"


def is_negative(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in NEGATIVE_STANCES


def independent_group(ev: Dict[str, Any], section: str) -> str:
    text = re.sub(r"\W+", " ", str(ev.get("evidence") or "").lower()).strip()
    digest = hashlib.sha1(" ".join(text.split()[:18]).encode("utf-8")).hexdigest()[:8] if text else "empty"
    return f"{ev.get('claim_id') or ''}:{section}:{digest}"


def report_text(row: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    return str(row.get("final_report") or state.get("final_report") or "")


def criterion_features(row: Dict[str, Any], support_sections: Counter) -> Dict[str, Any]:
    report = report_text(row)
    features: Dict[str, Any] = {}
    covered = []
    grounded = []
    unsupported = []
    meta = []
    not_assessable = []
    positive_grounded = []
    weak_grounded = []
    for key, cfg in CRITERIA.items():
        is_covered = bool(cfg["coverage"].search(report))
        is_negative = bool(cfg["negative"].search(report))
        is_positive = bool(cfg["positive"].search(report)) and not is_negative
        is_na = is_covered and bool(NOT_ASSESSABLE_RE.search(report))
        has_section_grounding = any(support_sections.get(section, 0) for section in cfg["sections"])
        has_ref = is_covered and bool(EVIDENCE_REF_RE.search(report))
        is_grounded = is_covered and (has_section_grounding or has_ref or is_na)
        is_meta = is_covered and is_negative and bool(META_RE.search(report))
        is_unsupported = is_covered and is_negative and not is_grounded
        rating = "not_assessable" if is_na else ("weak" if is_negative else ("moderate_or_strong" if is_positive else "neutral_or_mentioned" if is_covered else "missing"))
        features[f"criterion_rating_{key}"] = rating
        features[f"criterion_covered_{key}"] = is_covered
        features[f"criterion_grounded_{key}"] = is_grounded
        features[f"criterion_not_assessable_{key}"] = is_na
        features[f"criterion_unsupported_{key}"] = is_unsupported
        features[f"criterion_meta_leakage_{key}"] = is_meta
        if is_covered:
            covered.append(cfg["label"])
        if is_grounded:
            grounded.append(cfg["label"])
        if is_unsupported:
            unsupported.append(cfg["label"])
        if is_meta:
            meta.append(cfg["label"])
        if is_na:
            not_assessable.append(cfg["label"])
        if rating == "moderate_or_strong" and is_grounded:
            positive_grounded.append(cfg["label"])
        if rating == "weak" and is_grounded and key in {"soundness", "empirical"}:
            weak_grounded.append(cfg["label"])
    features.update({
        "covered_criteria": covered,
        "grounded_criteria": grounded,
        "unsupported_criteria": unsupported,
        "meta_leakage_criteria": meta,
        "not_assessable_criteria": not_assessable,
        "positive_grounded_criteria": positive_grounded,
        "grounded_weak_core_criteria": weak_grounded,
    })
    return features


def flaw_features(state: Dict[str, Any]) -> Dict[str, Any]:
    confirmed_critical = 0
    grounded_major = 0
    ungrounded_candidate = 0
    system_meta = 0
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        status = norm(flaw.get("status")) or "candidate"
        severity = norm(flaw.get("severity"))
        text = " ".join(str(flaw.get(k) or "") for k in ("title", "description", "source", "status", "reason"))
        grounded = bool(flaw.get("evidence_ids") or flaw.get("supporting_evidence_ids") or flaw.get("evidence_id"))
        if status == "confirmed" and severity == "critical" and grounded:
            confirmed_critical += 1
        if severity in {"major", "critical"} and grounded:
            grounded_major += 1
        if status == "candidate" and not grounded:
            ungrounded_candidate += 1
        if META_RE.search(text):
            system_meta += 1
    return {
        "confirmed_critical_flaw_count": confirmed_critical,
        "grounded_major_flaw_count": grounded_major,
        "ungrounded_candidate_flaw_count": ungrounded_candidate,
        "system_meta_flaw_count": system_meta,
    }


def hygiene_features(state: Dict[str, Any], real_strong_claim_ids: set[str]) -> Dict[str, Any]:
    stale_gap = 0
    meta_leakage = 0
    gaps = state.get("evidence_gaps", []) or []
    for gap in gaps:
        text = str(gap if not isinstance(gap, dict) else gap.get("description") or gap.get("question") or gap)
        if META_RE.search(text):
            meta_leakage += 1
        if real_strong_claim_ids and re.search(r"lack|missing|insufficient|not enough", text, re.I):
            stale_gap += 1
    unsupported_with_strong = 0
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        cid = str(claim.get("claim_id") or "")
        if cid in real_strong_claim_ids and norm(claim.get("status")) in {"unsupported", "weak", "uncertain"}:
            unsupported_with_strong += 1
    return {
        "stale_gap_count": stale_gap,
        "unsupported_with_strong_support_count": unsupported_with_strong,
        "meta_leakage_count": meta_leakage,
    }


def derive_features(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    evidence = [ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]
    real_strong = []
    sections = Counter()
    independent = set()
    claim_ids = set()
    abstract_only = 0
    for ev in evidence:
        section = evidence_section(ev)
        if is_positive_strong(ev) and is_real_claim_id(ev.get("claim_id")):
            real_strong.append(ev)
            sections[section] += 1
            independent.add(independent_group(ev, section))
            claim_ids.add(str(ev.get("claim_id") or ""))
            if section == "abstract":
                abstract_only += 1
    non_abs = sum(count for section, count in sections.items() if section not in {"abstract", "unknown"})
    empirical = sections["result"] + sections["ablation"] + sections["table_or_figure"]
    method = sections["method"]
    table = sections["table_or_figure"]
    support = {
        "real_strong_support_total": len(real_strong),
        "non_abstract_support_total": non_abs,
        "empirical_support_total": empirical,
        "independent_support_group_total": len(independent),
        "claims_with_method_plus_result_support": int(method > 0 and empirical > 0),
        "abstract_only_support_count": abstract_only,
        "fallback_strong_support_total": sum(1 for ev in evidence if is_positive_strong(ev) and not is_real_claim_id(ev.get("claim_id"))),
        "negative_evidence_total": sum(1 for ev in evidence if is_negative(ev)),
    }
    features = {
        "paper_id": row.get("paper_id"),
        "gold_decision": infer_gold(row),
        "current_decision": pred_decision(row),
        "reward": row.get("reward"),
        **support,
        **criterion_features(row, sections),
        **flaw_features(state),
        **hygiene_features(state, claim_ids),
    }
    return features


def rule_current(f: Dict[str, Any]) -> str:
    return f["current_decision"] if f["current_decision"] in ACCEPT_REJECT else "borderline"


def rule_support_count(f: Dict[str, Any]) -> str:
    if f["real_strong_support_total"] >= 2 and f["grounded_major_flaw_count"] == 0:
        return "accept_like"
    return "reject_like"


def has_grounded_reject_blocker(f: Dict[str, Any]) -> bool:
    return bool(
        f["confirmed_critical_flaw_count"] > 0
        or f["grounded_weak_core_criteria"]
        or (f["grounded_major_flaw_count"] > 0 and f["real_strong_support_total"] < 2)
    )


def has_support_quality_accept_signal(f: Dict[str, Any]) -> bool:
    return bool(
        f["non_abstract_support_total"] >= 1
        and f["independent_support_group_total"] >= 2
        and f["positive_grounded_criteria"]
    )


def rule_criterion_gated_reject(f: Dict[str, Any]) -> str:
    if has_grounded_reject_blocker(f):
        return "reject_like"
    if f["positive_grounded_criteria"] and f["real_strong_support_total"] >= 1:
        return "borderline"
    return "not_assessable"


def rule_support_quality_accept(f: Dict[str, Any]) -> str:
    if has_grounded_reject_blocker(f):
        return "reject_like"
    if has_support_quality_accept_signal(f):
        return "accept_like"
    if f["real_strong_support_total"] >= 1:
        return "borderline"
    return "reject_like"


def rule_combined(f: Dict[str, Any]) -> str:
    if has_grounded_reject_blocker(f):
        return "reject_like"
    if f["meta_leakage_count"] >= 4 and f["real_strong_support_total"] == 0:
        return "not_assessable"
    if has_support_quality_accept_signal(f) and f["stale_gap_count"] <= 4 and f["unsupported_with_strong_support_count"] <= 1:
        return "accept_like"
    if f["real_strong_support_total"] >= 1 and f["positive_grounded_criteria"]:
        return "borderline"
    if f["covered_criteria"] and len(f["grounded_criteria"]) < max(1, len(f["covered_criteria"]) // 2):
        return "not_assessable"
    return "reject_like"


RULES = {
    "sim0_current_rule": rule_current,
    "sim1_support_count_rule": rule_support_count,
    "sim2_criterion_gated_reject": rule_criterion_gated_reject,
    "sim3_support_quality_accept": rule_support_quality_accept,
    "sim4_combined_criterion_support_hygiene": rule_combined,
}


def binary_for(label: str, borderline_policy: str = "strict") -> str:
    if label in {"accept", "accept_like", "recommend_accept", "weak_accept"}:
        return "accept"
    if label in {"reject", "reject_like", "recommend_reject", "weak_reject"}:
        return "reject"
    if borderline_policy == "lenient" and label == "borderline":
        return "accept"
    return "reject"


def metrics(features: List[Dict[str, Any]], labels: Dict[str, str], borderline_policy: str = "strict") -> Dict[str, Any]:
    rows = [f for f in features if f["gold_decision"] in ACCEPT_REJECT]
    tp = tn = fp = fn = 0
    false_accept = []
    false_reject = []
    recovered_accept = []
    pred_accept = pred_reject = 0
    borderline = []
    not_assessable = []
    for f in rows:
        raw = labels[f["paper_id"]]
        pred = binary_for(raw, borderline_policy)
        gold = f["gold_decision"]
        pred_accept += int(pred == "accept")
        pred_reject += int(pred == "reject")
        if raw == "borderline":
            borderline.append(f["paper_id"])
        if raw == "not_assessable":
            not_assessable.append(f["paper_id"])
        if pred == "accept" and gold == "accept":
            tp += 1
            if f["current_decision"] == "reject":
                recovered_accept.append(f["paper_id"])
        elif pred == "accept" and gold == "reject":
            fp += 1
            false_accept.append(f["paper_id"])
        elif pred == "reject" and gold == "reject":
            tn += 1
        elif pred == "reject" and gold == "accept":
            fn += 1
            false_reject.append(f["paper_id"])
    total = len(rows) or 1
    acc = (tp + tn) / total
    accept_recall = tp / (tp + fn) if (tp + fn) else 0.0
    reject_recall = tn / (tn + fp) if (tn + fp) else 0.0
    accept_prec = tp / (tp + fp) if (tp + fp) else 0.0
    reject_prec = tn / (tn + fn) if (tn + fn) else 0.0
    f1_accept = 2 * accept_prec * accept_recall / (accept_prec + accept_recall) if (accept_prec + accept_recall) else 0.0
    f1_reject = 2 * reject_prec * reject_recall / (reject_prec + reject_recall) if (reject_prec + reject_recall) else 0.0
    return {
        "rows": len(rows),
        "accuracy": round(acc, 4),
        "macro_f1": round((f1_accept + f1_reject) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": pred_accept,
        "predicted_reject_count": pred_reject,
        "predicted_borderline_count": len(borderline),
        "predicted_not_assessable_count": len(not_assessable),
        "false_accept_ids": false_accept,
        "false_reject_ids": false_reject,
        "recovered_accept_ids": recovered_accept,
        "borderline_ids": borderline,
        "not_assessable_ids": not_assessable,
    }


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines) + "\n"


def write_docs(outdir: Path, input_path: Path, features: List[Dict[str, Any]], results: Dict[str, Any], case_rows: List[Dict[str, Any]]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "CRITERION_GROUNDED_DECISION_SCHEMA.md").write_text("""# Criterion-Grounded Decision Schema v1\n\n本文件定义离线 final decision simulation 的派生字段和规则。\n\n## 设计原则\n\n本轮不改 runtime、不改 `ReviewState`、不重跑模型，也不让模型自由输出 accept/reject。模型或已有报告只提供审稿维度信号；规则层只做证据约束、状态卫生约束和决策校准。\n\n## Criterion 字段\n\n- `criterion_rating_novelty / significance / soundness / empirical / clarity`: 规则从 final report 中派生的维度倾向，取值包括 `moderate_or_strong`、`weak`、`neutral_or_mentioned`、`not_assessable`、`missing`。\n- `criterion_grounded_*`: 维度判断是否有 evidence section、claim/evidence/table/figure 引用，或明确标记为 not assessable。\n- `criterion_not_assessable_*`: 系统是否承认该维度上下文不足。\n\n## Support 字段\n\n- `real_strong_support_total`: 绑定到真实 claim 的 strong positive support 总数。\n- `non_abstract_support_total`: 非 abstract 的 strong support 数量。\n- `empirical_support_total`: result / table / figure / ablation support 数量。\n- `independent_support_group_total`: 去重后的独立 support group 数量。\n\n## Flaw / Hygiene 字段\n\n- `confirmed_critical_flaw_count`: grounded confirmed critical flaw。\n- `grounded_major_flaw_count`: grounded major/critical flaw。\n- `ungrounded_candidate_flaw_count`: 未 grounding 的 candidate flaw。\n- `stale_gap_count`: 有 strong support 时仍存在的可能 stale gap。\n- `meta_leakage_count`: excerpt/system/fallback/recovery 相关 meta 信息进入负面状态。\n\n## 模拟规则\n\n- Sim 0: 当前 final decision。\n- Sim 1: strong support count rule。\n- Sim 2: criterion-gated reject。\n- Sim 3: support-quality accept。\n- Sim 4: combined criterion + support quality + hygiene。\n\n本轮输出只用于离线诊断，不直接作为论文系统 runtime decision。\n""", encoding="utf-8")

    sim_rows = []
    for name, values in results["simulations"].items():
        strict = values["strict"]
        lenient = values.get("lenient")
        sim_rows.append([
            name,
            strict["accuracy"],
            strict["macro_f1"],
            strict["accept_recall"],
            strict["reject_recall"],
            strict["predicted_accept_count"],
            strict["predicted_borderline_count"],
            ", ".join(strict["false_accept_ids"]),
            ", ".join(strict["recovered_accept_ids"]),
            lenient["predicted_accept_count"] if lenient else "-",
        ])
    (outdir / "CRITERION_GROUNDED_DECISION_SIMULATION.md").write_text(
        "# Criterion-Grounded Decision Simulation v1\n\n"
        f"输入文件：`{input_path}`\n\n"
        "## 模拟结果\n\n"
        + md_table(["simulation", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept(strict)", "borderline", "false_accept", "recovered_accept", "pred_accept(lenient)"], sim_rows)
        + "\n## 关键读法\n\n"
        + "- `strict` 映射中，borderline / not_assessable 仍按 reject 计算，用于安全下界。\n"
        + "- `lenient` 只用于 Sim 4，把 borderline 视为 accept，以观察上界风险。\n"
        + "- 本轮不把 novelty / soundness 等维度直接接入 runtime decision。\n",
        encoding="utf-8",
    )

    case_table = []
    for row in case_rows:
        case_table.append([
            row["paper_id"], row["gold_decision"], row["current_decision"], row["sim4_label"],
            row["real_strong_support_total"], row["non_abstract_support_total"], row["independent_support_group_total"],
            ", ".join(row["positive_grounded_criteria"]), ", ".join(row["grounded_weak_core_criteria"]),
            row["confirmed_critical_flaw_count"], row["grounded_major_flaw_count"], row["stale_gap_count"],
        ])
    (outdir / "CRITERION_DECISION_CASE_TABLE.md").write_text(
        "# Criterion Decision Case Table\n\n"
        + md_table(["paper_id", "gold", "current", "sim4", "real_strong", "non_abs", "ind_groups", "positive_grounded", "weak_core", "critical_flaw", "grounded_major", "stale_gap"], case_table),
        encoding="utf-8",
    )

    sim4 = results["simulations"]["sim4_combined_criterion_support_hygiene"]["strict"]
    decision = """# Criterion Decision Next Step

## 当前结论

离线模拟确认了一个负结论：最终推荐确实不能只看 strong support 数量，但当前这版 criterion-grounded aggregation 也不能接入 runtime decision。它能把结果拆成 `accept_like / reject_like / borderline / not_assessable`，但没有恢复任何 gold accept，并且在 accept-like 分支上产生了 false accept。

因此，criterion 现在只能作为论文评估与报告诊断层，不能作为接收/拒收聚合规则。

## 本轮发现

- Sim 1 的 strong-support-count rule 仍然恢复不了 accept，说明单纯 support 数量不是 paper-level 接收标准。
- Sim 2 的 criterion-gated reject 最安全：false accept 为 0，reject recall 为 1.0，但 accept recall 仍为 0；它更适合作为“安全拒绝/不可评估”审计，而不是恢复 accept 的规则。
- Sim 4 的 combined rule 在 strict 映射下仍产生 {false_accept_count} 个 false accept，且 recovered accept 为 {recovered_accept_count}；说明当前 criterion 信号和 support-quality 信号还不足以安全推动 accept-like decision。
- 当前 final reports 中的 criterion positive wording 仍然偏弱、偏浅，不能作为论文级 accept 的充分依据。

## Sim 4 安全下界

- accuracy: {accuracy}
- macro_f1: {macro_f1}
- accept_recall: {accept_recall}
- reject_recall: {reject_recall}
- predicted_accept_count: {predicted_accept_count}
- predicted_borderline_count: {predicted_borderline_count}
- false_accept_ids: {false_accept_ids}
- recovered_accept_ids: {recovered_accept_ids}

## 下一步建议

下一步不应 runtime 化 criterion-grounded final decision，也不应继续调 final decision 阈值。建议保持 **audit-only**：

1. criterion 继续用于 final report 丰富度、coverage、grounding 和 meta-leakage 审计。
2. final decision 暂时仍不要接入 novelty / soundness / empirical adequacy 等维度。
3. 后续如果要让 criterion 进入决策，必须先提高 criterion assessment 的 grounding 质量，并证明它能恢复 gold accept 且不制造 false accept。
4. 近期更值得做的是补强 evidence/support quality 与 criterion grounding，而不是增加新的 controller 或 decision rule。

## 暂时不要做

- 不要让模型自由拍板 final decision。
- 不要写 `low novelty -> reject` 或 `criterion positive -> accept` 的硬规则。
- 不要让 ungrounded candidate flaw 触发强 reject。
- 不要把 not_assessable 当作 paper weakness。
- 不要把本轮 Sim 4 当成可以上线的 final-view decision rule。
""".format(**{**sim4, "false_accept_ids": ", ".join(sim4["false_accept_ids"]), "recovered_accept_ids": ", ".join(sim4["recovered_accept_ids"]), "false_accept_count": len(sim4["false_accept_ids"]), "recovered_accept_count": len(sim4["recovered_accept_ids"])})
    (outdir / "CRITERION_DECISION_NEXT_STEP.md").write_text(decision, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("outputs/results_main/review_infer/decision_hygiene_view_v1_fulltest39_4b.jsonl"))
    parser.add_argument("--outdir", type=Path, default=Path("docs/experiments/mainline_current"))
    parser.add_argument("--json-out", type=Path, default=Path("outputs/results_main/review_infer/criterion_grounded_decision_sim_v1.json"))
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    features = [derive_features(row) for row in rows]
    labels_by_rule: Dict[str, Dict[str, str]] = {}
    simulations: Dict[str, Any] = {}
    for name, func in RULES.items():
        labels = {f["paper_id"]: func(f) for f in features}
        labels_by_rule[name] = labels
        entry = {"strict": metrics(features, labels, "strict")}
        if name == "sim4_combined_criterion_support_hygiene":
            entry["lenient"] = metrics(features, labels, "lenient")
        simulations[name] = entry

    case_rows = []
    for f in features:
        row = dict(f)
        row["sim4_label"] = labels_by_rule["sim4_combined_criterion_support_hygiene"][f["paper_id"]]
        case_rows.append(row)
    case_rows.sort(key=lambda x: (x["gold_decision"], x["paper_id"]))

    results = {
        "input": str(args.input),
        "rows": len(features),
        "simulations": simulations,
        "aggregate_features": {
            "real_strong_support_total": sum(f["real_strong_support_total"] for f in features),
            "non_abstract_support_total": sum(f["non_abstract_support_total"] for f in features),
            "empirical_support_total": sum(f["empirical_support_total"] for f in features),
            "confirmed_critical_flaw_count": sum(f["confirmed_critical_flaw_count"] for f in features),
            "grounded_major_flaw_count": sum(f["grounded_major_flaw_count"] for f in features),
            "unsupported_criterion_used_count": sum(len(f["unsupported_criteria"]) for f in features),
            "not_assessable_count": sum(len(f["not_assessable_criteria"]) for f in features),
            "meta_leakage_count": sum(f["meta_leakage_count"] for f in features),
        },
        "case_rows": case_rows,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_docs(args.outdir, args.input, features, results, case_rows)
    print(json.dumps({"json_out": str(args.json_out), "rows": len(features), "sim4": simulations["sim4_combined_criterion_support_hygiene"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
