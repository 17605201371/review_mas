#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

META_RE = re.compile(r"\b(excerpt|truncat|cut off|cuts off|provided text|provided paper|full text|complete text|not available|not provided|missing section|missing results section|insufficient context|cannot assess|not assessable|cannot verify|unable to verify|fallback|malformed|raw output|parse|parser|system|agent|prompt|format requirements)\b", re.I)
NEGATIVE_RE = re.compile(r"\b(lack|lacks|missing|insufficient|weak|limited|unclear|unsupported|inadequate|fails? to|does not|cannot|could not|absence|concern|flaw|limitation|not demonstrate|no evidence|without)\b", re.I)
EMPIRICAL_RE = re.compile(r"\b(experiment|evaluation|baseline|ablation|dataset|metric|result|table|figure|benchmark|comparison|empirical|performance)\b", re.I)
SOUNDNESS_RE = re.compile(r"\b(method|algorithm|assumption|validity|soundness|proof|theory|mechanism|architecture|objective|training)\b", re.I)
NOVELTY_RE = re.compile(r"\b(novelty|novel|original|incremental|prior work|related work|contribution|significance)\b", re.I)
SUPPORT_STANCES = {"supports", "partially_supports"}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def is_real_claim(claim_id: Any) -> bool:
    value = norm(claim_id)
    return bool(value) and "fallback" not in value and "general" not in value and "unbound" not in value


def as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def item_text(item: Any) -> str:
    if isinstance(item, dict):
        keys = ("title", "description", "question", "note", "reason", "source", "status", "severity")
        return " ".join(str(item.get(key) or "") for key in keys)
    return str(item or "")


def evidence_ids(item: Any) -> List[str]:
    if not isinstance(item, dict):
        return []
    ids = item.get("evidence_ids") or item.get("supporting_evidence_ids") or []
    return [str(x) for x in as_list(ids) if str(x).strip()]


def claim_ids(item: Any) -> List[str]:
    if not isinstance(item, dict):
        return []
    ids = item.get("related_claim_ids") or item.get("claim_ids") or item.get("target_claim_ids") or []
    return [str(x) for x in as_list(ids) if str(x).strip()]


def evidence_map(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(ev.get("evidence_id")): ev for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict) and ev.get("evidence_id")}


def evidence_real_bound(ids: Iterable[str], ev_map: Dict[str, Dict[str, Any]]) -> bool:
    for evid in ids:
        ev = ev_map.get(str(evid))
        if not ev:
            continue
        if norm(ev.get("source")) == "fallback-extraction":
            continue
        if is_real_claim(ev.get("claim_id")):
            return True
    return False


def criterion_for_text(text: str) -> str:
    if EMPIRICAL_RE.search(text):
        return "empirical"
    if SOUNDNESS_RE.search(text):
        return "soundness"
    if NOVELTY_RE.search(text):
        return "novelty_significance"
    return "general"


def strong_support_count(state: Dict[str, Any]) -> int:
    total = 0
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict):
            continue
        if norm(ev.get("stance")) in SUPPORT_STANCES and norm(ev.get("strength")) == "strong" and is_real_claim(ev.get("claim_id")):
            total += 1
    return total


def support_quality_signal(rec: Dict[str, Any]) -> bool:
    return int(rec.get("real_strong") or 0) >= 2 and int(rec.get("nonabstract_support") or 0) >= 2 and int(rec.get("empirical_support") or 0) >= 1 and int(rec.get("independent_groups") or 0) >= 2


def criterion_negative_grounded(criterion_row: Dict[str, Any], criterion: str) -> bool:
    if criterion == "empirical":
        keys = ["criterion_negative_grounded_empirical", "criterion_state_grounded_empirical"]
    elif criterion == "soundness":
        keys = ["criterion_negative_grounded_soundness", "criterion_state_grounded_soundness"]
    elif criterion == "novelty_significance":
        keys = ["criterion_negative_grounded_novelty", "criterion_negative_grounded_significance"]
    else:
        keys = []
    return any(bool(criterion_row.get(key)) for key in keys)


