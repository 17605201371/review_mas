#!/usr/bin/env python3
"""Translate one paper's P34 human-audit display text without mutating frozen packets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from agent_system.inference.review_runner import ApiReviewGenerator
from scripts.p33_freeform_critique_probe import _extract_json_object, _load_dotenv


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def collect_display_strings(
    paper_id: str,
    packets: Mapping[str, Mapping[str, Any]],
    templates: Mapping[str, Mapping[str, Any]],
    anchor_template: Mapping[str, Any],
) -> List[str]:
    values: List[str] = []
    seen = set()

    def add(value: Any) -> None:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            values.append(text)

    def add_sources(packet: Mapping[str, Any], key: str) -> None:
        for source in list(packet.get(key) or [])[:8]:
            if isinstance(source, dict):
                add(source.get("quote") or source.get("text"))

    for task in ("evidence_relation", "claim_faithfulness", "review_issue"):
        for label in list(templates[task].get("labels") or []):
            if str(label.get("paper_id") or "") != paper_id:
                continue
            packet = packets.get(str(label.get("packet_id") or ""), {})
            claim = packet.get("claim") if isinstance(packet.get("claim"), dict) else {}
            add(claim.get("claim_text") or claim.get("claim"))
            if task == "evidence_relation":
                evidence = packet.get("candidate_evidence") if isinstance(packet.get("candidate_evidence"), dict) else {}
                add(evidence.get("quote"))
                add_sources(packet, "counterevidence_candidates")
            elif task == "claim_faithfulness":
                add_sources(packet, "claim_source_spans")
            else:
                issue = packet.get("issue_hypothesis") if isinstance(packet.get("issue_hypothesis"), dict) else {}
                contract = packet.get("verification_contract") if isinstance(packet.get("verification_contract"), dict) else {}
                add(issue.get("hypothesis") or contract.get("alleged_defect"))
                add(contract.get("required_resolution_evidence") or issue.get("expected_evidence"))
                add(contract.get("falsification_query") or issue.get("counterevidence_query"))
                add_sources(packet, "retrieved_evidence" if packet.get("retrieved_evidence") else "counterevidence_candidates")

    anchor_case = next(
        (item for item in list(anchor_template.get("cases") or []) if str(item.get("paper_id") or "") == paper_id),
        None,
    )
    if anchor_case is None:
        raise ValueError(f"paper_id not found in PaperIndex anchor template: {paper_id}")
    for key in (
        "machine_boundary_suggestions",
        "machine_anchor_suggestions",
        "machine_false_boundary_suggestions",
    ):
        for suggestion in list(anchor_case.get(key) or []):
            if not isinstance(suggestion, dict):
                continue
            for field in ("heading", "query", "text_preview", "text", "reason"):
                add(suggestion.get(field))
    return values


def _batches(values: Sequence[str], max_chars: int, max_items: int) -> List[List[tuple[str, str]]]:
    result: List[List[tuple[str, str]]] = []
    current: List[tuple[str, str]] = []
    current_chars = 0
    for index, value in enumerate(values, start=1):
        item = (f"t{index:04d}", value)
        if current and (len(current) >= max_items or current_chars + len(value) > max_chars):
            result.append(current)
            current, current_chars = [], 0
        current.append(item)
        current_chars += len(value)
    if current:
        result.append(current)
    return result


def _prompt(batch: Sequence[tuple[str, str]]) -> str:
    payload = [{"id": item_id, "text": value} for item_id, value in batch]
    return (
        "Translate every text field into accurate Simplified Chinese for academic peer review. "
        "Do not summarize, omit, add conclusions, or soften criticism. Preserve LaTeX, equations, "
        "numbers, citations, model names, dataset names, metric names, table/figure identifiers, and IDs. "
        "Return exactly one JSON object shaped as "
        '{"translations":[{"id":"t0001","text":"完整中文翻译"}]}. '
        "Return exactly one item for every input id and no extra ids.\n"
        f"Input: {json.dumps(payload, ensure_ascii=False)}"
    )


def translate(
    values: Sequence[str],
    model: str,
    max_chars: int,
    max_items: int,
    max_tokens: int,
    max_workers: int,
    timeout: int,
) -> List[Dict[str, Any]]:
    pending = _batches(values, max_chars=max_chars, max_items=max_items)
    generator = ApiReviewGenerator(
        model=model,
        provider="mimo",
        temperature=0.0,
        top_p=1.0,
        max_tokens=max_tokens,
        max_workers=max_workers,
        timeout=timeout,
        max_retries=1,
        system_prompt="Return exactly one valid compact JSON object. No markdown or explanation.",
    )
    translated_by_id: Dict[str, str] = {}
    failure_notes: List[str] = []
    for round_index in range(4):
        if not pending:
            break
        responses = generator.generate_many([
            ("P34 Audit Chinese Translator", _prompt(batch)) for batch in pending
        ])
        retry: List[List[tuple[str, str]]] = []
        for batch, raw in zip(pending, responses):
            parsed, error = _extract_json_object(raw)
            rows = parsed.get("translations") if isinstance(parsed, dict) else None
            expected = {item_id for item_id, _ in batch}
            received = {
                str(item.get("id") or "")
                for item in (rows or [])
                if isinstance(item, dict) and str(item.get("text") or "").strip()
            } if isinstance(rows, list) else set()
            if not error and isinstance(rows, list) and received == expected:
                for item in rows:
                    translated_by_id[str(item["id"])] = str(item["text"]).strip()
                continue
            failure_notes.append(
                f"round={round_index + 1}, ids={sorted(expected)}, error={error or 'id_mismatch'}, raw_chars={len(raw)}"
            )
            if len(batch) > 1:
                midpoint = max(1, len(batch) // 2)
                retry.extend([list(batch[:midpoint]), list(batch[midpoint:])])
            else:
                retry.append(list(batch))
        pending = retry
    if pending:
        unresolved = sorted(item_id for batch in pending for item_id, _ in batch)
        raise ValueError(f"translation retries exhausted for {unresolved}; diagnostics={failure_notes[-10:]}")
    entries = []
    for index, source in enumerate(values, start=1):
        item_id = f"t{index:04d}"
        translated = translated_by_id.get(item_id, "")
        if not translated:
            raise ValueError(f"empty translation: {item_id}")
        entries.append({
            "id": item_id,
            "source_sha256": _sha256_text(source),
            "source_chars": len(source),
            "translated_text": translated,
        })
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--packets", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_PACKETS.jsonl")
    parser.add_argument("--issue-packets", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_PACKETS.jsonl")
    parser.add_argument("--positive-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_POSITIVE_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--claim-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_CLAIM_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--issue-template", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--anchors", default="P34_1_PAPER_INDEX_HUMAN_ANCHORS_HARDNEG20_TEMPLATE_20260711.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--model", default="mimo-v2.5-pro")
    parser.add_argument("--max-batch-chars", type=int, default=4500)
    parser.add_argument("--max-batch-items", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="P34_AUDIT_TRANSLATIONS_ZH_20260711.json")
    args = parser.parse_args()
    _load_dotenv(Path(args.env_file))

    packets = {
        str(item.get("packet_id") or ""): item
        for path in (Path(args.packets), Path(args.issue_packets))
        for item in _load_jsonl(path)
        if str(item.get("packet_id") or "")
    }
    templates = {
        "evidence_relation": _load_json(Path(args.positive_template)),
        "claim_faithfulness": _load_json(Path(args.claim_template)),
        "review_issue": _load_json(Path(args.issue_template)),
    }
    values = collect_display_strings(args.paper_id, packets, templates, _load_json(Path(args.anchors)))
    scope_hash = hashlib.sha256("\n".join(_sha256_text(value) for value in values).encode("ascii")).hexdigest()
    entries = [] if args.dry_run else translate(
        values,
        model=args.model,
        max_chars=args.max_batch_chars,
        max_items=args.max_batch_items,
        max_tokens=args.max_tokens,
        max_workers=args.max_workers,
        timeout=args.timeout,
    )
    report = {
        "schema_version": "p34_audit_display_translation_v1",
        "boundary": "Display-only Simplified Chinese translation; frozen packets, labels, spans, gates, and Judge prompts remain English",
        "language": "zh-CN",
        "paper_id": args.paper_id,
        "model": args.model if not args.dry_run else "NOT_RUN",
        "source_string_count": len(values),
        "source_char_count": sum(len(value) for value in values),
        "source_scope_sha256": scope_hash,
        "translation_count": len(entries),
        "coverage": (len(entries) / len(values)) if values else 1.0,
        "entries": entries,
        "status": "DRY_RUN" if args.dry_run else "PASS",
    }
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "entries"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
