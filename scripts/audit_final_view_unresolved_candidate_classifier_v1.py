#!/usr/bin/env python3
"""Offline unresolved/candidate-flaw classifier audit for final-view decisions.

The script reads an existing run jsonl plus support-quality summary and derives
report/decision-facing lifecycle labels. It never mutates live ReviewState.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence

CLAIM_RE = re.compile(r"claim-[A-Za-z0-9_-]+")
META_RE = re.compile(r"\b(fallback|json|parse|parser|raw output|model output|system|agent|the user wants me)\b", re.I)
EXCERPT_RE = re.compile(r"\b(excerpt|truncated|complete text|full paper|not visible|missing due to|provided text|cuts off|not provided|insufficient context)\b", re.I)
EMPIRICAL_RE = re.compile(r"\b(experiment|experimental|result|metric|benchmark|dataset|baseline|ablation|table|figure|comparison|quantitative|performance)\b", re.I)
METHOD_RE = re.compile(r"\b(method|mechanism|formulation|algorithm|training|procedure|architecture|implementation|classifier|model|approach|assumption)\b", re.I)
EVIDENCE_GAP_RE = re.compile(r"Claim\s+(claim-[A-Za-z0-9_-]+)\s+lacks grounded supporting evidence", re.I)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def as_int(row: Dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        return " ".join(str(item.get(k) or "") for k in ["question", "title", "description", "note", "source", "status", "question_id"]).strip()
    return str(item or "").strip()


def item_claim_ids(item: Any) -> List[str]:
    if isinstance(item, dict):
        ids = item.get("related_claim_ids") or item.get("claim_ids") or []
        if isinstance(ids, str):
            ids = [ids]
        ids = [str(x) for x in ids if str(x).strip()]
        if ids:
            return ids
    return CLAIM_RE.findall(item_text(item))


def support_claim_sets(state: Dict[str, Any]) -> tuple[set[str], set[str]]:
    supported: set[str] = set()
    strong: set[str] = set()
    for e in state.get("evidence_map", []) or []:
        if not isinstance(e, dict):
            continue
        claim_id = str(e.get("claim_id") or "")
        if not claim_id or claim_id.startswith("claim-fallback"):
            continue
        stance = norm(e.get("stance"))
        strength = norm(e.get("strength"))
        binding = norm(e.get("binding_status"))
        if stance in {"supports", "support", "positive"} and strength in {"medium", "strong"} and binding == "bound_real_claim":
            supported.add(claim_id)
        if stance in {"supports", "support", "positive"} and strength == "strong" and binding == "bound_real_claim":
            strong.add(claim_id)
    return supported, strong


def classify_unresolved(item: Any, supported_claims: set[str], strong_claims: set[str]) -> str:
    text = item_text(item)
    low = text.lower()
    status = norm(item.get("status")) if isinstance(item, dict) else "open"
    if status in {"resolved", "closed", "downgraded", "retracted"}:
        return "closed_or_resolved"
    if META_RE.search(text) or "claim-fallback" in low:
        return "system_or_fallback"
    if EXCERPT_RE.search(text):
        return "review_context_limitation"
    claim_ids = set(item_claim_ids(item))
    if claim_ids and claim_ids <= supported_claims:
        return "resolved_by_support"
    if claim_ids and claim_ids <= strong_claims:
        return "resolved_by_strong_support"
    if EMPIRICAL_RE.search(text):
        return "paper_empirical_open"
    if METHOD_RE.search(text):
        return "paper_method_open"
    if not claim_ids and text.endswith("?"):
        return "open_review_question"
    if claim_ids:
        return "paper_grounded_open"
    return "weak_open"


def classify_gap(gap: Any, supported_claims: set[str]) -> str:
    text = str(gap or "")
    low = text.lower()
    m = EVIDENCE_GAP_RE.search(text)
    if m and m.group(1) in supported_claims:
        return "stale_gap_resolved_by_support"
    if "claim-fallback" in low or META_RE.search(text):
        return "system_or_fallback_gap"
    if m:
        return "active_claim_gap"
    if EXCERPT_RE.search(text):
        return "review_context_gap"
    return "weak_or_generic_gap"


def is_fallback_or_meta_flaw(flaw: Dict[str, Any]) -> bool:
    flaw_id = norm(flaw.get("flaw_id"))
    source = norm(flaw.get("source"))
    status = norm(flaw.get("status"))
    text = item_text(flaw).lower()
    return (
        flaw_id.startswith("flaw-fallback")
        or source in {"fallback", "fallback-extraction", "system_meta"}
        or status in {"downgraded", "retracted"}
        or '"flaw_candidates"' in text
        or text.strip().startswith("{")
        or bool(META_RE.search(text))
    )


def classify_flaw(flaw: Dict[str, Any]) -> str:
    if is_fallback_or_meta_flaw(flaw):
        return "system_or_fallback_flaw"
    text = item_text(flaw)
    severity = norm(flaw.get("severity"))
    status = norm(flaw.get("status")) or "candidate"
    confidence = float(flaw.get("confidence") or 0.0)
    grounded = bool(flaw.get("evidence_ids")) or norm(flaw.get("grounding_status")) in {"grounded", "paper_grounded"}
    if EXCERPT_RE.search(text):
        return "review_context_limitation_flaw"
    if status == "confirmed" and grounded and severity in {"major", "critical"}:
        return "confirmed_grounded_hard_flaw"
    if severity == "critical" and grounded and confidence >= 0.65:
        return "trusted_critical_flaw"
    if severity == "major" and grounded and confidence >= 0.75:
        return "trusted_major_flaw"
    if severity in {"major", "critical"} and status == "candidate" and confidence >= 0.75:
        if EMPIRICAL_RE.search(text):
            return "candidate_empirical_hard_flaw"
        if METHOD_RE.search(text):
            return "candidate_method_hard_flaw"
        return "candidate_generic_hard_flaw"
    if severity in {"major", "critical"}:
        return "weak_candidate_hard_flaw"
    return "minor_or_nonblocking_flaw"


def view_label(row: Dict[str, Any]) -> str:
    if as_int(row, "confirmed_or_trusted_hard_flaw") > 0:
        return "reject_like"
    if as_int(row, "candidate_hard_flaw") >= 2:
        return "reject_like"
    if as_int(row, "paper_empirical_open") > 0 or as_int(row, "paper_method_open") > 0 or as_int(row, "paper_grounded_open") > 0:
        return "not_assessable"
    if as_int(row, "review_context_limitation") >= 2 or as_int(row, "weak_open") >= 2:
        return "not_assessable"
    if as_int(row, "active_claim_gap") > 2:
        return "not_assessable"
    enough_support = as_int(row, "real_strong_support_total") >= 2 and as_int(row, "non_abstract_support_total") >= 2 and as_int(row, "independent_support_group_total") >= 2
    method_ok = as_int(row, "method_support_total") >= 1
    empirical_ok = as_int(row, "empirical_support_total") >= 1
    if enough_support and method_ok and empirical_ok and as_int(row, "candidate_hard_flaw") == 0:
        return "accept_like"
    if enough_support and empirical_ok:
        return "borderline_positive"
    return "borderline_insufficient"


def binary_from_view(row: Dict[str, Any]) -> str:
    return "accept" if view_label(row) == "accept_like" else "reject"


def metrics(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept: List[str] = []
    recovered: List[str] = []
    false_reject: List[str] = []
    for r in rows:
        pred = binary_from_view(r)
        gold = r.get("gold_decision")
        if pred == "accept" and gold == "accept":
            tp += 1; recovered.append(r["paper_id"])
        elif pred == "accept" and gold == "reject":
            fp += 1; false_accept.append(r["paper_id"])
        elif pred == "reject" and gold == "accept":
            fn += 1; false_reject.append(r["paper_id"])
        elif pred == "reject" and gold == "reject":
            tn += 1
    total = max(1, tp + tn + fp + fn)
    accept_recall = tp / max(1, tp + fn)
    reject_recall = tn / max(1, tn + fp)
    accept_precision = tp / max(1, tp + fp)
    reject_precision = tn / max(1, tn + fn)
    f1_a = 0 if accept_precision + accept_recall == 0 else 2 * accept_precision * accept_recall / (accept_precision + accept_recall)
    f1_r = 0 if reject_precision + reject_recall == 0 else 2 * reject_precision * reject_recall / (reject_precision + reject_recall)
    return {
        "accuracy": round((tp + tn) / total, 4),
        "macro_f1": round((f1_a + f1_r) / 2, 4),
        "accept_recall": round(accept_recall, 4),
        "reject_recall": round(reject_recall, 4),
        "predicted_accept_count": tp + fp,
        "false_accept_ids": false_accept,
        "recovered_accept_ids": recovered,
        "false_reject_ids": false_reject,
    }


def derive_rows(jsonl_rows: Sequence[Dict[str, Any]], support_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {r.get("paper_id"): r for r in jsonl_rows}
    derived: List[Dict[str, Any]] = []
    for support in support_rows:
        pid = support.get("paper_id")
        raw = by_id.get(pid)
        if not raw:
            continue
        state = raw.get("review_state") or {}
        supported, strong = support_claim_sets(state)
        unresolved_classes = Counter(classify_unresolved(x, supported, strong) for x in state.get("unresolved_questions", []) or [])
        gap_classes = Counter(classify_gap(x, supported) for x in state.get("evidence_gaps", []) or [])
        flaw_classes = Counter(classify_flaw(f) for f in state.get("flaw_candidates", []) or [] if isinstance(f, dict))
        row = dict(support)
        row.update({
            "runtime_pred": norm(raw.get("final_decision")) or "reject",
            "unresolved_classes": dict(unresolved_classes),
            "gap_classes": dict(gap_classes),
            "flaw_classes": dict(flaw_classes),
            "system_or_fallback_unresolved": unresolved_classes["system_or_fallback"],
            "review_context_limitation": unresolved_classes["review_context_limitation"],
            "resolved_by_support": unresolved_classes["resolved_by_support"] + unresolved_classes["resolved_by_strong_support"],
            "paper_empirical_open": unresolved_classes["paper_empirical_open"],
            "paper_method_open": unresolved_classes["paper_method_open"],
            "paper_grounded_open": unresolved_classes["paper_grounded_open"],
            "open_review_question": unresolved_classes["open_review_question"],
            "weak_open": unresolved_classes["weak_open"],
            "active_claim_gap": gap_classes["active_claim_gap"],
            "stale_gap_resolved_by_support": gap_classes["stale_gap_resolved_by_support"],
            "system_or_fallback_gap": gap_classes["system_or_fallback_gap"],
            "confirmed_or_trusted_hard_flaw": flaw_classes["confirmed_grounded_hard_flaw"] + flaw_classes["trusted_critical_flaw"] + flaw_classes["trusted_major_flaw"],
            "candidate_hard_flaw": flaw_classes["candidate_empirical_hard_flaw"] + flaw_classes["candidate_method_hard_flaw"] + flaw_classes["candidate_generic_hard_flaw"],
            "system_or_fallback_flaw": flaw_classes["system_or_fallback_flaw"],
            "review_context_limitation_flaw": flaw_classes["review_context_limitation_flaw"],
        })
        row["classifier_view"] = view_label(row)
        row["classifier_pred"] = binary_from_view(row)
        derived.append(row)
    return derived


def aggregate(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    keys = [
        "system_or_fallback_unresolved", "review_context_limitation", "resolved_by_support",
        "paper_empirical_open", "paper_method_open", "paper_grounded_open", "open_review_question", "weak_open",
        "active_claim_gap", "stale_gap_resolved_by_support", "system_or_fallback_gap",
        "confirmed_or_trusted_hard_flaw", "candidate_hard_flaw", "system_or_fallback_flaw", "review_context_limitation_flaw",
    ]
    out = {k: sum(as_int(r, k) for r in rows) for k in keys}
    out["rows"] = len(rows)
    out["view_counts"] = dict(Counter(r["classifier_view"] for r in rows))
    out["gold_accept_count"] = sum(1 for r in rows if r.get("gold_decision") == "accept")
    out["gold_reject_count"] = sum(1 for r in rows if r.get("gold_decision") == "reject")
    return out


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(out)


def render_schema() -> str:
    return """# Final-View Unresolved / Candidate-Flaw Classifier v1 Schema

