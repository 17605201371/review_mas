#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent_system.inference.review_runner import _row_to_env_kwargs, load_review_rows
from agent_system.environments.env_package.review.state import _clean_paper_body

ANCHOR_PATTERNS = [
    ("table", re.compile(r"\b(table\s*\d+|table)\b", re.I), 8),
    ("figure", re.compile(r"\b(fig\.?\s*\d+|figure\s*\d+|figure)\b", re.I), 8),
    ("results", re.compile(r"\b(results?|evaluation|experiments?|performance|benchmark)\b", re.I), 7),
    ("baseline", re.compile(r"\b(baseline|comparison|compare|state-of-the-art|sota|outperform)\b", re.I), 6),
    ("ablation", re.compile(r"\bablation\b|ablat", re.I), 6),
    ("dataset_metric", re.compile(r"\b(dataset|metric|accuracy|f1|auc|bleu|rouge|rmse|precision|recall)\b", re.I), 5),
    ("limitation", re.compile(r"\b(limitation|failure|fails|weakness|future work|threats to validity)\b", re.I), 4),
]
QUANT_RE = re.compile(r"\b(\d+(?:\.\d+)?\s*%?|accuracy|f1|auc|bleu|rouge|rmse|score|metric|outperform|improve|baseline)\b", re.I)
META_RE = re.compile(r"\b(instruction|format requirements|begin paper|end paper|review must|json|schema)\b", re.I)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(v).replace("\n", " ") for v in values) + " |"


def compact(text: str, limit: int = 700) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 18].rstrip() + " ...[truncated]"


def extract_anchors(body: str, max_anchors: int = 6) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen_spans: List[tuple[int, int]] = []
    for label, pattern, priority in ANCHOR_PATTERNS:
        for match in pattern.finditer(body):
            start = max(0, match.start() - 420)
            end = min(len(body), match.end() + 900)
            if any(abs(start - s) < 450 for s, _ in seen_spans):
                continue
            text = body[start:end]
            if META_RE.search(text[:250]):
                continue
            score = priority
            if QUANT_RE.search(text):
                score += 3
            if re.search(r"\b(table|figure|fig\.?|baseline|ablation)\b", text, re.I):
                score += 2
            candidates.append({
                "anchor_id": f"anchor-{len(candidates)+1}",
                "anchor_type": label,
                "start_char": start,
                "end_char": end,
                "score": score,
                "has_quantitative_signal": bool(QUANT_RE.search(text)),
                "text": compact(text, 900),
            })
            seen_spans.append((start, end))
            break
    candidates.sort(key=lambda item: (-item["score"], item["start_char"]))
    selected = candidates[:max_anchors]
    for idx, item in enumerate(selected, 1):
        item["anchor_id"] = f"anchor-{idx}"
    return selected


def render_report(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Negative Evidence Anchor Extraction v1",
        "",
        "## 定位",
        "",
        "本轮只做离线锚点抽取，不改 runtime、不改 final decision。目标是给 negative evidence confirmation pass 提供 result/table/figure/experiment/baseline 等非 abstract 锚点，减少把 context-limited 当 paper flaw 的风险。",
        "",
        "## Aggregate",
        "",
        table_row(["metric", "value"]),
        table_row(["---", "---:"]),
        table_row(["rows", len(rows)]),
        table_row(["rows_with_anchor", sum(1 for r in rows if r["anchor_count"] > 0)]),
        table_row(["avg_anchor_count", round(sum(r["anchor_count"] for r in rows) / len(rows), 3) if rows else 0]),
        table_row(["rows_with_quant_anchor", sum(1 for r in rows if r["quant_anchor_count"] > 0)]),
        "",
        "## Anchor Type Counts",
        "",
        table_row(["anchor_type", "count"]),
        table_row(["---", "---:"]),
    ]
    counts = Counter(anchor["anchor_type"] for row in rows for anchor in row["anchors"])
    for key, count in counts.most_common():
        lines.append(table_row([key, count]))
    return "\n".join(lines)


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Negative Evidence Anchor Case Table v1",
        "",
        table_row(["paper_id", "tag", "anchor_count", "quant_anchor_count", "top_anchor_types", "top_anchor_preview"]),
        table_row(["---", "---", "---:", "---:", "---", "---"]),
    ]
    for row in rows:
        top_types = ",".join(anchor["anchor_type"] for anchor in row["anchors"][:4])
        preview = row["anchors"][0]["text"][:260] if row["anchors"] else ""
        lines.append(table_row([row["paper_id"], row["tag"], row["anchor_count"], row["quant_anchor_count"], top_types, preview]))
    return "\n".join(lines)


