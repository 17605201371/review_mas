#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence

ACCEPT_REJECT = {"accept", "reject"}

CRITERIA = {
    "novelty": {
        "label": "novelty_originality",
        "coverage": r"\b(novel|novelty|original|originality|new contribution|first to|prior work|related work)\b",
        "negative": r"\b(lack(?:s|ing)? novelty|not novel|incremental|limited novelty|insufficient novelty)\b",
        "grounding_sections": {"abstract", "method", "result", "ablation", "table_or_figure"},
    },
    "significance": {
        "label": "significance_contribution",
        "coverage": r"\b(significant|significance|important|impact|contribution|practical|useful|meaningful|relevance)\b",
        "negative": r"\b(limited significance|minor contribution|unclear impact|limited impact|weak contribution)\b",
        "grounding_sections": {"abstract", "result", "ablation", "table_or_figure"},
    },
    "soundness": {
        "label": "technical_soundness",
        "coverage": r"\b(sound|soundness|valid|validity|method|methodology|algorithm|theory|assumption|proof|objective|optimization|design|technical)\b",
        "negative": r"\b(unsound|invalid|flaw(?:ed)? method|methodological flaw|unsupported assumption|weak theory|incorrect)\b",
        "grounding_sections": {"method", "result", "ablation", "table_or_figure"},
    },
    "empirical": {
        "label": "empirical_adequacy",
        "coverage": r"\b(empirical|experiment|evaluation|result|baseline|dataset|metric|ablation|table|figure|benchmark)\b",
        "negative": r"\b(insufficient experiment|weak evaluation|missing baseline|no ablation|limited empirical|inadequate experiment)\b",
        "grounding_sections": {"result", "ablation", "table_or_figure"},
    },
    "clarity": {
        "label": "clarity_reproducibility",
        "coverage": r"\b(clear|clarity|reproducib|readab|implementation|detail|code|hyperparameter|description|presentation)\b",
        "negative": r"\b(unclear|not clear|lacks detail|insufficient detail|hard to reproduce|not reproducible|poorly written)\b",
        "grounding_sections": {"method", "result", "table_or_figure", "abstract"},
    },
}

SECTION_PATTERNS = [
    ("ablation", re.compile(r"\bablation\b|ablat", re.I)),
    ("table_or_figure", re.compile(r"\b(table|figure|fig\.?|appendix table)\b", re.I)),
    ("result", re.compile(r"\b(result|evaluation|experiment|benchmark|baseline|outperform|accuracy|f1|auc|bleu|rouge|performance|metric|dataset)\b", re.I)),
    ("method", re.compile(r"\b(method|approach|model|framework|algorithm|architecture|training objective|loss function|inference|design)\b", re.I)),
    ("abstract", re.compile(r"\babstract\b|\btitle\b", re.I)),
    ("conclusion", re.compile(r"\bconclusion\b|\bdiscussion\b", re.I)),
]

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
    text = " ".join(str(ev.get(k) or "") for k in ("source", "evidence", "support_quality_reason", "binding_rationale"))
    for section, pattern in SECTION_PATTERNS:
        if pattern.search(text):
            return section
    return "unknown"


def collect_sections(state: Dict[str, Any]) -> Counter:
    sections = Counter()
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict):
            continue
        if norm(ev.get("stance")) not in {"supports", "partially_supports", "contradicts"}:
            continue
        sections[evidence_section(ev)] += 1
    return sections


