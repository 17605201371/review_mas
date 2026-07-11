#!/usr/bin/env python3
"""Durable request-level response ledger for resumable P34 API experiments."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def request_key(title: str, prompt: str, context: Mapping[str, Any], generation_config: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes({
        "title": title,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "context": dict(context),
        "generation_config": dict(generation_config),
    })).hexdigest()


class RequestLedger:
    def __init__(self, path: Path):
        self.path = path
        self.records: Dict[str, Dict[str, Any]] = {}
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("records", {}), dict):
                raise ValueError(f"invalid request ledger: {path}")
            self.records = {str(key): dict(item) for key, item in value.get("records", {}).items() if isinstance(item, dict)}

    def get(self, key: str) -> str | None:
        item = self.records.get(key) or {}
        if item.get("status") != "success":
            return None
        response = item.get("raw_response")
        return str(response) if isinstance(response, str) else None

    def put_success(self, key: str, response: str, metadata: Mapping[str, Any]) -> None:
        self.records[key] = {
            "status": "success",
            "raw_response": str(response),
            "response_sha256": hashlib.sha256(str(response).encode("utf-8")).hexdigest(),
            "metadata": dict(metadata),
        }

    def flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "p34_request_ledger_v1",
            "record_count": len(self.records),
            "records": self.records,
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_bytes(_canonical_bytes(payload))
        temporary.replace(self.path)


def generate_resumable(
    generator: Any,
    requests: Sequence[Tuple[str, str]],
    contexts: Sequence[Mapping[str, Any]],
    generation_config: Mapping[str, Any],
    ledger: RequestLedger,
    batch_size: int,
) -> Tuple[List[str | None], List[Dict[str, Any]], Dict[str, int]]:
    if len(requests) != len(contexts):
        raise ValueError("requests and contexts must have equal length")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    keys = [
        request_key(title, prompt, context, generation_config)
        for (title, prompt), context in zip(requests, contexts)
    ]
    results: List[str | None] = [None] * len(requests)
    missing = []
    cache_hits = 0
    for index, key in enumerate(keys):
        cached = ledger.get(key)
        if cached is None:
            missing.append(index)
        else:
            results[index] = cached
            cache_hits += 1
    errors: List[Dict[str, Any]] = []
    api_calls = 0
    completed_new = 0
    for offset in range(0, len(missing), batch_size):
        indexes = missing[offset : offset + batch_size]
        batch = [requests[index] for index in indexes]
        api_calls += len(batch)
        try:
            responses = generator.generate_many(batch)
            if len(responses) != len(batch):
                raise RuntimeError(f"response_count_mismatch:{len(responses)}/{len(batch)}")
        except Exception as exc:
            errors.extend({
                "index": index,
                "request_key": keys[index],
                "error_type": type(exc).__name__,
                "message": str(exc)[:500],
            } for index in indexes)
            continue
        for index, response in zip(indexes, responses):
            results[index] = str(response)
            ledger.put_success(keys[index], str(response), contexts[index])
            completed_new += 1
        ledger.flush()
    return results, errors, {
        "request_count": len(requests),
        "cache_hit_count": cache_hits,
        "api_request_count": api_calls,
        "new_success_count": completed_new,
        "error_count": len(errors),
    }
