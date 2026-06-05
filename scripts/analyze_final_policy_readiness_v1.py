#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence

try:
    import pyarrow.parquet as pq
except Exception:
    pq = None

SUPPORT_STANCES = {"supports", "partially_supports"}
META_RE = re.compile(r"excerpt|truncated|not available|cannot verify|could not verify|fallback|recovery failure|system|agent|raw output|parse|prompt|instruction|format requirements|insufficient context", re.I)
CLAIM_GAP_RE = re.compile(r"claim\s+(claim-[\w-]+)\s+lacks grounded supporting evidence", re.I)


def norm(x: Any) -> str:
    return str(x or "").strip().lower()


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_gold(dataset: Path) -> Dict[str, str]:
    if not dataset.exists() or pq is None:
        return {}
    out = {}
    for row in pq.read_table(dataset).to_pylist():
        env = row.get("env_kwargs") or {}
        pid = row.get("id") or env.get("paper_id")
        decision = norm(row.get("decision") or env.get("ground_truth_decision"))
        if pid and decision in {"accept", "reject"}:
            out[str(pid)] = decision
    return out


def gold_for(row: Dict[str, Any], gold_map: Dict[str, str]) -> str:
    pid = str(row.get("paper_id") or "")
    if pid in gold_map:
        return gold_map[pid]
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision"))
    return explicit if explicit in {"accept", "reject"} else "unknown"


def pred_for(row: Dict[str, Any]) -> str:
    st = row.get("review_state") or {}
    pred = norm(row.get("final_decision") or st.get("final_decision"))
    return pred if pred in {"accept", "reject"} else "reject"


def is_real_claim(cid: Any) -> bool:
    s = norm(cid)
    return bool(s) and "fallback" not in s and "general" not in s and "unbound" not in s


def evidence_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ["source", "support_source_bucket", "support_quality", "support_quality_reason", "binding_rationale", "evidence"])


def corrected_support_bucket(ev: Dict[str, Any]) -> str:
    source = norm(ev.get("source"))
    bucket = norm(ev.get("support_source_bucket"))
    text = evidence_text(ev).lower()
    if "abstract" in source or bucket == "abstract":
        return "abstract"
    if "ablation" in source or bucket == "ablation" or re.search(r"\bablat", text):
        return "ablation"
    if any(x in source for x in ["table", "figure", "fig"]):
        return "table_or_figure"
    if any(x in text for x in ["table", "figure", "fig."]):
        return "table_or_figure"
    if bucket in {"result_or_experiment", "experiment", "results", "evaluation"}:
        return "empirical_result"
    if any(x in text for x in ["experiment", "evaluation", "result", "baseline", "dataset", "metric", "benchmark", "performance", "outperform"]):
        return "empirical_result"
    if bucket in {"method_or_approach", "method_or_design", "method"}:
        return "method"
    if any(x in text for x in ["method", "approach", "model", "framework", "algorithm", "architecture"]):
        return "method"
    return "unknown"


def is_strong_support(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in SUPPORT_STANCES and norm(ev.get("strength")) == "strong"


def claim_support_index(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"strong": 0, "nonabstract": 0, "empirical": 0, "method": 0, "ids": []})
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict) or not is_strong_support(ev) or not is_real_claim(ev.get("claim_id")):
            continue
        cid = str(ev.get("claim_id"))
        bucket = corrected_support_bucket(ev)
        idx[cid]["strong"] += 1
        idx[cid]["ids"].append(ev.get("evidence_id"))
        if bucket != "abstract":
            idx[cid]["nonabstract"] += 1
        if bucket in {"empirical_result", "table_or_figure", "ablation"}:
            idx[cid]["empirical"] += 1
        if bucket == "method":
            idx[cid]["method"] += 1
    return idx


