#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence

POSITIVE_STANCES = {"supports", "partially_supports"}
ACCEPT_REJECT = {"accept", "reject"}

SECTION_PATTERNS = [
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    ("result", re.compile(r"\b(result|evaluation|experiment|benchmark|baseline|outperform|accuracy|f1|auc|bleu|rouge|win rate|performance)\b", re.I)),
    ("method", re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training objective|loss function|inference)\b", re.I)),
    ("abstract", re.compile(r"\babstract\b|^title$|\btitle\b", re.I)),
    ("introduction", re.compile(r"\bintroduction\b", re.I)),
    ("related_work", re.compile(r"\brelated work\b|\bprior work\b", re.I)),
    ("conclusion", re.compile(r"\bconclusion\b|\bdiscussion\b", re.I)),
]

CRITERIA = {
    "novelty": (re.compile(r"\b(novel|novelty|original|originality|new contribution|first to|prior work|related work)\b", re.I), re.compile(r"\b(lack(?:s|ing)? novelty|not novel|incremental|limited novelty|insufficient novelty)\b", re.I), {"method", "result", "ablation", "table_or_figure", "abstract"}),
    "significance": (re.compile(r"\b(significant|significance|important|impact|contribution|practical|useful|value|relevance)\b", re.I), re.compile(r"\b(limited significance|minor contribution|unclear impact|limited impact|weak contribution)\b", re.I), {"result", "ablation", "table_or_figure", "abstract"}),
    "soundness": (re.compile(r"\b(sound|soundness|valid|validity|method|algorithm|theory|assumption|proof|objective|optimization|design)\b", re.I), re.compile(r"\b(unsound|invalid|flaw(?:ed)? method|methodological flaw|unsupported assumption|weak theory|incorrect)\b", re.I), {"method", "result", "ablation", "table_or_figure"}),
    "empirical": (re.compile(r"\b(empirical|experiment|evaluation|result|baseline|dataset|metric|ablation|table|figure|benchmark)\b", re.I), re.compile(r"\b(insufficient experiment|weak evaluation|missing baseline|no ablation|limited empirical|inadequate experiment)\b", re.I), {"result", "ablation", "table_or_figure"}),
    "clarity": (re.compile(r"\b(clear|clarity|reproducib|readab|implementation|detail|code|hyperparameter|description|presentation)\b", re.I), re.compile(r"\b(unclear|not clear|lacks detail|insufficient detail|hard to reproduce|not reproducible|poorly written)\b", re.I), {"method", "table_or_figure", "result", "abstract"}),
}

META_RE = re.compile(r"\b(excerpt|truncated|not available|cannot verify|could not verify|fallback|recovery failure|system|agent|raw output|parse|complete text|insufficient context)\b", re.I)
NOT_ASSESSABLE_RE = re.compile(r"\b(not assessable|cannot assess|insufficient information|not enough information|needs more context)\b", re.I)


def norm(v: Any) -> str:
    return str(v or "").strip().lower()


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
    cid = str(claim_id or "").lower()
    return bool(cid) and "fallback" not in cid and "general" not in cid


def ev_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ("source", "evidence", "support_quality_reason", "binding_rationale"))


def ev_section(ev: Dict[str, Any]) -> str:
    bucket = norm(ev.get("support_source_bucket"))
    bucket_map = {"result_or_experiment": "result", "method_or_approach": "method", "conclusion_or_discussion": "conclusion", "abstract": "abstract"}
    if bucket in bucket_map:
        return bucket_map[bucket]
    text = ev_text(ev)
    for section, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section
    return "unknown"


def ev_role(ev: Dict[str, Any], section: str) -> str:
    text = ev_text(ev)
    if section in {"result", "table_or_figure"}:
        return "comparison_support" if re.search(r"\b(compare|baseline|outperform|better than|versus|vs\.)\b", text, re.I) else "empirical_result"
    if section == "ablation":
        return "ablation_support"
    if section == "method":
        return "method_description"
    if section == "abstract":
        return "claim_articulation"
    if re.search(r"\b(limitation|future work|weakness)\b", text, re.I):
        return "limitation_discussion"
    if re.search(r"\b(clear|reproduc|implementation detail|hyperparameter)\b", text, re.I):
        return "clarity_support"
    return "unclear"