本审计只做离线 final-view 分类，不改 runtime、不改 live `ReviewState`。

## Unresolved 分类

- `system_or_fallback`：fallback / JSON / parser / agent / system 相关，不是论文缺陷。
- `review_context_limitation`：文本截断、excerpt 不足、完整论文缺失，应进入 limitation / not_assessable。
- `resolved_by_support`：相关 claim 已有 real support，但 unresolved 未关闭。
- `paper_empirical_open`：实验、指标、表格、消融等仍未验证的问题。
- `paper_method_open`：方法、机制、算法、训练过程仍未验证的问题。
- `paper_grounded_open`：绑定明确 claim 的 open paper risk。
- `open_review_question`：普通待查问题，不应直接当 weakness。
- `weak_open`：无法可靠归类的 open item。

## Candidate flaw 分类

- `system_or_fallback_flaw`：fallback / malformed JSON / system-meta flaw。
- `review_context_limitation_flaw`：上下文不足导致的 limitation，不能直接作为 paper flaw。
- `confirmed_or_trusted_hard_flaw`：grounded/confirmed high-confidence major/critical flaw。
- `candidate_hard_flaw`：高置信 candidate major/critical flaw，应作为 reject_like 或 not_assessable blocker，但不能等同 confirmed flaw。
"""


def render_audit(rows: Sequence[Dict[str, Any]], agg: Dict[str, Any]) -> str:
    summary = [[k, v] for k, v in agg.items() if k != "view_counts"]
    summary.extend([[f"view:{k}", v] for k, v in sorted(agg["view_counts"].items())])
    gold_accept = []
    for r in rows:
        if r.get("gold_decision") == "accept":
            gold_accept.append([
                r["paper_id"], r["classifier_view"], r["real_strong_support_total"], r["method_support_total"],
                r["paper_empirical_open"], r["paper_method_open"], r["review_context_limitation"],
                r["candidate_hard_flaw"], r["confirmed_or_trusted_hard_flaw"],
            ])
    return "# Final-View Unresolved / Candidate-Flaw Classifier v1 Audit\n\n## 汇总\n\n" + md_table(["metric", "value"], summary) + "\n\n## Gold accept cases\n\n" + md_table(["paper_id", "view", "real", "method", "emp_open", "method_open", "context_limit", "candidate_hard", "trusted_hard"], gold_accept)


def render_case_table(rows: Sequence[Dict[str, Any]]) -> str:
    table = []
    for r in rows:
        if r.get("gold_decision") == "accept" or r["classifier_view"] in {"accept_like", "borderline_positive", "not_assessable"}:
            table.append([
                r["paper_id"], r.get("gold_decision"), r["runtime_pred"], r["classifier_view"],
                r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["method_support_total"],
                r["paper_empirical_open"], r["paper_method_open"], r["open_review_question"], r["review_context_limitation"], r["candidate_hard_flaw"],
            ])
    return "# Final-View Unresolved / Candidate-Flaw Classifier v1 Case Table\n\n" + md_table(["paper_id", "gold", "runtime", "view", "real", "nonabs", "empirical", "method", "emp_open", "method_open", "open_question", "context_limit", "candidate_hard"], table)


def render_simulation(result: Dict[str, Any], agg: Dict[str, Any]) -> str:
    rows = [["classifier_view", result["accuracy"], result["macro_f1"], result["accept_recall"], result["reject_recall"], result["predicted_accept_count"], ", ".join(result["false_accept_ids"]) or "无", ", ".join(result["recovered_accept_ids"]) or "无"]]
    text = "# Final-View Unresolved / Candidate-Flaw Classifier v1 Simulation\n\n"
    text += md_table(["rule", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"], rows)
    text += "\n\n## View counts\n\n" + md_table(["view", "count"], sorted(agg["view_counts"].items()))
    return text


def render_decision(result: Dict[str, Any], agg: Dict[str, Any]) -> str:
    return f"""# Final-View Unresolved / Candidate-Flaw Classifier v1 Decision

