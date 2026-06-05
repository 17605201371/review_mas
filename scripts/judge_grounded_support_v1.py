#!/usr/bin/env python3
"""B2 / C0a — LLM judge of paper-grounded support precision and flaw rate.

Implements the judge step from `PAPER_GAP_REMEDIATION_PLAN.md` §B2 and
addresses `PAPER_C_DIRECTION_LIMITATION_AUDIT.md` 不足十二 红线 6: the
upgrade from agent self-claimed grounded rate to **judge-verified**
grounded rate.

What this script does
---------------------
For each paper in fulltest39:

  1. Load the raw paper text from DeepReview-13K test split
     (`/reviewF/datasets/WestLakeNLP___deep_review-13_k`). The paper text
     lives inside `inputs[1]['content']` of each row keyed by `id`.

  2. Load every `evidence` and `flaw_candidate` from the closure-run
     ReviewState in
     `outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl`.

  3. For each evidence: ask an LLM judge (via an OpenAI-compatible
     endpoint — defaults are wired to Volcengine ARK) whether the
     evidence is *paper_grounded* given the paper text + claim + stance.

  4. For each flaw: ask the same judge whether the flaw is
     *paper_grounded* given the paper text + flaw record + cited
     evidence text.

  5. Cache every judge call by `sha256(paper_id + entry_id + prompt)` so
     re-runs only re-issue calls that changed. Cache is a single JSON
     file (path configurable).

  6. Aggregate:
       Grounded_Support_Precision = grounded_evidence / total_strong_support_evidence
       Grounded_Flaw_Rate         = grounded_flaw / total_flaw

  7. Emit a structured JSON + Markdown report.

API configuration
-----------------
Reads from environment variables (defaults indicated):

  ARK_API_KEY    (required)
  ARK_BASE_URL   default: https://ark.cn-beijing.volces.com/api/v3
  ARK_MODEL      default: doubao-seed-1-6   (replace with your endpoint id)
  ARK_TIMEOUT    default: 120  (seconds)
  ARK_MAX_TOKENS default: 256
  ARK_TEMPERATURE default: 0.0

The script does not hardcode an API key. To switch to local Qwen3-9B,
set ARK_BASE_URL=http://localhost:8000/v1 and ARK_API_KEY=anything.

Caveats / honest framing
------------------------
- judge_agreement against human labels is **not** measured here.
  PAPER_GAP_REMEDIATION_PLAN.md §B2 lists 30-sample human alignment as a
  follow-up; this script produces machine-judged numbers only and tags
  them as such. Paper text must say *"LLM-judged paper-grounded rate"*,
  not *"human-verified grounding"*.
- The judge model itself can be wrong. We persist the full judge
  response (judgment + quote + reason) so reviewers can spot-check.
- For long papers we truncate `paper_text` to MAX_PAPER_CHARS to keep
  token usage bounded (default 50000 chars ≈ 12k tokens). This is a
  pragmatic cap to fit Volcengine ARK 32k/128k context windows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import string
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
DEFAULT_JSONL = "outputs/results_main/review_infer/mainline_final_v1_closure_9b_fulltest39_20260504_gold.jsonl"
DEFAULT_GOLD_LABELS = "docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/fulltest39_gold_labels_locked_20260504.json"
DEFAULT_DATASET_ARROW = "/reviewF/datasets/WestLakeNLP___deep_review-13_k/default/0.0.0/3db597e1e789ce04af98c5eae9e9430341face23/deep_review-13_k-test.arrow"
DEFAULT_PROMPT_FILE = "prompts/judge_grounded_support_v1.txt"
DEFAULT_CACHE = "outputs/results_main/review_infer/grounded_judge_v1_cache.json"
DEFAULT_OUTPUT_JSON = "outputs/results_main/review_infer/grounded_judge_v1.json"
DEFAULT_OUTPUT_MD = "docs/experiments/mainline_current/MAIN_EXPERIMENT_CODE_CLOSURE_V1/GROUNDED_JUDGE_V1.md"

MAX_PAPER_CHARS = 50_000  # ~12k tokens; fits 32k-context models with slack
MAX_RETRIES = 1


# -----------------------------------------------------------------------------
# Prompt loader
# -----------------------------------------------------------------------------
SECTION_RE = re.compile(r"^# === ([A-Z\-]+) ===\s*$", re.MULTILINE)


def load_prompt_sections(path: Path) -> Dict[str, str]:
    """Parse `# === NAME ===` delimited prompt template file."""
    text = path.read_text(encoding="utf-8")
    sections: Dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    required = {"SYSTEM-EVIDENCE", "USER-EVIDENCE", "SYSTEM-FLAW", "USER-FLAW"}
    missing = required - set(sections)
    if missing:
        raise RuntimeError(f"prompt file missing sections: {missing}")
    return sections


# -----------------------------------------------------------------------------
# Dataset loader (DeepReview-13K test split via Arrow)
# -----------------------------------------------------------------------------
def load_paper_text_map(arrow_path: Path) -> Dict[str, str]:
    """Return {paper_id: paper_text} from DeepReview-13K test split.

    `inputs` field is a JSON-encoded list of chat messages; the paper
    text lives in the user-role message content.
    """
    import pyarrow.ipc as ipc  # local import: pyarrow is heavy
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
        # paper text is the user-role message content
        text = ""
        for msg in messages or []:
            if isinstance(msg, dict) and msg.get("role") == "user":
                text = str(msg.get("content") or "")
                break
        if text:
            out[str(paper_id)] = text
    return out


# -----------------------------------------------------------------------------
# Closure-run jsonl loader
# -----------------------------------------------------------------------------
SUPPORT_STANCES = {"supports", "partially_supports"}


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def collect_judge_targets(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (evidence_targets, flaw_targets).

    evidence_target fields: paper_id, evidence_id, claim_id, claim_text,
        evidence, stance, strength, source, support_source_bucket
    flaw_target fields: paper_id, flaw_id, title, description, severity,
        status, evidence_ids, evidence_texts (list of strings),
        post_hygiene_status, has_real_strong_evidence

    Only `strength==strong` evidence is included in the precision
    denominator (the paper claim is about *strong support precision*),
    but we judge ALL strong-support evidence regardless of stance to be
    consistent with the paper's binding-precision counter.

    For each flaw we also compute two hygiene-aware annotations so the
    aggregator can produce three Grounded_Flaw_Rate views:
      - `post_hygiene_status`: status after running
        `build_decision_hygiene_view` (the same hygiene layer the
        reviewer report uses). The "hygiene" view counts only flaws
        whose post_hygiene_status is candidate or confirmed.
      - `has_real_strong_evidence`: true iff at least one referenced
        evidence_id resolves to an evidence record with strength=='strong',
        binding_status=='bound_real_claim', and stance != 'missing'. The
        "hygiene_evidence_aware" view rescues flaws that hygiene downgraded
        but that have at least one real-strong evidence anchor.
    """
    # Lazy-import the hygiene layer so this script runs even when
    # state.py changes; failures degrade to "no hygiene info".
    try:
        from agent_system.environments.env_package.review.state import (
            build_decision_hygiene_view as _build_hygiene_view,
        )
    except Exception:
        _build_hygiene_view = None  # type: ignore

    evidence_targets: List[Dict[str, Any]] = []
    flaw_targets: List[Dict[str, Any]] = []
    for row in rows:
        pid = row.get("paper_id") or ""
        state = row.get("review_state") or {}
        # build claim_id -> claim_text
        claim_map: Dict[str, str] = {}
        for c in state.get("claims") or []:
            cid = str(c.get("claim_id") or "")
            if cid:
                claim_map[cid] = str(c.get("claim_text") or c.get("text") or "")
        # evidence map
        evidence_by_id: Dict[str, Dict[str, Any]] = {}
        for ev in state.get("evidence_map") or []:
            stance = str(ev.get("stance") or "").lower()
            strength = str(ev.get("strength") or "").lower()
            if strength != "strong" or stance not in SUPPORT_STANCES:
                continue
            cid = str(ev.get("claim_id") or "")
            evidence_targets.append({
                "paper_id": pid,
                "evidence_id": str(ev.get("evidence_id") or ""),
                "claim_id": cid,
                "claim_text": claim_map.get(cid, ""),
                "evidence": str(ev.get("evidence") or ""),
                "stance": stance,
                "strength": strength,
                "source": str(ev.get("source") or ""),
                "support_source_bucket": str(ev.get("support_source_bucket") or ""),
                "binding_status": str(ev.get("binding_status") or ""),
            })
        for ev in state.get("evidence_map") or []:
            evidence_by_id[str(ev.get("evidence_id") or "")] = ev

        # Run decision hygiene view once per paper to get post-hygiene status.
        post_hygiene_status_by_id: Dict[str, str] = {}
        if _build_hygiene_view is not None:
            try:
                view = _build_hygiene_view(state)
                for hf in view.get("flaw_candidates") or []:
                    fid = str(hf.get("flaw_id") or "")
                    if fid:
                        post_hygiene_status_by_id[fid] = str(hf.get("status") or "")
            except Exception:
                pass

        # flaws — judge every flaw regardless of status, but tag fallback
        for fl in state.get("flaw_candidates") or []:
            flaw_id = str(fl.get("flaw_id") or "")
            ev_ids = [str(x) for x in (fl.get("evidence_ids") or [])]
            ev_texts: List[Tuple[str, str]] = []
            has_real_strong_evidence = False
            for eid in ev_ids:
                src = evidence_by_id.get(eid)
                if src:
                    ev_texts.append((eid, str(src.get("evidence") or "")))
                    if (
                        str(src.get("strength") or "").lower() == "strong"
                        and str(src.get("binding_status") or "").lower() == "bound_real_claim"
                        and str(src.get("stance") or "").lower() not in {"", "missing"}
                    ):
                        has_real_strong_evidence = True
            flaw_targets.append({
                "paper_id": pid,
                "flaw_id": flaw_id,
                "title": str(fl.get("title") or ""),
                "description": str(fl.get("description") or ""),
                "severity": str(fl.get("severity") or ""),
                "status": str(fl.get("status") or ""),
                "post_hygiene_status": post_hygiene_status_by_id.get(flaw_id, str(fl.get("status") or "")),
                "has_real_strong_evidence": has_real_strong_evidence,
                "grounding_status": str(fl.get("grounding_status") or ""),
                "evidence_ids": ev_ids,
                "evidence_texts": ev_texts,
                "is_fallback_flaw": flaw_id.startswith("flaw-fallback")
                or "fallback" in str(fl.get("source") or "").lower()
                or "fallback" in str(fl.get("grounding_status") or "").lower(),
            })
    return evidence_targets, flaw_targets