def ev_depth(section: str, role: str) -> str:
    if section in {"result", "table_or_figure", "ablation"} or role in {"empirical_result", "ablation_support", "comparison_support"}:
        return "deep"
    if section == "method" or role == "method_description":
        return "moderate"
    return "shallow"


def ev_group(ev: Dict[str, Any], section: str, role: str) -> str:
    text = re.sub(r"\W+", " ", str(ev.get("evidence") or "").lower()).strip()
    digest = hashlib.sha1(" ".join(text.split()[:16]).encode("utf-8")).hexdigest()[:8] if text else "empty"
    return f"{ev.get('claim_id') or ''}:{section}:{role}:{digest}"


def enrich_ev(ev: Dict[str, Any]) -> Dict[str, Any]:
    section = ev_section(ev)
    role = ev_role(ev, section)
    depth = ev_depth(section, role)
    out = dict(ev)
    out.update({
        "evidence_section": section,
        "support_role": role,
        "support_depth": depth,
        "is_abstract_only": section == "abstract",
        "is_non_abstract": section not in {"abstract", "unknown"},
        "is_empirical_result": section == "result" or role in {"empirical_result", "comparison_support"},
        "is_table_or_figure_based": section == "table_or_figure",
        "is_ablation_based": section == "ablation" or role == "ablation_support",
        "is_method_based": section == "method" or role == "method_description",
        "is_result_based": section == "result" or role in {"empirical_result", "comparison_support"},
    })
    out["independence_group_id"] = ev_group(out, section, role)
    return out


def is_positive_strong(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) == "strong"


def support_label(real_strong: Sequence[Dict[str, Any]]) -> str:
    if not real_strong:
        return "no_real_strong_support"
    if any(ev["support_depth"] == "deep" for ev in real_strong):
        return "deep_empirical_or_ablation_support"
    if any(ev["support_depth"] == "moderate" for ev in real_strong):
        return "method_grounded_support"
    if all(ev["is_abstract_only"] for ev in real_strong):
        return "abstract_only_support"
    return "mixed_shallow_support"


def is_fallback_or_meta_flaw(flaw: Dict[str, Any]) -> bool:
    flaw_id = norm(flaw.get("flaw_id"))
    source = norm(flaw.get("source"))
    text = " ".join(str(flaw.get(k) or "") for k in ("title", "description", "source", "status")).lower()
    malformed_json_leak = text.strip().startswith("{") or "\"flaw_candidates\"" in text or "the user wants me" in text
    return (
        flaw_id.startswith("flaw-fallback")
        or source in {"fallback", "system_meta", "fallback-extraction"}
        or bool(META_RE.search(text))
        or malformed_json_leak
    )


def flaw_counts(state: Dict[str, Any]) -> Counter:
    c = Counter({
        "major_or_critical_flaws": 0,
        "confirmed_flaws": 0,
        "grounded_flaws": 0,
        "ungrounded_flaws": 0,
        "meta_flaws": 0,
        "trusted_major_or_critical_flaws": 0,
        "trusted_confirmed_flaws": 0,
        "trusted_grounded_flaws": 0,
        "fallback_or_meta_flaws": 0,
    })
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        severity = norm(flaw.get("severity"))
        status = norm(flaw.get("status")) or "candidate"
        is_meta = is_fallback_or_meta_flaw(flaw)
        has_evidence = bool(flaw.get("evidence_ids"))
        if severity in {"critical", "major"}:
            c["major_or_critical_flaws"] += 1
            if not is_meta and status not in {"downgraded", "retracted"}:
                c["trusted_major_or_critical_flaws"] += 1
        if status == "confirmed":
            c["confirmed_flaws"] += 1
            if not is_meta:
                c["trusted_confirmed_flaws"] += 1
        if has_evidence:
            c["grounded_flaws"] += 1
            if not is_meta:
                c["trusted_grounded_flaws"] += 1
        else:
            c["ungrounded_flaws"] += 1
        if is_meta:
            c["meta_flaws"] += 1
            c["fallback_or_meta_flaws"] += 1
    return c