## 结论

本轮分类器支持继续推进 final-view derived recommendation，但仍不应改 live state。

- `classifier_view` 恢复 accept：`{', '.join(result['recovered_accept_ids']) or '无'}`。
- false accept：`{', '.join(result['false_accept_ids']) or '无'}`。
- `review_context_limitation` 总数：`{agg['review_context_limitation']}`。
- `open_review_question` 总数：`{agg['open_review_question']}`。
- `candidate_hard_flaw` 总数：`{agg['candidate_hard_flaw']}`。
- `system_or_fallback_flaw` 总数：`{agg['system_or_fallback_flaw']}`。

## 对论文主线的含义

当前系统的 reject bias 不是单纯阈值问题。大量 negative item 实际属于系统限制、上下文限制、未验证候选或普通待查问题。它们需要在 final-view 层被分区展示：Confirmed Weaknesses、Potential Concerns、Review Limitations、Unresolved Questions，而不是全部压成 Key Weaknesses。

## 下一步

下一步可以做 **Criterion-Aware Final Report Section v2 / Final-View Report Renderer v1**：把这些分类用于报告渲染，不进入 live state，不直接改变 runtime manager。推荐先改 report rendering，再考虑 final recommendation policy runtime 化。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True, type=Path)
    parser.add_argument("--support-summary", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--doc-dir", required=True, type=Path)
    parser.add_argument("--doc-prefix", default="FINAL_VIEW_UNRESOLVED_CANDIDATE_CLASSIFIER_V1")
    args = parser.parse_args()
    jsonl_rows = load_jsonl(args.jsonl)
    support_rows = load_json(args.support_summary)["rows"]
    rows = derive_rows(jsonl_rows, support_rows)
    agg = aggregate(rows)
    result = metrics(rows)
    output = {"jsonl": str(args.jsonl), "support_summary": str(args.support_summary), "aggregate": agg, "metrics": result, "rows": rows}
    write_json(args.output_json, output)
    prefix = args.doc_prefix
    write_md(args.doc_dir / f"{prefix}_SCHEMA.md", render_schema())
    write_md(args.doc_dir / f"{prefix}_AUDIT.md", render_audit(rows, agg))
    write_md(args.doc_dir / f"{prefix}_CASE_TABLE.md", render_case_table(rows))
    write_md(args.doc_dir / f"{prefix}_SIMULATION.md", render_simulation(result, agg))
    write_md(args.doc_dir / f"{prefix}_DECISION.md", render_decision(result, agg))
    print(json.dumps({"output_json": str(args.output_json), "aggregate": agg, "metrics": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