def report_text(row: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    return str(row.get("final_report") or state.get("final_report") or "")


def audit_row(row: Dict[str, Any]) -> Dict[str, Any]:
    state = row.get("review_state") or {}
    report = report_text(row)
    sections = collect_sections(state)
    out: Dict[str, Any] = {
        "paper_id": row.get("paper_id"),
        "gold_decision": infer_gold(row),
        "pred_decision": pred_decision(row),
        "covered_criteria": [],
        "grounded_criteria": [],
        "unsupported_criterion_critiques": [],
        "meta_leakage_criteria": [],
        "not_assessable_criteria": [],
        "criterion_summary": "",
    }
    for key, cfg in CRITERIA.items():
        coverage_re = re.compile(cfg["coverage"], re.I)
        negative_re = re.compile(cfg["negative"], re.I)
        covered = bool(coverage_re.search(report))
        negative = bool(negative_re.search(report))
        not_assessable = covered and bool(NOT_ASSESSABLE_RE.search(report))
        has_section_grounding = any(sections.get(section, 0) for section in cfg["grounding_sections"])
        has_text_ref = covered and bool(EVIDENCE_REF_RE.search(report))
        grounded = covered and (has_section_grounding or has_text_ref or not_assessable)
        unsupported = covered and negative and not grounded
        meta_leakage = covered and negative and bool(META_RE.search(report))
        out[f"criterion_covered_{key}"] = covered
        out[f"criterion_grounded_{key}"] = grounded
        out[f"unsupported_{key}_critique_count"] = int(unsupported)
        out[f"criterion_not_assessable_{key}"] = not_assessable
        out[f"meta_leakage_{key}"] = meta_leakage
        if covered:
            out["covered_criteria"].append(cfg["label"])
        if grounded:
            out["grounded_criteria"].append(cfg["label"])
        if unsupported:
            out["unsupported_criterion_critiques"].append(cfg["label"])
        if meta_leakage:
            out["meta_leakage_criteria"].append(cfg["label"])
        if not_assessable:
            out["not_assessable_criteria"].append(cfg["label"])
    out["criterion_summary"] = f"covered={len(out['covered_criteria'])}, grounded={len(out['grounded_criteria'])}, unsupported={len(out['unsupported_criterion_critiques'])}, meta={len(out['meta_leakage_criteria'])}"
    return out


def md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("\n", " ") for x in row) + " |")
    return "\n".join(lines) + "\n"


def aggregate(rows: List[Dict[str, Any]]) -> Counter:
    c = Counter()
    for row in rows:
        for key, cfg in CRITERIA.items():
            label = cfg["label"]
            c[f"covered_{label}"] += int(row[f"criterion_covered_{key}"])
            c[f"grounded_{label}"] += int(row[f"criterion_grounded_{key}"])
            c[f"unsupported_{label}"] += int(row[f"unsupported_{key}_critique_count"])
            c[f"not_assessable_{label}"] += int(row[f"criterion_not_assessable_{key}"])
            c[f"meta_leakage_{label}"] += int(row[f"meta_leakage_{key}"])
    c["total_covered"] = sum(len(r["covered_criteria"]) for r in rows)
    c["total_grounded"] = sum(len(r["grounded_criteria"]) for r in rows)
    c["total_unsupported"] = sum(len(r["unsupported_criterion_critiques"]) for r in rows)
    c["total_meta_leakage"] = sum(len(r["meta_leakage_criteria"]) for r in rows)
    return c