def criterion_audit(row: Dict[str, Any], support_sections: Counter) -> Dict[str, Any]:
    report = str(row.get("final_report") or (row.get("review_state") or {}).get("final_report") or "")
    out: Dict[str, Any] = {}
    covered, grounded, unsupported, meta, not_assess = [], [], [], [], []
    for name, (cover_re, neg_re, ground_sections) in CRITERIA.items():
        is_cov = bool(cover_re.search(report))
        has_neg = bool(neg_re.search(report))
        has_support = any(support_sections.get(s, 0) for s in ground_sections)
        is_na = is_cov and bool(NOT_ASSESSABLE_RE.search(report))
        is_ground = is_cov and (has_support or is_na)
        is_unsupported = int(is_cov and has_neg and not has_support and not is_na)
        has_meta = is_cov and has_neg and bool(META_RE.search(report))
        out[f"criterion_covered_{name}"] = is_cov
        out[f"criterion_grounded_{name}"] = is_ground
        out[f"unsupported_{name}_critique_count"] = is_unsupported
        out[f"criterion_not_assessable_{name}"] = is_na
        out[f"meta_leakage_{name}"] = has_meta
        if is_cov:
            covered.append(name)
        if is_ground:
            grounded.append(name)
        if is_unsupported:
            unsupported.append(name)
        if has_meta:
            meta.append(name)
        if is_na:
            not_assess.append(name)
    out.update({"covered_criteria": covered, "grounded_criteria": grounded, "unsupported_criteria": unsupported, "meta_leakage_criteria": meta, "not_assessable_criteria": not_assess})
    return out


def summarize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    evidence = [enrich_ev(ev) for ev in state.get("evidence_map", []) or [] if isinstance(ev, dict)]
    positive_strong = [ev for ev in evidence if is_positive_strong(ev)]
    real_strong = [ev for ev in positive_strong if is_real_claim_id(ev.get("claim_id"))]
    support_sections = Counter(ev["evidence_section"] for ev in real_strong)
    support_roles = Counter(ev["support_role"] for ev in real_strong)
    claim_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in real_strong:
        claim_groups[str(ev.get("claim_id") or "")].append(ev)
    claim_summaries = {}
    for cid, items in claim_groups.items():
        groups = {ev["independence_group_id"] for ev in items}
        claim_summaries[cid] = {
            "claim_real_strong_support_count": len(items),
            "claim_non_abstract_support_count": sum(ev["is_non_abstract"] for ev in items),
            "claim_empirical_support_count": sum(ev["is_empirical_result"] for ev in items),
            "claim_method_support_count": sum(ev["is_method_based"] for ev in items),
            "claim_table_or_figure_support_count": sum(ev["is_table_or_figure_based"] for ev in items),
            "claim_ablation_support_count": sum(ev["is_ablation_based"] for ev in items),
            "claim_independent_support_group_count": len(groups),
            "claim_has_only_abstract_support": bool(items) and all(ev["is_abstract_only"] for ev in items),
            "claim_has_empirical_support": any(ev["is_empirical_result"] for ev in items),
            "claim_has_method_plus_result_support": any(ev["is_method_based"] for ev in items) and any(ev["is_result_based"] or ev["is_empirical_result"] for ev in items),
            "claim_support_depth_label": support_label(items),
        }
    all_groups = {ev["independence_group_id"] for ev in real_strong}
    sample = {
        "paper_id": row.get("paper_id"),
        "gold_decision": infer_gold(row),
        "original_pred": pred_decision(row),
        "decision_correct": row.get("accept_reject_correct", row.get("decision_correct")),
        "real_strong_support_total": len(real_strong),
        "non_abstract_support_total": sum(ev["is_non_abstract"] for ev in real_strong),
        "empirical_support_total": sum(ev["is_empirical_result"] for ev in real_strong),
        "method_support_total": sum(ev["is_method_based"] for ev in real_strong),
        "table_or_figure_support_total": sum(ev["is_table_or_figure_based"] for ev in real_strong),
        "ablation_support_total": sum(ev["is_ablation_based"] for ev in real_strong),
        "independent_support_group_total": len(all_groups),
        "claims_with_2plus_independent_support": sum(1 for v in claim_summaries.values() if v["claim_independent_support_group_count"] >= 2),
        "claims_with_only_abstract_support": sum(1 for v in claim_summaries.values() if v["claim_has_only_abstract_support"]),
        "claims_with_empirical_support": sum(1 for v in claim_summaries.values() if v["claim_has_empirical_support"]),
        "claims_with_method_plus_result_support": sum(1 for v in claim_summaries.values() if v["claim_has_method_plus_result_support"]),
        "abstract_only_support_count": sum(ev["is_abstract_only"] for ev in real_strong),
        "fallback_or_unbound_strong_support": sum(1 for ev in positive_strong if not is_real_claim_id(ev.get("claim_id"))),
        "support_sections": dict(support_sections),
        "support_roles": dict(support_roles),
        "support_quality_label": support_label(real_strong),
        "unresolved_count": len(state.get("unresolved_questions", []) or []),
    }
    sample.update(flaw_counts(state))
    sample.update(criterion_audit(row, support_sections))
    sample["claim_summaries"] = claim_summaries
    return sample


