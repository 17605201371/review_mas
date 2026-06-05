#!/usr/bin/env python3
"""Meta-leakage audit v1 (offline, rule-based, 0 LLM calls).

Implements **B1 / C0c** from `PAPER_GAP_REMEDIATION_PLAN.md` and addresses
`PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足十二 + INTEGRATED #C0c.

Why this script exists
----------------------
`scripts/analyze_mainline_final_v1.py` reads a `total_meta_leakage` field
from criterion summaries (`scripts/analyze_mainline_final_v1.py:346`) but
**no producer ever writes it** — so the value is always `0` (a silent
empty shell). At the same time, `final_report` strings on fulltest39
contain large amounts of system-level language that should never reach a
human reviewer:

  - inline schema id dumps such as `[claims: claim-1; evidence: evidence-2-turn-2]`
    (102 hits across 39 papers).
  - snake_case decision labels copied from internal enums such as
    `some_real_support_but_not_enough_quality_or_coverage_for_accept_like`
    (78 hits, all from the `Recommendation Reason` field).
  - system status language (`review halted`, `abstract is truncated`,
    `full text is unavailable`, `missing input data`).
  - boilerplate audit phrases (`by the end of the review process`,
    `not fully resolved`, `fallback evidence`).

Each of these is a meta-leakage: signals from the agent system that have
"leaked" out of internal logging into the human-facing review report. The
paper's *State Hygiene* and *auditability* claims are weakened if these
leaks are not measured and reported.

Severity tiers
--------------
We score in three tiers (no LLM calls):

  - **L1 critical** — schema or system-state strings that should never
    reach a human reviewer (inline ID dumps, snake_case enum labels,
    `review halted`, JSON code fences, `<think>` tags, raw schema keys).
  - **L2 high**    — context / truncation language that exposes a system
    limitation but uses natural-language framing
    (`abstract is truncated`, `text truncation prevents`, etc.).
  - **L3 soft**    — boilerplate that mentions the review process or
    fallback semantics
    (`by the end of the review process`, `not fully resolved`,
    `fallback evidence`, `reviewer agent`).

A leakage_score is reported as a weighted sum (`L1*3 + L2*2 + L3*1`).
Counts are reported separately so the author can choose which tiers to
quote in the paper.

Inputs / outputs
----------------
  - --jsonl: closure-run jsonl with `final_report` + `review_state` per row.
  - --output-json: structured per-paper + aggregate audit (default
    `outputs/results_main/review_infer/meta_leakage_v1.json`).
  - --output-md: human-readable report.
  - --write-back-criterion: optional path to a criterion summary JSON;
    when provided, the script writes back `total_meta_leakage` (= sum of
    L1 + L2 + L3 hits across all papers) so that
    `analyze_mainline_final_v1.py` picks up a real value next run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# -----------------------------------------------------------------------------
# Tiered probes. Each probe = (label, regex, tier, weight, short_explanation)
# Order within a tier is informational only.
# -----------------------------------------------------------------------------
TIER_WEIGHT = {"L1": 3, "L2": 2, "L3": 1}

PROBES: List[Tuple[str, "re.Pattern[str]", str, str]] = [
    # ---- L1 critical ----
    (
        "inline_schema_id_dump",
        re.compile(r"\[(claims|evidence|flaws|claim|flaw):\s*(claim|evidence|flaw|hypothesis)-[0-9]", re.IGNORECASE),
        "L1",
        "schema-level claim/evidence/flaw IDs leaked into prose",
    ),
    (
        "snake_case_decision_enum",
        re.compile(r"\b[a-z]+(?:_[a-z]+){3,}\b"),
        "L1",
        "snake_case enum labels (4+ tokens) dumped as natural language",
    ),
    (
        "json_codeblock_fence",
        re.compile(r"```(json|jsonc)", re.IGNORECASE),
        "L1",
        "fenced JSON code block in final report",
    ),
    (
        "json_schema_key_literal",
        re.compile(r'"(flaw_candidates|supporting_evidence_ids|related_claim_ids|claim_id|evidence_id|flaw_id|grounding_status)"'),
        "L1",
        "raw JSON schema keys",
    ),
    (
        "think_tag",
        re.compile(r"<\s*/?\s*think\s*>?", re.IGNORECASE),
        "L1",
        "<think> tag leaked from generation",
    ),
    (
        "review_halted",
        re.compile(r"review (halted|aborted|stopped)", re.IGNORECASE),
        "L1",
        "system explicitly says it stopped reviewing",
    ),
    (
        "missing_input_data",
        re.compile(r"missing input data", re.IGNORECASE),
        "L1",
        "system status: missing input",
    ),
    (
        "full_text_unavailable",
        re.compile(r"full text (is\s+)?(unavailable|missing|not provided|not available)", re.IGNORECASE),
        "L1",
        "system status: input text not available",
    ),

    # ---- L2 high ----
    (
        "abstract_truncated",
        re.compile(r"abstract\s+(is|was)?\s*truncat", re.IGNORECASE),
        "L2",
        "context window: abstract was truncated",
    ),
    (
        "text_truncation_prevents",
        re.compile(r"(text\s+truncation|truncation)\s+prevents?", re.IGNORECASE),
        "L2",
        "context window: truncation prevents verification",
    ),
    (
        "context_truncation_generic",
        re.compile(r"\b(truncated text|due to truncation|truncated abstract|context window|excerpt|snippet)", re.IGNORECASE),
        "L2",
        "generic truncation / excerpt language",
    ),
    (
        "insufficient_context",
        re.compile(r"insufficient context|limited context|partial context", re.IGNORECASE),
        "L2",
        "system says context was insufficient",
    ),
    (
        "as_an_ai",
        re.compile(r"\bas an? (ai|language model)|this (llm|language model)", re.IGNORECASE),
        "L2",
        "agent self-reference (as an AI / language model)",
    ),

    # ---- L3 soft ----
    (
        "by_end_of_review_process",
        re.compile(r"(by|at) the end of the review( process)?", re.IGNORECASE),
        "L3",
        "boilerplate review-process phrasing",
    ),
    (
        "not_fully_resolved_phrase",
        re.compile(r"\bnot fully resolved\b", re.IGNORECASE),
        "L3",
        "boilerplate audit phrase",
    ),
    (
        "fallback_evidence_word",
        re.compile(r"\bfallback (evidence|support|claim|payload)\b", re.IGNORECASE),
        "L3",
        "internal `fallback` term used in prose",
    ),
    (
        "reviewer_agent_word",
        re.compile(r"\b(reviewer agent|review process)\b", re.IGNORECASE),
        "L3",
        "agent / review-process phrasing",
    ),
    (
        "parse_error_word",
        re.compile(r"\b(parse[\s_-]*(error|fail|failure)|malformed|could not parse|unparsed|unparseable)\b", re.IGNORECASE),
        "L3",
        "parse-error related language",
    ),
]


# Ignore-list for snake_case probe — avoid double-counting our own tokens.
SNAKE_IGNORE = {"claim_id", "evidence_id", "flaw_id", "hypothesis_id", "supporting_evidence_ids", "related_claim_ids"}


def safe_findall(probe_label: str, pattern: "re.Pattern[str]", text: str) -> List[Tuple[int, int, str]]:
    """Return list of (start, end, matched_token); applies probe-specific filters."""
    out: List[Tuple[int, int, str]] = []
    for m in pattern.finditer(text):
        token = m.group(0)
        if probe_label == "snake_case_decision_enum":
            # Filter out our own schema names so we don't double-count L1
            if token.lower() in SNAKE_IGNORE:
                continue
            # Filter out obviously non-leaky long natural compound words (rare)
            if not re.search(r"[a-z]+_[a-z]+_[a-z]+_[a-z]+", token):
                continue
        out.append((m.start(), m.end(), token))
    return out


def excerpt(text: str, start: int, end: int, pad_left: int = 40, pad_right: int = 60) -> str:
    s = max(0, start - pad_left)
    e = min(len(text), end + pad_right)
    snippet = text[s:e].strip().replace("\n", " ")
    return f"...{snippet}..."


# Header that separates human-readable sections (1-6) from the machine-readable
# audit trace (Section 7) introduced by HygieneV3 `render_final_review`.
AUDIT_TRACE_HEADER = "7. Audit Trace (machine-readable)"


def split_final_report(final_report: str) -> Tuple[str, str, bool]:
    """Split a final report into (human_readable, audit_trace, has_split).

    HygieneV3 renders the final report as Sections 1-6 (human-readable) followed
    by Section 7 ``7. Audit Trace (machine-readable)`` which intentionally
    contains internal claim/evidence/flaw IDs and machine-readable hygiene
    counters. Reviewer-visible leakage MUST be measured on Sections 1-6 only;
    the audit trace is by design and is reported as a separate scope.

    Backward-compatible: if no audit trace header is present (older artifacts),
    the entire text is returned as ``human_readable`` and the audit_trace is
    empty, so legacy detector behaviour is preserved on legacy artifacts.
    """
    text = final_report or ""
    idx = text.find(AUDIT_TRACE_HEADER)
    if idx < 0:
        return text, "", False
    return text[:idx], text[idx:], True


def _scope_metrics(text: str) -> Tuple[Dict[str, Dict[str, Any]], Counter, Dict[str, List[str]]]:
    """Run all probes on ``text`` and return (per_probe, tier_counts, sample_excerpts)."""
    per_probe: Dict[str, Dict[str, Any]] = {}
    tier_counts: Counter = Counter()
    sample_excerpts: Dict[str, List[str]] = {}
    for label, pattern, tier, _expl in PROBES:
        hits = safe_findall(label, pattern, text)
        if not hits:
            continue
        per_probe[label] = {
            "tier": tier,
            "count": len(hits),
            "tokens_sample": list({h[2] for h in hits})[:5],
        }
        tier_counts[tier] += len(hits)
        sample_excerpts[label] = [excerpt(text, h[0], h[1]) for h in hits[:2]]
    return per_probe, tier_counts, sample_excerpts


def audit_paper(paper_id: str, final_report: str, review_state: Dict[str, Any]) -> Dict[str, Any]:
    """Audit a single paper for meta-leakage.

    Three scopes are reported separately because they have different
    reviewer-visibility semantics:

    - **final_report** scope (PRIMARY): Sections 1-6 of the final report —
      text the human reviewer actually sees. The weighted leakage_score and
      ``total_meta_leakage`` write-back are computed ONLY on this scope.
    - **audit_trace** scope (BY DESIGN): Section 7 ``Audit Trace`` of the
      final report. Contains internal IDs/hygiene counters intentionally for
      machine consumption. Reported as a separate volume; **NOT** counted as
      reviewer-visible leakage.
    - **state_field** scope: hits inside ``review_state.flaw_candidates[]``
      ``title`` / ``description``. Real hygiene issues (fallback flaw
      extractor dumps raw JSON) but do not necessarily appear in the
      final_report. Reported as a separate hygiene volume.

    Backward-compatible: if a final report has no Section 7 (older artifacts),
    ``audit_trace`` is empty and ``final_report`` covers the entire text — so
    legacy artifacts produce the same numbers as before.
    """
    text = final_report or ""
    human_text, audit_text, has_split = split_final_report(text)

    # Build per-flaw chunk list for state-field scope.
    state_chunks: List[Tuple[str, str]] = []
    for fl in (review_state or {}).get("flaw_candidates") or []:
        for k in ("title", "description"):
            v = fl.get(k)
            if isinstance(v, str) and v:
                state_chunks.append((f"flaw_candidates.{fl.get('flaw_id', '?')}.{k}", v))

    # final_report (human-readable) scope
    per_probe_fr, tier_counts_fr, sample_excerpts_fr = _scope_metrics(human_text)
    # audit_trace scope (Section 7 only)
    per_probe_audit, tier_counts_audit, sample_excerpts_audit = _scope_metrics(audit_text)

    # state_field scope (per-chunk, cumulative)
    per_probe_state: Dict[str, Dict[str, Any]] = {}
    tier_counts_state: Counter = Counter()
    sample_excerpts_state: Dict[str, List[str]] = {}
    for label, pattern, tier, _expl in PROBES:
        state_count = 0
        state_token_set = set()
        state_excerpts: List[str] = []
        for chunk_origin, chunk_text in state_chunks:
            chunk_hits = safe_findall(label, pattern, chunk_text)
            for h in chunk_hits:
                state_count += 1
                state_token_set.add(h[2])
                if len(state_excerpts) < 2:
                    state_excerpts.append(f"[{chunk_origin}] {excerpt(chunk_text, h[0], h[1])}")
        if state_count > 0:
            per_probe_state[label] = {
                "tier": tier,
                "count": state_count,
                "tokens_sample": list(state_token_set)[:5],
            }
            tier_counts_state[tier] += state_count
            sample_excerpts_state[label] = state_excerpts

    fr_raw = sum(tier_counts_fr.values())
    audit_raw = sum(tier_counts_audit.values())
    state_raw = sum(tier_counts_state.values())
    fr_weighted = sum(TIER_WEIGHT[t] * c for t, c in tier_counts_fr.items())
    audit_weighted = sum(TIER_WEIGHT[t] * c for t, c in tier_counts_audit.items())
    state_weighted = sum(TIER_WEIGHT[t] * c for t, c in tier_counts_state.items())

    return {
        "paper_id": paper_id,
        # Reviewer-visible scope (primary). Sections 1-6 only.
        "final_report": {
            "tier_counts": dict(tier_counts_fr),
            "raw_total": fr_raw,
            "leakage_score_weighted": fr_weighted,
            "per_probe": per_probe_fr,
            "sample_excerpts": sample_excerpts_fr,
            "char_count": len(human_text),
            "scope": "final_report sections 1-6 (human-readable)",
            "has_audit_trace_split": has_split,
        },
        # Audit trace scope (Section 7+). By design contains internal IDs.
        "audit_trace": {
            "tier_counts": dict(tier_counts_audit),
            "raw_total": audit_raw,
            "leakage_score_weighted": audit_weighted,
            "per_probe": per_probe_audit,
            "sample_excerpts": sample_excerpts_audit,
            "char_count": len(audit_text),
            "scope": "final_report section 7 (machine-readable audit trace)",
            "present": has_split,
        },
        # Internal-state scope (hygiene volume; not directly reviewer-visible)
        "state_field": {
            "tier_counts": dict(tier_counts_state),
            "raw_total": state_raw,
            "leakage_score_weighted": state_weighted,
            "per_probe": per_probe_state,
            "sample_excerpts": sample_excerpts_state,
            "scope": "review_state.flaw_candidates[].title|description",
        },
        # Convenience top-level fields (final_report scope only) for sorting.
        "tier_counts": dict(tier_counts_fr),
        "raw_total": fr_raw,
        "leakage_score_weighted": fr_weighted,
    }


def _scope_aggregate(per_paper: List[Dict[str, Any]], scope_key: str) -> Dict[str, Any]:
    tier_total = Counter()
    probe_total = Counter()
    rows_with_any = rows_with_l1 = rows_with_l2 = 0
    score_total = 0
    for entry in per_paper:
        scope = entry.get(scope_key) or {}
        tc = scope.get("tier_counts") or {}
        raw = scope.get("raw_total", 0)
        if raw > 0:
            rows_with_any += 1
        if tc.get("L1", 0) > 0:
            rows_with_l1 += 1
        if tc.get("L2", 0) > 0:
            rows_with_l2 += 1
        score_total += scope.get("leakage_score_weighted", 0)
        for tier, count in tc.items():
            tier_total[tier] += count
        for probe, payload in (scope.get("per_probe") or {}).items():
            probe_total[probe] += payload["count"]
    rows = len(per_paper)
    return {
        "rows_with_any_leak": rows_with_any,
        "rows_with_L1_leak": rows_with_l1,
        "rows_with_L2_leak": rows_with_l2,
        "tier_total_hits": dict(tier_total),
        "probe_total_hits": dict(probe_total),
        "raw_total_hits": sum(tier_total.values()),
        "leakage_score_weighted_total": score_total,
        "rates": {
            "any_leak_rate": rows_with_any / rows if rows else 0.0,
            "L1_leak_rate": rows_with_l1 / rows if rows else 0.0,
            "L2_leak_rate": rows_with_l2 / rows if rows else 0.0,
            "mean_score_per_paper": score_total / rows if rows else 0.0,
            "mean_raw_hits_per_paper": sum(tier_total.values()) / rows if rows else 0.0,
        },
    }


def merge_aggregate(per_paper: List[Dict[str, Any]]) -> Dict[str, Any]:
    audit_present = sum(1 for entry in per_paper if (entry.get("audit_trace") or {}).get("present"))
    return {
        "row_count": len(per_paper),
        "tier_weights": dict(TIER_WEIGHT),
        "final_report": _scope_aggregate(per_paper, "final_report"),
        "audit_trace": {
            **_scope_aggregate(per_paper, "audit_trace"),
            "rows_with_audit_trace_section": audit_present,
        },
        "state_field": _scope_aggregate(per_paper, "state_field"),
    }


def _render_scope_section(scope_label: str, scope_agg: Dict[str, Any], scope_note: str) -> List[str]:
    rates = scope_agg["rates"]
    tier_total = scope_agg["tier_total_hits"]
    probe_total = scope_agg["probe_total_hits"]
    out: List[str] = [
        f"## Scope: {scope_label}",
        "",
        scope_note,
        "",
        f"- rows_with_any_leak: **{scope_agg['rows_with_any_leak']}** "
        f"(rate = {rates['any_leak_rate']:.4f})",
        f"- rows_with_L1_leak: **{scope_agg['rows_with_L1_leak']}** "
        f"(rate = {rates['L1_leak_rate']:.4f})",
        f"- rows_with_L2_leak: **{scope_agg['rows_with_L2_leak']}** "
        f"(rate = {rates['L2_leak_rate']:.4f})",
        f"- raw_total_hits: **{scope_agg['raw_total_hits']}**",
        f"- leakage_score_weighted_total: **{scope_agg['leakage_score_weighted_total']}** (L1×3 + L2×2 + L3×1)",
        f"- mean_score_per_paper: {rates['mean_score_per_paper']:.4f}",
        "",
        "### Tier breakdown",
        "",
        "| tier | weight | hits |",
        "|---|---:|---:|",
    ]
    for tier in ("L1", "L2", "L3"):
        out.append(f"| **{tier}** | {TIER_WEIGHT[tier]} | {tier_total.get(tier, 0)} |")
    out += [
        "",
        "### Probe breakdown",
        "",
        "| probe | tier | hits |",
        "|---|---|---:|",
    ]
    tier_order = {"L1": 0, "L2": 1, "L3": 2}
    probe_meta = {label: tier for label, _, tier, _ in PROBES}
    for probe, count in sorted(probe_total.items(), key=lambda kv: (tier_order.get(probe_meta.get(kv[0], "L3"), 9), -kv[1])):
        tier = probe_meta.get(probe, "?")
        out.append(f"| `{probe}` | {tier} | {count} |")
    return out


def write_markdown(out_path: Path, payload: Dict[str, Any]) -> None:
    agg = payload["aggregate"]
    fr = agg["final_report"]
    audit = agg["audit_trace"]
    state = agg["state_field"]

    lines: List[str] = [
        "# Meta-Leakage Audit v1",
        "",
        f"- input: `{payload['input']}`",
        f"- row_count: **{agg['row_count']}**",
        f"- audit-trace section present in: **{audit.get('rows_with_audit_trace_section', 0)} / {agg['row_count']}** rows",
        f"- tier weights: L1={TIER_WEIGHT['L1']} (critical) / L2={TIER_WEIGHT['L2']} (high) / L3={TIER_WEIGHT['L3']} (soft)",
        "",
        "**Three scopes are reported separately.** The *final_report (sections 1-6)* scope corresponds to text the human reviewer actually sees; this is the **primary** leakage measurement and the only one written back via `--write-back-criterion`. The *audit_trace (section 7)* scope is the machine-readable trace introduced by HygieneV3 — it intentionally contains internal IDs and hygiene counters and is **not** counted as reviewer-visible leakage. The *state_field* scope is a hygiene volume measured inside `review_state.flaw_candidates[]` `title` / `description`, which often contains raw JSON dumps from the fallback flaw extractor but does not necessarily reach the reviewer.",
        "",
    ]
    lines += _render_scope_section(
        "final_report sections 1-6 (reviewer-visible — PRIMARY)",
        fr,
        "Hits inside the human-readable sections (1-6) of the final report. These tokens are visible to a human reviewer and are the strict measurement of meta-leakage for the paper's *State Hygiene* claim.",
    )
    lines += [""]
    lines += _render_scope_section(
        "audit_trace section 7 (machine-readable — BY DESIGN)",
        audit,
        "Hits inside the `7. Audit Trace (machine-readable)` section. By design this section carries internal claim/evidence/flaw IDs and hygiene counters for offline auditing; matches here are expected and **NOT** counted toward reviewer-visible leakage.",
    )
    lines += [""]
    lines += _render_scope_section(
        "state_field (internal hygiene volume — secondary)",
        state,
        "Hits inside `review_state.flaw_candidates[].title|description` only. These reveal fallback-flaw extractor regressions (raw JSON dumps stored as flaw title) but do not directly expose the human reviewer.",
    )

    # Top 10 by final-report weighted score
    sorted_per = sorted(payload["per_paper"], key=lambda x: -(x.get("final_report") or {}).get("leakage_score_weighted", 0))
    lines += [
        "",
        "## Top 10 papers by final_report weighted_score",
        "",
        "| paper_id | weighted | raw | L1 | L2 | L3 | state_raw | state_weighted |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for entry in sorted_per[:10]:
        f = entry.get("final_report") or {}
        s = entry.get("state_field") or {}
        tc = f.get("tier_counts") or {}
        lines.append(
            f"| `{entry['paper_id']}` | {f.get('leakage_score_weighted', 0)} | "
            f"{f.get('raw_total', 0)} | {tc.get('L1', 0)} | {tc.get('L2', 0)} | {tc.get('L3', 0)} | "
            f"{s.get('raw_total', 0)} | {s.get('leakage_score_weighted', 0)} |"
        )

    # Sample excerpts (final_report only)
    lines += [
        "",
        "## Final-report sample excerpts (top 3 worst, final_report scope)",
        "",
    ]
    for entry in sorted_per[:3]:
        f = entry.get("final_report") or {}
        score = f.get("leakage_score_weighted", 0)
        lines.append(f"### `{entry['paper_id']}` (final_report weighted_score={score})")
        lines.append("")
        for probe, excerpts_list in (f.get("sample_excerpts") or {}).items():
            tier = (f.get("per_probe") or {}).get(probe, {}).get("tier", "?")
            lines.append(f"- **{probe}** ({tier}):")
            for ex in excerpts_list[:2]:
                lines.append(f"  - _{ex}_")
        lines.append("")

    # State-field sample excerpts (separate)
    lines += [
        "## State-field sample excerpts (worst paper, state_field scope)",
        "",
    ]
    sorted_state = sorted(payload["per_paper"], key=lambda x: -(x.get("state_field") or {}).get("leakage_score_weighted", 0))
    for entry in sorted_state[:1]:
        s = entry.get("state_field") or {}
        score = s.get("leakage_score_weighted", 0)
        if score == 0:
            continue
        lines.append(f"### `{entry['paper_id']}` (state_field weighted_score={score})")
        lines.append("")
        for probe, excerpts_list in (s.get("sample_excerpts") or {}).items():
            tier = (s.get("per_probe") or {}).get(probe, {}).get("tier", "?")
            lines.append(f"- **{probe}** ({tier}):")
            for ex in excerpts_list[:2]:
                lines.append(f"  - _{ex}_")
        lines.append("")

    lines += [
        "## How to interpret",
        "",
        "- The **final_report scope** is the strict measurement: every hit is text that a human reviewer would actually read. The dominant L1 contributors here are `inline_schema_id_dump` (e.g. `[claims: claim-1; evidence: evidence-2-turn-2]`) and `snake_case_decision_enum` (e.g. `some_real_support_but_not_enough_quality_or_coverage_for_accept_like` copied from the recommendation enum). Both come from the final-report writer prompt rendering internal schema tokens verbatim.",
        "- The **state_field scope** is a separate hygiene volume. The fallback flaw extractor on some papers stores the raw JSON envelope (e.g. `{ \"flaw_candidates\": [ { \"flaw_id\": \"flaw-1\", ...} ] }`) inside the flaw `title` / `description` fields. This is invisible to a reviewer reading the final report, but it is a real hygiene regression that should be reported alongside the State Hygiene narrative.",
        "- L2 hits surface context-window or truncation language in natural prose (`abstract is truncated`, `text truncation prevents`). They are factually accurate but reveal a coverage limit the paper should disclose explicitly rather than emit silently.",
        "- L3 hits are boilerplate (`by the end of the review process`, `not fully resolved`, `fallback evidence`). They are the easiest to clean up at the report-writer prompt level.",
        "- The `total_meta_leakage` field consumed by `analyze_mainline_final_v1.py:346` is filled when this script is invoked with `--write-back-criterion`; the value written is the **final_report scope raw_total** (the strict reviewer-visible volume).",
        "",
        "Generated by `scripts/audit_meta_leakage_v1.py`.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_back_criterion(criterion_path: Path, raw_total: int) -> bool:
    """Inject `total_meta_leakage` into a criterion summary file (if it exists and is JSON)."""
    if not criterion_path.exists():
        return False
    try:
        data = json.loads(criterion_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    agg = data.get("aggregate")
    if isinstance(agg, dict):
        agg["total_meta_leakage"] = raw_total
    else:
        data["total_meta_leakage"] = raw_total
    criterion_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Meta-leakage audit v1 (rule-based, 0 LLM calls).")
    parser.add_argument(
        "--jsonl",
        default="outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl",
    )
    parser.add_argument(
        "--output-json",
        default="outputs/results_main/review_infer/meta_leakage_v1.json",
    )
    parser.add_argument(
        "--output-md",
        default="docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/META_LEAKAGE_V1.md",
    )
    parser.add_argument(
        "--write-back-criterion",
        default="",
        help="Optional path to a criterion summary JSON; will write `total_meta_leakage` back if provided.",
    )
    args = parser.parse_args()

    rows = []
    for line in Path(args.jsonl).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        rows.append(audit_paper(d.get("paper_id", ""), d.get("final_report") or "", d.get("review_state") or {}))

    aggregate = merge_aggregate(rows)
    payload = {
        "input": args.jsonl,
        "schema_version": "v1",
        "rule_set": "tiered regex (L1 critical / L2 high / L3 soft)",
        "tier_weights": dict(TIER_WEIGHT),
        "per_paper": rows,
        "aggregate": aggregate,
    }

    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)

    written = False
    fr_agg = aggregate["final_report"]
    audit_agg = aggregate["audit_trace"]
    state_agg = aggregate["state_field"]
    if args.write_back_criterion:
        # Strict measurement: only reviewer-visible hits (sections 1-6) go to total_meta_leakage.
        written = write_back_criterion(Path(args.write_back_criterion), fr_agg["raw_total_hits"])

    summary = {
        "row_count": aggregate["row_count"],
        "final_report": {
            "scope": "sections_1_6_human_readable",
            "rows_with_any_leak": fr_agg["rows_with_any_leak"],
            "rows_with_L1_leak": fr_agg["rows_with_L1_leak"],
            "tier_total_hits": fr_agg["tier_total_hits"],
            "raw_total_hits": fr_agg["raw_total_hits"],
            "leakage_score_weighted_total": fr_agg["leakage_score_weighted_total"],
            "mean_score_per_paper": fr_agg["rates"]["mean_score_per_paper"],
        },
        "audit_trace": {
            "scope": "section_7_machine_readable_by_design",
            "rows_with_audit_trace_section": audit_agg.get("rows_with_audit_trace_section", 0),
            "rows_with_any_leak": audit_agg["rows_with_any_leak"],
            "tier_total_hits": audit_agg["tier_total_hits"],
            "raw_total_hits": audit_agg["raw_total_hits"],
            "leakage_score_weighted_total": audit_agg["leakage_score_weighted_total"],
        },
        "state_field": {
            "rows_with_any_leak": state_agg["rows_with_any_leak"],
            "tier_total_hits": state_agg["tier_total_hits"],
            "raw_total_hits": state_agg["raw_total_hits"],
            "leakage_score_weighted_total": state_agg["leakage_score_weighted_total"],
        },
        "output_json": str(out_json),
        "output_md": str(out_md),
        "criterion_writeback": written,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