def classify_issue(item: Any, ev_map: Dict[str, Dict[str, Any]], criterion_row: Dict[str, Any]) -> Dict[str, Any]:
    text = item_text(item)
    criterion = criterion_for_text(text)
    meta = bool(META_RE.search(text))
    negative = bool(NEGATIVE_RE.search(text))
    evids = evidence_ids(item)
    claims = claim_ids(item)
    real_evidence = evidence_real_bound(evids, ev_map)
    real_claim = any(is_real_claim(cid) for cid in claims)
    criterion_grounded = criterion_negative_grounded(criterion_row, criterion)
    if meta:
        category = "review_context_limitation"
    elif negative and criterion in {"empirical", "soundness"} and (real_evidence or real_claim or criterion_grounded):
        category = "grounded_actionable_hard_negative"
    elif negative and criterion in {"empirical", "soundness", "novelty_significance"}:
        category = "ungrounded_negative_unresolved"
    elif negative:
        category = "weak_negative_unresolved"
    elif not claims and not evids:
        category = "targetless_open_question"
    else:
        category = "paper_open_question"
    return {
        "category": category,
        "criterion": criterion,
        "meta": meta,
        "negative": negative,
        "real_evidence_bound": real_evidence,
        "real_claim_bound": real_claim,
        "criterion_grounded": criterion_grounded,
        "evidence_ids": evids,
        "claim_ids": claims,
        "text": " ".join(text.split())[:260],
    }


def classify_flaw(flaw: Dict[str, Any], ev_map: Dict[str, Dict[str, Any]], criterion_row: Dict[str, Any]) -> Dict[str, Any]:
    base = classify_issue(flaw, ev_map, criterion_row)
    severity = norm(flaw.get("severity"))
    status = norm(flaw.get("status")) or "candidate"
    grounded = base["real_evidence_bound"] or base["real_claim_bound"] or base["criterion_grounded"]
    if base["category"] == "review_context_limitation":
        category = "review_context_limitation_flaw"
    elif severity in {"major", "critical"} and status == "confirmed" and grounded:
        category = "confirmed_grounded_hard_flaw"
    elif severity in {"major", "critical"} and grounded:
        category = "candidate_grounded_hard_flaw"
    elif severity in {"major", "critical"}:
        category = "candidate_ungrounded_hard_flaw"
    else:
        category = base["category"]
    base.update({"category": category, "severity": severity, "status": status})
    return base