def analyze_support(rows: List[Dict[str, Any]], gold: Dict[str, str]) -> Dict[str, Any]:
    c = Counter()
    cases = []
    ablation_suspects = []
    for row in rows:
        st = row.get("review_state") or {}
        pid = str(row.get("paper_id"))
        by_bucket = Counter()
        real_strong = 0
        support_claims = set()
        groups = set()
        for ev in st.get("evidence_map", []) or []:
            if not isinstance(ev, dict) or not is_strong_support(ev):
                continue
            if not is_real_claim(ev.get("claim_id")):
                c["fallback_or_unbound_strong"] += 1
                continue
            real_strong += 1
            support_claims.add(str(ev.get("claim_id")))
            bucket = corrected_support_bucket(ev)
            by_bucket[bucket] += 1
            groups.add((str(ev.get("claim_id")), bucket, re.sub(r"\W+", " ", str(ev.get("evidence") or "").lower())[:80]))
            raw_text = evidence_text(ev).lower()
            if "ablation" in raw_text and bucket != "ablation":
                ablation_suspects.append({"paper_id": pid, "evidence_id": ev.get("evidence_id"), "bucket": bucket, "source": ev.get("source"), "support_source_bucket": ev.get("support_source_bucket"), "support_quality": ev.get("support_quality")})
        for k, v in by_bucket.items():
            c[f"strong_{k}"] += v
        c["real_strong_total"] += real_strong
        c["independent_group_total"] += len(groups)
        c["rows_with_2plus_independent_groups"] += int(len(groups) >= 2)
        c["rows_with_method_plus_empirical"] += int(by_bucket["method"] > 0 and (by_bucket["empirical_result"] + by_bucket["table_or_figure"] + by_bucket["ablation"]) > 0)
        c["claims_with_support_total"] += len(support_claims)
        cases.append({
            "paper_id": pid,
            "gold": gold_for(row, gold),
            "pred": pred_for(row),
            "real_strong": real_strong,
            "abstract": by_bucket["abstract"],
            "method": by_bucket["method"],
            "empirical_result": by_bucket["empirical_result"],
            "table_or_figure": by_bucket["table_or_figure"],
            "ablation": by_bucket["ablation"],
            "unknown": by_bucket["unknown"],
            "independent_groups": len(groups),
            "method_plus_empirical": by_bucket["method"] > 0 and (by_bucket["empirical_result"] + by_bucket["table_or_figure"] + by_bucket["ablation"]) > 0,
            "support_claims": len(support_claims),
        })
    return {"summary": dict(c), "case_rows": cases, "ablation_suspects": ablation_suspects[:30]}


def analyze_unresolved_gaps(rows: List[Dict[str, Any]], gold: Dict[str, str]) -> Dict[str, Any]:
    c = Counter()
    cases = []
    examples = []
    for row in rows:
        st = row.get("review_state") or {}
        pid = str(row.get("paper_id"))
        support = claim_support_index(st)
        stale_gaps = paper_gaps = meta_gaps = 0
        for gap in st.get("evidence_gaps", []) or []:
            text = str(gap)
            m = CLAIM_GAP_RE.search(text)
            if META_RE.search(text):
                meta_gaps += 1
            elif m and support.get(m.group(1), {}).get("strong", 0) > 0:
                stale_gaps += 1
                if len(examples) < 20:
                    examples.append({"paper_id": pid, "type": "stale_gap", "text": text, "support": support.get(m.group(1))})
            else:
                paper_gaps += 1
        stale_unresolved = meta_unresolved = targetless_unresolved = paper_unresolved = 0
        for q in st.get("unresolved_questions", []) or []:
            qtext = " ".join(str(q.get(k) or "") for k in ["question", "status", "source", "reason"] if isinstance(q, dict)) if isinstance(q, dict) else str(q)
            rel = q.get("related_claim_ids", []) if isinstance(q, dict) else []
            if META_RE.search(qtext):
                meta_unresolved += 1
            elif rel and any(support.get(str(cid), {}).get("strong", 0) > 0 for cid in rel):
                stale_unresolved += 1
            elif not rel:
                targetless_unresolved += 1
            else:
                paper_unresolved += 1
        c["stale_gap_count"] += stale_gaps
        c["paper_gap_count"] += paper_gaps
        c["meta_gap_count"] += meta_gaps
        c["stale_unresolved_count"] += stale_unresolved
        c["meta_unresolved_count"] += meta_unresolved
        c["targetless_unresolved_count"] += targetless_unresolved
        c["paper_unresolved_count"] += paper_unresolved
        cases.append({
            "paper_id": pid,
            "gold": gold_for(row, gold),
            "pred": pred_for(row),
            "total_gaps": len(st.get("evidence_gaps", []) or []),
            "stale_gaps": stale_gaps,
            "paper_gaps": paper_gaps,
            "meta_gaps": meta_gaps,
            "total_unresolved": len(st.get("unresolved_questions", []) or []),
            "stale_unresolved": stale_unresolved,
            "meta_unresolved": meta_unresolved,
            "targetless_unresolved": targetless_unresolved,
            "paper_unresolved": paper_unresolved,
        })
    return {"summary": dict(c), "case_rows": cases, "examples": examples}


