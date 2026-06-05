#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pyarrow.parquet as pq

NEGATIVE_ANCHORS = [
    ("empirical", re.compile(r"\b(limitation|limitations|baseline|baselines|ablation|dataset|metric|evaluation|experiment|comparison|outperform|underperform|failure|error analysis|statistical|significance)\b", re.I)),
    ("soundness", re.compile(r"\b(assumption|validity|soundness|methodological|algorithm|objective|loss|proof|theorem|architecture|mechanism|complexity)\b", re.I)),
    ("novelty", re.compile(r"\b(novelty|novel|original|incremental|prior work|related work|contribution|significance|impact)\b", re.I)),
    ("negative", re.compile(r"\b(lack|lacks|missing|insufficient|weak|limited|unclear|not demonstrate|does not demonstrate|no evidence|without|unsupported|inadequate|fails? to|cannot|absence|concern)\b", re.I)),
]
SECTION_HEADERS = [
    ("limitations", re.compile(r"(?:^|\n)\s*(?:\\(?:sub)*section\*?\{[^}]*|#{1,6}\s*)?(?:\d+(?:\.\d+)*\.?\s*)?(limitation|limitations|discussion|failure analysis|error analysis)[^\n}]*", re.I)),
    ("results", re.compile(r"(?:^|\n)\s*(?:\\(?:sub)*section\*?\{[^}]*|#{1,6}\s*)?(?:\d+(?:\.\d+)*\.?\s*)?(experiment|experiments|evaluation|results|analysis|benchmark)[^\n}]*", re.I)),
    ("method", re.compile(r"(?:^|\n)\s*(?:\\(?:sub)*section\*?\{[^}]*|#{1,6}\s*)?(?:\d+(?:\.\d+)*\.?\s*)?(method|methods|approach|model|framework|algorithm)[^\n}]*", re.I)),
    ("related_work", re.compile(r"(?:^|\n)\s*(?:\\(?:sub)*section\*?\{[^}]*|#{1,6}\s*)?(?:\d+(?:\.\d+)*\.?\s*)?(related work|prior work|background)[^\n}]*", re.I)),
]


def norm(v: Any) -> str:
    return str(v or "").strip().lower()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _message_contents(value: Any) -> List[str]:
    if not value:
        return []
    parsed = value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return [value]
    if isinstance(parsed, list):
        contents = []
        for item in parsed:
            if isinstance(item, dict):
                content = item.get("content")
                if content:
                    contents.append(str(content))
            elif item:
                contents.append(str(item))
        return contents
    if isinstance(parsed, dict):
        content = parsed.get("content")
        return [str(content)] if content else [str(parsed)]
    return [str(parsed)]


def _extract_paper_text_from_row(row: Dict[str, Any]) -> str:
    env = row.get("env_kwargs") or {}
    direct = row.get("paper_text") or env.get("paper_text") or row.get("text") or env.get("text")
    if direct:
        return str(direct)
    candidates: List[str] = []
    candidates.extend(_message_contents(row.get("prompt")))
    candidates.extend(_message_contents(row.get("inputs")))
    for candidate in candidates:
        if re.search(r"---\s*BEGIN\s+PAPER\s*---", candidate, re.I):
            return candidate
    for candidate in candidates:
        if "\\begin{abstract}" in candidate or "\\title{" in candidate:
            return candidate
    return candidates[-1] if candidates else ""


def dataset_map(path: Path, limit: int = 39) -> Dict[str, Dict[str, Any]]:
    rows = pq.read_table(path).to_pylist()[:limit]
    out = {}
    for row in rows:
        env = row.get("env_kwargs") or {}
        pid = str(row.get("id") or env.get("paper_id") or "")
        paper_text = _extract_paper_text_from_row(row)
        out[pid] = {"paper_text": str(paper_text or ""), "decision": str(row.get("decision") or env.get("ground_truth_decision") or "")}
    return out