def derive_case(row: Dict[str, Any], rec: Dict[str, Any], criterion_row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    ev_map = evidence_map(state)
    unresolved = [classify_issue(item, ev_map, criterion_row) for item in state.get("unresolved_questions", []) or []]
    flaws = [classify_flaw(item, ev_map, criterion_row) for item in state.get("flaw_candidates", []) or [] if isinstance(item, dict)]
    unresolved_counts = Counter(item["category"] for item in unresolved)
    flaw_counts = Counter(item["category"] for item in flaws)
    grounded_hard_negative = flaw_counts["confirmed_grounded_hard_flaw"] + flaw_counts["candidate_grounded_hard_flaw"] + unresolved_counts["grounded_actionable_hard_negative"]
    context_limitations = unresolved_counts["review_context_limitation"] + flaw_counts["review_context_limitation_flaw"]
    ungrounded_negative = unresolved_counts["ungrounded_negative_unresolved"] + unresolved_counts["weak_negative_unresolved"] + flaw_counts["candidate_ungrounded_hard_flaw"]
    targetless_questions = unresolved_counts["targetless_open_question"]
    old_view = rec.get("final_view_v2") or "not_assessable"
    if grounded_hard_negative > 0:
        v4 = "reject_like"
        reason = "grounded_or_candidate_hard_negative_present"
    elif context_limitations > 0 and support_quality_signal(rec):
        v4 = "not_assessable_context_limited"
        reason = "support_positive_but_review_context_limited"
    elif ungrounded_negative > 0:
        v4 = "not_assessable_hard_negative_unverified"
        reason = "negative_concern_exists_but_not_grounded"
    elif targetless_questions >= 3:
        v4 = "not_assessable_targetless_unresolved"
        reason = "targetless_unresolved_too_high"
    elif support_quality_signal(rec):
        v4 = "borderline_positive"
        reason = "support_positive_no_grounded_blocker_found"
    else:
        v4 = "borderline_insufficient"
        reason = "insufficient_support_or_grounding"
    examples = [x for x in unresolved + flaws if x["category"] in {"grounded_actionable_hard_negative", "confirmed_grounded_hard_flaw", "candidate_grounded_hard_flaw", "ungrounded_negative_unresolved", "review_context_limitation", "review_context_limitation_flaw"}]
    return {
        "paper_id": rec.get("paper_id"),
        "gold": rec.get("gold"),
        "runtime_pred": rec.get("runtime_pred"),
        "old_view_v2": old_view,
        "final_view_v4": v4,
        "v4_reason": reason,
        "real_strong": int(rec.get("real_strong") or strong_support_count(state)),
        "nonabstract_support": int(rec.get("nonabstract_support") or 0),
        "empirical_support": int(rec.get("empirical_support") or 0),
        "independent_groups": int(rec.get("independent_groups") or 0),
        "grounded_hard_negative_v2_count": grounded_hard_negative,
        "context_limitation_count": context_limitations,
        "ungrounded_negative_count": ungrounded_negative,
        "targetless_open_question_count": targetless_questions,
        "unresolved_category_counts": dict(unresolved_counts),
        "flaw_category_counts": dict(flaw_counts),
        "examples": examples[:5],
    }


def metrics(rows: List[Dict[str, Any]], accept_labels: set[str]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept: List[str] = []
    recovered_accept: List[str] = []
    for row in rows:
        gold = row.get("gold")
        pred_accept = row.get("final_view_v4") in accept_labels
        if gold == "accept" and pred_accept:
            tp += 1
            recovered_accept.append(row["paper_id"])
        elif gold == "accept":
            fn += 1
        elif gold == "reject" and pred_accept:
            fp += 1
            false_accept.append(row["paper_id"])
        elif gold == "reject":
            tn += 1
    total = max(1, tp + tn + fp + fn)
    acc = (tp + tn) / total
    ar = tp / max(1, tp + fn)
    rr = tn / max(1, tn + fp)
    ap = tp / max(1, tp + fp)
    rp = tn / max(1, tn + fn)
    af1 = 0 if ap + ar == 0 else 2 * ap * ar / (ap + ar)
    rf1 = 0 if rp + rr == 0 else 2 * rp * rr / (rp + rr)
    return {"accuracy": round(acc, 4), "macro_f1": round((af1 + rf1) / 2, 4), "accept_recall": round(ar, 4), "reject_recall": round(rr, 4), "predicted_accept_count": tp + fp, "false_accept_ids": false_accept, "recovered_accept_ids": recovered_accept}


def non_reject_labels(rows: List[Dict[str, Any]]) -> set[str]:
    return {str(row.get("final_view_v4")) for row in rows if row.get("final_view_v4") != "reject_like"}


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def render_docs(payload: Dict[str, Any], outdir: Path) -> None:
    rows = payload["case_rows"]
    write(outdir / "HARD_NEGATIVE_GROUNDING_V2_SCHEMA.md", """# Hard-Negative Grounding v2 Schema

本层是离线 final-view 修复，不改 runtime。v2 的关键变化是：

- `review_context_limitation`: 截断、excerpt、full text unavailable、fallback/malformed/system 相关内容，不能当 hard-negative。
- `grounded_actionable_hard_negative`: empirical 或 soundness 负面疑点，且绑定 evidence、real claim 或 criterion grounding。
- `ungrounded_negative_unresolved`: 有负面语义但没有 evidence/claim/criterion grounding，只能触发 not_assessable，不能触发 reject_like。
- `candidate_grounded_hard_flaw`: major/critical candidate，已有 grounding，但未 confirmed；可作为 reject_like blocker 的候选，需要人工复核。
""")
    audit_rows = [[k, v] for k, v in payload["aggregate"].items() if k != "view_transition_counts"]
    write(outdir / "HARD_NEGATIVE_GROUNDING_V2_AUDIT.md", "# Hard-Negative Grounding v2 Audit\n\n" + table(["metric", "value"], audit_rows) + "\n\n## View transitions\n\n" + table(["transition", "count"], sorted(payload["aggregate"]["view_transition_counts"].items())))
    case_rows = []
    for row in rows:
        if row["old_view_v2"] == "borderline_positive" or row["final_view_v4"].startswith("not_assessable") or row["grounded_hard_negative_v2_count"]:
            case_rows.append([row["paper_id"], row["gold"], row["old_view_v2"], row["final_view_v4"], row["v4_reason"], row["real_strong"], row["empirical_support"], row["grounded_hard_negative_v2_count"], row["context_limitation_count"], row["ungrounded_negative_count"], row["targetless_open_question_count"]])
    write(outdir / "HARD_NEGATIVE_GROUNDING_V2_CASE_TABLE.md", "# Hard-Negative Grounding v2 Case Table\n\n" + table(["paper_id", "gold", "v2", "v4", "reason", "real", "empirical", "grounded_hn", "context_limit", "ungrounded_neg", "targetless"], case_rows))
    sim_rows = [[name, data["accuracy"], data["macro_f1"], data["accept_recall"], data["reject_recall"], data["predicted_accept_count"], ", ".join(data["false_accept_ids"]) or "无", ", ".join(data["recovered_accept_ids"]) or "无"] for name, data in payload["simulations"].items()]
    write(outdir / "FINAL_RECOMMENDATION_POLICY_V4_SIMULATION.md", "# Final Recommendation Policy v4 Simulation\n\n" + table(["mapping", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept", "recovered_accept"], sim_rows))
    write(outdir / "FINAL_RECOMMENDATION_POLICY_V4_FINAL.md", f"""# Final Recommendation Policy v4 Final

## 结论

v4 解决两个问题：

1. hard-negative grounding：不再把 targetless/context-limited negative 当作 hard-negative；只有 evidence/claim/criterion grounded 的 empirical/soundness blocker 才进入 `reject_like`。
2. final recommendation policy：`borderline_positive` 不自动 accept；遇到上下文限制时降为 `not_assessable_context_limited`。

## View 分布

{table(['view_v4', 'count'], sorted(payload['view_v4_counts'].items()))}

## 与 v2 的变化

{table(['transition', 'count'], sorted(payload['aggregate']['view_transition_counts'].items()))}

## Policy

- `reject_like`: grounded hard-negative 存在。
- `not_assessable_context_limited`: 有 support，但审稿上下文不足或 fallback/meta 限制明显。
- `not_assessable_hard_negative_unverified`: 有负面疑点，但没有 grounding。
- `not_assessable_targetless_unresolved`: targetless unresolved 太多。
- `borderline_positive`: 有 support，且没有 grounded blocker / context limitation / ungrounded negative burden。
- `borderline_insufficient`: support 或 grounding 不足。

## 下一步

如果继续优化，不应调 accept 阈值；应做小样本 `Hard-Negative Grounding v2` 人工核查，确认 `grounded_hard_negative_v2_count` 的 precision。
""")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-jsonl", type=Path, required=True)
    ap.add_argument("--recommendation-json", type=Path, required=True)
    ap.add_argument("--criterion-json", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--doc-dir", type=Path, required=True)
    args = ap.parse_args()
    runtime = {str(row.get("paper_id")): row for row in load_jsonl(args.runtime_jsonl)}
    rec_rows = load_json(args.recommendation_json).get("case_rows", [])
    criteria = {str(row.get("paper_id")): row for row in load_json(args.criterion_json).get("rows", [])}
    rows = [derive_case(runtime.get(str(rec.get("paper_id")), {}), rec, criteria.get(str(rec.get("paper_id")), {})) for rec in rec_rows]
    agg = Counter()
    transitions = Counter()
    for row in rows:
        agg[f"gold_{row['gold']}"] += 1
        agg[f"old_view_{row['old_view_v2']}"] += 1
        agg[f"v4_{row['final_view_v4']}"] += 1
        agg["grounded_hard_negative_v2_total"] += row["grounded_hard_negative_v2_count"]
        agg["context_limitation_total"] += row["context_limitation_count"]
        agg["ungrounded_negative_total"] += row["ungrounded_negative_count"]
        agg["targetless_open_question_total"] += row["targetless_open_question_count"]
        transitions[f"{row['old_view_v2']} -> {row['final_view_v4']}"] += 1
    payload = {
        "inputs": {"runtime_jsonl": str(args.runtime_jsonl), "recommendation_json": str(args.recommendation_json), "criterion_json": str(args.criterion_json)},
        "aggregate": {**dict(agg), "view_transition_counts": dict(transitions)},
        "view_v4_counts": dict(Counter(row["final_view_v4"] for row in rows)),
        "case_rows": rows,
        "simulations": {
            "strict_accept_like_only": metrics(rows, {"accept_like"}),
            "borderline_positive_as_accept": metrics(rows, {"accept_like", "borderline_positive"}),
            "context_limited_as_accept_risk": metrics(rows, {"not_assessable_context_limited"}),
            "targetless_unresolved_as_accept_risk": metrics(rows, {"not_assessable_targetless_unresolved"}),
            "unverified_hard_negative_as_accept_risk": metrics(rows, {"not_assessable_hard_negative_unverified"}),
            "all_non_reject_as_accept_upper_bound": metrics(rows, non_reject_labels(rows)),
        },
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    render_docs(payload, args.doc_dir)
    print(json.dumps({"view_v4_counts": payload["view_v4_counts"], "simulations": payload["simulations"], "output_json": str(args.output_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