def flaw_kind(flaw: Dict[str, Any]) -> str:
    text = " ".join(str(flaw.get(k) or "") for k in ["source", "grounding_status", "status", "title", "description", "hygiene_status_reason"])
    nt = text.lower()
    if "fallback" in nt or META_RE.search(text):
        return "fallback_or_meta"
    if norm(flaw.get("status")) in {"downgraded", "retracted", "resolved"}:
        return "downgraded_or_resolved"
    if norm(flaw.get("grounding_status")) in {"grounded", "paper_grounded"} or flaw.get("evidence_ids"):
        sev = norm(flaw.get("severity"))
        if sev in {"critical", "major"}:
            return "grounded_major_or_critical"
        return "grounded_minor_or_candidate"
    return "ungrounded_candidate"


def analyze_flaws(rows: List[Dict[str, Any]], gold: Dict[str, str]) -> Dict[str, Any]:
    c = Counter()
    cases = []
    examples = []
    for row in rows:
        st = row.get("review_state") or {}
        pid = str(row.get("paper_id"))
        kinds = Counter()
        for flaw in st.get("flaw_candidates", []) or []:
            if not isinstance(flaw, dict):
                continue
            k = flaw_kind(flaw)
            kinds[k] += 1
            c[k] += 1
            if k in {"fallback_or_meta", "grounded_major_or_critical"} and len(examples) < 30:
                examples.append({"paper_id": pid, "kind": k, "flaw_id": flaw.get("flaw_id"), "severity": flaw.get("severity"), "status": flaw.get("status"), "source": flaw.get("source"), "title": str(flaw.get("title") or "")[:140]})
        cases.append({
            "paper_id": pid,
            "gold": gold_for(row, gold),
            "pred": pred_for(row),
            "total_flaws": len(st.get("flaw_candidates", []) or []),
            **{k: kinds.get(k, 0) for k in ["fallback_or_meta", "downgraded_or_resolved", "grounded_major_or_critical", "grounded_minor_or_candidate", "ungrounded_candidate"]},
        })
    return {"summary": dict(c), "case_rows": cases, "examples": examples}


def metric_from_preds(case_preds: List[Dict[str, Any]]) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept = []
    false_reject = []
    recovered = []
    borderline = []
    for r in case_preds:
        gold = r["gold"]
        pred = r["binary_pred"]
        if r.get("view") in {"borderline", "not_assessable"}:
            borderline.append(r["paper_id"])
        if gold == "accept" and pred == "accept":
            tp += 1; recovered.append(r["paper_id"])
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1; false_accept.append(r["paper_id"])
        elif gold == "accept" and pred == "reject":
            fn += 1; false_reject.append(r["paper_id"])
    n = max(1, tp + tn + fp + fn)
    ar = tp / max(1, tp + fn)
    rr = tn / max(1, tn + fp)
    ap = tp / max(1, tp + fp)
    rp = tn / max(1, tn + fn)
    af1 = 0 if ap + ar == 0 else 2 * ap * ar / (ap + ar)
    rf1 = 0 if rp + rr == 0 else 2 * rp * rr / (rp + rr)
    return {"accuracy": round((tp+tn)/n,4), "macro_f1": round((af1+rf1)/2,4), "accept_recall": round(ar,4), "reject_recall": round(rr,4), "predicted_accept_count": tp+fp, "false_accept_ids": false_accept, "false_reject_ids": false_reject, "recovered_accept_ids": recovered, "borderline_ids": borderline}