def blockers(row: Dict[str, Any]) -> bool:
    trusted_major = int(row.get("trusted_major_or_critical_flaws", row.get("major_or_critical_flaws", 0)) or 0)
    trusted_confirmed = int(row.get("trusted_confirmed_flaws", row.get("confirmed_flaws", 0)) or 0)
    return bool(trusted_major >= 1 or trusted_confirmed >= 1)


def confusion(rows: Sequence[Dict[str, Any]], key: str) -> Dict[str, Any]:
    tp = tn = fp = fn = 0
    false_accept, recovered_accept, wrongly_flipped = [], [], []
    for r in rows:
        gold, pred, orig = r.get("gold_decision"), r.get(key), r.get("original_pred")
        if gold not in ACCEPT_REJECT or pred not in ACCEPT_REJECT:
            continue
        if gold == "accept" and pred == "accept":
            tp += 1
            if orig == "reject":
                recovered_accept.append(r["paper_id"])
        elif gold == "accept" and pred == "reject":
            fn += 1
        elif gold == "reject" and pred == "reject":
            tn += 1
        elif gold == "reject" and pred == "accept":
            fp += 1
            false_accept.append(r["paper_id"])
            if orig == "reject":
                wrongly_flipped.append(r["paper_id"])
    total = tp + tn + fp + fn
    acc = (tp + tn) / total if total else 0.0
    ar = tp / (tp + fn) if (tp + fn) else 0.0
    rr = tn / (tn + fp) if (tn + fp) else 0.0
    ap = tp / (tp + fp) if (tp + fp) else 0.0
    rp = tn / (tn + fn) if (tn + fn) else 0.0
    af1 = 2 * ap * ar / (ap + ar) if (ap + ar) else 0.0
    rf1 = 2 * rp * rr / (rp + rr) if (rp + rr) else 0.0
    return {"accuracy": round(acc, 4), "macro_f1": round((af1 + rf1) / 2, 4), "accept_recall": round(ar, 4), "reject_recall": round(rr, 4), "predicted_accept_count": sum(r.get(key) == "accept" for r in rows), "false_accept_ids": false_accept, "recovered_accept_ids": recovered_accept, "wrongly_flipped_reject_ids": wrongly_flipped}


