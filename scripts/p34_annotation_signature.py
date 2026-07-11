#!/usr/bin/env python3
"""Sign and verify P34 human submissions with an external Ed25519 key."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


SIGNATURE_VERSION = "p34_annotation_ed25519_v2"

LABEL_FIELDS = (
    "packet_id", "paper_id", "task_type", "human_label", "human_reason",
    "annotator_id", "human_reviewer_id", "primary_label_for_audit",
    "secondary_label_for_audit",
)
ANCHOR_FIELDS = (
    "paper_id", "expected_boundaries", "key_anchors", "false_boundaries",
    "human_review_complete", "human_review_notes", "annotator_id",
    "human_reviewer_id",
)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _openssl() -> str:
    executable = shutil.which("openssl")
    if not executable:
        raise RuntimeError("OpenSSL is required for P34 Ed25519 annotation signatures")
    return executable


def _run(args: Sequence[str], *, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        [_openssl(), *args], input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip() or "OpenSSL command failed")
    return completed.stdout


def load_or_create_keypair(private_path: Path, public_path: Path) -> Dict[str, Any]:
    private_path = private_path.expanduser().resolve()
    public_path = public_path.resolve()
    private_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(private_path.parent, 0o700)
    if not private_path.exists():
        temporary = private_path.with_suffix(private_path.suffix + ".tmp")
        _run(["genpkey", "-algorithm", "ED25519", "-out", str(temporary)])
        os.chmod(temporary, 0o600)
        temporary.replace(private_path)
    os.chmod(private_path, 0o600)
    public_pem = _run(["pkey", "-in", str(private_path), "-pubout"])
    if public_path.exists() and public_path.read_bytes() != public_pem:
        raise ValueError("workspace annotation public key does not match the configured private key")
    if not public_path.exists():
        public_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = public_path.with_suffix(public_path.suffix + ".tmp")
        temporary.write_bytes(public_pem)
        os.chmod(temporary, 0o644)
        temporary.replace(public_path)
    os.chmod(public_path, 0o644)
    return {
        "private_key_path": str(private_path),
        "public_key_path": str(public_path),
        "public_key_sha256": hashlib.sha256(public_pem).hexdigest(),
    }


def load_public_key(path: Path) -> Dict[str, Any]:
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    content = path.read_bytes()
    if b"BEGIN PUBLIC KEY" not in content:
        raise ValueError("invalid annotation public key")
    _run(["pkey", "-pubin", "-in", str(path), "-noout"])
    return {"public_key_path": str(path), "public_key_sha256": hashlib.sha256(content).hexdigest()}


def signature_payload(row: Mapping[str, Any], kind: str) -> Dict[str, Any]:
    fields = ANCHOR_FIELDS if kind == "anchor" else LABEL_FIELDS
    return {
        "signature_version": SIGNATURE_VERSION,
        "kind": kind,
        "row": {field: row.get(field) for field in fields if field in row},
    }


def _sign_bytes(payload: bytes, private_path: Path) -> bytes:
    with tempfile.NamedTemporaryFile() as message:
        message.write(payload)
        message.flush()
        return _run(["pkeyutl", "-sign", "-rawin", "-inkey", str(private_path), "-in", message.name])


def _verify_bytes(payload: bytes, signature: bytes, public_path: Path) -> bool:
    with tempfile.NamedTemporaryFile() as message, tempfile.NamedTemporaryFile() as signature_file:
        message.write(payload)
        message.flush()
        signature_file.write(signature)
        signature_file.flush()
        completed = subprocess.run(
            [
                _openssl(), "pkeyutl", "-verify", "-rawin", "-pubin", "-inkey", str(public_path),
                "-in", message.name, "-sigfile", signature_file.name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return completed.returncode == 0


def sign_row(row: Mapping[str, Any], kind: str, private_path: Path) -> Dict[str, Any]:
    result = dict(row)
    result["submission_signature_version"] = SIGNATURE_VERSION
    signature = _sign_bytes(_canonical_bytes(signature_payload(result, kind)), private_path)
    result["submission_signature"] = base64.b64encode(signature).decode("ascii")
    return result


def verify_row(row: Mapping[str, Any], kind: str, public_path: Path) -> bool:
    if str(row.get("submission_signature_version") or "") != SIGNATURE_VERSION:
        return False
    try:
        signature = base64.b64decode(str(row.get("submission_signature") or ""), validate=True)
    except (ValueError, TypeError):
        return False
    return _verify_bytes(_canonical_bytes(signature_payload(row, kind)), signature, public_path)


def audit_rows(rows: Sequence[Mapping[str, Any]], kind: str, public_path: Path) -> Dict[str, Any]:
    public = load_public_key(public_path)
    relevant = []
    for row in rows:
        submitted = bool(row.get("human_review_complete")) if kind == "anchor" else bool(str(row.get("human_label") or "").strip())
        if submitted:
            relevant.append(row)
    invalid_ids = []
    for row in relevant:
        if not verify_row(row, kind, public_path):
            invalid_ids.append(str(row.get("paper_id") if kind == "anchor" else row.get("packet_id") or ""))
    return {
        "kind": kind,
        "signature_version": SIGNATURE_VERSION,
        "public_key_sha256": public["public_key_sha256"],
        "submitted_count": len(relevant),
        "valid_count": len(relevant) - len(invalid_ids),
        "invalid_ids": invalid_ids,
        "status": "PASS" if not invalid_ids else "BLOCKED",
    }