def simulate_recommendation(support: Dict[str, Any], gaps: Dict[str, Any], flaws: Dict[str, Any]) -> Dict[str, Any]:
    supp = {r["paper_id"]: r for r in support["case_rows"]}
    gap = {r["paper_id"]: r for r in gaps["case_rows"]}
    fl = {r["paper_id"]: r for r in flaws["case_rows"]}
    sims = {}
    for rule in ["current_runtime", "support_quality", "hard_negative_aware", "combined_three_way"]:
        preds = []
        for pid, sr in supp.items():
            gr = gap[pid]
            fr = fl[pid]
            gold = sr["gold"]
            runtime = sr["pred"]
            view = "reject_like"
            binary = runtime
            if rule == "current_runtime":
                binary = runtime if runtime in {"accept", "reject"} else "reject"
                view = "accept_like" if binary == "accept" else "reject_like"
            elif rule == "support_quality":
                ok = (sr["real_strong"] - sr["abstract"]) >= 2 and sr["independent_groups"] >= 2 and sr["empirical_result"] + sr["table_or_figure"] + sr["ablation"] >= 1
                binary = "accept" if ok else "reject"
                view = "accept_like" if ok else "reject_like"
            elif rule == "hard_negative_aware":
                hard = fr["grounded_major_or_critical"] > 0
                accept_signal = (sr["real_strong"] - sr["abstract"]) >= 2 and sr["independent_groups"] >= 2
                if hard:
                    view, binary = "reject_like", "reject"
                elif accept_signal:
                    view, binary = "borderline", "reject"
                else:
                    view, binary = "not_assessable", "reject"
            else:
                hard = fr["grounded_major_or_critical"] > 0
                stale_burden = gr["stale_gaps"] + gr["stale_unresolved"] + gr["meta_unresolved"]
                accept_signal = (sr["real_strong"] - sr["abstract"]) >= 2 and sr["independent_groups"] >= 2 and (sr["empirical_result"] + sr["table_or_figure"] + sr["ablation"] >= 1)
                if hard:
                    view, binary = "reject_like", "reject"
                elif accept_signal and stale_burden <= 2 and gr["paper_unresolved"] <= 3:
                    view, binary = "accept_like", "accept"
                elif accept_signal:
                    view, binary = "borderline", "reject"
                else:
                    view, binary = "not_assessable", "reject"
            preds.append({"paper_id": pid, "gold": gold, "view": view, "binary_pred": binary})
        sims[rule] = {"metrics": metric_from_preds(preds), "view_counts": dict(Counter(p["view"] for p in preds)), "case_preds": preds}
    return sims


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip()+"\n", encoding="utf-8")


def render_support_md(data: Dict[str, Any]) -> str:
    s = data["summary"]
    rows = [[k, s.get(k, 0)] for k in ["real_strong_total", "strong_abstract", "strong_method", "strong_empirical_result", "strong_table_or_figure", "strong_ablation", "strong_unknown", "fallback_or_unbound_strong", "independent_group_total", "rows_with_2plus_independent_groups", "rows_with_method_plus_empirical"]]
    case_rows = [[r["paper_id"], r["gold"], r["pred"], r["real_strong"], r["abstract"], r["method"], r["empirical_result"], r["table_or_figure"], r["ablation"], r["independent_groups"], r["method_plus_empirical"]] for r in data["case_rows"]]
    return "\n\n".join(["# Support Quality Final Audit 4B Clean", "## 结论", "clean run 的 strong support 绑定仍然干净，但早先 `ablation=19 / table=0` 的口径不能直接当真：`empirical_or_ablation_support` 是通用标签，必须用更严格的 corrected bucket 区分 abstract/method/result/table/ablation。", "## 汇总", table(["metric", "value"], rows), "## 逐样本", table(["paper_id","gold","pred","real","abstract","method","result","table_fig","ablation","independent_groups","method_plus_empirical"], case_rows)])


def render_gap_md(data: Dict[str, Any]) -> str:
    s = data["summary"]
    rows = [[k, s.get(k, 0)] for k in ["stale_gap_count", "paper_gap_count", "meta_gap_count", "stale_unresolved_count", "meta_unresolved_count", "targetless_unresolved_count", "paper_unresolved_count"]]
    case_rows = [[r["paper_id"], r["gold"], r["pred"], r["total_gaps"], r["stale_gaps"], r["paper_gaps"], r["total_unresolved"], r["targetless_unresolved"], r["paper_unresolved"]] for r in data["case_rows"]]
    return "\n\n".join(["# Unresolved / Gap Lifecycle Audit", "## 结论", "负面状态仍是 final decision collapse 的主要压力源。大量 unresolved 没有 target claim，很多 gap 是 `claim lacks grounded evidence` 这类可被后续 support 反证或需要 final-view 重新判定的中间状态。下一步仍不建议 live 清理，应先在 final-view policy 中区分 paper-grounded 与 stale/system burden。", "## 汇总", table(["metric", "value"], rows), "## 逐样本", table(["paper_id","gold","pred","gaps","stale_gaps","paper_gaps","unresolved","targetless_unresolved","paper_unresolved"], case_rows[:39])])