def render_decision(rows: List[Dict[str, Any]]) -> str:
    missing = [row["paper_id"] for row in rows if row["anchor_count"] == 0]
    return f"""# Negative Evidence Anchor Extraction v1 Decision

## 结论

锚点抽取可以作为下一轮 negative confirmation pass 的输入，但仍是离线诊断层，不进入 final decision。

## 关键数字

- diagnostic rows: `{len(rows)}`
- rows_with_anchor: `{sum(1 for r in rows if r['anchor_count'] > 0)}`
- rows_with_quant_anchor: `{sum(1 for r in rows if r['quant_anchor_count'] > 0)}`
- rows_without_anchor: `{len(missing)}`

## 判断

如果 anchor 覆盖足够，下一步可以运行 `Negative Evidence Anchor Confirmation Pass v1`，只允许模型基于这些 anchor 确认 flaw；不允许基于 abstract/context missing 形成 blocker。

## 无锚点样本

{', '.join(missing) if missing else 'none'}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", default="/reviewF/datasets/drmas_review/test.parquet")
    parser.add_argument("--subset-json", default="outputs/results_main/review_infer/negative_evidence_formation_v1_diagnostic_subset.json")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/negative_evidence_anchor_extraction_v1.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()

    subset = load_json(Path(args.subset_json))
    target_ids = set(subset["paper_ids"])
    subset_case = {case["paper_id"]: case for case in subset["cases"]}
    rows = []
    for raw in load_review_rows(args.dataset_path, split="test"):
        task = _row_to_env_kwargs(raw)
        pid = task.get("paper_id")
        if pid not in target_ids:
            continue
        body, cleaned = _clean_paper_body(str(task.get("paper_text") or ""))
        anchors = extract_anchors(body)
        rows.append({
            "paper_id": pid,
            "tag": subset_case.get(pid, {}).get("tag", ""),
            "gold_decision": subset_case.get(pid, {}).get("gold_decision", ""),
            "cleaned_wrapper": cleaned,
            "body_chars": len(body),
            "anchor_count": len(anchors),
            "quant_anchor_count": sum(1 for anchor in anchors if anchor["has_quantitative_signal"]),
            "anchors": anchors,
        })
    rows.sort(key=lambda r: (0 if r["tag"] == "false_accept" else 1, r["paper_id"]))
    out = {"subset_json": args.subset_json, "rows": len(rows), "case_rows": rows}
    write_json(Path(args.output_json), out)
    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_EXTRACTION_V1.md", render_report(rows))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_CASE_TABLE_V1.md", render_case_table(rows))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_ANCHOR_EXTRACTION_V1_DECISION.md", render_decision(rows))
    print(json.dumps({
        "json": args.output_json,
        "docs": [
            "NEGATIVE_EVIDENCE_ANCHOR_EXTRACTION_V1.md",
            "NEGATIVE_EVIDENCE_ANCHOR_CASE_TABLE_V1.md",
            "NEGATIVE_EVIDENCE_ANCHOR_EXTRACTION_V1_DECISION.md",
        ],
        "rows": len(rows),
        "rows_with_anchor": sum(1 for r in rows if r["anchor_count"] > 0),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