def clean_body(text: str) -> Tuple[str, bool]:
    raw = str(text or "").strip()[:64000]
    cleaned = False
    begin = re.search(r"---\s*BEGIN\s+PAPER\s*---", raw, re.I)
    if begin:
        raw = raw[begin.end():]
        cleaned = True
    end = re.search(r"---\s*END\s+PAPER\s*---", raw, re.I)
    if end:
        raw = raw[:end.start()]
        cleaned = True
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith("[instruction]") or low.startswith("format requirements"):
            cleaned = True
            continue
        lines.append(s)
    return "\n".join(lines), cleaned


def win(text: str, pos: int, window: int = 680) -> str:
    start = max(0, pos - window // 3)
    end = min(len(text), pos + window)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def hard_negative_context(body: str, max_chars: int = 2600) -> Tuple[str, List[str]]:
    snippets: List[Tuple[str, str]] = []
    seen: List[Tuple[int, int, str]] = []

    def add(label: str, pos: int, window: int = 720) -> None:
        start = max(0, pos - window // 3)
        end = min(len(body), pos + window)
        for s, e, old_label in seen:
            if old_label == label and min(end, e) - max(start, s) > 180:
                return
        seen.append((start, end, label))
        text = win(body, pos, window)
        if len(text) >= 80:
            snippets.append((label, text))

    for label, pat in SECTION_HEADERS:
        m = pat.search(body)
        if m:
            add(label, m.start(), 850 if label in {"limitations", "results"} else 650)
    start = min(len(body), 800)
    for label, pat in NEGATIVE_ANCHORS:
        for m in list(pat.finditer(body, pos=start))[:3]:
            add(label, m.start(), 720)
    if not snippets:
        snippets.append(("body_start", re.sub(r"\s+", " ", body[:max_chars]).strip()))

    order = ["limitations", "negative", "results", "empirical", "soundness", "method", "novelty", "related_work", "body_start"]
    ordered = []
    for label in order:
        ordered.extend((l, s) for l, s in snippets if l == label)
    ordered.extend((l, s) for l, s in snippets if l not in order)
    parts: List[str] = []
    sources: List[str] = []
    remaining = max_chars
    per_source = Counter()
    for label, snippet in ordered:
        if remaining < 120:
            break
        if per_source[label] >= 2:
            continue
        prefix = f"[{label}] "
        budget = min(620, remaining - len(prefix))
        if budget < 100:
            continue
        rendered = snippet[:budget].rsplit(" ", 1)[0]
        part = prefix + rendered
        parts.append(part)
        remaining -= len(part) + 2
        per_source[label] += 1
        if label not in sources:
            sources.append(label)
    return "\n\n".join(parts), sources


def count_terms(text: str) -> Dict[str, int]:
    return {label: len(pat.findall(text or "")) for label, pat in NEGATIVE_ANCHORS}


def render_prompt(row: Dict[str, Any], context: str) -> str:
    return f"""# Hard-Negative Extraction v1

You are auditing whether this paper has grounded reject-level weaknesses. Do not make an accept/reject decision.

Rules:
- Extract only paper-grounded hard negatives.
- Do not treat excerpt truncation, missing full text, parser failure, fallback, or system uncertainty as a paper weakness.
- Prefer empirical inadequacy, technical soundness, novelty/significance weakness, and reproducibility weakness.
- Every hard negative must cite a claim/evidence id when available and a short paper excerpt from the context.
- If no grounded hard negative is visible, output not_assessable rather than inventing a flaw.

Return JSON:
{{
  "hard_negative_candidates": [
    {{"type": "empirical|soundness|novelty_significance|clarity_reproducibility", "severity": "critical|major|minor", "grounding": "grounded|weak|not_assessable", "related_claim_ids": [], "evidence_ids": [], "paper_excerpt": "short excerpt", "rationale": "why this is a paper-level weakness"}}
  ],
  "not_assessable_reasons": [],
  "recommendation_effect": "reject_like|borderline|not_assessable"
}}

Paper id: {row['paper_id']}
Current final-view: {row['final_view_v2']}
Current support: real={row['real_strong']} nonabstract={row['nonabstract_support']} empirical={row['empirical_support']} groups={row['independent_groups']}
Current unresolved/flaw burden: targetless_unresolved={row['targetless_unresolved']} ungrounded_candidate_flaws={row['ungrounded_candidate_flaws']} fallback_or_meta_flaws={row['fallback_or_meta_flaws']}

# Hard-Negative Context
{context}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, required=True)
    ap.add_argument("--recommendation-json", type=Path, required=True)
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=39)
    args = ap.parse_args()

    data = dataset_map(args.dataset, args.limit)
    rec = load_json(args.recommendation_json)
    rows = [r for r in rec.get("case_rows", []) if r.get("final_view_v2") == "borderline_positive"]
    previews = []
    for row in rows:
        pid = row["paper_id"]
        body, cleaned = clean_body(data.get(pid, {}).get("paper_text", ""))
        old = re.sub(r"\s+", " ", str(data.get(pid, {}).get("paper_text", ""))[:800]).strip()
        ctx, sources = hard_negative_context(body)
        old_terms = count_terms(old)
        new_terms = count_terms(ctx)
        previews.append({
            "paper_id": pid,
            "gold": row.get("gold"),
            "final_view_v2": row.get("final_view_v2"),
            "cleaned_wrapper": cleaned,
            "old_chars": len(old),
            "new_chars": len(ctx),
            "sources": sources,
            "old_negative_terms": old_terms,
            "new_negative_terms": new_terms,
            "old_preview": old[:600],
            "new_preview": ctx[:1200],
            "prompt": render_prompt(row, ctx),
        })
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps({"rows": previews}, ensure_ascii=False, indent=2), encoding="utf-8")
    rows_md = []
    for p in previews:
        rows_md.append([p["paper_id"], p["gold"], ",".join(p["sources"]), p["old_negative_terms"], p["new_negative_terms"]])
    write(args.outdir / "HARD_NEGATIVE_EXTRACTION_V1_PROTOCOL.md", "# Hard-Negative Extraction v1 Protocol\n\n本轮只做离线 prompt/context 验证，不改 runtime、不改 final decision。目标是验证 reject 样本中是否能暴露 empirical/soundness/novelty hard-negative 线索。\n")
    write(args.outdir / "HARD_NEGATIVE_CONTEXT_PREVIEW_V1.md", "# Hard-Negative Context Preview v1\n\n" + table(["paper_id", "gold", "sources", "old_terms", "new_terms"], rows_md))
    prompt_parts = ["# Hard-Negative Extraction Prompt Pack v1", ""]
    for p in previews:
        prompt_parts.append(f"## {p['paper_id']} ({p['gold']})\n\n```text\n{p['prompt'][:4200]}\n```\n")
    write(args.outdir / "HARD_NEGATIVE_EXTRACTION_PROMPT_PACK_V1.md", "\n".join(prompt_parts))
    total_old = Counter(); total_new = Counter(); source_counts = Counter()
    for p in previews:
        total_old.update(p["old_negative_terms"])
        total_new.update(p["new_negative_terms"])
        source_counts.update(p["sources"])
    decision = f"""# Hard-Negative Extraction v1 Decision

## 结论

已生成 hard-negative extractor prompt pack。当前验证仍是离线层，不接 runtime。

## Context 可见性

- old 800-char critique excerpt negative terms: `{dict(total_old)}`
- new hard-negative context negative terms: `{dict(total_new)}`
- new context sources: `{dict(source_counts)}`

## 判断

如果 new context 明显暴露更多 empirical/soundness/novelty negative anchors，下一步才值得考虑把 Critique Agent 的 `Critique-Relevant Paper Excerpt` 从 800-char prefix 改成 hard-negative section-aware context。若仍没有足够 negative anchors，则应停止 runtime 改动，把这些样本标为 not_assessable / borderline，而不是强行找 flaws。
"""
    write(args.outdir / "HARD_NEGATIVE_EXTRACTION_V1_DECISION.md", decision)
    print(json.dumps({"rows": len(previews), "old_terms": dict(total_old), "new_terms": dict(total_new), "sources": dict(source_counts), "output_json": str(args.output_json)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