def run_sims(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sims = {
        "original": lambda r: r["original_pred"],
        "sim_a_abstract_only_excluded": lambda r: "accept" if r["non_abstract_support_total"] >= 2 and not blockers(r) else "reject",
        "sim_b_non_abstract_support_ge1": lambda r: "accept" if r["real_strong_support_total"] >= 2 and r["non_abstract_support_total"] >= 1 and not blockers(r) else "reject",
        "sim_c_independent_groups_ge2": lambda r: "accept" if r["independent_support_group_total"] >= 2 and not blockers(r) else "reject",
        "sim_d_empirical_support_for_empirical_claims": lambda r: "accept" if r["empirical_support_total"] >= 1 and r["real_strong_support_total"] >= 2 and not blockers(r) else "reject",
        "sim_e_method_plus_result_combination": lambda r: "accept" if r["method_support_total"] >= 1 and (r["empirical_support_total"] + r["table_or_figure_support_total"] + r["ablation_support_total"]) >= 1 and not blockers(r) else "reject",
        "sim_f_criterion_grounded_accept_signal": lambda r: "accept" if len(r["grounded_criteria"]) >= 3 and r["non_abstract_support_total"] >= 1 and not blockers(r) and not r["unsupported_criteria"] else "reject",
    }
    out = []
    for name, fn in sims.items():
        for r in rows:
            r[name] = fn(r)
        out.append({"simulation_name": name, **confusion(rows, name)})
    return out


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines) + "\n"


def aggregate(rows: Sequence[Dict[str, Any]]) -> Counter:
    c = Counter()
    numeric = ["real_strong_support_total", "non_abstract_support_total", "empirical_support_total", "method_support_total", "table_or_figure_support_total", "ablation_support_total", "independent_support_group_total", "claims_with_2plus_independent_support", "claims_with_only_abstract_support", "claims_with_empirical_support", "claims_with_method_plus_result_support", "fallback_or_unbound_strong_support", "unresolved_count", "major_or_critical_flaws", "confirmed_flaws", "trusted_major_or_critical_flaws", "trusted_confirmed_flaws", "trusted_grounded_flaws", "fallback_or_meta_flaws"]
    for r in rows:
        for k in numeric:
            c[k] += int(r.get(k, 0) or 0)
        for crit in CRITERIA:
            c[f"criterion_covered_{crit}"] += int(bool(r.get(f"criterion_covered_{crit}")))
            c[f"criterion_grounded_{crit}"] += int(bool(r.get(f"criterion_grounded_{crit}")))
            c[f"unsupported_{crit}_critique_count"] += int(r.get(f"unsupported_{crit}_critique_count", 0) or 0)
            c[f"meta_leakage_{crit}"] += int(bool(r.get(f"meta_leakage_{crit}")))
    return c