# -----------------------------------------------------------------------------
# Prompt rendering
# -----------------------------------------------------------------------------
def truncate_paper(paper_text: str, limit: int = MAX_PAPER_CHARS) -> str:
    if len(paper_text) <= limit:
        return paper_text
    head = paper_text[: int(limit * 0.7)]
    tail = paper_text[-int(limit * 0.3):]
    return head + "\n\n[... paper truncated for prompt budget ...]\n\n" + tail


def render_evidence_prompt(sections: Dict[str, str], paper_text: str, ev: Dict[str, Any]) -> Tuple[str, str]:
    sys_t = sections["SYSTEM-EVIDENCE"]
    user_t = string.Template(sections["USER-EVIDENCE"]).safe_substitute(
        paper_text=truncate_paper(paper_text),
        claim=ev.get("claim_text") or "(claim text unavailable)",
        evidence=ev.get("evidence") or "",
        stance=ev.get("stance") or "",
        source=ev.get("source") or "",
    )
    return sys_t, user_t


def render_flaw_prompt(sections: Dict[str, str], paper_text: str, fl: Dict[str, Any]) -> Tuple[str, str]:
    block_lines = []
    for eid, etext in fl.get("evidence_texts") or []:
        block_lines.append(f"  - {eid}: {etext[:400]}")
    if not block_lines:
        block_lines.append("  - (no referenced evidence)")
    sys_t = sections["SYSTEM-FLAW"]
    user_t = string.Template(sections["USER-FLAW"]).safe_substitute(
        paper_text=truncate_paper(paper_text),
        flaw_title=fl.get("title") or "",
        flaw_description=fl.get("description") or "",
        flaw_severity=fl.get("severity") or "",
        flaw_status=fl.get("status") or "",
        flaw_evidence_block="\n".join(block_lines),
    )
    return sys_t, user_t