def render_flaw_md(data: Dict[str, Any]) -> str:
    s = data["summary"]
    rows = [[k, s.get(k, 0)] for k in ["fallback_or_meta", "downgraded_or_resolved", "grounded_major_or_critical", "grounded_minor_or_candidate", "ungrounded_candidate"]]
    case_rows = [[r["paper_id"], r["gold"], r["pred"], r["total_flaws"], r["fallback_or_meta"], r["grounded_major_or_critical"], r["ungrounded_candidate"], r["downgraded_or_resolved"]] for r in data["case_rows"]]
    return "\n\n".join(["# Flaw Lifecycle Final Audit", "## 结论", "flaw 层仍需要 final-view lifecycle：fallback/meta flaw 和 downgraded flaw 不应进入 confirmed weakness；grounded major/critical flaw 才能作为强 reject blocker。当前不应让 candidate flaw 直接等同 confirmed flaw。", "## 汇总", table(["flaw_kind", "count"], rows), "## 逐样本", table(["paper_id","gold","pred","total","fallback_meta","grounded_major","ungrounded_candidate","downgraded"], case_rows)])


def render_sim_md(sims: Dict[str, Any]) -> str:
    rows = []
    for name, data in sims.items():
        m = data["metrics"]
        rows.append([name, data["view_counts"], m["accuracy"], m["macro_f1"], m["accept_recall"], m["reject_recall"], m["predicted_accept_count"], ", ".join(m["false_accept_ids"]) or "无", ", ".join(m["recovered_accept_ids"]) or "无"])
    return "\n\n".join(["# Final Recommendation Policy Simulation V2", "## 结论", "单纯 support-quality 规则会产生 accept，但必须结合 hard-negative / unresolved lifecycle 才能避免把正向 evidence 误当充分接收条件。当前最稳妥的正式口径仍是多类 recommendation view：`accept_like / borderline / reject_like / not_assessable`；runtime binary accept/reject 不作为主指标。", "## Simulation", table(["rule","view_counts","accuracy","macro_f1","accept_recall","reject_recall","pred_accept","false_accept","recovered_accept"], rows), "## 下一步", "保留 clean 4B dry-run baseline；正式主试验前把 final recommendation 固定为 final-view 派生口径，不改 live state，不回 controller。"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="MAINLINE_FINAL_V1_CLEAN_4B_FULLTEST39_20260502.jsonl", type=Path)
    ap.add_argument("--dataset", default="/reviewF/datasets/drmas_review/test.parquet", type=Path)
    ap.add_argument("--outdir", default="docs/experiments/mainline_current", type=Path)
    ap.add_argument("--json", default="MAINLINE_FINAL_V1_CLEAN_4B_LIFECYCLE_AUDIT_V1.json", type=Path)
    args = ap.parse_args()
    rows = load_jsonl(args.input)
    gold = load_gold(args.dataset)
    support = analyze_support(rows, gold)
    gaps = analyze_unresolved_gaps(rows, gold)
    flaws = analyze_flaws(rows, gold)
    sims = simulate_recommendation(support, gaps, flaws)
    payload = {"input": str(args.input), "support": support, "unresolved_gap": gaps, "flaw": flaws, "recommendation_simulation": sims}
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write(args.outdir / "SUPPORT_QUALITY_FINAL_AUDIT_4B_CLEAN.md", render_support_md(support))
    write(args.outdir / "UNRESOLVED_GAP_LIFECYCLE_AUDIT.md", render_gap_md(gaps))
    write(args.outdir / "FLAW_LIFECYCLE_FINAL_AUDIT.md", render_flaw_md(flaws))
    write(args.outdir / "FINAL_RECOMMENDATION_POLICY_SIMULATION_V2.md", render_sim_md(sims))
    print(json.dumps({"support": support["summary"], "unresolved_gap": gaps["summary"], "flaw": flaws["summary"], "simulation": {k: v["metrics"] for k,v in sims.items()}}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
