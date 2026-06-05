#!/usr/bin/env python3
"""Hygiene Gap Types Audit v1 (PEND-5 / B7-2; offline, 0 LLM calls).

Classifies every flaw_candidate in the closure run into one of five mutually
exclusive *types*, then cross-tabulates the type against the decision-hygiene
view (visible vs filtered) and, when available, against the LLM-judge
paper-grounding verdict from `grounded_judge_v1.json`.

The output answers the question reviewers always ask after seeing
`Hygiene_Precision = 0.66`:

    "What exactly is the hygiene layer filtering out?"

Five types (priority order, first match wins):
  1. `schema_dump`          — title/description is a raw JSON schema dump.
  2. `truncation_meta`      — flaw is about paper-text truncation / availability.
  3. `fallback_or_system_meta` — flaw produced by fallback/system paths.
  4. `boilerplate_generic`  — generic template text without paper-specific anchors.
  5. `substantive`          — residual; contains paper-specific signal.

Usage
-----
    python scripts/audit_hygiene_gap_types_v1.py  # uses closure defaults

Outputs:
  - JSON:  outputs/results_main/review_infer/hygiene_gap_types_v1.json
  - MD:    docs/.../HYGIENE_GAP_TYPES_V1.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (  # noqa: E402
    _DECISION_HYGIENE_META_TERMS,
    _is_fallback_or_meta_flaw,
    build_decision_hygiene_view,
)

# -----------------------------------------------------------------------------
# Classification
# -----------------------------------------------------------------------------
# Truncation subset: use the same terms state.py considers meta, then narrow to
# the truncation/availability subfamily so the bucket is interpretable.
TRUNCATION_KEYWORDS = (
    "excerpt",
    "cuts off",
    "truncated",
    "incomplete abstract",
    "available text",
    "not yet visible",
    "please provide",
    "full text",
    "cannot be extracted",
    "cannot verify",
    "prevents verification",
    "insufficient context",
    "unable to",
)

# Boilerplate patterns: generic reviewer templates that recur across papers
# without any paper-specific anchor. Intentionally conservative — missing one
# is fine; misclassifying a substantive flaw is worse.
BOILERPLATE_PATTERNS = (
    r"insufficient\s+evidence\s+for\s+core\s+claims",
    r"lacks\s+(?:rigorous|comprehensive|thorough)\s+(?:evaluation|comparison|analysis)",
    r"lacks?\s+empirical\s+(?:support|validation|evaluation)",
    r"overstated\s+performance\s+claim",
    r"unclear\s+motivation",
    r"missing\s+limitation\s+discussion",
    r"lacks\s+grounded\s+supporting\s+evidence",
    r"without\s+sufficient\s+evidence",
    r"overstated\s+without\s+evidence",
)
BOILERPLATE_RX = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)

# Inverse signals: if any of these appear in the flaw text we treat it as
# substantive (paper-specific) and do NOT classify it as boilerplate.
SUBSTANTIVE_SIGNALS_RX = re.compile(
    r"\b\d+(?:\.\d+)?\s*%"               # percentages
    r"|\btable\s+\d+"                    # table refs
    r"|\bfigure\s+\d+"                   # figure refs
    r"|\bsection\s+\d+"                  # section refs
    r"|\bequation\s+\d+"                 # equation refs
    r"|\b(?:accuracy|bleu|rouge|f1|em|map|auc)\b\s*[=:]?\s*\d"  # metric values
    r"|\bdataset[s]?\s+[A-Z]"            # named datasets (Dataset X)
    ,
    re.IGNORECASE,
)


def classify_flaw(flaw: Dict[str, Any]) -> str:
    """Return one of schema_dump / truncation_meta / fallback_or_system_meta /
    boilerplate_generic / substantive."""
    title = str(flaw.get("title") or "")
    desc = str(flaw.get("description") or "")
    flaw_id = str(flaw.get("flaw_id") or "")
    source = str(flaw.get("source") or "").lower()
    grounding = str(flaw.get("grounding_status") or "").lower()
    text = f"{title}\n{desc}".strip()
    text_lower = text.lower()

    # 1. schema dump
    if text.lstrip().startswith("{"):
        return "schema_dump"
    if '"flaw_candidates"' in text_lower or '"claim_id"' in text_lower:
        return "schema_dump"
    if '"evidence_ids"' in text_lower and '"flaw_id"' in text_lower:
        return "schema_dump"

    # 2. truncation / paper-availability meta
    if any(kw in text_lower for kw in TRUNCATION_KEYWORDS):
        return "truncation_meta"

    # 3. fallback / system-meta (covers flaw-fallback*, source=fallback*, etc.)
    if flaw_id.startswith("flaw-fallback"):
        return "fallback_or_system_meta"
    if source in {"fallback", "fallback-extraction", "system_meta", "system-meta"}:
        return "fallback_or_system_meta"
    if grounding in {"fallback_unverified", "system_meta", "ungrounded_meta"}:
        return "fallback_or_system_meta"

    # 4. boilerplate (only if no substantive paper-specific signal)
    if BOILERPLATE_RX.search(text) and not SUBSTANTIVE_SIGNALS_RX.search(text):
        return "boilerplate_generic"

    # 5. substantive — residual
    return "substantive"


# -----------------------------------------------------------------------------
# Input loading
# -----------------------------------------------------------------------------
def load_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def load_judge_map(path: Optional[Path]) -> Dict[Tuple[str, str], str]:
    """Return {(paper_id, flaw_id): judgment} from grounded_judge_v1.json."""
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping: Dict[Tuple[str, str], str] = {}
    for r in data.get("flaw_results", []) or []:
        pid = str(r.get("paper_id") or "")
        fid = str(r.get("flaw_id") or "")
        if pid and fid:
            mapping[(pid, fid)] = str(r.get("judgment") or "")
    return mapping


# -----------------------------------------------------------------------------
# Build flaw index
# -----------------------------------------------------------------------------
VISIBLE_STATUSES = {"candidate", "confirmed"}


def build_flaw_index(
    rows: List[Dict[str, Any]],
    judge_map: Dict[Tuple[str, str], str],
) -> List[Dict[str, Any]]:
    all_flaws: List[Dict[str, Any]] = []
    for row in rows:
        pid = str(row.get("paper_id") or "")
        state = row.get("review_state") or {}
        raw_flaws = list(state.get("flaw_candidates") or [])

        # post-hygiene status map (deep-copy inside build_decision_hygiene_view)
        post_status_by_id: Dict[str, str] = {}
        try:
            view = build_decision_hygiene_view(state)
            for fl in view.get("flaw_candidates") or []:
                fid = str(fl.get("flaw_id") or "")
                if fid:
                    post_status_by_id[fid] = str(fl.get("status") or "")
        except Exception:
            pass

        for fl in raw_flaws:
            fid = str(fl.get("flaw_id") or "")
            raw_st = str(fl.get("status") or "candidate").lower()
            post_st = (post_status_by_id.get(fid) or raw_st).lower()
            ftype = classify_flaw(fl)

            visible_post = post_st in VISIBLE_STATUSES
            filtered_by_hygiene = (raw_st in VISIBLE_STATUSES) and not visible_post
            judge = judge_map.get((pid, fid), "")

            # also expose state.py's own classification for audit parity
            is_meta_state_py = bool(_is_fallback_or_meta_flaw(fl))

            all_flaws.append(
                {
                    "paper_id": pid,
                    "flaw_id": fid,
                    "type": ftype,
                    "raw_status": raw_st,
                    "post_hygiene_status": post_st,
                    "visible_post_hygiene": visible_post,
                    "filtered_by_hygiene": filtered_by_hygiene,
                    "judge": judge,
                    "is_meta_state_py": is_meta_state_py,
                    "title": str(fl.get("title") or "")[:200],
                    "description": str(fl.get("description") or "")[:400],
                    "source": str(fl.get("source") or ""),
                    "grounding_status": str(fl.get("grounding_status") or ""),
                }
            )
    return all_flaws


# -----------------------------------------------------------------------------
# Aggregation
# -----------------------------------------------------------------------------
def aggregate(all_flaws: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_total = len(all_flaws)
    n_papers = len({f["paper_id"] for f in all_flaws if f["paper_id"]})

    type_dist = Counter(f["type"] for f in all_flaws)
    visible_dist = Counter(f["type"] for f in all_flaws if f["visible_post_hygiene"])
    filtered_dist = Counter(f["type"] for f in all_flaws if f["filtered_by_hygiene"])

    # hygiene precision per type (only among filtered flaws with judge verdict)
    per_type_hygiene: Dict[str, Dict[str, Any]] = {}
    for t in sorted(type_dist.keys()):
        filtered = [f for f in all_flaws if f["type"] == t and f["filtered_by_hygiene"]]
        with_judge = [f for f in filtered if f["judge"] in {"paper_grounded", "not_paper_grounded"}]
        n_correct = sum(1 for f in with_judge if f["judge"] == "not_paper_grounded")
        n_fn = sum(1 for f in with_judge if f["judge"] == "paper_grounded")
        denom = len(with_judge)
        per_type_hygiene[t] = {
            "type_total": type_dist[t],
            "visible_post_hygiene": visible_dist[t],
            "filtered_by_hygiene": filtered_dist[t],
            "with_judge": denom,
            "correctly_filtered_not_grounded": n_correct,
            "false_negative_paper_grounded": n_fn,
            "hygiene_precision": (n_correct / denom) if denom else None,
        }

    # parity with state.py's own meta classifier (should broadly agree)
    state_meta_total = sum(1 for f in all_flaws if f["is_meta_state_py"])
    state_meta_vs_our_non_substantive = sum(
        1 for f in all_flaws if f["is_meta_state_py"] and f["type"] != "substantive"
    )

    return {
        "n_papers": n_papers,
        "n_flaws": n_total,
        "type_distribution": dict(type_dist),
        "visible_post_hygiene_by_type": dict(visible_dist),
        "filtered_by_hygiene_by_type": dict(filtered_dist),
        "per_type_hygiene_diagnostics": per_type_hygiene,
        "parity_with_state_py": {
            "state_py_meta_total": state_meta_total,
            "state_py_meta_and_non_substantive_by_ours": state_meta_vs_our_non_substantive,
            "agreement_rate": (
                state_meta_vs_our_non_substantive / state_meta_total if state_meta_total else None
            ),
        },
    }


# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------
TYPE_ORDER = [
    "schema_dump",
    "truncation_meta",
    "fallback_or_system_meta",
    "boilerplate_generic",
    "substantive",
]


def _pick_examples(all_flaws: List[Dict[str, Any]], ftype: str, limit: int = 3) -> List[Dict[str, Any]]:
    return [f for f in all_flaws if f["type"] == ftype][:limit]


def write_markdown(
    out_path: Path,
    input_jsonl: Path,
    judge_json: Optional[Path],
    all_flaws: List[Dict[str, Any]],
    agg: Dict[str, Any],
) -> None:
    lines: List[str] = [
        "# Hygiene Gap Types Audit v1 (offline; 0 LLM calls)",
        "",
        f"- input jsonl: `{input_jsonl}`",
        f"- judge source: `{judge_json if judge_json else '(none provided — hygiene precision diagnostics disabled)'}`",
        f"- n_papers: **{agg['n_papers']}**",
        f"- n_flaws: **{agg['n_flaws']}**",
        "",
        "## Type taxonomy",
        "",
        "Flaws are classified into five mutually exclusive types (first-match priority):",
        "",
        "1. **`schema_dump`** — title/description leaks a raw JSON schema "
        "(`{...\"flaw_candidates\": ...}`). Worker output escaped the prompt boundary.",
        "2. **`truncation_meta`** — flaw is about paper-text availability "
        "(truncation, missing full text, cannot verify due to excerpt limits).",
        "3. **`fallback_or_system_meta`** — flaw_id starts with `flaw-fallback`, "
        "or source/grounding_status marks it as fallback/system-meta produced by parser/recovery paths.",
        "4. **`boilerplate_generic`** — matches generic reviewer templates "
        "(*\"insufficient evidence for core claims\"*, *\"lacks rigorous evaluation\"*, etc.) "
        "with no paper-specific anchor (no percentages / table refs / metric values / dataset names).",
        "5. **`substantive`** — residual. Contains paper-specific signal.",
        "",
        "## Type distribution",
        "",
        "| type | total | visible post-hygiene | filtered by hygiene |",
        "|---|---:|---:|---:|",
    ]
    for t in TYPE_ORDER:
        total = agg["type_distribution"].get(t, 0)
        vis = agg["visible_post_hygiene_by_type"].get(t, 0)
        filt = agg["filtered_by_hygiene_by_type"].get(t, 0)
        lines.append(f"| `{t}` | {total} | {vis} | {filt} |")

    # Parity
    parity = agg["parity_with_state_py"]
    agreement = parity["agreement_rate"]
    agreement_s = f"{agreement:.4f}" if agreement is not None else "n/a"
    lines += [
        "",
        "## Parity with `state.py::_is_fallback_or_meta_flaw`",
        "",
        f"- state.py classifies **{parity['state_py_meta_total']}** flaws as meta/fallback.",
        f"- Of those, **{parity['state_py_meta_and_non_substantive_by_ours']}** also classified as non-`substantive` here.",
        f"- Agreement rate with state.py: **{agreement_s}** "
        "(high agreement validates the classifier; low agreement signals drift to investigate).",
        "",
        "## Hygiene diagnostics per type",
        "",
        "*For flaws that hygiene filtered out (raw=candidate/confirmed → post=downgraded/retracted), "
        "how many did the LLM judge also flag as `not_paper_grounded` (hygiene correct) vs `paper_grounded` "
        "(hygiene false negative)? Only flaws with a judge verdict are counted in the denominator.*",
        "",
        "| type | filtered | with_judge | correctly filtered | hygiene FN | hygiene_precision |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for t in TYPE_ORDER:
        d = agg["per_type_hygiene_diagnostics"].get(t)
        if d is None:
            continue
        prec = d["hygiene_precision"]
        prec_s = f"{prec:.4f}" if prec is not None else "—"
        lines.append(
            f"| `{t}` | {d['filtered_by_hygiene']} | {d['with_judge']} | "
            f"{d['correctly_filtered_not_grounded']} | {d['false_negative_paper_grounded']} | {prec_s} |"
        )

    # Examples
    lines += ["", "## Examples per type", ""]
    for t in TYPE_ORDER:
        examples = _pick_examples(all_flaws, t, limit=3)
        lines.append(f"### `{t}` ({agg['type_distribution'].get(t, 0)} flaws)")
        lines.append("")
        if not examples:
            lines.append("_(none)_")
            lines.append("")
            continue
        for ex in examples:
            lines.append(
                f"- `{ex['paper_id']}/{ex['flaw_id']}` "
                f"[raw={ex['raw_status']} → post={ex['post_hygiene_status']}] "
                f"judge={ex['judge'] or '—'}"
            )
            title = (ex["title"] or "").strip().replace("\n", " ")
            desc = (ex["description"] or "").strip().replace("\n", " ")
            if title:
                lines.append(f"    - **title**: {title[:180]}")
            if desc:
                lines.append(f"    - **desc**:  {desc[:220]}")
        lines.append("")

    lines += [
        "## How to interpret",
        "",
        "- The `type_distribution` row answers *\"where does the flaw stream spend its volume?\"* — a healthy "
        "system wants `substantive` to dominate; high `schema_dump` / `fallback_or_system_meta` counts mean "
        "workers or fallback paths are leaking into flaws.",
        "- The `visible post-hygiene` column equals what the reviewer ultimately sees. **Every non-`substantive` "
        "type should drop to near 0 here** — if not, the hygiene layer has a gap for that type.",
        "- The `hygiene_precision` column quantifies how often hygiene's filtering decision agrees with the "
        "LLM judge on a per-type basis. `schema_dump` / `truncation_meta` should be ~1.0 (easy, hygiene nearly never wrong). "
        "`boilerplate_generic` is the hardest type and where hygiene FN rate is expected to be highest.",
        "- Pair this table with `GROUNDED_JUDGE_V1.md` (overall `Hygiene_Precision`) and "
        "`AUDIT_META_LEAKAGE_V1.md` (for meta-leakage text indicators).",
        "",
        "Generated by `scripts/audit_hygiene_gap_types_v1.py`.",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
DEFAULT_INPUT_JSONL = (
    "outputs/results_main/review_infer/"
    "mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl"
)
DEFAULT_JUDGE_JSON = "outputs/results_main/review_infer/grounded_judge_v1.json"
DEFAULT_OUTPUT_JSON = "outputs/results_main/review_infer/hygiene_gap_types_v1.json"
DEFAULT_OUTPUT_MD = (
    "docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/"
    "HYGIENE_GAP_TYPES_V1.md"
)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--input-jsonl", default=DEFAULT_INPUT_JSONL)
    p.add_argument("--judge-json", default=DEFAULT_JUDGE_JSON,
                   help="Optional grounded_judge_v1.json for per-type hygiene precision.")
    p.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    p.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    input_jsonl = Path(args.input_jsonl)
    judge_json = Path(args.judge_json) if args.judge_json else None
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    if not input_jsonl.exists():
        print(f"ERROR: input jsonl not found: {input_jsonl}", file=sys.stderr)
        return 2

    rows = load_rows(input_jsonl)
    judge_map = load_judge_map(judge_json)

    all_flaws = build_flaw_index(rows, judge_map)
    agg = aggregate(all_flaws)

    payload = {
        "mode": "offline",
        "input_jsonl": str(input_jsonl),
        "judge_json": str(judge_json) if judge_json and judge_json.exists() else None,
        "aggregate": agg,
        "flaws": all_flaws,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    write_markdown(output_md, input_jsonl, judge_json if judge_json and judge_json.exists() else None, all_flaws, agg)

    summary = {
        "n_papers": agg["n_papers"],
        "n_flaws": agg["n_flaws"],
        "type_distribution": agg["type_distribution"],
        "output_json": str(output_json),
        "output_md": str(output_md),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
