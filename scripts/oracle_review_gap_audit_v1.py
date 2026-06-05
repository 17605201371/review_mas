#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent_system.environments.env_package.review.state import (
    _flaw_has_negative_grounding,
    _is_paper_negative_evidence_record,
    build_decision_hygiene_view,
    infer_final_recommendation_view,
)

DEFAULT_JSONL = "critique_hygienev5_full39_20260511_qwen35.jsonl"
DEFAULT_DATASET_ARROW = "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-test.arrow"
DEFAULT_CACHE = "outputs/results_main/review_infer/oracle_review_gap_audit_v1_cache.json"
DEFAULT_OUTPUT_JSON = "outputs/results_main/review_infer/oracle_review_gap_audit_v1.json"
DEFAULT_OUTPUT_MD = "docs/experiments/ORACLE_REVIEW_GAP_AUDIT_V1.md"
DEFAULT_ENV_FILE = ".env"
MAX_PAPER_CHARS = 50_000
MAX_RETRIES = 1

SYSTEM_PROMPT = """You are an expert ML/NLP conference area-chair style reviewer and diagnostic oracle.

You will receive a paper text plus the current multi-agent ReviewState summary produced by an automated reviewer. Your job is NOT to write a full review. Your job is to diagnose what the system missed.

Focus on functional gaps:
1. Whether the paper has enough evidence for accept-like judgment.
2. Whether there are paper-level weaknesses, overclaims, missing experiments, weak baselines, insufficient metrics, reproducibility issues, or novelty issues.
3. Which paper passages act as positive evidence and which act as negative/challenge/insufficient evidence.
4. Whether existing system flaws are grounded or invalid.
5. Whether unlinked negative evidence should become a grounded flaw, potential concern, unresolved question, or false negative evidence.

Return exactly one JSON object. Do not use markdown. Do not include prose outside JSON.

Required JSON schema:
{
  "paper_decision_signal": "accept_like" | "borderline_positive" | "borderline_insufficient" | "reject_like" | "not_assessable",
  "decision_rationale": "short explanation",
  "system_failure_modes": ["negative_evidence_missing" | "negative_evidence_unbound" | "false_negative_grounding" | "positive_support_missing" | "positive_support_not_discriminative" | "claim_priority_wrong" | "context_visibility_gap" | "critique_too_conservative" | "critique_too_generic" | "decision_calibration_gap" | "state_schema_gap"],
  "core_claim_support": [
    {"claim_id": "claim id or oracle-claim-N", "claim": "claim text", "support_level": "strong" | "partial" | "weak" | "none", "evidence_quote": "short paper quote or paraphrase", "is_primary": true}
  ],
  "negative_evidence": [
    {"target_claim_id": "claim id or oracle-claim-N", "stance": "contradicts" | "weakens" | "missing" | "overclaim" | "insufficient", "evidence_quote": "short quote/paraphrase", "why_it_matters": "short reason"}
  ],
  "grounded_flaws": [
    {"title": "short title", "description": "specific paper-level weakness", "severity": "critical" | "major" | "minor", "grounding_quote": "short quote/paraphrase", "related_claim_ids": ["claim id"], "should_be_negative_evidence": true}
  ],
  "existing_flaw_assessment": [
    {"flaw_id": "flaw id", "verdict": "grounded" | "not_grounded" | "overstated" | "supporting_evidence_misused_as_negative", "reason": "short reason"}
  ],
  "next_system_action": "extract_more_evidence" | "bind_negative_evidence_to_flaw" | "validate_negative_grounding" | "revise_claim_priority" | "decision_sufficiency_check" | "no_action_needed"
}
"""

USER_TEMPLATE = """Paper ID: {paper_id}
Gold label inferred for audit: {gold_label}
System final decision: {final_decision}
System recommendation view: {recommendation_view}
System recommendation reason: {recommendation_reason}
Case tags: {case_tags}

Paper text:
<<<
{paper_text}
>>>

System claims:
{claims_block}

System evidence map:
{evidence_block}

System flaw candidates:
{flaws_block}

System hygiene metrics:
{hygiene_block}

System final report excerpt:
<<<
{final_report_excerpt}
>>>

Diagnose the gap between the paper and the system ReviewState. Output exactly one JSON object following the required schema.
"""

JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)
INVALID_BACKSLASH_RE = re.compile(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})')


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_paper_text_map(arrow_path: Path) -> Dict[str, str]:
    import pyarrow.ipc as ipc
    with open(arrow_path, "rb") as f:
        table = ipc.open_stream(f).read_all()
    out: Dict[str, str] = {}
    ids = table.column("id").to_pylist()
    inputs = table.column("inputs").to_pylist()
    for paper_id, payload in zip(ids, inputs):
        if not isinstance(payload, str):
            continue
        try:
            messages = json.loads(payload)
        except Exception:
            continue
        text = ""
        for msg in messages or []:
            if isinstance(msg, dict) and msg.get("role") == "user":
                text = str(msg.get("content") or "")
                break
        if text:
            out[str(paper_id)] = text
    return out


def truncate_text(text: str, limit: int = MAX_PAPER_CHARS) -> str:
    if len(text) <= limit:
        return text
    head = text[: int(limit * 0.65)]
    tail = text[-int(limit * 0.35):]
    return head + "\n\n[... paper truncated for oracle prompt budget ...]\n\n" + tail


def compact(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\n", " ").strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def format_claims(state: Dict[str, Any]) -> str:
    lines = []
    for claim in state.get("claims", []) or []:
        if not isinstance(claim, dict):
            continue
        lines.append(
            f"- {claim.get('claim_id')}: status={claim.get('status')}; importance={claim.get('importance')}; claim={compact(claim.get('claim') or claim.get('claim_text'), 320)}; supporting_evidence_ids={claim.get('supporting_evidence_ids') or []}"
        )
    return "\n".join(lines) if lines else "- (none)"


def format_evidence(state: Dict[str, Any]) -> str:
    lines = []
    for ev in state.get("evidence_map", []) or []:
        if not isinstance(ev, dict):
            continue
        is_negative = _is_paper_negative_evidence_record(ev)
        text = ev.get("evidence") or ev.get("evidence_text") or ""
        lines.append(
            f"- {ev.get('evidence_id')}: claim_id={ev.get('claim_id')}; stance={ev.get('stance')}; strength={ev.get('strength')}; source={ev.get('source')}; paper_negative={is_negative}; text={compact(text, 360)}"
        )
    return "\n".join(lines) if lines else "- (none)"


def format_flaws(state: Dict[str, Any], hygiene_view: Dict[str, Any]) -> str:
    by_id = {str(f.get("flaw_id") or ""): f for f in hygiene_view.get("flaw_candidates", []) or [] if isinstance(f, dict)}
    lines = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        fid = str(flaw.get("flaw_id") or "")
        hf = by_id.get(fid, flaw)
        lines.append(
            f"- {fid}: title={compact(flaw.get('title'), 120)}; severity={flaw.get('severity')}; raw_status={flaw.get('status')}; hygiene_status={hf.get('status')}; evidence_ids={flaw.get('evidence_ids') or []}; negative_evidence_ids={flaw.get('negative_evidence_ids') or []}; has_negative_grounding={_flaw_has_negative_grounding(hf, hygiene_view)}; description={compact(flaw.get('description'), 420)}"
        )
    return "\n".join(lines) if lines else "- (none)"


def infer_gold(row: Dict[str, Any]) -> str:
    final_decision = str(row.get("final_decision") or "")
    correct = float(row.get("decision_correct") or 0.0)
    if final_decision == "reject" and correct >= 0.5:
        return "reject"
    if final_decision == "accept" and correct >= 0.5:
        return "accept"
    if final_decision == "reject":
        return "accept"
    if final_decision == "accept":
        return "reject"
    return "unknown"


def case_tags(row: Dict[str, Any]) -> List[str]:
    state = row.get("review_state") or {}
    hygiene_view = build_decision_hygiene_view(state)
    hygiene = hygiene_view.get("decision_hygiene", {}) or {}
    rec = infer_final_recommendation_view(state, {})
    gold = infer_gold(row)
    tags: List[str] = []
    if gold == "accept" and row.get("final_decision") == "reject":
        tags.append("gold_accept_false_reject")
    if gold == "reject" and rec.get("recommendation_view") == "borderline_positive":
        tags.append("support_rich_gold_reject")
    if int(hygiene.get("negative_evidence_unlinked_to_flaw_count", 0) or 0) > 0:
        tags.append("unlinked_negative_evidence")
    if int(hygiene.get("grounded_active_flaw_count", 0) or 0) > 0:
        tags.append("grounded_flaw_present")
    if int(hygiene.get("real_strong_support_total", 0) or 0) == 0:
        tags.append("zero_strong_support")
    if float(hygiene.get("primary_claim_support_coverage", 0.0) or 0.0) >= 1.0:
        tags.append("primary_support_covered")
    if int(hygiene.get("support_only_flaw_filtered_count", 0) or 0) > 0:
        tags.append("support_only_flaw_filtered")
    return tags


def select_cases(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    scored: List[Tuple[Tuple[int, int, str], Dict[str, Any]]] = []
    for row in rows:
        tags = case_tags(row)
        priority = 100
        if "unlinked_negative_evidence" in tags:
            priority = 0
        elif "grounded_flaw_present" in tags:
            priority = 1
        elif "gold_accept_false_reject" in tags and "zero_strong_support" in tags:
            priority = 2
        elif "gold_accept_false_reject" in tags:
            priority = 3
        elif "support_rich_gold_reject" in tags:
            priority = 4
        if priority < 100:
            scored.append(((priority, -len(tags), str(row.get("paper_id") or "")), row))
    scored.sort(key=lambda item: item[0])
    selected = [row for _, row in scored]
    if limit > 0:
        selected = selected[:limit]
    return selected


def render_prompt(row: Dict[str, Any], paper_text: str) -> Tuple[str, str, Dict[str, Any]]:
    state = row.get("review_state") or {}
    hygiene_view = build_decision_hygiene_view(state)
    hygiene = hygiene_view.get("decision_hygiene", {}) or {}
    rec = infer_final_recommendation_view(state, {})
    tags = case_tags(row)
    hygiene_keys = [
        "real_strong_support_total",
        "empirical_real_strong_support_count",
        "claims_with_real_strong_support",
        "claims_with_2plus_independent_support",
        "primary_claim_support_coverage",
        "primary_claim_empirical_coverage",
        "negative_evidence_candidate_count",
        "negative_evidence_linked_to_flaw_count",
        "negative_evidence_unlinked_to_flaw_count",
        "grounded_active_flaw_count",
        "support_only_flaw_filtered_count",
        "total_limitation_count",
        "context_limitation_count",
        "open_evidence_gap_count",
    ]
    hygiene_block = json.dumps({k: hygiene.get(k) for k in hygiene_keys}, ensure_ascii=False, sort_keys=True)
    final_report = str(row.get("final_report") or "")
    user_prompt = USER_TEMPLATE.format(
        paper_id=row.get("paper_id") or "",
        gold_label=infer_gold(row),
        final_decision=row.get("final_decision") or "",
        recommendation_view=rec.get("recommendation_view") or "",
        recommendation_reason=rec.get("reason") or "",
        case_tags=", ".join(tags),
        paper_text=truncate_text(paper_text),
        claims_block=format_claims(state),
        evidence_block=format_evidence(state),
        flaws_block=format_flaws(state, hygiene_view),
        hygiene_block=hygiene_block,
        final_report_excerpt=truncate_text(final_report, 6_000),
    )
    meta = {
        "paper_id": row.get("paper_id") or "",
        "gold_label": infer_gold(row),
        "final_decision": row.get("final_decision") or "",
        "recommendation_view": rec.get("recommendation_view") or "",
        "recommendation_reason": rec.get("reason") or "",
        "case_tags": tags,
        "hygiene": {k: hygiene.get(k) for k in hygiene_keys},
    }
    return SYSTEM_PROMPT, user_prompt, meta


def parse_json_response(content: str) -> Dict[str, Any]:
    raw = content or ""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    match = JSON_OBJ_RE.search(text)
    if not match:
        return {"parse_error": "no_json", "raw": raw[:2000]}
    block = match.group(0)
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        try:
            return json.loads(INVALID_BACKSLASH_RE.sub(r"\\\\", block))
        except json.JSONDecodeError as exc:
            return {"parse_error": str(exc), "raw": raw[:2000]}


def cache_key(model: str, paper_id: str, system_prompt: str, user_prompt: str) -> str:
    h = hashlib.sha256()
    for part in [model, paper_id, system_prompt, user_prompt]:
        h.update(str(part).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def load_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(path: Path, cache: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


class ArkOracle:
    def __init__(self) -> None:
        from openai import OpenAI
        api_key = os.environ.get("ARK_API_KEY")
        if not api_key:
            raise SystemExit("ARK_API_KEY is required; put it in .env or export it")
        self.base_url = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.environ.get("ARK_MODEL", "deepseek-v3-2-251201")
        self.max_tokens = int(os.environ.get("ARK_MAX_TOKENS", "1200"))
        self.temperature = float(os.environ.get("ARK_TEMPERATURE", "0.0"))
        self.client = OpenAI(base_url=self.base_url, api_key=api_key, timeout=float(os.environ.get("ARK_TIMEOUT", "120")))

    def call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        last_err: Optional[Exception] = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                usage = getattr(resp, "usage", None)
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                } if usage else {}
                return {"content": resp.choices[0].message.content or "", "usage": usage_dict, "attempt": attempt}
            except Exception as exc:
                last_err = exc
                time.sleep(1.5 * (attempt + 1))
        return {"content": "", "usage": {}, "attempt": MAX_RETRIES, "error": str(last_err)}


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    signal_counts = Counter(str(r.get("oracle", {}).get("paper_decision_signal") or "parse_error") for r in results)
    failure_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    by_tag: Dict[str, Counter[str]] = {}
    total_negative = 0
    total_flaws = 0
    parse_errors = 0
    token_total = 0
    for r in results:
        oracle = r.get("oracle") or {}
        if oracle.get("parse_error"):
            parse_errors += 1
        token_total += int((r.get("usage") or {}).get("total_tokens") or 0)
        for mode in oracle.get("system_failure_modes") or []:
            failure_counts[str(mode)] += 1
        action_counts[str(oracle.get("next_system_action") or "")] += 1
        total_negative += len(oracle.get("negative_evidence") or []) if isinstance(oracle.get("negative_evidence"), list) else 0
        total_flaws += len(oracle.get("grounded_flaws") or []) if isinstance(oracle.get("grounded_flaws"), list) else 0
        for tag in r.get("case_tags") or []:
            by_tag.setdefault(tag, Counter())[str(oracle.get("paper_decision_signal") or "parse_error")] += 1
    return {
        "case_count": len(results),
        "parse_errors": parse_errors,
        "oracle_signal_counts": dict(signal_counts),
        "failure_mode_counts": dict(failure_counts),
        "next_action_counts": dict(action_counts),
        "oracle_negative_evidence_total": total_negative,
        "oracle_grounded_flaw_total": total_flaws,
        "token_total": token_total,
        "signal_by_case_tag": {tag: dict(counter) for tag, counter in by_tag.items()},
    }


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    agg = payload.get("aggregate") or {}
    lines = [
        "# Oracle Review Gap Audit v1",
        "",
        f"- input: `{payload.get('input_jsonl')}`",
        f"- model: `{payload.get('model')}`",
        f"- base_url: `{payload.get('base_url')}`",
        f"- cases: **{agg.get('case_count', 0)}**",
        f"- parse_errors: **{agg.get('parse_errors', 0)}**",
        f"- token_total: **{agg.get('token_total', 0)}**",
        "",
        "## Aggregate",
        "",
        "### Oracle decision signals",
        "",
    ]
    for k, v in sorted((agg.get("oracle_signal_counts") or {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{k}`: {v}")
    lines += ["", "### Failure modes", ""]
    for k, v in sorted((agg.get("failure_mode_counts") or {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{k}`: {v}")
    lines += ["", "### Next system actions", ""]
    for k, v in sorted((agg.get("next_action_counts") or {}).items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        f"- oracle negative evidence total: **{agg.get('oracle_negative_evidence_total', 0)}**",
        f"- oracle grounded flaw total: **{agg.get('oracle_grounded_flaw_total', 0)}**",
        "",
        "## Per-case summary",
        "",
        "| paper_id | tags | system view | oracle signal | next action | failure modes | negative evidence | grounded flaws |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for r in payload.get("results") or []:
        oracle = r.get("oracle") or {}
        lines.append(
            "| `{}` | {} | `{}` | `{}` | `{}` | {} | {} | {} |".format(
                r.get("paper_id", ""),
                ", ".join(f"`{x}`" for x in r.get("case_tags") or []),
                r.get("recommendation_view", ""),
                oracle.get("paper_decision_signal", "parse_error"),
                oracle.get("next_system_action", ""),
                ", ".join(f"`{x}`" for x in (oracle.get("system_failure_modes") or [])),
                len(oracle.get("negative_evidence") or []) if isinstance(oracle.get("negative_evidence"), list) else 0,
                len(oracle.get("grounded_flaws") or []) if isinstance(oracle.get("grounded_flaws"), list) else 0,
            )
        )
    lines += ["", "Generated by `scripts/oracle_review_gap_audit_v1.py`."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek/ARK oracle audit for V5 review gaps.")
    parser.add_argument("--jsonl", default=DEFAULT_JSONL)
    parser.add_argument("--dataset-arrow", default=DEFAULT_DATASET_ARROW)
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE)
    parser.add_argument("--cache", default=DEFAULT_CACHE)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--paper-ids", nargs="*")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / args.env_file)
    rows = load_jsonl(Path(args.jsonl))
    if args.paper_ids:
        keep = set(args.paper_ids)
        rows = [r for r in rows if str(r.get("paper_id") or "") in keep]
        selected = rows
    else:
        selected = select_cases(rows, args.limit)

    paper_text_map = load_paper_text_map(Path(args.dataset_arrow))
    prompts: List[Tuple[Dict[str, Any], str, str, Dict[str, Any]]] = []
    for row in selected:
        paper_id = str(row.get("paper_id") or "")
        paper_text = paper_text_map.get(paper_id, "")
        if not paper_text:
            print(f"[oracle] missing paper text for {paper_id}", file=sys.stderr)
            continue
        sys_p, user_p, meta = render_prompt(row, paper_text)
        prompts.append((row, sys_p, user_p, meta))

    if args.dry_run:
        print(json.dumps({
            "selected_count": len(prompts),
            "selected": [meta for _, _, _, meta in prompts],
            "model": os.environ.get("ARK_MODEL", "deepseek-v3-2-251201"),
            "base_url": os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
            "api_key_present": bool(os.environ.get("ARK_API_KEY")),
            "first_prompt_chars": len(prompts[0][2]) if prompts else 0,
            "first_prompt_preview": prompts[0][2][:1200] if prompts else "",
        }, ensure_ascii=False, indent=2))
        return 0

    oracle_client = ArkOracle()
    cache_path = Path(args.cache)
    cache = load_cache(cache_path)
    results: List[Dict[str, Any]] = []
    dirty = False
    for idx, (_, sys_p, user_p, meta) in enumerate(prompts, start=1):
        key = cache_key(oracle_client.model, meta["paper_id"], sys_p, user_p)
        if key in cache:
            entry = cache[key]
            oracle_obj = entry.get("oracle") or {}
            usage = entry.get("usage") or {}
            from_cache = True
        else:
            resp = oracle_client.call(sys_p, user_p)
            oracle_obj = parse_json_response(resp.get("content") or "")
            usage = resp.get("usage") or {}
            cache[key] = {
                "paper_id": meta["paper_id"],
                "model": oracle_client.model,
                "oracle": oracle_obj,
                "usage": usage,
                "raw": (resp.get("content") or "")[:4000],
                "error": resp.get("error"),
            }
            dirty = True
            from_cache = False
        result = {**meta, "oracle": oracle_obj, "usage": usage, "from_cache": from_cache}
        results.append(result)
        print(f"[oracle] {idx}/{len(prompts)} {meta['paper_id']} cache={from_cache} signal={oracle_obj.get('paper_decision_signal', 'parse_error')}", file=sys.stderr)
        if dirty:
            save_cache(cache_path, cache)
            dirty = False
    aggregate_payload = aggregate(results)
    payload = {
        "input_jsonl": args.jsonl,
        "dataset_arrow": args.dataset_arrow,
        "model": oracle_client.model,
        "base_url": oracle_client.base_url,
        "schema_version": "oracle_review_gap_audit_v1",
        "aggregate": aggregate_payload,
        "results": results,
    }
    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(Path(args.output_md), payload)
    print(json.dumps({
        "case_count": aggregate_payload["case_count"],
        "parse_errors": aggregate_payload["parse_errors"],
        "token_total": aggregate_payload["token_total"],
        "output_json": str(out_json),
        "output_md": args.output_md,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
