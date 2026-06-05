#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

CORE_CRITERIA = {"empirical", "soundness", "novelty", "significance"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")
CONTEXT_LIMITED_RE = re.compile(
    r"\b(abstract cuts off|cuts off|cut off|truncat|provided context|current context|visible|not visible|"
    r"missing from context|prevents verification|cannot verify|unable to verify|not assessable|"
    r"full text|provided text|figure itself is missing|table itself is missing)\b",
    re.I,
)
META_RE = re.compile(r"\b(fallback|parse|raw output|agent|system|review limitation|excerpt)\b", re.I)
ANCHOR_RE = re.compile(r"\b(results? section|experiment(?:al)? section|evaluation section|table\s*\d*|figure\s*\d*|fig\.?\s*\d*|baseline comparison|metric table|ablation|dataset section|benchmark results)\b", re.I)
ABSTRACT_ONLY_RE = re.compile(r"\babstract\b", re.I)
MISSING_SUPPORT_RE = re.compile(r"\b(lacks?|missing|no |not provide|insufficient|without)\b", re.I)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def item_claim_id(item: Dict[str, Any]) -> str:
    if item.get("claim_id"):
        return str(item.get("claim_id"))
    ids = item.get("related_claim_ids") or []
    if isinstance(ids, str):
        return ids
    return str(ids[0]) if ids else ""


def item_text(item: Dict[str, Any]) -> str:
    fields = ["paper_anchor", "evidence_text", "rationale"]
    text = " ".join(str(item.get(k) or "") for k in fields)
    refs = item.get("evidence_refs") or []
    if isinstance(refs, list):
        text += " " + " ".join(str(x) for x in refs)
    else:
        text += " " + str(refs)
    return text


def v2_label(item: Dict[str, Any]) -> tuple[str, List[str]]:
    reasons: List[str] = []
    criterion = norm(item.get("criterion"))
    claim_id = item_claim_id(item)
    text = item_text(item)
    anchor = str(item.get("paper_anchor") or ",".join(item.get("evidence_refs") or []) or "")
    try:
        conf = float(item.get("confidence") or 0)
    except (TypeError, ValueError):
        conf = 0.0
    grounding = norm(item.get("grounding_strength"))
    status = norm(item.get("status"))
    severity = norm(item.get("severity"))

    if criterion not in CORE_CRITERIA:
        reasons.append("non_core_criterion")
    if not is_real_claim_id(claim_id):
        reasons.append("not_real_claim")
    if conf < 0.55:
        reasons.append("low_confidence")
    if META_RE.search(text):
        reasons.append("meta_or_fallback_language")
    if CONTEXT_LIMITED_RE.search(text):
        reasons.append("context_limited_language")
    has_anchor = bool(ANCHOR_RE.search(anchor))
    if not has_anchor:
        reasons.append("missing_nonabstract_anchor")
    if ABSTRACT_ONLY_RE.search(anchor) and MISSING_SUPPORT_RE.search(text) and not has_anchor:
        reasons.append("abstract_only_missing_support")

    is_negative_evidence = item.get("kind") == "negative_evidence"
    is_flaw = item.get("kind") == "flaw_confirmation"
    if is_negative_evidence and grounding not in {"medium", "strong"}:
        reasons.append("weak_grounding")
    if is_flaw and not (status == "confirmed" and severity in {"major", "critical"}):
        reasons.append("not_confirmed_major_or_critical")

    if not reasons:
        return "v2_trusted_blocker", []
    if "context_limited_language" in reasons:
        return "not_assessable_context_limited", reasons
    if "abstract_only_missing_support" in reasons or "missing_nonabstract_anchor" in reasons:
        return "weak_candidate_anchor_insufficient", reasons
    return "rejected_by_v2", reasons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-jsonl", default="outputs/results_main/review_infer/negative_evidence_formation_pass_v1_2_4b_diagnostic10.jsonl")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/negative_evidence_formation_v2_rule_simulation.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()

    case_rows: List[Dict[str, Any]] = []
    item_rows: List[Dict[str, Any]] = []
    for line in Path(args.input_jsonl).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        items = []
        for item in row.get("trusted_negative_items", []) or []:
            items.append({"kind": "negative_evidence", **item})
        for item in row.get("trusted_flaw_items", []) or []:
            items.append({"kind": "flaw_confirmation", **item})
        labels = []
        trusted = []
        for item in items:
            label, reasons = v2_label(item)
            labels.append(label)
            item_row = {
                "paper_id": row["paper_id"],
                "gold_decision": row["gold_decision"],
                "tag": row["tag"],
                "kind": item.get("kind"),
                "criterion": item.get("criterion"),
                "claim_id": item_claim_id(item),
                "v2_label": label,
                "v2_reasons": reasons,
                "anchor": item.get("paper_anchor") or ",".join(item.get("evidence_refs") or []),
                "text": (item.get("evidence_text") or item.get("rationale") or "")[:500],
            }
            if label == "v2_trusted_blocker":
                trusted.append(item_row)
            item_rows.append(item_row)
        case_rows.append({
            "paper_id": row["paper_id"],
            "gold_decision": row["gold_decision"],
            "tag": row["tag"],
            "v1_2_trusted_blocker_count": row.get("trusted_blocker_count", 0),
            "v2_trusted_blocker_count": len(trusted),
            "v2_labels": dict(Counter(labels)),
            "parse_error": row.get("parse_error", False),
        })

    group = {}
    for tag in ["false_accept", "recovered_accept"]:
        sub = [r for r in case_rows if r["tag"] == tag]
        group[tag] = {
            "rows": len(sub),
            "v1_2_trusted_rows": sum(1 for r in sub if r["v1_2_trusted_blocker_count"] > 0),
            "v2_trusted_rows": sum(1 for r in sub if r["v2_trusted_blocker_count"] > 0),
            "parse_error_rows": sum(1 for r in sub if r["parse_error"]),
        }
    label_counts = Counter(r["v2_label"] for r in item_rows)
    by_tag = defaultdict(Counter)
    for r in item_rows:
        by_tag[r["tag"]][r["v2_label"]] += 1

    out = {
        "input_jsonl": args.input_jsonl,
        "group_summaries": group,
        "label_counts": dict(label_counts),
        "label_counts_by_tag": {k: dict(v) for k, v in by_tag.items()},
        "case_rows": case_rows,
        "item_rows": item_rows,
    }
    Path(args.output_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    doc_dir = Path(args.doc_dir)
    doc_dir.mkdir(parents=True, exist_ok=True)
    spec = """# Negative Evidence Formation v2 Spec\n\n## 目标\n\nv2 不再扩大生成能力，而是收紧 blocker 语义：只有 paper-grounded、非 context-limited、非 abstract-only、绑定真实 claim、关联核心 criterion 的负向证据才能成为 trusted blocker。\n\n## Trusted blocker 必要条件\n\n1. criterion 属于 `empirical / soundness / novelty / significance`。\n2. claim_id 是真实 claim，不是 fallback/general。\n3. evidence/flaw anchor 包含 `result / experiment / table / figure / baseline / metric / ablation / dataset / benchmark`。\n4. 不包含 `context not visible / abstract cuts off / cannot verify / missing from provided context` 等 context-limited 语言。\n5. negative evidence 的 grounding strength 为 medium/strong；flaw 必须 confirmed 且 major/critical。\n6. confidence >= 0.55。\n\n## 不进入 trusted blocker 的情况\n\n- abstract-only missing support。\n- context-limited not-assessable。\n- meta / fallback / parse / system limitation。\n- anchor insufficient 的 weak candidate。\n\n## 本轮定位\n\n该 spec 仍是离线规则，不接入 final decision。\n"""
    (doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V2_SPEC.md").write_text(spec, encoding="utf-8")

    lines = ["# Negative Evidence Formation v2 Rule Simulation", "", "## Group Summary", "", table_row(["group", "rows", "v1_2_trusted_rows", "v2_trusted_rows", "parse_error_rows"]), table_row(["---", "---:", "---:", "---:", "---:"])]
    for tag, data in group.items():
        lines.append(table_row([tag, data["rows"], data["v1_2_trusted_rows"], data["v2_trusted_rows"], data["parse_error_rows"]]))
    lines += ["", "## Label Counts", "", table_row(["label", "count"]), table_row(["---", "---:"])]
    for label, count in label_counts.most_common():
        lines.append(table_row([label, count]))
    lines += ["", "## Case Table", "", table_row(["paper_id", "gold", "tag", "v1_2", "v2", "labels"]), table_row(["---", "---", "---", "---:", "---:", "---"])]
    for r in case_rows:
        labels = ", ".join(f"{k}:{v}" for k, v in r["v2_labels"].items())
        lines.append(table_row([r["paper_id"], r["gold_decision"], r["tag"], r["v1_2_trusted_blocker_count"], r["v2_trusted_blocker_count"], labels]))
    (doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V2_RULE_SIMULATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    decision = f"""# Negative Evidence Formation v2 Decision\n\n## 结论\n\nv2 规则可以显著降低 blocker 过宽问题，但覆盖仍不足，暂时不能接入 final decision。\n\n## 关键结果\n\n- false accept: v1.2 trusted rows `{group['false_accept']['v1_2_trusted_rows']}/7` -> v2 trusted rows `{group['false_accept']['v2_trusted_rows']}/7`。\n- recovered accept: v1.2 trusted rows `{group['recovered_accept']['v1_2_trusted_rows']}/3` -> v2 trusted rows `{group['recovered_accept']['v2_trusted_rows']}/3`。\n\n## 判断\n\n如果 v2 能把 recovered accept blocker 降到 0，同时保留一部分 false accept blocker，说明 precision 方向正确。但如果 false accept 覆盖过低，下一步不能靠 final decision 使用它，而应继续改 negative evidence formation 的 evidence retrieval / anchor extraction。\n\n## 下一步\n\n建议做 `Negative Evidence Anchor Extraction v1`：离线抽取 result/table/figure/experiment 附近原文锚点，再让 pass 只基于这些锚点确认 flaw。不要继续使用 abstract/context-missing 作为负向依据。\n"""
    (doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V2_DECISION.md").write_text(decision, encoding="utf-8")

    print(json.dumps({
        "json": args.output_json,
        "docs": [
            "NEGATIVE_EVIDENCE_FORMATION_V2_SPEC.md",
            "NEGATIVE_EVIDENCE_FORMATION_V2_RULE_SIMULATION.md",
            "NEGATIVE_EVIDENCE_FORMATION_V2_DECISION.md",
        ],
        "group_summaries": group,
        "label_counts": dict(label_counts),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
