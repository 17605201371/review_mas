#!/usr/bin/env python3
"""Generate blinded M/P review-issue discoveries and neutral AuditPackets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from agent_system.environments.env_package.review.paper_index import PaperIndex, build_paper_index
from agent_system.inference.review_runner import ApiReviewGenerator
from scripts.p33_freeform_critique_probe import _disable_proxy_env_for_api, _extract_json_object, _load_dotenv
from scripts.p34_dual_model_judge_guard import MODEL_CODES, build_audit_packet


ISSUE_TYPES = {
    "result_claim_mismatch",
    "unfair_or_weak_baseline",
    "evaluation_protocol_risk",
    "scope_overclaim",
    "method_support_gap",
    "reproducibility_gap",
    "statistical_or_reporting_gap",
    "missing_ablation",
    "missing_baseline",
    "efficiency_cost_gap",
    "insufficient_evaluation",
    "missing_robustness_or_generalization",
    "negative_result",
    "direct_contradiction",
    "other",
}

_TOKEN_STOPWORDS = {
    "about", "after", "again", "also", "because", "before", "could", "does", "from",
    "have", "into", "lacks", "missing", "paper", "reported", "reports", "should", "shows",
    "that", "their", "there", "these", "this", "those", "using", "with", "without", "would",
}


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} must contain an object")
        rows.append(value)
    return rows


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _states_from_runner(path: Path, limit: int = 0) -> Dict[str, Dict[str, Any]]:
    states = {}
    for row in _load_jsonl(path):
        state = row.get("review_state") if isinstance(row.get("review_state"), dict) else {}
        paper_id = str(row.get("paper_id") or state.get("paper_id") or "")
        if paper_id and str(state.get("paper_text") or row.get("paper_text") or ""):
            state = dict(state)
            state["paper_text"] = str(state.get("paper_text") or row.get("paper_text") or "")
            states[paper_id] = state
            if limit and len(states) >= limit:
                break
    return states


def build_discovery_context(index: PaperIndex, state: Mapping[str, Any], max_chars: int) -> Dict[str, Any]:
    claims = [
        {
            "claim_id": str(item.get("claim_id") or ""),
            "claim": str(item.get("claim") or "")[:500],
            "claim_type": str(item.get("claim_type") or "other"),
        }
        for item in state.get("claims", [])
        if isinstance(item, dict) and str(item.get("claim") or "").strip()
    ][:8]
    preferred = ("abstract", "introduction", "method", "results", "analysis", "limitations", "discussion", "conclusion")
    sections = []
    remaining = max_chars
    for section_type in preferred:
        matching = [item for item in index.sections if item.section_type == section_type]
        for section in matching[:2]:
            if remaining < 300:
                break
            text = section.text[: min(2200, remaining)]
            sections.append({
                "section_id": section.section_id,
                "section_type": section.section_type,
                "heading": section.heading,
                "source_span_start": section.source_span_start,
                "source_span_end": section.source_span_start + len(text),
                "text": text,
            })
            remaining -= len(text)
        if remaining < 300:
            break
    artifacts = []
    for artifact in index.artifacts:
        if artifact.artifact_type not in {"table", "figure", "caption"}:
            continue
        artifacts.append({
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "locator": artifact.locator,
            "source_span_start": artifact.source_span_start,
            "source_span_end": artifact.source_span_end,
            "text": artifact.text[:900],
        })
        if len(artifacts) >= 10:
            break
    return {
        "claims": claims,
        "paper_sections": sections,
        "paper_artifacts": artifacts,
        "unsearched_scope": f"PaperIndex strategic context capped at {max_chars} characters.",
    }


def build_discovery_prompt(paper_id: str, context: Mapping[str, Any], max_hypotheses: int) -> str:
    schema = {
        "hypotheses": [{
            "hypothesis_id": "h1",
            "issue_type": "|".join(sorted(ISSUE_TYPES)),
            "claim_id": "claim id or empty",
            "claim_anchor": "specific paper claim",
            "hypothesis": "specific falsifiable reviewer concern",
            "paper_anchor": "exact or near-exact paper anchor",
            "expected_evidence": "paper-internal evidence required to resolve the concern",
            "counterevidence_query": "precise search query that could falsify the concern",
            "named_entities_or_metrics": ["paper-specific entity, dataset, metric, table, or method"],
            "confidence": 0.0,
        }],
        "no_issue_reason": "required only when no concrete issue can be proposed",
    }
    return (
        "Act as a peer-review Critique Agent. Independently discover concrete, paper-grounded issue hypotheses. "
        "Do not verify, admit, score, or decide the paper. Do not use generic checklist wording. "
        "Each issue must identify a specific paper claim or anchor, a falsifiable concern, the exact evidence needed to resolve it, "
        "and a counterevidence query. The decisive premise must be checkable inside this paper; otherwise omit the issue. "
        f"Return at most {max_hypotheses} hypotheses in one compact JSON object and stop.\n"
        f"Schema: {json.dumps(schema, ensure_ascii=False)}\n"
        f"Paper context: {json.dumps({'paper_id': paper_id, **dict(context)}, ensure_ascii=False)}"
    )


def _clean_text(value: Any, max_chars: int) -> str:
    return " ".join(str(value or "").split())[:max_chars]


def parse_discoveries(raw: str, paper_id: str, discovery_code: str, max_hypotheses: int) -> Tuple[List[Dict[str, Any]], str]:
    parsed, error = _extract_json_object(raw)
    values = parsed.get("hypotheses") if isinstance(parsed, dict) else None
    if error or not isinstance(values, list):
        return [], error or "missing_hypotheses"
    result = []
    for index, item in enumerate(values[:max_hypotheses], start=1):
        if not isinstance(item, dict):
            continue
        hypothesis = _clean_text(item.get("hypothesis"), 700)
        paper_anchor = _clean_text(item.get("paper_anchor"), 500)
        expected = _clean_text(item.get("expected_evidence"), 500)
        counter_query = _clean_text(item.get("counterevidence_query"), 300)
        if min(len(hypothesis), len(paper_anchor), len(expected), len(counter_query)) < 8:
            continue
        issue_type = _clean_text(item.get("issue_type"), 80).lower()
        if issue_type not in ISSUE_TYPES:
            issue_type = "other"
        result.append({
            "source_candidate_id": f"{discovery_code}-{paper_id}-{_clean_text(item.get('hypothesis_id'), 80) or index}",
            "paper_id": paper_id,
            "issue_type": issue_type,
            "claim_id": _clean_text(item.get("claim_id"), 120),
            "claim_anchor": _clean_text(item.get("claim_anchor"), 500),
            "hypothesis": hypothesis,
            "paper_anchor": paper_anchor,
            "expected_evidence": expected,
            "counterevidence_query": counter_query,
            "named_entities_or_metrics": [
                _clean_text(value, 120)
                for value in item.get("named_entities_or_metrics", [])[:10]
                if _clean_text(value, 120)
            ] if isinstance(item.get("named_entities_or_metrics"), list) else [],
            "confidence": max(0.0, min(1.0, float(item.get("confidence") or 0.0))),
            "_discovery_code": discovery_code,
            "_discovery_model": MODEL_CODES[discovery_code],
        })
    return result, "" if result or not values else "no_valid_hypotheses"


def _tokens(item: Mapping[str, Any]) -> set[str]:
    text = " ".join([
        str(item.get("claim_anchor") or ""),
        str(item.get("hypothesis") or ""),
        str(item.get("expected_evidence") or ""),
        " ".join(str(value) for value in item.get("named_entities_or_metrics", []) or []),
    ]).lower()
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9_-]{2,}", text)
        if token not in _TOKEN_STOPWORDS
    }


def candidate_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    if str(left.get("paper_id") or "") != str(right.get("paper_id") or ""):
        return 0.0
    if str(left.get("issue_type") or "") != str(right.get("issue_type") or ""):
        return 0.0
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def cluster_candidates(candidates: Sequence[Dict[str, Any]], threshold: float = 0.58) -> List[List[Dict[str, Any]]]:
    clusters: List[List[Dict[str, Any]]] = []
    ordered = sorted(
        candidates,
        key=lambda item: (
            str(item.get("paper_id") or ""),
            str(item.get("issue_type") or ""),
            str(item.get("source_candidate_id") or ""),
        ),
    )
    for candidate in ordered:
        best_index = -1
        best_score = 0.0
        for index, cluster in enumerate(clusters):
            score = max(candidate_similarity(candidate, existing) for existing in cluster)
            if score >= threshold and score > best_score:
                best_index, best_score = index, score
        if best_index >= 0:
            clusters[best_index].append(candidate)
        else:
            clusters.append([candidate])
    return clusters


def _canonical_candidate(cluster: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return max(
        cluster,
        key=lambda item: (
            len(item.get("named_entities_or_metrics", []) or []),
            len(_tokens(item)),
            len(str(item.get("hypothesis") or "")),
        ),
    )


def build_neutral_packets(
    states: Mapping[str, Mapping[str, Any]],
    candidates: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    packets, provenance, annotations = [], [], []
    for cluster in cluster_candidates(candidates):
        canonical = _canonical_candidate(cluster)
        paper_id = str(canonical["paper_id"])
        index = build_paper_index(str(states[paper_id].get("paper_text") or ""))
        packet = build_audit_packet(paper_id, index, canonical)
        fingerprint = hashlib.sha256(_canonical_bytes({
            "paper_id": paper_id,
            "issue_type": canonical.get("issue_type"),
            "claim_anchor": canonical.get("claim_anchor"),
            "hypothesis": canonical.get("hypothesis"),
            "expected_evidence": canonical.get("expected_evidence"),
        })).hexdigest()[:14]
        packet_id = f"discovery-{paper_id}-{fingerprint}"
        packet["packet_id"] = packet_id
        packet["task_type"] = "review_issue"
        packet["verification_contract"] = {
            "alleged_defect": str(canonical.get("hypothesis") or ""),
            "required_resolution_evidence": str(canonical.get("expected_evidence") or ""),
            "falsification_query": str(canonical.get("counterevidence_query") or ""),
            "resolution_standard": (
                "Counterevidence resolves the issue only if it directly satisfies the required evidence or directly falsifies the alleged defect."
            ),
        }
        discovery_codes = sorted({str(item.get("_discovery_code") or "") for item in cluster if item.get("_discovery_code")})
        packets.append(packet)
        provenance.append({
            "packet_id": packet_id,
            "paper_id": paper_id,
            "discovery_codes": discovery_codes,
            "discovery_models": [MODEL_CODES[code] for code in discovery_codes],
            "source_candidate_ids": sorted(str(item.get("source_candidate_id") or "") for item in cluster),
            "cluster_size": len(cluster),
        })
        annotations.append({
            "packet_id": packet_id,
            "paper_id": paper_id,
            "task_type": "review_issue",
            "human_label": "",
            "allowed_labels": ["A", "B", "C", "D"],
            "human_reason": "",
            "label_semantics": {
                "A": "specific verified issue with direct paper support",
                "B": "specific valid issue established by paper-internal absence or relation audit",
                "C": "plausible but uncertain or insufficiently auditable",
                "D": "incorrect, generic, resolved by counterevidence, or not paper-internally verifiable",
            },
        })
    return packets, provenance, annotations


def _validate_packet_spans(packet: Mapping[str, Any], paper_text: str) -> bool:
    for key in ("retrieved_evidence", "counterevidence_candidates"):
        for item in packet.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            start, end = item.get("source_span_start"), item.get("source_span_end")
            if not isinstance(start, int) or not isinstance(end, int) or paper_text[start:end] != str(item.get("quote") or ""):
                return False
    return True


def run_discovery(args: argparse.Namespace) -> Dict[str, Any]:
    runner_path = Path(args.runner_jsonl)
    states = _states_from_runner(runner_path, args.limit)
    indexes = {paper_id: build_paper_index(str(state.get("paper_text") or "")) for paper_id, state in states.items()}
    contexts = {paper_id: build_discovery_context(indexes[paper_id], state, args.max_context_chars) for paper_id, state in states.items()}
    generators = {
        code: ApiReviewGenerator(
            model=MODEL_CODES[code], provider="mimo", temperature=0.0, top_p=1.0,
            max_tokens=args.max_tokens, max_workers=args.max_workers, timeout=args.timeout,
            max_retries=args.max_retries,
            system_prompt="Return exactly one compact JSON object. No chain-of-thought or markdown.",
        )
        for code in args.model_codes
    } if args.run_api else {}
    cases, all_candidates, api_errors = [], [], []
    for code in args.model_codes:
        paper_ids = list(states)
        requests = [
            ("P34 Symmetric Critique Discovery", build_discovery_prompt(paper_id, contexts[paper_id], args.max_hypotheses))
            for paper_id in paper_ids
        ]
        try:
            responses = generators[code].generate_many(requests) if args.run_api else [
                '{"hypotheses":[],"no_issue_reason":"dry_run"}' for _ in requests
            ]
        except Exception as exc:
            api_errors.append({"discovery_code": code, "error_type": type(exc).__name__, "message": str(exc)[:500]})
            responses = [""] * len(requests)
        for paper_id, raw in zip(paper_ids, responses):
            candidates, error = parse_discoveries(raw, paper_id, code, args.max_hypotheses)
            cases.append({
                "paper_id": paper_id,
                "discovery_code": code,
                "discovery_model": MODEL_CODES[code],
                "valid": not error,
                "error": error,
                "candidate_count": len(candidates),
                "candidates": candidates,
                "raw_response": raw,
            })
            all_candidates.extend(candidates)
    packets, provenance, annotations = build_neutral_packets(states, all_candidates)
    invalid_spans = [
        packet["packet_id"]
        for packet in packets
        if not _validate_packet_spans(packet, str(states[packet["paper_id"]].get("paper_text") or ""))
    ]
    code_candidate_counts = Counter(str(item.get("_discovery_code") or "") for item in all_candidates)
    code_paper_coverage = {
        code: len({str(item.get("paper_id") or "") for item in all_candidates if item.get("_discovery_code") == code})
        for code in args.model_codes
    }
    blocking = []
    if api_errors:
        blocking.append(f"api_errors:{len(api_errors)}")
    if args.run_api:
        for code in args.model_codes:
            if code_candidate_counts.get(code, 0) == 0:
                blocking.append(f"no_candidates_for_discovery_code:{code}")
    if invalid_spans:
        blocking.append(f"invalid_packet_spans:{len(invalid_spans)}")
    packet_bytes = b"".join(_canonical_bytes(item) for item in packets)
    provenance_bytes = _canonical_bytes(provenance)
    manifest = {
        "schema_version": "p34_symmetric_discovery_v1",
        "status": "DRY_RUN" if not args.run_api else ("PASS_GENERATION" if not blocking else "BLOCKED"),
        "boundary": "Symmetric blinded discovery generation; no Judge verdict and no ReviewState mutation",
        "runner_jsonl": str(runner_path),
        "runner_jsonl_sha256": hashlib.sha256(runner_path.read_bytes()).hexdigest(),
        "paper_count": len(states),
        "model_codes": args.model_codes,
        "models": {code: MODEL_CODES[code] for code in args.model_codes},
        "prompt_identity_symmetric": True,
        "generator_identity_absent_from_packets": all("discovery_" not in json.dumps(packet) for packet in packets),
        "max_context_chars": args.max_context_chars,
        "max_hypotheses": args.max_hypotheses,
        "case_count": len(cases),
        "valid_case_count": sum(bool(item["valid"]) for item in cases),
        "raw_candidate_count": len(all_candidates),
        "candidate_counts_by_code": dict(code_candidate_counts),
        "paper_coverage_by_code": code_paper_coverage,
        "neutral_cluster_count": len(packets),
        "shared_cross_model_cluster_count": sum(len(item.get("discovery_codes", [])) > 1 for item in provenance),
        "packet_type_counts": dict(Counter(item.get("task_type") for item in packets)),
        "invalid_span_packet_count": len(invalid_spans),
        "invalid_span_packet_ids": invalid_spans,
        "packets_sha256": hashlib.sha256(packet_bytes).hexdigest(),
        "provenance_sha256": hashlib.sha256(provenance_bytes).hexdigest(),
        "human_labels_complete": False,
        "api_errors": api_errors,
        "blocking_issues": blocking + (["human_labels_incomplete"] if packets else []),
    }
    return {"manifest": manifest, "cases": cases, "packets": packets, "provenance": provenance, "annotation_template": annotations}


def render_manifest(manifest: Mapping[str, Any]) -> str:
    lines = [
        "# P34 Symmetric M/P Discovery Manifest", "",
        f"- status: **{manifest['status']}**",
        f"- paper_count: `{manifest['paper_count']}`",
        f"- models: `{manifest['models']}`",
        f"- raw_candidate_count: `{manifest['raw_candidate_count']}`",
        f"- candidate_counts_by_code: `{manifest['candidate_counts_by_code']}`",
        f"- paper_coverage_by_code: `{manifest['paper_coverage_by_code']}`",
        f"- neutral_cluster_count: `{manifest['neutral_cluster_count']}`",
        f"- shared_cross_model_cluster_count: `{manifest['shared_cross_model_cluster_count']}`",
        f"- generator_identity_absent_from_packets: `{manifest['generator_identity_absent_from_packets']}`",
        f"- invalid_span_packet_count: `{manifest['invalid_span_packet_count']}`", "",
        "## Blocking Issues", "",
    ]
    lines.extend(f"- `{item}`" for item in manifest["blocking_issues"]) if manifest["blocking_issues"] else lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-jsonl", required=True)
    parser.add_argument("--model-codes", nargs="+", choices=["M", "P"], default=["M", "P"])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-context-chars", type=int, default=12000)
    parser.add_argument("--max-hypotheses", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--run-api", action="store_true")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()
    _load_dotenv(Path(args.env_file))
    _disable_proxy_env_for_api()
    MODEL_CODES["M"] = str(os.getenv("MIMO_MODEL") or MODEL_CODES["M"])
    MODEL_CODES["P"] = str(os.getenv("MIMO_PRO_MODEL") or MODEL_CODES["P"])
    result = run_discovery(args)
    prefix = Path(args.output_prefix)
    Path(str(prefix) + "_PACKETS.jsonl").write_bytes(b"".join(_canonical_bytes(item) for item in result["packets"]))
    Path(str(prefix) + "_MANIFEST.json").write_text(json.dumps(result["manifest"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(str(prefix) + "_MANIFEST.md").write_text(render_manifest(result["manifest"]), encoding="utf-8")
    Path(str(prefix) + "_CASES.json").write_text(json.dumps({"cases": result["cases"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(str(prefix) + "_DISCOVERY_PROVENANCE.json").write_text(json.dumps({"items": result["provenance"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(str(prefix) + "_HUMAN_AUDIT_TEMPLATE.json").write_text(json.dumps({"labels": result["annotation_template"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["manifest"], ensure_ascii=False))
    return 0 if result["manifest"]["status"] in {"DRY_RUN", "PASS_GENERATION"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
