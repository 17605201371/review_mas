#!/usr/bin/env python3
"""Serve a local P34 human-annotation workspace with durable JSON outputs."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Mapping
from urllib.parse import parse_qs, urlparse

from agent_system.inference.review_runner import _row_to_env_kwargs, load_review_rows
from scripts.p34_annotation_signature import load_or_create_keypair, sign_row


LABEL_TASKS = {"evidence_relation", "claim_faithfulness", "review_issue"}
LABEL_ANNOTATORS = {"primary", "secondary"}
ANNOTATOR_PROFILES = {"primary", "secondary", "adjudicator"}


def _load_paper_texts(path: Path) -> Dict[str, str]:
    result = {}
    for row in load_review_rows(str(path)):
        mapped = _row_to_env_kwargs(row)
        paper_id = str(row.get("id") or row.get("paper_id") or mapped.get("paper_id") or "")
        if paper_id:
            result[paper_id] = str(mapped.get("paper_text") or "")
    return result


def _load_json(path: Path) -> Dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


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


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _canonical_sha256(value: Any) -> str:
    encoded = (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _render_portable_bundle(template_path: Path, bundle: Mapping[str, Any]) -> str:
    template = template_path.read_text(encoding="utf-8")
    marker = "__P34_BUNDLE_BASE64__"
    if template.count(marker) != 1:
        raise ValueError("portable annotation template must contain exactly one bundle marker")
    encoded = base64.b64encode(
        (json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    ).decode("ascii")
    return template.replace(marker, encoded)


def _build_role_package(
    store: "AnnotationStore",
    annotator: str,
    auth_token: Any,
    portable_label_path: Path,
    portable_paper_index_path: Path,
) -> tuple[str, bytes, Dict[str, Any]]:
    if annotator not in ANNOTATOR_PROFILES:
        raise ValueError("unsupported annotator role")
    reviewer_id = store._registered_reviewer_id(annotator)
    store._validate_reviewer(annotator, reviewer_id or annotator, auth_token)
    files: List[tuple[str, bytes, Dict[str, Any]]] = []
    for task in sorted(LABEL_TASKS):
        bundle = store.export_label_bundle(task, annotator, auth_token)
        if not bundle["items"]:
            continue
        filename = f"p34_{task}_{annotator}_{bundle['bundle_sha256'][:12]}.html"
        content = _render_portable_bundle(portable_label_path, bundle).encode("utf-8")
        files.append((filename, content, {
            "task_type": task,
            "schema_version": bundle["schema_version"],
            "bundle_sha256": bundle["bundle_sha256"],
            "item_count": len(bundle["items"]),
            "html_sha256": hashlib.sha256(content).hexdigest(),
        }))
    if annotator in LABEL_ANNOTATORS:
        bundle = store.export_anchor_bundle(annotator, auth_token)
        filename = f"p34_paper_index_{annotator}_{bundle['bundle_sha256'][:12]}.html"
        content = _render_portable_bundle(portable_paper_index_path, bundle).encode("utf-8")
        files.append((filename, content, {
            "task_type": "paper_index",
            "schema_version": bundle["schema_version"],
            "bundle_sha256": bundle["bundle_sha256"],
            "item_count": len(bundle["items"]),
            "html_sha256": hashlib.sha256(content).hexdigest(),
        }))
    if not files:
        raise ValueError("annotator role has no exportable audit tasks")
    file_manifest = [item[2] | {"filename": item[0]} for item in files]
    manifest = {
        "schema_version": "p34_annotation_role_package_v1",
        "annotator_role": annotator,
        "reviewer_id": reviewer_id,
        "assignment_sha256": str(store.assignment.get("assignment_sha256") or ""),
        "files": file_manifest,
    }
    manifest["package_contract_sha256"] = _canonical_sha256(manifest)
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for filename, content, _metadata in [("manifest.json", manifest_bytes, {})] + files:
            info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, content)
    filename = f"p34_{annotator}_{manifest['package_contract_sha256'][:12]}.zip"
    return filename, output.getvalue(), manifest


class AnnotationStore:
    def __init__(
        self,
        *,
        packets_path: Path,
        positive_template_path: Path,
        claim_template_path: Path,
        issue_template_path: Path | None,
        anchors_path: Path,
        output_dir: Path,
        issue_packets_path: Path | None = None,
        issue_provenance_path: Path | None = None,
        assignment_path: Path | None = None,
        paper_texts: Mapping[str, str] | None = None,
        require_annotator_identity: bool = False,
        signing_private_key_path: Path | None = None,
        repo: Path | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.repo = (repo or Path(__file__).resolve().parents[1]).resolve()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.signing_private_key_path = (
            signing_private_key_path
            or Path(os.environ.get("P34_ANNOTATION_PRIVATE_KEY") or "~/.config/drmas/p34_annotation_ed25519_private.pem")
        ).expanduser()
        self.signing_public_key_path = self.output_dir / "annotation_signing_public.pem"
        self.signing_key_info = load_or_create_keypair(
            self.signing_private_key_path, self.signing_public_key_path
        )
        packets = _load_jsonl(packets_path)
        self.packets = {str(item.get("packet_id") or ""): item for item in packets if item.get("packet_id")}
        self.issue_template_path = issue_template_path
        self.issue_packets_path = issue_packets_path
        self.issue_provenance_path = issue_provenance_path
        self.assignment_path = assignment_path
        self.assignment = _load_json(assignment_path) if assignment_path is not None and assignment_path.exists() else {}
        self.paper_texts = {str(key): str(value) for key, value in (paper_texts or {}).items()}
        self.require_annotator_identity = bool(require_annotator_identity)
        self.annotator_registry_path = self.output_dir / "annotator_registry.json"
        self.annotator_registry = (
            _load_json(self.annotator_registry_path)
            if self.annotator_registry_path.exists()
            else {"schema_version": "p34_annotator_registry_v3", "roles": {}}
        )
        if issue_packets_path is not None and issue_packets_path.exists():
            for item in _load_jsonl(issue_packets_path):
                if item.get("packet_id"):
                    self.packets[str(item["packet_id"])] = item
        self.templates = {
            "evidence_relation": _load_json(positive_template_path),
            "claim_faithfulness": _load_json(claim_template_path),
            "review_issue": (
                _load_json(issue_template_path)
                if issue_template_path is not None and issue_template_path.exists()
                else {"labels": []}
            ),
        }
        self.anchor_template = _load_json(anchors_path)
        self._template_rows = {
            task: {str(item.get("packet_id") or ""): item for item in value.get("labels", []) if item.get("packet_id")}
            for task, value in self.templates.items()
        }
        self._anchor_rows = {
            str(item.get("paper_id") or ""): item
            for item in self.anchor_template.get("cases", [])
            if item.get("paper_id")
        }
        self._initialize_workspace_files()

    def _label_path(self, task: str, annotator: str) -> Path:
        return self.output_dir / f"{task}_{annotator}.json"

    def _resolution_path(self, task: str) -> Path:
        return self.output_dir / f"{task}_resolution.json"

    def _anchor_path(self, annotator: str) -> Path:
        return self.output_dir / f"paper_index_anchors_{annotator}.json"

    def _assigned_packet_ids(self, task: str, annotator: str) -> List[str]:
        if annotator != "secondary" or not self.assignment:
            return list(self._template_rows[task])
        task_assignment = (self.assignment.get("tasks") or {}).get(task) or {}
        assigned = [str(item) for item in task_assignment.get("secondary_packet_ids", []) if str(item)]
        return [packet_id for packet_id in assigned if packet_id in self._template_rows[task]]

    def reload_assignment(self) -> Dict[str, Any]:
        if self.assignment_path is None or not self.assignment_path.exists():
            raise ValueError("annotation assignment manifest is not configured")
        assignment = _load_json(self.assignment_path)
        with self._lock:
            self.assignment = assignment
            for task in LABEL_TASKS:
                rows = self._load_label_rows(task, "secondary")
                self._write_label_rows(task, "secondary", rows)
        return {
            "status": "RELOADED",
            "assignment_status": str(assignment.get("status") or "UNKNOWN"),
            "assignment_sha256": str(assignment.get("assignment_sha256") or ""),
            "secondary_counts": {
                task: len(self._assigned_packet_ids(task, "secondary"))
                for task in sorted(LABEL_TASKS)
            },
        }

    def _gate_report_path(self) -> Path:
        return self.repo / "P34_ANNOTATION_GATE_REFRESH_20260711.json"

    def _quality_report_path(self) -> Path:
        return self.repo / "P34_ANNOTATION_QUALITY_DASHBOARD_20260711.json"

    @staticmethod
    def _clean_reviewer_id(value: Any) -> str:
        reviewer_id = str(value or "").strip()
        if not re.fullmatch(r"[^\s/\\]{2,64}", reviewer_id):
            raise ValueError("reviewer_id must be 2-64 non-whitespace characters")
        return reviewer_id

    def register_annotator(self, role: str, reviewer_id: Any) -> Dict[str, Any]:
        if role not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported annotator role")
        reviewer_id = self._clean_reviewer_id(reviewer_id)
        with self._lock:
            roles = dict(self.annotator_registry.get("roles") or {})
            existing_value = roles.get(role)
            existing = (
                str(existing_value.get("reviewer_id") or "")
                if isinstance(existing_value, dict)
                else str(existing_value or "")
            )
            if existing and existing != reviewer_id:
                raise ValueError("annotator role is already bound to another reviewer_id")
            conflicting_role = next(
                (
                    item_role
                    for item_role, item_value in roles.items()
                    if item_role != role
                    and (
                        str(item_value.get("reviewer_id") or "")
                        if isinstance(item_value, dict)
                        else str(item_value or "")
                    ) == reviewer_id
                ),
                "",
            )
            if conflicting_role:
                raise ValueError(f"reviewer_id is already bound to role {conflicting_role}")
            if isinstance(existing_value, dict) and existing_value.get("token_sha256"):
                return {"status": "ALREADY_REGISTERED", "role": role, "reviewer_id": reviewer_id}
            return self._issue_annotator_credentials(
                role, reviewer_id, roles, status="REGISTERED", recovery_increment=0
            )

    def _issue_annotator_credentials(
        self,
        role: str,
        reviewer_id: str,
        roles: Mapping[str, Any],
        *,
        status: str,
        recovery_increment: int,
    ) -> Dict[str, Any]:
        current = roles.get(role) if isinstance(roles.get(role), dict) else {}
        auth_token = secrets.token_urlsafe(32)
        recovery_code = secrets.token_urlsafe(32)
        updated_roles = dict(roles)
        updated_roles[role] = {
            "reviewer_id": reviewer_id,
            "token_sha256": hashlib.sha256(auth_token.encode("utf-8")).hexdigest(),
            "recovery_code_sha256": hashlib.sha256(recovery_code.encode("utf-8")).hexdigest(),
            "credential_generation": int(current.get("credential_generation") or 0) + 1,
            "recovery_count": int(current.get("recovery_count") or 0) + recovery_increment,
        }
        self.annotator_registry = {
            "schema_version": "p34_annotator_registry_v3",
            "roles": updated_roles,
        }
        _atomic_write_json(self.annotator_registry_path, self.annotator_registry)
        return {
            "status": status,
            "role": role,
            "reviewer_id": reviewer_id,
            "auth_token": auth_token,
            "recovery_code": recovery_code,
            "credential_generation": updated_roles[role]["credential_generation"],
        }

    def verify_annotator(self, role: str, reviewer_id: Any, auth_token: Any) -> Dict[str, Any]:
        if not self.require_annotator_identity:
            raise ValueError("annotator credential management requires the identity gate")
        if role not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported annotator role")
        reviewer_id = self._validate_reviewer(role, reviewer_id, auth_token)
        role_value = (self.annotator_registry.get("roles") or {}).get(role) or {}
        return {
            "status": "VERIFIED",
            "role": role,
            "reviewer_id": reviewer_id,
            "credential_generation": int(role_value.get("credential_generation") or 0),
            "recovery_enabled": bool(role_value.get("recovery_code_sha256")),
        }

    def rotate_annotator(self, role: str, reviewer_id: Any, auth_token: Any) -> Dict[str, Any]:
        if not self.require_annotator_identity:
            raise ValueError("annotator credential management requires the identity gate")
        if role not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported annotator role")
        reviewer_id = self._validate_reviewer(role, reviewer_id, auth_token)
        with self._lock:
            roles = dict(self.annotator_registry.get("roles") or {})
            return self._issue_annotator_credentials(
                role, reviewer_id, roles, status="ROTATED", recovery_increment=0
            )

    def recover_annotator(self, role: str, reviewer_id: Any, recovery_code: Any) -> Dict[str, Any]:
        if not self.require_annotator_identity:
            raise ValueError("annotator credential management requires the identity gate")
        if role not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported annotator role")
        reviewer_id = self._clean_reviewer_id(reviewer_id)
        code = str(recovery_code or "").strip()
        if not code:
            raise ValueError("annotator recovery code is required")
        with self._lock:
            roles = dict(self.annotator_registry.get("roles") or {})
            role_value = roles.get(role)
            if not isinstance(role_value, dict) or str(role_value.get("reviewer_id") or "") != reviewer_id:
                raise ValueError("reviewer_id does not match the registered annotator role")
            expected_hash = str(role_value.get("recovery_code_sha256") or "")
            if not expected_hash:
                raise ValueError("annotator recovery is not enabled; rotate with the current token first")
            actual_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            if not hmac.compare_digest(actual_hash, expected_hash):
                raise ValueError("annotator recovery code is invalid")
            return self._issue_annotator_credentials(
                role, reviewer_id, roles, status="RECOVERED", recovery_increment=1
            )

    def _registered_reviewer_id(self, role: str) -> str:
        value = (self.annotator_registry.get("roles") or {}).get(role)
        return str(value.get("reviewer_id") or "") if isinstance(value, dict) else str(value or "")

    def _validate_reviewer(self, role: str, reviewer_id: Any, auth_token: Any = "") -> str:
        if not self.require_annotator_identity:
            return str(reviewer_id or role)
        reviewer_id = self._clean_reviewer_id(reviewer_id)
        registered = self._registered_reviewer_id(role)
        if not registered:
            raise ValueError("annotator role must be registered before saving")
        if reviewer_id != registered:
            raise ValueError("reviewer_id does not match the registered annotator role")
        role_value = (self.annotator_registry.get("roles") or {}).get(role)
        expected_hash = str(role_value.get("token_sha256") or "") if isinstance(role_value, dict) else ""
        token = str(auth_token or "").strip()
        if not expected_hash or not token:
            raise ValueError("annotator authentication token is required")
        actual_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(actual_hash, expected_hash):
            raise ValueError("annotator authentication token is invalid")
        return reviewer_id

    def gate_status(self) -> Dict[str, Any]:
        path = self._gate_report_path()
        if not path.exists():
            return {
                "status": "NOT_REFRESHED",
                "run_api": False,
                "stages": {},
                "counts": {},
                "report_path": str(path),
            }
        report = _load_json(path)
        return {
            "status": str(report.get("status") or "UNKNOWN"),
            "run_api": bool(report.get("run_api")),
            "stages": dict(report.get("stages") or {}),
            "counts": dict(report.get("counts") or {}),
            "config_sha256": str(report.get("config_sha256") or ""),
            "blocking_issues": list(report.get("blocking_issues") or []),
            "report_path": str(path),
        }

    def quality_status(self) -> Dict[str, Any]:
        path = self._quality_report_path()
        if not path.exists():
            return {
                "status": "NOT_REFRESHED",
                "tasks": {},
                "paper_index": {},
                "discovery": {},
                "actionable_now": [],
                "blocking_issues": [],
                "report_path": str(path),
            }
        report = _load_json(path)
        report["report_path"] = str(path)
        return report

    def refresh_gate_status(self) -> Dict[str, Any]:
        with self._lock:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self.repo / "scripts/p34_annotation_gate_refresh.py"),
                    "--repo",
                    str(self.repo),
                    "--workspace",
                    str(self.output_dir.resolve()),
                ],
                cwd=self.repo,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            status = self.gate_status()
            status["refresh_returncode"] = completed.returncode
            status["refresh_completed"] = True
            if completed.returncode not in {0, 1}:
                detail = (completed.stderr or completed.stdout or "gate refresh failed").strip()
                raise RuntimeError(detail[-2000:])
            return status

    def reload_issue_artifacts(self) -> Dict[str, Any]:
        if self.issue_template_path is None or self.issue_packets_path is None or self.issue_provenance_path is None:
            raise ValueError("active discovery artifact paths are not configured")
        for path in (self.issue_template_path, self.issue_packets_path, self.issue_provenance_path):
            if not path.exists():
                raise ValueError(f"active discovery artifact is missing: {path}")
        templates_value = _load_json(self.issue_template_path)
        template_rows = {
            str(item.get("packet_id") or ""): item
            for item in templates_value.get("labels", [])
            if isinstance(item, dict) and item.get("packet_id")
        }
        issue_packets = {
            str(item.get("packet_id") or ""): item
            for item in _load_jsonl(self.issue_packets_path)
            if item.get("packet_id")
        }
        provenance_rows = {
            str(item.get("packet_id") or ""): item
            for item in _load_json(self.issue_provenance_path).get("items", [])
            if isinstance(item, dict) and item.get("packet_id")
        }
        if set(template_rows) != set(issue_packets) or set(template_rows) != set(provenance_rows):
            raise ValueError("active discovery packet/template/provenance ids do not match")
        if any(str(item.get("task_type") or "") != "review_issue" for item in issue_packets.values()):
            raise ValueError("active discovery contains a non-review_issue packet")
        with self._lock:
            if self.assignment_path is not None and self.assignment_path.exists():
                self.assignment = _load_json(self.assignment_path)
            saved_by_annotator = {}
            for annotator in LABEL_ANNOTATORS:
                path = self._label_path("review_issue", annotator)
                value = _load_json(path) if path.exists() else {"labels": []}
                saved_by_annotator[annotator] = {
                    str(item.get("packet_id") or ""): item
                    for item in value.get("labels", [])
                    if isinstance(item, dict) and item.get("packet_id")
                }
            resolution_path = self._resolution_path("review_issue")
            resolution_value = _load_json(resolution_path) if resolution_path.exists() else {"labels": []}
            saved_resolutions = {
                str(item.get("packet_id") or ""): item
                for item in resolution_value.get("labels", [])
                if isinstance(item, dict) and item.get("packet_id")
            }

            self.templates["review_issue"] = templates_value
            self._template_rows["review_issue"] = template_rows
            self.packets = {
                packet_id: item
                for packet_id, item in self.packets.items()
                if str(item.get("task_type") or "") != "review_issue"
            }
            self.packets.update(issue_packets)

            orphaned_counts = {}
            for annotator, saved in saved_by_annotator.items():
                assigned_ids = self._assigned_packet_ids("review_issue", annotator)
                rows = {
                    packet_id: {
                        **dict(template),
                        **dict(saved.get(packet_id, {})),
                        "annotator_id": annotator,
                    }
                    for packet_id, template in template_rows.items()
                    if packet_id in assigned_ids
                }
                orphaned = [dict(item) for packet_id, item in saved.items() if packet_id not in template_rows]
                orphaned_counts[annotator] = len(orphaned)
                _atomic_write_json(
                    self._label_path("review_issue", annotator),
                    {
                        "schema_version": "p34_human_labels_v1",
                        "task_type": "review_issue",
                        "annotator_id": annotator,
                        "labels": [rows[packet_id] for packet_id in assigned_ids if packet_id in rows],
                        "orphaned_labels": orphaned,
                    },
                )
            active_resolutions = [dict(saved_resolutions[packet_id]) for packet_id in template_rows if packet_id in saved_resolutions]
            orphaned_resolutions = [dict(item) for packet_id, item in saved_resolutions.items() if packet_id not in template_rows]
            _atomic_write_json(
                resolution_path,
                {
                    "schema_version": "p34_human_label_resolutions_v1",
                    "task_type": "review_issue",
                    "annotator_id": "adjudicator",
                    "labels": active_resolutions,
                    "orphaned_resolutions": orphaned_resolutions,
                },
            )
        return {
            "status": "RELOADED",
            "packet_count": len(issue_packets),
            "provenance_count": len(provenance_rows),
            "orphaned_label_counts": orphaned_counts,
            "orphaned_resolution_count": len(orphaned_resolutions),
            "issue_template_path": str(self.issue_template_path),
        }

    def _initialize_workspace_files(self) -> None:
        for task in LABEL_TASKS:
            for annotator in LABEL_ANNOTATORS:
                path = self._label_path(task, annotator)
                if not path.exists():
                    self._write_label_rows(task, annotator, self._load_label_rows(task, annotator))
            resolution_path = self._resolution_path(task)
            if not resolution_path.exists():
                _atomic_write_json(
                    resolution_path,
                    {
                        "schema_version": "p34_human_label_resolutions_v1",
                        "task_type": task,
                        "annotator_id": "adjudicator",
                        "labels": [],
                    },
                )
        for annotator in LABEL_ANNOTATORS:
            path = self._anchor_path(annotator)
            if path.exists():
                continue
            rows = [
                {
                    **dict(self._anchor_rows[paper_id]),
                    "human_reviewer_id": self._registered_reviewer_id(annotator) or (annotator if not self.require_annotator_identity else ""),
                }
                for paper_id in self._anchor_rows
            ]
            _atomic_write_json(
                path,
                {
                    "schema_version": self.anchor_template.get("schema_version", "p34_paper_index_human_anchors_v1"),
                    "dataset_sha256": self.anchor_template.get("dataset_sha256", ""),
                    "machine_suggestions_are_not_labels": True,
                    "annotator_id": annotator,
                    "cases": rows,
                },
            )

    def _load_label_rows(self, task: str, annotator: str) -> Dict[str, Dict[str, Any]]:
        assigned_ids = set(self._assigned_packet_ids(task, annotator))
        path = self._label_path(task, annotator)
        if not path.exists():
            return {
                packet_id: {
                    **dict(template),
                    "human_label": "",
                    "human_reason": "",
                    "task_type": task,
                    "annotator_id": annotator,
                }
                for packet_id, template in self._template_rows[task].items()
                if packet_id in assigned_ids
            }
        value = _load_json(path)
        saved = {str(item.get("packet_id") or ""): item for item in value.get("labels", []) if item.get("packet_id")}
        return {
            packet_id: {
                **dict(template),
                **dict(saved.get(packet_id, {})),
                "task_type": task,
                "annotator_id": annotator,
            }
            for packet_id, template in self._template_rows[task].items()
            if packet_id in assigned_ids
        }

    def _write_label_rows(self, task: str, annotator: str, rows: Mapping[str, Mapping[str, Any]]) -> None:
        ordered = [
            dict(rows[packet_id])
            for packet_id in self._assigned_packet_ids(task, annotator)
            if packet_id in rows
        ]
        _atomic_write_json(
            self._label_path(task, annotator),
            {
                "schema_version": "p34_human_labels_v1",
                "task_type": task,
                "annotator_id": annotator,
                "labels": ordered,
            },
        )

    def label_workspace(self, task: str, annotator: str) -> Dict[str, Any]:
        if task not in LABEL_TASKS or annotator not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported task or annotator")
        if annotator == "adjudicator":
            return self._adjudication_workspace(task)
        with self._lock:
            rows = self._load_label_rows(task, annotator)
            items = []
            for packet_id in self._assigned_packet_ids(task, annotator):
                row = rows[packet_id]
                items.append({
                    "packet_id": packet_id,
                    "paper_id": row.get("paper_id", ""),
                    "task_type": row.get("task_type", task),
                    "human_label": row.get("human_label", ""),
                    "human_reason": row.get("human_reason", ""),
                    "allowed_labels": row.get("allowed_labels", []),
                    "packet": self.packets.get(packet_id, {}),
                })
            completed = sum(bool(str(item["human_label"]).strip()) for item in items)
            return {
                "task": task,
                "annotator": annotator,
                "identity_required": self.require_annotator_identity,
                "reviewer_id": self._registered_reviewer_id(annotator),
                "items": items,
                "progress": {"completed": completed, "total": len(items)},
                "output_path": str(self._label_path(task, annotator)),
            }

    def export_label_bundle(self, task: str, annotator: str, auth_token: Any = "") -> Dict[str, Any]:
        if task not in LABEL_TASKS or annotator not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported task or annotator")
        reviewer_id = self._registered_reviewer_id(annotator)
        if self.require_annotator_identity and not reviewer_id:
            raise ValueError("annotator role must be registered before exporting")
        reviewer_id = self._validate_reviewer(annotator, reviewer_id or annotator, auth_token)
        workspace = self.label_workspace(task, annotator)
        immutable_items = []
        labels = []
        for item in workspace["items"]:
            immutable = {
                "packet_id": str(item.get("packet_id") or ""),
                "paper_id": str(item.get("paper_id") or ""),
                "task_type": str(item.get("task_type") or task),
                "allowed_labels": list(item.get("allowed_labels") or []),
                "packet": dict(item.get("packet") or {}),
            }
            if annotator == "adjudicator":
                immutable.update({
                    "primary_label": str(item.get("primary_label") or ""),
                    "primary_reason": str(item.get("primary_reason") or ""),
                    "secondary_label": str(item.get("secondary_label") or ""),
                    "secondary_reason": str(item.get("secondary_reason") or ""),
                })
            immutable_items.append(immutable)
            labels.append({
                "packet_id": immutable["packet_id"],
                "human_label": str(item.get("human_label") or ""),
                "human_reason": str(item.get("human_reason") or ""),
            })
        contract = {
            "schema_version": "p34_annotation_exchange_v1",
            "task_type": task,
            "annotator_role": annotator,
            "reviewer_id": reviewer_id or annotator,
            "assignment_sha256": str(self.assignment.get("assignment_sha256") or ""),
            "template_sha256": _canonical_sha256(self.templates[task]),
            "label_state_sha256": _canonical_sha256(labels),
            "items": immutable_items,
        }
        bundle_sha256 = _canonical_sha256(contract)
        return {
            **contract,
            "bundle_sha256": bundle_sha256,
            "boundary": "Role-isolated blind annotation packet; edit only labels and return the same bundle hash",
            "labels": labels,
        }

    def import_label_bundle(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if str(payload.get("schema_version") or "") != "p34_annotation_exchange_v1":
            raise ValueError("unsupported annotation exchange schema")
        task = str(payload.get("task_type") or "")
        annotator = str(payload.get("annotator_role") or "")
        reviewer_id = self._validate_reviewer(
            annotator, payload.get("reviewer_id"), payload.get("auth_token")
        )
        current = self.export_label_bundle(task, annotator, payload.get("auth_token"))
        if str(payload.get("bundle_sha256") or "") != current["bundle_sha256"]:
            raise ValueError("annotation bundle is stale or does not match the current assignment")
        labels = payload.get("labels")
        if not isinstance(labels, list):
            raise ValueError("annotation bundle labels must be a list")
        expected_ids = [str(item.get("packet_id") or "") for item in current["labels"]]
        received_ids = [str(item.get("packet_id") or "") for item in labels if isinstance(item, dict)]
        if len(labels) != len(received_ids) or len(received_ids) != len(set(received_ids)):
            raise ValueError("annotation bundle contains malformed or duplicate label rows")
        if set(received_ids) != set(expected_ids):
            raise ValueError("annotation bundle label ids do not match the exported role assignment")
        result = self.save_label_batch(task, annotator, reviewer_id, payload.get("auth_token"), labels)
        return {**result, "bundle_sha256": current["bundle_sha256"]}

    def save_label_batch(
        self,
        task: str,
        annotator: str,
        reviewer_id: str,
        auth_token: Any,
        label_rows: List[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        if task not in LABEL_TASKS or annotator not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported task or annotator")
        reviewer_id = self._validate_reviewer(annotator, reviewer_id, auth_token)
        cleaned = []
        seen = set()
        for item in label_rows:
            packet_id = str(item.get("packet_id") or "")
            if not packet_id or packet_id in seen:
                raise ValueError("batch labels require unique packet ids")
            seen.add(packet_id)
            template = self._template_rows[task].get(packet_id)
            if template is None:
                raise ValueError("unknown packet_id")
            if annotator == "secondary" and packet_id not in self._assigned_packet_ids(task, annotator):
                raise ValueError("packet_id is not assigned to the secondary annotator")
            label = str(item.get("human_label") or "").strip()
            allowed = {str(value) for value in template.get("allowed_labels", [])}
            if label and label not in allowed:
                raise ValueError(f"label is not allowed for packet {packet_id}")
            cleaned.append((packet_id, label, " ".join(str(item.get("human_reason") or "").split())[:1200]))
        with self._lock:
            if annotator == "adjudicator":
                primary = self._load_label_rows(task, "primary")
                secondary = self._load_label_rows(task, "secondary")
                resolutions = self._load_resolution_rows(task)
                for packet_id, _, _ in cleaned:
                    primary_label = str(primary.get(packet_id, {}).get("human_label") or "")
                    secondary_label = str(secondary.get(packet_id, {}).get("human_label") or "")
                    if not primary_label or not secondary_label or primary_label == secondary_label:
                        raise ValueError(f"packet {packet_id} is not an active labeling disagreement")
                for packet_id, label, reason in cleaned:
                    template = self._template_rows[task][packet_id]
                    resolutions[packet_id] = {
                        "packet_id": packet_id,
                        "paper_id": str(template.get("paper_id") or ""),
                        "task_type": task,
                        "allowed_labels": list(template.get("allowed_labels", [])),
                        "human_label": label,
                        "human_reason": reason,
                        "annotator_id": "adjudicator",
                        "human_reviewer_id": reviewer_id,
                        "primary_label_for_audit": str(primary[packet_id].get("human_label") or ""),
                        "secondary_label_for_audit": str(secondary[packet_id].get("human_label") or ""),
                    }
                    resolutions[packet_id] = sign_row(
                        resolutions[packet_id], "label", self.signing_private_key_path
                    )
                ordered = [resolutions[key] for key in self._template_rows[task] if key in resolutions]
                _atomic_write_json(self._resolution_path(task), {
                    "schema_version": "p34_human_label_resolutions_v1",
                    "task_type": task,
                    "annotator_id": "adjudicator",
                    "labels": ordered,
                })
                completed = sum(bool(str(item.get("human_label") or "").strip()) for item in ordered)
                total = len(self._adjudication_workspace(task)["items"])
                output_path = self._resolution_path(task)
            else:
                rows = self._load_label_rows(task, annotator)
                for packet_id, label, reason in cleaned:
                    rows[packet_id]["human_label"] = label
                    rows[packet_id]["human_reason"] = reason
                    rows[packet_id]["annotator_id"] = annotator
                    rows[packet_id]["human_reviewer_id"] = reviewer_id
                    rows[packet_id] = sign_row(rows[packet_id], "label", self.signing_private_key_path)
                self._write_label_rows(task, annotator, rows)
                completed = sum(bool(str(item.get("human_label") or "").strip()) for item in rows.values())
                total = len(rows)
                output_path = self._label_path(task, annotator)
        return {
            "saved": True,
            "imported_count": len(cleaned),
            "completed": completed,
            "total": total,
            "output_path": str(output_path),
        }

    def _load_resolution_rows(self, task: str) -> Dict[str, Dict[str, Any]]:
        path = self._resolution_path(task)
        if not path.exists():
            return {}
        value = _load_json(path)
        return {
            str(item.get("packet_id") or ""): dict(item)
            for item in value.get("labels", [])
            if isinstance(item, dict) and item.get("packet_id")
        }

    def _adjudication_workspace(self, task: str) -> Dict[str, Any]:
        with self._lock:
            primary = self._load_label_rows(task, "primary")
            secondary = self._load_label_rows(task, "secondary")
            resolutions = self._load_resolution_rows(task)
            items = []
            for packet_id in self._assigned_packet_ids(task, "secondary"):
                if packet_id not in primary or packet_id not in secondary:
                    continue
                primary_row, secondary_row = primary[packet_id], secondary[packet_id]
                primary_label = str(primary_row.get("human_label") or "")
                secondary_label = str(secondary_row.get("human_label") or "")
                if not primary_label or not secondary_label or primary_label == secondary_label:
                    continue
                resolution = resolutions.get(packet_id, {})
                template = self._template_rows[task][packet_id]
                items.append({
                    "packet_id": packet_id,
                    "paper_id": str(template.get("paper_id") or ""),
                    "human_label": str(resolution.get("human_label") or ""),
                    "human_reason": str(resolution.get("human_reason") or ""),
                    "allowed_labels": list(template.get("allowed_labels", [])),
                    "primary_label": primary_label,
                    "primary_reason": str(primary_row.get("human_reason") or ""),
                    "secondary_label": secondary_label,
                    "secondary_reason": str(secondary_row.get("human_reason") or ""),
                    "packet": self.packets.get(packet_id, {}),
                })
            completed = sum(bool(str(item["human_label"]).strip()) for item in items)
            return {
                "task": task,
                "annotator": "adjudicator",
                "identity_required": self.require_annotator_identity,
                "reviewer_id": self._registered_reviewer_id("adjudicator"),
                "items": items,
                "progress": {"completed": completed, "total": len(items)},
                "output_path": str(self._resolution_path(task)),
            }

    def save_label(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        task = str(payload.get("task") or "")
        annotator = str(payload.get("annotator") or "")
        packet_id = str(payload.get("packet_id") or "")
        label = str(payload.get("human_label") or "").strip()
        reason = " ".join(str(payload.get("human_reason") or "").split())[:1200]
        if task not in LABEL_TASKS or annotator not in ANNOTATOR_PROFILES:
            raise ValueError("unsupported task or annotator")
        reviewer_id = self._validate_reviewer(
            annotator, payload.get("reviewer_id"), payload.get("auth_token")
        )
        template = self._template_rows[task].get(packet_id)
        if template is None:
            raise ValueError("unknown packet_id")
        if annotator == "secondary" and packet_id not in self._assigned_packet_ids(task, annotator):
            raise ValueError("packet_id is not assigned to the secondary annotator")
        allowed = {str(item) for item in template.get("allowed_labels", [])}
        if label and label not in allowed:
            raise ValueError("label is not allowed for this packet")
        if annotator == "adjudicator":
            return self._save_resolution(task, packet_id, label, reason, reviewer_id)
        with self._lock:
            rows = self._load_label_rows(task, annotator)
            rows[packet_id]["human_label"] = label
            rows[packet_id]["human_reason"] = reason
            rows[packet_id]["annotator_id"] = annotator
            rows[packet_id]["human_reviewer_id"] = reviewer_id
            rows[packet_id] = sign_row(rows[packet_id], "label", self.signing_private_key_path)
            self._write_label_rows(task, annotator, rows)
            completed = sum(bool(str(item.get("human_label") or "").strip()) for item in rows.values())
        return {"saved": True, "completed": completed, "total": len(rows), "output_path": str(self._label_path(task, annotator))}

    def _save_resolution(self, task: str, packet_id: str, label: str, reason: str, reviewer_id: str) -> Dict[str, Any]:
        with self._lock:
            primary = self._load_label_rows(task, "primary")
            secondary = self._load_label_rows(task, "secondary")
            primary_label = str(primary[packet_id].get("human_label") or "")
            secondary_label = str(secondary[packet_id].get("human_label") or "")
            if not primary_label or not secondary_label or primary_label == secondary_label:
                raise ValueError("packet is not an active labeling disagreement")
            resolutions = self._load_resolution_rows(task)
            template = self._template_rows[task][packet_id]
            resolutions[packet_id] = {
                "packet_id": packet_id,
                "paper_id": str(template.get("paper_id") or ""),
                "task_type": task,
                "allowed_labels": list(template.get("allowed_labels", [])),
                "human_label": label,
                "human_reason": reason,
                "annotator_id": "adjudicator",
                "human_reviewer_id": reviewer_id,
                "primary_label_for_audit": primary_label,
                "secondary_label_for_audit": secondary_label,
            }
            resolutions[packet_id] = sign_row(
                resolutions[packet_id], "label", self.signing_private_key_path
            )
            ordered = [resolutions[key] for key in self._template_rows[task] if key in resolutions]
            _atomic_write_json(
                self._resolution_path(task),
                {
                    "schema_version": "p34_human_label_resolutions_v1",
                    "task_type": task,
                    "annotator_id": "adjudicator",
                    "labels": ordered,
                },
            )
            workspace = self._adjudication_workspace(task)
        return {
            "saved": True,
            "completed": workspace["progress"]["completed"],
            "total": workspace["progress"]["total"],
            "output_path": str(self._resolution_path(task)),
        }

    def _load_anchor_rows(self, annotator: str) -> Dict[str, Dict[str, Any]]:
        path = self._anchor_path(annotator)
        if not path.exists():
            return {
                paper_id: {
                    **dict(template),
                    "human_reviewer_id": self._registered_reviewer_id(annotator) or (annotator if not self.require_annotator_identity else ""),
                }
                for paper_id, template in self._anchor_rows.items()
            }
        value = _load_json(path)
        saved = {str(item.get("paper_id") or ""): item for item in value.get("cases", []) if item.get("paper_id")}
        return {
            paper_id: {
                **dict(template),
                **{
                    key: value
                    for key, value in dict(saved.get(paper_id, {})).items()
                    if not key.startswith("machine_")
                },
                "human_reviewer_id": str(
                    dict(saved.get(paper_id, {})).get("human_reviewer_id")
                    or self._registered_reviewer_id(annotator)
                    or (annotator if not self.require_annotator_identity else "")
                ),
            }
            for paper_id, template in self._anchor_rows.items()
        }

    def anchor_workspace(self, annotator: str) -> Dict[str, Any]:
        if annotator not in LABEL_ANNOTATORS:
            raise ValueError("unsupported annotator")
        with self._lock:
            rows = self._load_anchor_rows(annotator)
            items = [rows[paper_id] for paper_id in self._anchor_rows]
            completed = sum(bool(item.get("human_review_complete")) for item in items)
            return {
                "task": "paper_index",
                "annotator": annotator,
                "identity_required": self.require_annotator_identity,
                "reviewer_id": self._registered_reviewer_id(annotator),
                "items": items,
                "progress": {"completed": completed, "total": len(items)},
                "output_path": str(self._anchor_path(annotator)),
            }

    def export_anchor_bundle(self, annotator: str, auth_token: Any = "") -> Dict[str, Any]:
        if annotator not in LABEL_ANNOTATORS:
            raise ValueError("unsupported PaperIndex annotator")
        reviewer_id = self._registered_reviewer_id(annotator)
        reviewer_id = self._validate_reviewer(annotator, reviewer_id or annotator, auth_token)
        workspace = self.anchor_workspace(annotator)
        immutable_items = []
        cases = []
        for item in workspace["items"]:
            paper_id = str(item.get("paper_id") or "")
            immutable_items.append({
                "paper_id": paper_id,
                "paper_text": str(self.paper_texts.get(paper_id) or ""),
                "machine_boundary_suggestions": list(item.get("machine_boundary_suggestions") or []),
                "machine_anchor_suggestions": list(item.get("machine_anchor_suggestions") or []),
                "machine_false_boundary_suggestions": list(item.get("machine_false_boundary_suggestions") or []),
            })
            cases.append({
                "paper_id": paper_id,
                "expected_boundaries": list(item.get("expected_boundaries") or []),
                "key_anchors": list(item.get("key_anchors") or []),
                "false_boundaries": list(item.get("false_boundaries") or []),
                "human_review_complete": bool(item.get("human_review_complete")),
                "human_review_notes": str(item.get("human_review_notes") or ""),
            })
        contract = {
            "schema_version": "p34_paper_index_exchange_v1",
            "task_type": "paper_index",
            "annotator_role": annotator,
            "reviewer_id": reviewer_id,
            "anchor_template_sha256": _canonical_sha256(self.anchor_template),
            "case_state_sha256": _canonical_sha256(cases),
            "items": immutable_items,
        }
        return {
            **contract,
            "bundle_sha256": _canonical_sha256(contract),
            "boundary": "Role-isolated PaperIndex audit packet with exact paper text; edit only cases",
            "cases": cases,
        }

    def import_anchor_bundle(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        if str(payload.get("schema_version") or "") != "p34_paper_index_exchange_v1":
            raise ValueError("unsupported PaperIndex exchange schema")
        annotator = str(payload.get("annotator_role") or "")
        reviewer_id = self._validate_reviewer(
            annotator, payload.get("reviewer_id"), payload.get("auth_token")
        )
        current = self.export_anchor_bundle(annotator, payload.get("auth_token"))
        if str(payload.get("bundle_sha256") or "") != current["bundle_sha256"]:
            raise ValueError("PaperIndex bundle is stale or does not match the current anchor template")
        cases = payload.get("cases")
        if not isinstance(cases, list):
            raise ValueError("PaperIndex bundle cases must be a list")
        expected_ids = [str(item.get("paper_id") or "") for item in current["cases"]]
        received_ids = [str(item.get("paper_id") or "") for item in cases if isinstance(item, dict)]
        if len(cases) != len(received_ids) or len(received_ids) != len(set(received_ids)):
            raise ValueError("PaperIndex bundle contains malformed or duplicate cases")
        if set(received_ids) != set(expected_ids):
            raise ValueError("PaperIndex bundle paper ids do not match the exported workspace")
        result = self.save_anchor_batch(annotator, reviewer_id, payload.get("auth_token"), cases)
        return {**result, "bundle_sha256": current["bundle_sha256"]}

    @staticmethod
    def _clean_anchor_items(value: Any, allowed_fields: set[str], max_items: int) -> List[Dict[str, Any]]:
        if not isinstance(value, list):
            raise ValueError("anchor collections must be lists")
        cleaned = []
        for item in value[:max_items]:
            if not isinstance(item, dict):
                continue
            cleaned.append({key: item[key] for key in allowed_fields if key in item})
        return cleaned

    @staticmethod
    def _valid_boundary(item: Mapping[str, Any]) -> bool:
        start = item.get("source_span_start")
        return (
            bool(str(item.get("heading") or "").strip())
            and bool(str(item.get("section_type") or "").strip())
            and isinstance(start, int)
            and not isinstance(start, bool)
            and start >= 0
        )

    @staticmethod
    def _valid_anchor(item: Mapping[str, Any]) -> bool:
        start, end = item.get("source_span_start"), item.get("source_span_end")
        return (
            bool(str(item.get("query") or "").strip())
            and bool(str(item.get("text") or "").strip())
            and isinstance(start, int)
            and not isinstance(start, bool)
            and isinstance(end, int)
            and not isinstance(end, bool)
            and 0 <= start < end
        )

    @staticmethod
    def _valid_false_boundary(item: Mapping[str, Any]) -> bool:
        start = item.get("source_span_start")
        return (
            bool(str(item.get("heading") or "").strip())
            and bool(str(item.get("reason") or "").strip())
            and isinstance(start, int)
            and not isinstance(start, bool)
            and start >= 0
        )

    @staticmethod
    def _heading_matches_source(item: Mapping[str, Any], paper_text: str) -> bool:
        start = int(item.get("source_span_start") or 0)
        heading = " ".join(str(item.get("heading") or "").lower().split())
        if not heading or start < 0 or start >= len(paper_text):
            return False
        window = " ".join(paper_text[start : min(len(paper_text), start + 400)].lower().split())
        return heading in window

    @staticmethod
    def _anchor_matches_source(item: Mapping[str, Any], paper_text: str) -> bool:
        start, end = int(item.get("source_span_start") or 0), int(item.get("source_span_end") or 0)
        return 0 <= start < end <= len(paper_text) and paper_text[start:end] == str(item.get("text") or "")

    def _prepare_anchor_case(self, payload: Mapping[str, Any]) -> tuple[str, Dict[str, Any]]:
        paper_id = str(payload.get("paper_id") or "")
        if paper_id not in self._anchor_rows:
            raise ValueError("unsupported PaperIndex paper_id")
        boundaries = self._clean_anchor_items(
            payload.get("expected_boundaries"), {"heading", "section_type", "source_span_start"}, 16
        )
        anchors = self._clean_anchor_items(
            payload.get("key_anchors"),
            {"query", "text", "section_types", "artifact_type", "source_span_start", "source_span_end"},
            16,
        )
        false_boundaries = self._clean_anchor_items(
            payload.get("false_boundaries"), {"heading", "section_type", "source_span_start", "reason"}, 16
        )
        complete = bool(payload.get("human_review_complete"))
        if complete and (not boundaries or not anchors):
            raise ValueError(f"completed anchor review requires at least one boundary and one anchor for {paper_id}")
        if complete and not all(self._valid_boundary(item) for item in boundaries):
            raise ValueError(f"completed anchor review contains an invalid boundary for {paper_id}")
        if complete and not all(self._valid_anchor(item) for item in anchors):
            raise ValueError(f"completed anchor review contains an invalid anchor for {paper_id}")
        if complete and not all(self._valid_false_boundary(item) for item in false_boundaries):
            raise ValueError(f"completed anchor review contains an invalid false boundary for {paper_id}")
        paper_text = self.paper_texts.get(paper_id, "")
        if complete and paper_text:
            if not all(self._heading_matches_source(item, paper_text) for item in boundaries):
                raise ValueError(f"completed anchor review boundary does not match paper source for {paper_id}")
            if not all(self._anchor_matches_source(item, paper_text) for item in anchors):
                raise ValueError(f"completed anchor review anchor does not match paper source for {paper_id}")
            if not all(self._heading_matches_source(item, paper_text) for item in false_boundaries):
                raise ValueError(f"completed anchor review false boundary does not match paper source for {paper_id}")
        return paper_id, {
            "expected_boundaries": boundaries,
            "key_anchors": anchors,
            "false_boundaries": false_boundaries,
            "human_review_complete": complete,
            "human_review_notes": " ".join(str(payload.get("human_review_notes") or "").split())[:1200],
        }

    def _write_anchor_rows(self, annotator: str, rows: Mapping[str, Mapping[str, Any]]) -> None:
        _atomic_write_json(
            self._anchor_path(annotator),
            {
                "schema_version": self.anchor_template.get("schema_version", "p34_paper_index_human_anchors_v1"),
                "dataset_sha256": self.anchor_template.get("dataset_sha256", ""),
                "machine_suggestions_are_not_labels": True,
                "annotator_id": annotator,
                "cases": [dict(rows[item_id]) for item_id in self._anchor_rows],
            },
        )

    def save_anchor_batch(
        self,
        annotator: str,
        reviewer_id: str,
        auth_token: Any,
        cases: List[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        if annotator not in LABEL_ANNOTATORS:
            raise ValueError("unsupported PaperIndex annotator")
        reviewer_id = self._validate_reviewer(annotator, reviewer_id, auth_token)
        prepared = []
        seen = set()
        for case in cases:
            paper_id, values = self._prepare_anchor_case(case)
            if paper_id in seen:
                raise ValueError("PaperIndex batch requires unique paper ids")
            seen.add(paper_id)
            prepared.append((paper_id, values))
        with self._lock:
            rows = self._load_anchor_rows(annotator)
            for paper_id, values in prepared:
                rows[paper_id].update({
                    **values, "annotator_id": annotator, "human_reviewer_id": reviewer_id,
                })
                rows[paper_id] = sign_row(rows[paper_id], "anchor", self.signing_private_key_path)
            self._write_anchor_rows(annotator, rows)
            completed = sum(bool(item.get("human_review_complete")) for item in rows.values())
        return {
            "saved": True,
            "imported_count": len(prepared),
            "completed": completed,
            "total": len(rows),
            "output_path": str(self._anchor_path(annotator)),
        }

    def save_anchor_case(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        annotator = str(payload.get("annotator") or "")
        if annotator not in LABEL_ANNOTATORS:
            raise ValueError("unsupported PaperIndex annotator")
        reviewer_id = self._validate_reviewer(
            annotator, payload.get("reviewer_id"), payload.get("auth_token")
        )
        paper_id, values = self._prepare_anchor_case(payload)
        with self._lock:
            rows = self._load_anchor_rows(annotator)
            rows[paper_id].update({
                **values, "annotator_id": annotator, "human_reviewer_id": reviewer_id,
            })
            rows[paper_id] = sign_row(rows[paper_id], "anchor", self.signing_private_key_path)
            self._write_anchor_rows(annotator, rows)
            completed = sum(bool(item.get("human_review_complete")) for item in rows.values())
        return {"saved": True, "completed": completed, "total": len(rows), "output_path": str(self._anchor_path(annotator))}


def make_handler(
    store: AnnotationStore,
    html_path: Path,
    portable_html_path: Path,
    portable_paper_index_path: Path,
):
    class Handler(BaseHTTPRequestHandler):
        server_version = "P34Annotation/1.0"

        def log_message(self, format: str, *args: Any) -> None:
            print(f"[annotation] {self.address_string()} {format % args}")

        def _json(self, value: Mapping[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _error(self, exc: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
            self._json({"error": str(exc), "error_type": type(exc).__name__}, status)

        def _binary(self, body: bytes, content_type: str, filename: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                body = html_path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/api/workspace":
                try:
                    query = parse_qs(parsed.query)
                    task = str(query.get("task", ["evidence_relation"])[0])
                    annotator = str(query.get("annotator", ["primary"])[0])
                    result = store.anchor_workspace(annotator) if task == "paper_index" else store.label_workspace(task, annotator)
                    self._json(result)
                except Exception as exc:
                    self._error(exc)
                return
            if parsed.path == "/api/gates":
                try:
                    self._json(store.gate_status())
                except Exception as exc:
                    self._error(exc)
                return
            if parsed.path == "/api/quality":
                try:
                    self._json(store.quality_status())
                except Exception as exc:
                    self._error(exc)
                return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 2_000_000:
                    raise ValueError("invalid request body size")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("request body must be an object")
                if self.path == "/api/label":
                    self._json(store.save_label(payload))
                    return
                if self.path == "/api/register-annotator":
                    self._json(store.register_annotator(str(payload.get("role") or ""), payload.get("reviewer_id")))
                    return
                if self.path == "/api/verify-annotator":
                    self._json(store.verify_annotator(
                        str(payload.get("role") or ""), payload.get("reviewer_id"), payload.get("auth_token")
                    ))
                    return
                if self.path == "/api/rotate-annotator":
                    self._json(store.rotate_annotator(
                        str(payload.get("role") or ""), payload.get("reviewer_id"), payload.get("auth_token")
                    ))
                    return
                if self.path == "/api/recover-annotator":
                    self._json(store.recover_annotator(
                        str(payload.get("role") or ""), payload.get("reviewer_id"), payload.get("recovery_code")
                    ))
                    return
                if self.path == "/api/export-bundle":
                    task = str(payload.get("task") or "")
                    if task == "paper_index":
                        self._json(store.export_anchor_bundle(
                            str(payload.get("annotator") or ""), payload.get("auth_token")
                        ))
                    else:
                        self._json(store.export_label_bundle(
                            task, str(payload.get("annotator") or ""), payload.get("auth_token")
                        ))
                    return
                if self.path == "/api/export-portable":
                    task = str(payload.get("task") or "")
                    bundle = (
                        store.export_anchor_bundle(str(payload.get("annotator") or ""), payload.get("auth_token"))
                        if task == "paper_index"
                        else store.export_label_bundle(
                            task, str(payload.get("annotator") or ""), payload.get("auth_token")
                        )
                    )
                    portable_path = portable_paper_index_path if task == "paper_index" else portable_html_path
                    self._json({
                        "bundle_sha256": bundle["bundle_sha256"],
                        "filename": (
                            f"p34_{bundle['task_type']}_{bundle['annotator_role']}_"
                            f"{bundle['bundle_sha256'][:12]}.html"
                        ),
                        "html": _render_portable_bundle(portable_path, bundle),
                    })
                    return
                if self.path == "/api/export-role-package":
                    filename, content, _manifest = _build_role_package(
                        store,
                        str(payload.get("annotator") or ""),
                        payload.get("auth_token"),
                        portable_html_path,
                        portable_paper_index_path,
                    )
                    self._binary(content, "application/zip", filename)
                    return
                if self.path == "/api/import-bundle":
                    if str(payload.get("schema_version") or "") == "p34_paper_index_exchange_v1":
                        self._json(store.import_anchor_bundle(payload))
                    else:
                        self._json(store.import_label_bundle(payload))
                    return
                if self.path == "/api/anchor-case":
                    self._json(store.save_anchor_case(payload))
                    return
                if self.path == "/api/refresh-gates":
                    self._json(store.refresh_gate_status())
                    return
                if self.path == "/api/reload-discovery":
                    self._json(store.reload_issue_artifacts())
                    return
                if self.path == "/api/reload-assignment":
                    self._json(store.reload_assignment())
                    return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._error(exc)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_PACKETS.jsonl")
    parser.add_argument("--positive-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_POSITIVE_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--claim-template", default="P34_2_JUDGE_DATASET_HARDNEG20_20260711_CLAIM_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--issue-template", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_HUMAN_AUDIT_TEMPLATE.json")
    parser.add_argument("--issue-packets", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_PACKETS.jsonl")
    parser.add_argument("--issue-provenance", default="P34_2_SYMMETRIC_DISCOVERY_ACTIVE_20260711_DISCOVERY_PROVENANCE.json")
    parser.add_argument("--assignment", default="P34_ANNOTATION_ASSIGNMENT_20260711.json")
    parser.add_argument("--paper-dataset", default="hard_negative_20_20260611.parquet")
    parser.add_argument("--allow-role-only-identity", action="store_true")
    parser.add_argument("--anchors", default="P34_1_PAPER_INDEX_HUMAN_ANCHORS_HARDNEG20_TEMPLATE_20260711.json")
    parser.add_argument("--output-dir", default="P34_ANNOTATIONS_20260711")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    store = AnnotationStore(
        packets_path=Path(args.packets),
        positive_template_path=Path(args.positive_template),
        claim_template_path=Path(args.claim_template),
        issue_template_path=Path(args.issue_template) if args.issue_template else None,
        issue_packets_path=Path(args.issue_packets) if args.issue_packets else None,
        issue_provenance_path=Path(args.issue_provenance) if args.issue_provenance else None,
        assignment_path=Path(args.assignment) if args.assignment else None,
        paper_texts=_load_paper_texts(Path(args.paper_dataset)) if args.paper_dataset else None,
        require_annotator_identity=not args.allow_role_only_identity,
        anchors_path=Path(args.anchors),
        output_dir=Path(args.output_dir),
        repo=Path.cwd(),
    )
    html_path = Path(__file__).with_name("p34_annotation_app.html")
    portable_html_path = Path(__file__).with_name("p34_portable_annotation.html")
    portable_paper_index_path = Path(__file__).with_name("p34_portable_paper_index.html")
    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(store, html_path, portable_html_path, portable_paper_index_path),
    )
    print(json.dumps({"status": "READY", "url": f"http://{args.host}:{args.port}", "output_dir": str(store.output_dir)}, ensure_ascii=False))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