def write_outputs(outdir: Path, rows: List[Dict[str, Any]], input_path: Path, dataset_name: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    agg = aggregate(rows)
    n = len(rows) or 1
    schema = """# Criterion Dimension Schema\n\nThis is an offline audit layer for review quality diagnostics. It does not modify runtime behavior, prompts, ReviewState, or final decisions.\n\n## Dimensions\n\n- `novelty_originality`: whether the final report discusses novelty/originality or contribution novelty.\n- `significance_contribution`: whether the report discusses contribution significance, impact, usefulness, or importance.\n- `technical_soundness`: whether it discusses method validity, assumptions, algorithms, or technical design.\n- `empirical_adequacy`: whether it discusses experiments, datasets, metrics, baselines, tables, figures, or ablations.\n- `clarity_reproducibility`: whether it discusses presentation clarity, implementation details, reproducibility, code, or hyperparameters.\n\n## Field Semantics\n\n- `criterion_covered_*`: the report mentions the dimension.\n- `criterion_grounded_*`: the mention is linked to available evidence sections, explicit claim/evidence references, or a not-assessable statement.\n- `unsupported_*_critique_count`: negative critique for the dimension without grounding.\n- `criterion_not_assessable_*`: the report marks the dimension as not assessable because information is insufficient.\n- `meta_leakage_*`: system/excerpt/recovery/fallback limitation appears as a dimension weakness.\n\n## Guardrail\n\nCriterion labels must not drive accept/reject in this phase. They are paper-evaluation diagnostics only.\n"""
    (outdir / "CRITERION_DIMENSION_SCHEMA.md").write_text(schema, encoding="utf-8")

    coverage_rows = []
    grounding_rows = []
    meta_rows = []
    for key, cfg in CRITERIA.items():
        label = cfg["label"]
        covered = agg[f"covered_{label}"]
        grounded = agg[f"grounded_{label}"]
        unsupported = agg[f"unsupported_{label}"]
        not_assess = agg[f"not_assessable_{label}"]
        leakage = agg[f"meta_leakage_{label}"]
        coverage_rows.append([label, covered, round(covered / n, 4)])
        grounding_rows.append([label, grounded, round(grounded / n, 4), unsupported, not_assess])
        meta_rows.append([label, leakage, round(leakage / n, 4)])
    avg_cov = round(agg["total_covered"] / n, 3)
    (outdir / "CRITERION_COVERAGE_AUDIT.md").write_text(
        f"# Criterion Coverage Audit\n\nInput: `{input_path}`\nDataset: `{dataset_name}`\nRows: {len(rows)}\n\nAverage covered criteria per report: `{avg_cov}`.\n\n" + md_table(["criterion", "covered_rows", "coverage_rate"], coverage_rows),
        encoding="utf-8",
    )
    (outdir / "CRITERION_GROUNDING_AUDIT.md").write_text(
        "# Criterion Grounding Audit\n\n" + md_table(["criterion", "grounded_rows", "grounded_rate", "unsupported_critique_count", "not_assessable_rows"], grounding_rows),
        encoding="utf-8",
    )
    (outdir / "CRITERION_META_LEAKAGE_AUDIT.md").write_text(
        "# Criterion Meta-Leakage Audit\n\n" + md_table(["criterion", "meta_leakage_rows", "rate"], meta_rows),
        encoding="utf-8",
    )
    case_rows = [
        [
            r["paper_id"],
            r["gold_decision"],
            r["pred_decision"],
            ",".join(r["covered_criteria"]),
            ",".join(r["grounded_criteria"]),
            ",".join(r["unsupported_criterion_critiques"]),
            ",".join(r["meta_leakage_criteria"]),
            r["criterion_summary"],
        ]
        for r in rows
    ]
    (outdir / "CRITERION_CASE_TABLE.md").write_text(
        "# Criterion Case Table\n\n" + md_table(["paper_id", "gold", "pred", "covered_criteria", "grounded_criteria", "unsupported_critiques", "meta_leakage", "summary"], case_rows),
        encoding="utf-8",
    )

    missing = sorted(coverage_rows, key=lambda row: row[2])[:2]
    unsupported_total = agg["total_unsupported"]
    meta_total = agg["total_meta_leakage"]
    if avg_cov < 3:
        next_step = "add_criterion_section_to_final_report"
        reason = "Average criterion coverage is below 3 dimensions per report."
    elif unsupported_total > 0:
        next_step = "add_criterion_grounding_schema"
        reason = "Criterion coverage exists, but unsupported criterion critiques remain."
    elif meta_total > 0:
        next_step = "add_criterion_grounding_schema"
        reason = "Criterion meta-leakage remains and should be filtered/grounded before report rendering."
    else:
        next_step = "audit_only"
        reason = "Coverage and grounding are sufficient for now; keep as paper diagnostic metrics."
    decision = f"""# Criterion Next Step Decision\n\n## Summary\n\n- Rows: {len(rows)}\n- Average covered criteria per report: {avg_cov}\n- Total unsupported criterion critiques: {unsupported_total}\n- Total meta-leakage signals: {meta_total}\n- Lowest coverage dimensions: {', '.join(row[0] for row in missing)}\n\n## Decision\n\nNext step: **{next_step}**.\n\nReason: {reason}\n\n## Guardrail\n\nDo not let novelty, soundness, empirical adequacy, clarity, or significance directly affect accept/reject yet. If implemented later, criterion outputs should first become a structured final-report section or grounding schema, not a decision rule.\n"""
    (outdir / "CRITERION_NEXT_STEP_DECISION.md").write_text(decision, encoding="utf-8")
    (outdir / "criterion_dimension_summary.json").write_text(json.dumps({"input": str(input_path), "dataset": dataset_name, "aggregate": dict(agg), "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--dataset-name", default="criterion_audit")
    parser.add_argument("--outdir", default=Path("."), type=Path)
    args = parser.parse_args()
    rows = [audit_row(row) for row in load_jsonl(args.input)]
    write_outputs(args.outdir, rows, args.input, args.dataset_name)
    print(json.dumps({"rows": len(rows), "outdir": str(args.outdir)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