# -----------------------------------------------------------------------------
# LLM client
# -----------------------------------------------------------------------------
class LLMJudge:
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout: float, max_tokens: int, temperature: float):
        from openai import OpenAI
        self.client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

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
                content = resp.choices[0].message.content or ""
                usage = getattr(resp, "usage", None)
                usage_dict = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                } if usage else {}
                return {"content": content, "usage": usage_dict, "attempt": attempt}
            except Exception as e:  # broad on purpose; we surface errors in cache
                last_err = e
                time.sleep(1.5 * (attempt + 1))
        return {"content": "", "usage": {}, "attempt": MAX_RETRIES, "error": str(last_err)}


# -----------------------------------------------------------------------------
# Output parsing
# -----------------------------------------------------------------------------
JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)
# JSON allows escapes: \" \\ \/ \b \f \n \r \t \uXXXX. Anything else after a
# backslash is invalid. The judge frequently echoes LaTeX control sequences
# from the paper (\textbf, \mathbf, \ours, \%, \title, ...) verbatim into the
# `quote` field, which breaks json.loads. We harden parsing by escaping any
# invalid backslashes before retrying.
INVALID_BACKSLASH_RE = re.compile(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})')

# Last-resort regex for the judgment field if even the lenient parse fails.
JUDGMENT_FALLBACK_RE = re.compile(
    r'"judgment"\s*:\s*"(paper_grounded|not_paper_grounded)"', re.IGNORECASE
)
QUOTE_FIELD_RE = re.compile(r'"quote"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)
REASON_FIELD_RE = re.compile(r'"reason"\s*:\s*"((?:[^"\\]|\\.)*)"', re.DOTALL)


def _sanitize_json_string(text: str) -> str:
    """Escape backslashes that would otherwise produce JSON invalid-escape errors."""
    return INVALID_BACKSLASH_RE.sub(r"\\\\", text)


def parse_judge_response(content: str) -> Dict[str, Any]:
    """Try to parse the judge's JSON output.

    Strategy:
      1. Strip ``` fences.
      2. Find the *largest* {...} block (greedy) — judge sometimes embeds JSON
         after a short preamble.
      3. Try strict json.loads.
      4. On invalid-escape error, sanitize stray backslashes and retry.
      5. As last resort, regex-extract the `judgment` field directly. The
         paper precision metric only needs the judgment label; quote / reason
         are best-effort and used for spot checks.

    Returns dict with keys: judgment ("paper_grounded"/"not_paper_grounded"
    or "parse_error"), quote, reason, raw, parse_path.
    """
    raw = content or ""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
    m = JSON_OBJ_RE.search(text)
    if not m:
        return {
            "judgment": "parse_error", "quote": "", "reason": "no JSON found",
            "raw": raw, "parse_path": "no_json",
        }
    block = m.group(0)

    # Path 1: strict
    try:
        obj = json.loads(block)
        return _finalize_parse(obj, raw, "strict")
    except json.JSONDecodeError as e_strict:
        strict_err = str(e_strict)

    # Path 2: lenient (escape stray backslashes)
    try:
        obj = json.loads(_sanitize_json_string(block))
        return _finalize_parse(obj, raw, "lenient_escape")
    except json.JSONDecodeError as e_lenient:
        lenient_err = str(e_lenient)

    # Path 3: regex extract just the judgment (and best-effort quote/reason)
    jm = JUDGMENT_FALLBACK_RE.search(block)
    if jm:
        judgment = jm.group(1).lower()
        qm = QUOTE_FIELD_RE.search(block)
        rm = REASON_FIELD_RE.search(block)
        return {
            "judgment": judgment,
            "quote": (qm.group(1) if qm else "")[:600],
            "reason": (rm.group(1) if rm else "")[:400],
            "raw": raw,
            "parse_path": "regex_fallback",
        }
    return {
        "judgment": "parse_error",
        "quote": "",
        "reason": f"json decode error: strict={strict_err}; lenient={lenient_err}",
        "raw": raw,
        "parse_path": "all_failed",
    }


def _finalize_parse(obj: Any, raw: str, path: str) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        return {"judgment": "parse_error", "quote": "", "reason": "non-object JSON",
                "raw": raw, "parse_path": path}
    judgment = str(obj.get("judgment") or "").strip().lower()
    if judgment not in {"paper_grounded", "not_paper_grounded"}:
        return {
            "judgment": "parse_error",
            "quote": str(obj.get("quote") or ""),
            "reason": f"unrecognized judgment: {judgment!r}",
            "raw": raw,
            "parse_path": path,
        }
    return {
        "judgment": judgment,
        "quote": str(obj.get("quote") or "")[:600],
        "reason": str(obj.get("reason") or "")[:400],
        "raw": raw,
        "parse_path": path,
    }


# -----------------------------------------------------------------------------
# Cache
# -----------------------------------------------------------------------------
def cache_key(paper_id: str, target_id: str, kind: str, sys_prompt: str, user_prompt: str) -> str:
    h = hashlib.sha256()
    h.update(kind.encode())
    h.update(b"|")
    h.update(paper_id.encode())
    h.update(b"|")
    h.update(target_id.encode())
    h.update(b"|")
    h.update(sys_prompt.encode())
    h.update(b"|")
    h.update(user_prompt.encode())
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
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------------------------------------------------------
# Aggregation + report
# -----------------------------------------------------------------------------
VISIBLE_FLAW_STATUSES = {"candidate", "confirmed"}


def _flaw_in_hygiene_view(r: Dict[str, Any]) -> bool:
    """True iff flaw survives `build_decision_hygiene_view` as visible
    (status ∈ candidate/confirmed). This is what reviewers actually see in
    the final report."""
    return str(r.get("post_hygiene_status") or "").lower() in VISIBLE_FLAW_STATUSES


def _flaw_in_evidence_aware_view(r: Dict[str, Any]) -> bool:
    """True iff flaw is either visible after hygiene OR rescued by the
    evidence-aware relaxation: hygiene-downgraded but referenced at least
    one real-strong evidence anchor.

    We keep schema-dump fallback flaws excluded — even with strong evidence,
    a raw JSON dump in title/description is a reviewer-view hygiene red line
    we never want to cross. The rescue therefore *only* applies to
    non-fallback flaws.
    """
    if _flaw_in_hygiene_view(r):
        return True
    if r.get("is_fallback_flaw"):
        return False
    return bool(r.get("has_real_strong_evidence"))


def _flaw_view_stats(flaw_results: List[Dict[str, Any]], in_view: callable) -> Dict[str, Any]:
    """Aggregate grounded_flaw_rate over a flaw subset."""
    sub = [r for r in flaw_results if in_view(r)]
    g = sum(1 for r in sub if r["judgment"] == "paper_grounded")
    n = sum(1 for r in sub if r["judgment"] == "not_paper_grounded")
    e = sum(1 for r in sub if r["judgment"] == "parse_error")
    total = len(sub)
    return {
        "total": total,
        "paper_grounded": g,
        "not_paper_grounded": n,
        "parse_error": e,
        "grounded_flaw_rate": g / total if total else 0.0,
    }


def aggregate(evidence_results: List[Dict[str, Any]], flaw_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    ev_total = len(evidence_results)
    ev_grounded = sum(1 for r in evidence_results if r["judgment"] == "paper_grounded")
    ev_not_grounded = sum(1 for r in evidence_results if r["judgment"] == "not_paper_grounded")
    ev_parse_err = sum(1 for r in evidence_results if r["judgment"] == "parse_error")

    fl_total = len(flaw_results)
    fl_grounded = sum(1 for r in flaw_results if r["judgment"] == "paper_grounded")
    fl_not_grounded = sum(1 for r in flaw_results if r["judgment"] == "not_paper_grounded")
    fl_parse_err = sum(1 for r in flaw_results if r["judgment"] == "parse_error")

    # Optional: per-paper aggregates
    paper_ids = sorted({r["paper_id"] for r in evidence_results} | {r["paper_id"] for r in flaw_results})

    # Bucket-conditioned grounded rate (interpretive support)
    bucket_grounded: Dict[str, Dict[str, int]] = {}
    for r in evidence_results:
        b = r.get("support_source_bucket") or "unknown"
        bd = bucket_grounded.setdefault(b, {"total": 0, "grounded": 0})
        bd["total"] += 1
        if r["judgment"] == "paper_grounded":
            bd["grounded"] += 1

    # Fallback flaws separately
    fb_total = sum(1 for r in flaw_results if r.get("is_fallback_flaw"))
    fb_grounded = sum(1 for r in flaw_results if r.get("is_fallback_flaw") and r["judgment"] == "paper_grounded")

    # Three flaw views: raw, hygiene, hygiene_evidence_aware
    raw_stats = _flaw_view_stats(flaw_results, lambda r: True)
    hygiene_stats = _flaw_view_stats(flaw_results, _flaw_in_hygiene_view)
    evidence_aware_stats = _flaw_view_stats(flaw_results, _flaw_in_evidence_aware_view)

    # Hygiene precision diagnostics: of flaws that hygiene FILTERED OUT
    # (status moved out of candidate/confirmed by hygiene), how many were
    # truly fallback/meta vs how many were paper_grounded false negatives?
    filtered_out = [
        r for r in flaw_results
        if str(r.get("status") or "").lower() in VISIBLE_FLAW_STATUSES
        and not _flaw_in_hygiene_view(r)
    ] + [
        r for r in flaw_results
        if str(r.get("status") or "").lower() not in VISIBLE_FLAW_STATUSES
    ]
    # A flaw is "filtered out" if its raw status was visible but hygiene
    # downgraded it, OR if it was already non-visible at raw stage.
    hygiene_tp = sum(1 for r in filtered_out if r["judgment"] == "not_paper_grounded")
    hygiene_fn = sum(1 for r in filtered_out if r["judgment"] == "paper_grounded")
    hygiene_filtered_total = hygiene_tp + hygiene_fn
    hygiene_diag = {
        "filtered_out_total": len(filtered_out),
        "hygiene_true_positive_not_grounded": hygiene_tp,
        "hygiene_false_negative_grounded": hygiene_fn,
        "hygiene_precision": hygiene_tp / hygiene_filtered_total if hygiene_filtered_total else 0.0,
        "hygiene_fn_rate": hygiene_fn / hygiene_filtered_total if hygiene_filtered_total else 0.0,
    }

    return {
        "evidence": {
            "total": ev_total,
            "paper_grounded": ev_grounded,
            "not_paper_grounded": ev_not_grounded,
            "parse_error": ev_parse_err,
            "grounded_support_precision": ev_grounded / ev_total if ev_total else 0.0,
        },
        "flaw": {
            # legacy raw view (kept for back-compat with previous JSON consumers)
            "total": fl_total,
            "paper_grounded": fl_grounded,
            "not_paper_grounded": fl_not_grounded,
            "parse_error": fl_parse_err,
            "grounded_flaw_rate": fl_grounded / fl_total if fl_total else 0.0,
            "fallback_total": fb_total,
            "fallback_paper_grounded": fb_grounded,
            "fallback_grounded_rate": fb_grounded / fb_total if fb_total else 0.0,
        },
        "flaw_views": {
            "raw": raw_stats,
            "hygiene": hygiene_stats,
            "hygiene_evidence_aware": evidence_aware_stats,
        },
        "flaw_hygiene_diagnostics": hygiene_diag,
        "evidence_by_support_bucket": {
            b: {
                "total": v["total"],
                "grounded": v["grounded"],
                "rate": v["grounded"] / v["total"] if v["total"] else 0.0,
            }
            for b, v in bucket_grounded.items()
        },
        "n_papers": len(paper_ids),
    }


def write_markdown(out_path: Path, payload: Dict[str, Any]) -> None:
    agg = payload["aggregate"]
    ev = agg["evidence"]
    fl = agg["flaw"]
    bucket = agg["evidence_by_support_bucket"]

    lines = [
        "# Grounded-Support Judge v1 (LLM-judged paper-grounding)",
        "",
        f"- input jsonl: `{payload['input_jsonl']}`",
        f"- paper-text source: `{payload['paper_text_source']}`",
        f"- judge model: `{payload['judge_model']}`",
        f"- n_papers: **{agg['n_papers']}**",
        "",
        "**Honest framing.** These rates are **LLM-judged**, not human-verified. "
        "The judge model itself can be wrong. Per `PAPER_GAP_REMEDIATION_PLAN.md` §B2 "
        "the follow-up step is a 30-sample human alignment pass to bound judge agreement. "
        "Until then, paper text must say *\"LLM-judged paper-grounded rate\"*, not "
        "*\"human-verified grounding\"*.",
        "",
        "## Evidence (strong support, supports / partially_supports)",
        "",
        f"- total judged: **{ev['total']}**",
        f"- paper_grounded: **{ev['paper_grounded']}**",
        f"- not_paper_grounded: {ev['not_paper_grounded']}",
        f"- parse_error: {ev['parse_error']}",
        f"- **Grounded_Support_Precision = {ev['grounded_support_precision']:.4f}**",
        "",
        "### By support source bucket",
        "",
        "| bucket | total | grounded | rate |",
        "|---|---:|---:|---:|",
    ]
    for b, v in sorted(bucket.items(), key=lambda kv: -kv[1]["total"]):
        lines.append(f"| `{b}` | {v['total']} | {v['grounded']} | {v['rate']:.4f} |")
    views = agg.get("flaw_views") or {}
    diag = agg.get("flaw_hygiene_diagnostics") or {}
    raw_v = views.get("raw") or {}
    hyg_v = views.get("hygiene") or {}
    ev_aware_v = views.get("hygiene_evidence_aware") or {}

    # Identify rescue contributions (in evidence-aware but NOT in hygiene)
    flaw_results = payload.get("flaw_results") or []
    rescued = [
        r for r in flaw_results
        if _flaw_in_evidence_aware_view(r) and not _flaw_in_hygiene_view(r)
    ]

    lines += [
        "",
        "## Flaws — three nested views",
        "",
        "Flaw judgment is reported through three nested scopes so the paper "
        "narrative can match the metric to the audience:",
        "",
        "1. **`raw`** — every flaw_candidate the system ever produced (worker outputs + fallback). ",
        "   This is the upper bound on flaw output volume.",
        "2. **`hygiene`** — flaws that survive `build_decision_hygiene_view` "
        "with `status ∈ {candidate, confirmed}`. This is what the reviewer "
        "actually sees in the final report.",
        "3. **`hygiene_evidence_aware`** — `hygiene` plus rescued non-fallback "
        "flaws with at least one real-strong evidence anchor "
        "(`strength=strong`, `binding_status=bound_real_claim`, "
        "`stance != missing`). Schema-dump fallback flaws are never rescued.",
        "",
        "| view | total | grounded | not_grounded | parse_err | **rate** |",
        "|---|---:|---:|---:|---:|---:|",
        f"| `raw`                     | {raw_v.get('total',0)} | {raw_v.get('paper_grounded',0)} | {raw_v.get('not_paper_grounded',0)} | {raw_v.get('parse_error',0)} | **{raw_v.get('grounded_flaw_rate',0):.4f}** |",
        f"| `hygiene`                 | {hyg_v.get('total',0)} | {hyg_v.get('paper_grounded',0)} | {hyg_v.get('not_paper_grounded',0)} | {hyg_v.get('parse_error',0)} | **{hyg_v.get('grounded_flaw_rate',0):.4f}** |",
        f"| `hygiene_evidence_aware`  | {ev_aware_v.get('total',0)} | {ev_aware_v.get('paper_grounded',0)} | {ev_aware_v.get('not_paper_grounded',0)} | {ev_aware_v.get('parse_error',0)} | **{ev_aware_v.get('grounded_flaw_rate',0):.4f}** |",
        "",
        f"- fallback flaws (flaw-fallback*): {fl['fallback_total']} total, "
        f"{fl['fallback_paper_grounded']} grounded "
        f"(rate = {fl['fallback_grounded_rate']:.4f})",
        "",
        "### Evidence-aware rescue contributions",
        "",
        "Flaws appearing in `hygiene_evidence_aware` but **not** in `hygiene` "
        "are entries that the relaxation rescued. Both correct rescues "
        "(`paper_grounded`) and bad rescues (`not_paper_grounded`) are listed "
        "so the net contribution of the rescue rule is auditable.",
        "",
    ] + (
        [f"- (no flaws rescued — all hygiene_evidence_aware members are also in hygiene)"]
        if not rescued else
        [
            "| paper_id / flaw_id | judgment | title | reason |",
            "|---|---|---|---|",
        ] + [
            "| `{}/{}` | **{}** | {} | {} |".format(
                r.get("paper_id", ""),
                r.get("flaw_id", ""),
                r.get("judgment", ""),
                (r.get("title") or "")[:120].replace("|", "\\|"),
                (r.get("reason") or "")[:200].replace("|", "\\|"),
            )
            for r in rescued
        ]
    ) + [
        "",
        "### Hygiene diagnostics (filtered-out flaws)",
        "",
        f"- filtered_out_total: **{diag.get('filtered_out_total', 0)}** "
        "(raw-visible flaws that hygiene moved out of candidate/confirmed, plus flaws that were never visible)",
        f"- hygiene true positives (filtered & not_grounded by judge): **{diag.get('hygiene_true_positive_not_grounded', 0)}**",
        f"- hygiene false negatives (filtered but actually paper_grounded): **{diag.get('hygiene_false_negative_grounded', 0)}**",
        f"- **Hygiene_Precision** = {diag.get('hygiene_precision', 0):.4f} "
        f"(higher = hygiene was more correct in what it filtered)",
        f"- Hygiene_FN_Rate     = {diag.get('hygiene_fn_rate', 0):.4f} "
        f"(real grounded flaws lost to over-aggressive hygiene)",
        "",
        "## How to interpret",
        "",
        "- **Grounded_Support_Precision** is the LLM-judged share of strong support "
        "evidence whose claim/evidence/stance triple is grounded in the paper text. "
        "It is the V2 红线 6 upgrade from `criterion_self_claimed_grounded_rate` "
        "(agent self-claimed) to a paper-text-aware judge.",
        "- The three flaw views answer different paper questions:",
        "    - `raw` answers: *how much of the flaw stream from the workers is grounded?*",
        "    - `hygiene` answers: *how much of what the reviewer ultimately reads is grounded?*",
        "    - `hygiene_evidence_aware` answers: *what would happen if we relaxed hygiene only "
        "for flaws that already cite real-strong evidence?*",
        "- **Hygiene_Precision** quantifies how often the hygiene layer was right to "
        "filter a flaw. A high value (≥0.6) supports the conservative-by-design "
        "framing: the system prefers to lose some grounded flaws rather than "
        "expose hallucinated or schema-dump flaws to the reviewer.",
        "- The bucket breakdown shows whether grounding rates differ across "
        "abstract / method / result citations — paper-side claims are usually "
        "grounded at higher rates than result-table-derived claims, so this slice "
        "matters for the paper narrative.",
        "- `parse_error` rows are *not* counted as not_grounded; they are reported "
        "separately so prompt regressions are visible. If parse_error > 5% of "
        "total, refresh the prompt.",
        "",
        "Generated by `scripts/judge_grounded_support_v1.py`.",
    ]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def get_env(name: str, default: Optional[str] = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise SystemExit(f"environment variable {name} is required")
    return val


def main() -> None:
    p = argparse.ArgumentParser(description="B2 / C0a — LLM judge of paper-grounded support precision and flaw rate.")
    p.add_argument("--jsonl", default=DEFAULT_JSONL)
    p.add_argument("--gold-labels", default=DEFAULT_GOLD_LABELS)
    p.add_argument("--dataset-arrow", default=DEFAULT_DATASET_ARROW)
    p.add_argument("--prompt-file", default=DEFAULT_PROMPT_FILE)
    p.add_argument("--cache", default=DEFAULT_CACHE)
    p.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    p.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    p.add_argument("--limit-evidence", type=int, default=0, help="if > 0, only judge first N evidence (smoke test)")
    p.add_argument("--limit-flaws", type=int, default=0, help="if > 0, only judge first N flaws (smoke test)")
    p.add_argument("--dry-run", action="store_true", help="print prompts and exit without calling LLM")
    p.add_argument("--paper-ids", nargs="*", help="optional subset of paper_ids to restrict to")
    p.add_argument(
        "--reparse-cache", action="store_true",
        help="do NOT call LLM; re-run parse_judge_response on every cached raw "
             "response, update cache judgments in place, then re-emit the JSON "
             "+ Markdown report. Useful when the parser is hardened.",
    )
    args = p.parse_args()

    sections = load_prompt_sections(Path(args.prompt_file))
    rows = load_jsonl(Path(args.jsonl))
    if args.paper_ids:
        keep = set(args.paper_ids)
        rows = [r for r in rows if r.get("paper_id") in keep]
    paper_text_map = load_paper_text_map(Path(args.dataset_arrow))

    evidence_targets, flaw_targets = collect_judge_targets(rows)
    if args.limit_evidence > 0:
        evidence_targets = evidence_targets[: args.limit_evidence]
    if args.limit_flaws > 0:
        flaw_targets = flaw_targets[: args.limit_flaws]

    print(f"[B2] evidence to judge: {len(evidence_targets)}; flaws to judge: {len(flaw_targets)}", file=sys.stderr)

    cache_path = Path(args.cache)
    cache = load_cache(cache_path)
    cache_dirty = False

    # ------------------------------------------------------------------
    # --reparse-cache mode: rebuild results from cached raw responses.
    # No LLM calls. We rebuild target order from the same loaders so the
    # output JSON stays consistent with a fresh run, but every entry must
    # already have a cache hit (otherwise we mark it parse_error).
    # ------------------------------------------------------------------
    if args.reparse_cache:
        evidence_results: List[Dict[str, Any]] = []
        flaw_results: List[Dict[str, Any]] = []
        reparse_stats = {
            "evidence": {"reparse": 0, "fixed": 0, "still_error": 0, "missing_cache": 0},
            "flaw": {"reparse": 0, "fixed": 0, "still_error": 0, "missing_cache": 0},
            "by_path": {},
        }

        def _reparse_one(target_id_kind: str, paper_id: str, target_id: str, render_fn, target: Dict[str, Any]) -> Dict[str, Any]:
            paper_text = paper_text_map.get(paper_id, "")
            if not paper_text:
                return {"judgment": "parse_error", "quote": "", "reason": "paper text missing", "parse_path": "no_paper"}
            sys_p, usr_p = render_fn(sections, paper_text, target)
            key = cache_key(paper_id, target_id, target_id_kind, sys_p, usr_p)
            entry = cache.get(key)
            if not entry:
                reparse_stats[target_id_kind]["missing_cache"] += 1
                return {"judgment": "parse_error", "quote": "", "reason": "no cache entry", "parse_path": "missing_cache"}
            old_judgment = entry.get("judgment", "parse_error")
            raw = entry.get("raw") or ""
            parsed = parse_judge_response(raw)
            new_judgment = parsed["judgment"]
            reparse_stats[target_id_kind]["reparse"] += 1
            if old_judgment == "parse_error" and new_judgment != "parse_error":
                reparse_stats[target_id_kind]["fixed"] += 1
            if new_judgment == "parse_error":
                reparse_stats[target_id_kind]["still_error"] += 1
            path = parsed.get("parse_path", "?")
            reparse_stats["by_path"][path] = reparse_stats["by_path"].get(path, 0) + 1
            # update cache in place
            cache[key] = {
                **entry,
                "judgment": parsed["judgment"],
                "quote": parsed["quote"],
                "reason": parsed["reason"],
                "parse_path": path,
            }
            return parsed

        for ev in evidence_targets:
            parsed = _reparse_one("evidence", ev["paper_id"], ev["evidence_id"], render_evidence_prompt, ev)
            evidence_results.append({**ev, **{k: parsed[k] for k in ("judgment", "quote", "reason")}, "parse_path": parsed.get("parse_path"), "from_cache": True})
        for fl in flaw_targets:
            parsed = _reparse_one("flaw", fl["paper_id"], fl["flaw_id"], render_flaw_prompt, fl)
            flaw_results.append({**fl, **{k: parsed[k] for k in ("judgment", "quote", "reason")}, "parse_path": parsed.get("parse_path"), "from_cache": True})
        save_cache(cache_path, cache)

        # recover judge model from cache (first entry that has one)
        recovered_model = next(
            (entry.get("model") for entry in cache.values() if entry.get("model")),
            "(unknown — cache lacks model)"
        )

        aggregate_payload = aggregate(evidence_results, flaw_results)
        payload = {
            "input_jsonl": args.jsonl,
            "paper_text_source": args.dataset_arrow,
            "judge_model": f"{recovered_model} (reparsed from cache)",
            "judge_base_url": "(reparse only)",
            "schema_version": "v1",
            "evidence_results": evidence_results,
            "flaw_results": flaw_results,
            "aggregate": aggregate_payload,
            "reparse_stats": reparse_stats,
        }
        out_json = Path(args.output_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md = Path(args.output_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(out_md, payload)
        print(json.dumps({
            "mode": "reparse-cache",
            "n_papers": aggregate_payload["n_papers"],
            "evidence": aggregate_payload["evidence"],
            "flaw": aggregate_payload["flaw"],
            "reparse_stats": reparse_stats,
            "output_json": str(out_json),
            "output_md": str(out_md),
        }, ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        # show first 1 evidence and 1 flaw prompt, then exit
        if evidence_targets:
            ev = evidence_targets[0]
            sys_p, usr_p = render_evidence_prompt(sections, paper_text_map.get(ev["paper_id"], ""), ev)
            print("=== EVIDENCE PROMPT (first) ===")
            print("--- SYSTEM ---")
            print(sys_p)
            print("--- USER (first 1500 chars) ---")
            print(usr_p[:1500] + ("...<truncated>..." if len(usr_p) > 1500 else ""))
        if flaw_targets:
            fl = flaw_targets[0]
            sys_p, usr_p = render_flaw_prompt(sections, paper_text_map.get(fl["paper_id"], ""), fl)
            print("\n=== FLAW PROMPT (first) ===")
            print("--- SYSTEM ---")
            print(sys_p)
            print("--- USER (first 1500 chars) ---")
            print(usr_p[:1500] + ("...<truncated>..." if len(usr_p) > 1500 else ""))
        return

    # Build LLM client
    judge = LLMJudge(
        base_url=os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        api_key=get_env("ARK_API_KEY"),
        model=os.environ.get("ARK_MODEL", "doubao-seed-1-6"),
        timeout=float(os.environ.get("ARK_TIMEOUT", "120")),
        max_tokens=int(os.environ.get("ARK_MAX_TOKENS", "256")),
        temperature=float(os.environ.get("ARK_TEMPERATURE", "0.0")),
    )

    # ------------------------------------------------------------------
    # Judge evidence
    # ------------------------------------------------------------------
    evidence_results: List[Dict[str, Any]] = []
    for i, ev in enumerate(evidence_targets):
        paper_text = paper_text_map.get(ev["paper_id"], "")
        if not paper_text:
            evidence_results.append({**ev, "judgment": "parse_error", "quote": "", "reason": "paper text missing", "from_cache": False})
            continue
        sys_p, usr_p = render_evidence_prompt(sections, paper_text, ev)
        key = cache_key(ev["paper_id"], ev["evidence_id"], "evidence", sys_p, usr_p)
        if key in cache:
            r = cache[key]
            evidence_results.append({**ev, **{k: r[k] for k in ("judgment", "quote", "reason")}, "from_cache": True})
            continue
        resp = judge.call(sys_p, usr_p)
        parsed = parse_judge_response(resp.get("content") or "")
        cache[key] = {
            "kind": "evidence",
            "paper_id": ev["paper_id"],
            "target_id": ev["evidence_id"],
            "model": judge.model,
            "judgment": parsed["judgment"],
            "quote": parsed["quote"],
            "reason": parsed["reason"],
            "usage": resp.get("usage", {}),
            "raw": parsed.get("raw", "")[:1200],
            "error": resp.get("error"),
        }
        cache_dirty = True
        evidence_results.append({**ev, **{k: parsed[k] for k in ("judgment", "quote", "reason")}, "from_cache": False})
        # periodic checkpoint
        if (i + 1) % 10 == 0:
            save_cache(cache_path, cache)
            cache_dirty = False
            print(f"[B2] evidence {i + 1}/{len(evidence_targets)} judged (cache size {len(cache)})", file=sys.stderr)

    # ------------------------------------------------------------------
    # Judge flaws
    # ------------------------------------------------------------------
    flaw_results: List[Dict[str, Any]] = []
    for i, fl in enumerate(flaw_targets):
        paper_text = paper_text_map.get(fl["paper_id"], "")
        if not paper_text:
            flaw_results.append({**fl, "judgment": "parse_error", "quote": "", "reason": "paper text missing", "from_cache": False})
            continue
        sys_p, usr_p = render_flaw_prompt(sections, paper_text, fl)
        key = cache_key(fl["paper_id"], fl["flaw_id"], "flaw", sys_p, usr_p)
        if key in cache:
            r = cache[key]
            flaw_results.append({**fl, **{k: r[k] for k in ("judgment", "quote", "reason")}, "from_cache": True})
            continue
        resp = judge.call(sys_p, usr_p)
        parsed = parse_judge_response(resp.get("content") or "")
        cache[key] = {
            "kind": "flaw",
            "paper_id": fl["paper_id"],
            "target_id": fl["flaw_id"],
            "model": judge.model,
            "judgment": parsed["judgment"],
            "quote": parsed["quote"],
            "reason": parsed["reason"],
            "usage": resp.get("usage", {}),
            "raw": parsed.get("raw", "")[:1200],
            "error": resp.get("error"),
        }
        cache_dirty = True
        flaw_results.append({**fl, **{k: parsed[k] for k in ("judgment", "quote", "reason")}, "from_cache": False})
        if (i + 1) % 10 == 0:
            save_cache(cache_path, cache)
            cache_dirty = False
            print(f"[B2] flaw {i + 1}/{len(flaw_targets)} judged (cache size {len(cache)})", file=sys.stderr)

    if cache_dirty:
        save_cache(cache_path, cache)

    # Aggregate + report
    aggregate_payload = aggregate(evidence_results, flaw_results)
    payload = {
        "input_jsonl": args.jsonl,
        "paper_text_source": args.dataset_arrow,
        "judge_model": judge.model,
        "judge_base_url": os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        "schema_version": "v1",
        "evidence_results": evidence_results,
        "flaw_results": flaw_results,
        "aggregate": aggregate_payload,
    }
    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(out_md, payload)

    # CLI summary
    summary = {
        "n_papers": aggregate_payload["n_papers"],
        "evidence": aggregate_payload["evidence"],
        "flaw": aggregate_payload["flaw"],
        "output_json": str(out_json),
        "output_md": str(out_md),
        "cache": str(cache_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