def write_docs(outdir: Path, dataset: str, input_path: Path, rows: List[Dict[str, Any]], sims: List[Dict[str, Any]]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    agg = aggregate(rows)
    n = len(rows) or 1
    labels = Counter(r["support_quality_label"] for r in rows)
    false_accepts = [r for r in rows if r["gold_decision"] == "reject" and r["original_pred"] == "accept"]
    false_rejects = [r for r in rows if r["gold_decision"] == "accept" and r["original_pred"] == "reject"]
    abstract_false_accepts = [r for r in false_accepts if r["abstract_only_support_count"] and not r["non_abstract_support_total"]]
    accept_without_nonabstract = [r for r in rows if r["gold_decision"] == "accept" and not r["non_abstract_support_total"]]

    (outdir / "SUPPORT_QUALITY_SCHEMA.md").write_text(f"# Support Quality Schema\n\nInput: `{input_path}` (`{dataset}`).\n\nThis is an offline audit only. It derives evidence section, support role, support depth, and independence groups from existing final states. It does not change runtime, prompts, final decisions, thresholds, or live ReviewState.\n", encoding="utf-8")
    support_rows = [["rows", len(rows)], ["real_strong_support_total", agg["real_strong_support_total"]], ["non_abstract_support_total", agg["non_abstract_support_total"]], ["empirical_support_total", agg["empirical_support_total"]], ["method_support_total", agg["method_support_total"]], ["table_or_figure_support_total", agg["table_or_figure_support_total"]], ["ablation_support_total", agg["ablation_support_total"]], ["independent_support_group_total", agg["independent_support_group_total"]], ["claims_with_2plus_independent_support", agg["claims_with_2plus_independent_support"]], ["claims_with_only_abstract_support", agg["claims_with_only_abstract_support"]], ["fallback_or_unbound_strong_support", agg["fallback_or_unbound_strong_support"]], ["trusted_major_or_critical_flaws", agg["trusted_major_or_critical_flaws"]], ["fallback_or_meta_flaws", agg["fallback_or_meta_flaws"]]]
    subgroup_rows = []
    for name, subset in [("false_accept", false_accepts), ("false_reject", false_rejects), ("gold_accept_without_nonabstract", accept_without_nonabstract)]:
        denom = len(subset) or 1
        subgroup_rows.append([name, len(subset), round(sum(r["non_abstract_support_total"] for r in subset) / denom, 3), round(sum(r["independent_support_group_total"] for r in subset) / denom, 3), round(sum(r["empirical_support_total"] for r in subset) / denom, 3)])
    (outdir / "SUPPORT_QUALITY_AUDIT.md").write_text("# Support Quality Audit\n\n" + md_table(["metric", "value"], support_rows) + "\n## Labels\n" + md_table(["label", "rows"], labels.most_common()) + "\n## Error Subsets\n" + md_table(["subset", "rows", "non_abstract_avg", "independent_group_avg", "empirical_avg"], subgroup_rows), encoding="utf-8")
    independence_rows = [[r["paper_id"], r["gold_decision"], r["original_pred"], r["independent_support_group_total"], r["claims_with_2plus_independent_support"], r["support_quality_label"]] for r in rows]
    (outdir / "EVIDENCE_INDEPENDENCE_AUDIT.md").write_text("# Evidence Independence Audit\n\n" + md_table(["paper_id", "gold", "pred", "independent_groups", "claims_2plus_groups", "support_quality"], independence_rows), encoding="utf-8")
    (outdir / "CRITERION_DIMENSION_SCHEMA.md").write_text("# Criterion Dimension Schema\n\nTracks novelty, significance, soundness, empirical adequacy, and clarity/reproducibility. For each dimension this audit derives coverage, grounding, unsupported critique, not-assessable handling, and meta-leakage indicators.\n", encoding="utf-8")
    coverage_rows, grounding_rows, meta_rows = [], [], []
    for crit in CRITERIA:
        coverage = agg[f"criterion_covered_{crit}"]
        grounded = agg[f"criterion_grounded_{crit}"]
        unsupported = agg[f"unsupported_{crit}_critique_count"]
        leakage = agg[f"meta_leakage_{crit}"]
        coverage_rows.append([crit, coverage, round(coverage / n, 4)])
        grounding_rows.append([crit, grounded, round(grounded / n, 4), unsupported])
        meta_rows.append([crit, leakage, round(leakage / n, 4)])
    (outdir / "CRITERION_COVERAGE_AUDIT.md").write_text("# Criterion Coverage Audit\n\n" + md_table(["criterion", "covered_rows", "coverage_rate"], coverage_rows), encoding="utf-8")
    (outdir / "CRITERION_GROUNDING_AUDIT.md").write_text("# Criterion Grounding Audit\n\n" + md_table(["criterion", "grounded_rows", "grounded_rate", "unsupported_critique_count"], grounding_rows), encoding="utf-8")
    (outdir / "CRITERION_META_LEAKAGE_AUDIT.md").write_text("# Criterion Meta-Leakage Audit\n\n" + md_table(["criterion", "meta_leakage_rows", "rate"], meta_rows), encoding="utf-8")
    case_rows = [[r["paper_id"], r["gold_decision"], r["original_pred"], r["real_strong_support_total"], r["non_abstract_support_total"], r["empirical_support_total"], r["independent_support_group_total"], r["abstract_only_support_count"], ",".join(r["covered_criteria"]), ",".join(r["grounded_criteria"]), ",".join(r["unsupported_criteria"]), ",".join(r["meta_leakage_criteria"]), r["support_quality_label"]] for r in rows]
    (outdir / "SUPPORT_CRITERION_CASE_TABLE.md").write_text("# Support + Criterion Case Table\n\n" + md_table(["paper_id", "gold", "pred", "real_strong", "non_abstract", "empirical", "independent_groups", "abstract_only", "covered_criteria", "grounded_criteria", "unsupported_criteria", "meta_leakage", "support_quality"], case_rows), encoding="utf-8")
    sim_rows = [[s["simulation_name"], s["accuracy"], s["macro_f1"], s["accept_recall"], s["reject_recall"], s["predicted_accept_count"], ",".join(s["false_accept_ids"]), ",".join(s["recovered_accept_ids"]), ",".join(s["wrongly_flipped_reject_ids"])] for s in sims]
    (outdir / "SUPPORT_QUALITY_DECISION_SIMULATION.md").write_text("# Support Quality Decision Simulation\n\nOffline diagnostic simulations only. These are not runtime decision rules.\n\n" + md_table(["simulation", "accuracy", "macro_f1", "accept_recall", "reject_recall", "pred_accept", "false_accept_ids", "recovered_accept_ids", "wrongly_flipped_reject_ids"], sim_rows), encoding="utf-8")
    coverage_avg = sum(len(r["covered_criteria"]) for r in rows) / n
    unsupported_total = sum(len(r["unsupported_criteria"]) for r in rows)
    meta_total = sum(len(r["meta_leakage_criteria"]) for r in rows)
    if accept_without_nonabstract:
        next_cut, reason = "Evidence Context Selection v2", "Gold-accept rows still lack non-abstract/empirical support, so accept-like evidence is not deep enough."
    elif abstract_false_accepts:
        next_cut, reason = "Final-View Support Quality Filter v1", "False accepts are dominated by abstract-only support."
    elif coverage_avg < 3:
        next_cut, reason = "Criterion-Aware Final Report Section v1", "Final reports do not cover enough real review dimensions."
    elif unsupported_total > 0:
        next_cut, reason = "Criterion Grounding Linker v1", "Criterion coverage exists but unsupported criterion critique remains."
    elif meta_total > 0:
        next_cut, reason = "Criterion Meta-Leakage Filter v1", "System/excerpt/fallback limitations leak into criterion weaknesses."
    else:
        next_cut, reason = "audit-only", "No single support/criterion bottleneck dominates this audit."
    decision_doc = f"# Support + Criterion Next Cut Decision\n\n- Rows: {len(rows)}.\n- False accepts: {len(false_accepts)}.\n- False rejects: {len(false_rejects)}.\n- False accepts with abstract-only support: {len(abstract_false_accepts)}.\n- Gold-accept rows without non-abstract support: {len(accept_without_nonabstract)}.\n- Average covered criteria per report: {coverage_avg:.2f}.\n- Unsupported criterion critiques: {unsupported_total}.\n- Criterion meta-leakage signals: {meta_total}.\n\nNext unique cut: **{next_cut}**.\n\nReason: {reason}\n\nGuardrail: do not wire criterion labels directly into final decision yet. This audit only decides the next implementation direction.\n"
    (outdir / "SUPPORT_CRITERION_NEXT_CUT_DECISION.md").write_text(decision_doc, encoding="utf-8")
    (outdir / "support_quality_criterion_summary.json").write_text(json.dumps({"dataset": dataset, "input": str(input_path), "aggregate": dict(agg), "labels": dict(labels), "simulations": sims, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dataset-name", default="support_quality_criterion_audit")
    parser.add_argument("--outdir", default=Path("."), type=Path)
    args = parser.parse_args()
    rows = [summarize_row(row) for row in load_jsonl(args.input)]
    sims = run_sims(rows)
    write_docs(args.outdir, args.dataset_name, args.input, rows, sims)
    print(json.dumps({"rows": len(rows), "outdir": str(args.outdir), "simulations": sims}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
