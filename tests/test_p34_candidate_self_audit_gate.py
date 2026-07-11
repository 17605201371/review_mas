"""Tests for the P34 candidate self-audit gate v2.

Covers the cross-audit checklist (GPT 2026-07-11): enrich must not delete;
strict must emit a filtered set; window quotes must round-trip exactly against
raw paper text; missing required self-audit fields under the forward contract;
paper-id case-insensitive join; empty paper text; duplicate packets; label
join completeness.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import p34_candidate_self_audit_gate as G


PAPER = (
    "Introduction. We propose FooNet with a gating module. "
    "Section 4. Ablation study: we remove the gating module and accuracy drops by 2.1 points, "
    "see Table 3 for the component-wise comparison. "
    "We report standard deviation over 5 seeds in Table 4."
)


def _packet(**kw):
    base = {
        "packet_id": "discovery-PaperX-0001",
        "paper_id": "PaperX",
        "task_type": "review_issue",
        "issue_hypothesis": {
            "issue_type": "missing_ablation",
            "paper_anchor": "We propose FooNet with a gating module",
            "claim_anchor": "FooNet's gating module is key to performance",
            "hypothesis": "No ablation isolates the gating module contribution.",
            "named_entities_or_metrics": ["gating module", "Table 3"],
        },
        "verification_contract": {"issue_type": "missing_ablation"},
    }
    base.update(kw)
    return base


def _rows():
    return [{"paper_id": "PaperX", "review_state": {"paper_id": "PaperX", "paper_text": PAPER}}]


def test_enrich_mode_never_drops():
    r = G.audit_packet(_packet(), PAPER, strict=False)
    assert r["gate"].startswith(("pass", "flag_")), r["gate"]
    # counterevidence window found (ablation exists in paper) -> flag, kept
    assert r["gate"] == "flag_counterevidence_window"
    assert r["checks"]["counterevidence_window_count"] >= 1


def test_strict_mode_drops_counterevidence():
    r = G.audit_packet(_packet(), PAPER, strict=True)
    assert r["gate"] == "drop_paper_counterevidence"


def test_window_quote_roundtrips_exactly():
    r = G.audit_packet(_packet(), PAPER, strict=False)
    for w in r["counterevidence_windows"]:
        assert PAPER[w["source_span_start"]:w["source_span_end"]] == w["quote"]
        assert w["matched_marker"]
        assert w["entity"]
        assert w["evidence_id"] and w["evidence_id"].startswith("ce-window-")
        assert w["match_type"] == "exact_span_raw_slice"


def test_windows_citable_in_judge_id_contract(tmp_path):
    """P0 (GPT 2026-07-11): enriched windows must be legally citable by the Judge,
    i.e. appear in counterevidence_candidates with evidence_id and their
    section_id merged into searched_section_ids."""
    emitted, _ = _run_cli(str(tmp_path), "enrich", [_packet()])
    packet = emitted[0]
    cand_ids = {c.get("evidence_id") for c in packet.get("counterevidence_candidates", [])}
    window_ids = {w["evidence_id"] for w in packet.get("counterevidence_windows", [])}
    assert window_ids and window_ids <= cand_ids, "windows must be in counterevidence_candidates"
    searched = set(packet.get("searched_section_ids", []))
    for w in packet["counterevidence_windows"]:
        if w.get("section_id"):
            assert w["section_id"] in searched, "window section_id must be in searched_section_ids"


def test_full_sha256_not_prefix(tmp_path):
    emitted, _ = _run_cli(str(tmp_path), "enrich", [_packet()])
    for w in emitted[0].get("counterevidence_windows", []):
        assert len(w["paper_text_sha256"]) == 64  # full digest, not a 16-char prefix


def test_missing_self_audit_fields_invalid_under_forward_contract():
    r = G.audit_packet(_packet(), PAPER, require_self_audit_fields=True)
    assert r["gate"] == "invalid_missing_self_audit_fields"
    assert set(r["checks"]["self_audit_fields_missing"]) == {
        "searched_sections", "absence_check_terms", "confidence"}


def test_self_audit_fields_present_passes_forward_contract():
    p = _packet()
    p["issue_hypothesis"].update({
        "searched_sections": ["section-0001"],
        "absence_check_terms": ["gating module ablation"],
        "confidence": 0.8,
    })
    r = G.audit_packet(p, PAPER, require_self_audit_fields=True)
    assert r["gate"] != "invalid_missing_self_audit_fields"


def test_paper_id_join_is_case_insensitive():
    texts = G.paper_text_by_lower_id(_rows())
    assert texts.get("paperx") == PAPER
    assert "PaperX" not in texts  # keys are lowercase by contract


def test_empty_paper_text_flags_anchor():
    r = G.audit_packet(_packet(), "", strict=False)
    assert r["gate"] == "flag_anchor_unlocatable"
    assert r["checks"]["counterevidence_window_count"] == 0


def test_confidence_missing_is_flagged_not_failed():
    r = G.audit_packet(_packet(), PAPER)
    assert r["checks"]["confidence_missing"] is True
    assert r["checks"]["confidence_ok"] is True  # legacy tolerance


def test_low_confidence_flagged():
    p = _packet()
    p["issue_hypothesis"]["confidence"] = 0.2
    p["issue_hypothesis"]["issue_type"] = "scope_overclaim"  # non-absence: no window path
    p["verification_contract"]["issue_type"] = "scope_overclaim"
    r = G.audit_packet(p, PAPER)
    assert r["gate"] == "flag_low_confidence"


def _run_cli(tmpdir, mode, packets, require_fields=False):
    packets_path = os.path.join(tmpdir, "packets.jsonl")
    rows_path = os.path.join(tmpdir, "rows.jsonl")
    out_json = os.path.join(tmpdir, "out.json")
    out_packets = os.path.join(tmpdir, "out_packets.jsonl")
    out_dropped = os.path.join(tmpdir, "dropped.jsonl")
    with open(packets_path, "w") as fh:
        for p in packets:
            fh.write(json.dumps(p) + "\n")
    with open(rows_path, "w") as fh:
        for row in _rows():
            fh.write(json.dumps(row) + "\n")
    argv = [
        "--packets-jsonl", packets_path, "--input-jsonl", rows_path,
        "--out-json", out_json, "--out-packets-jsonl", out_packets,
        "--out-dropped-jsonl", out_dropped, "--mode", mode,
    ]
    if require_fields:
        argv.append("--require-self-audit-fields")
    G.main(argv)
    with open(out_packets) as fh:
        emitted = [json.loads(l) for l in fh if l.strip()]
    with open(out_dropped) as fh:
        dropped = [json.loads(l) for l in fh if l.strip()]
    return emitted, dropped


def test_cli_enrich_emits_all_packets_with_self_audit(tmp_path):
    packets = [_packet(), _packet(packet_id="discovery-PaperX-0002")]
    emitted, dropped = _run_cli(str(tmp_path), "enrich", packets)
    assert len(emitted) == 2 and not dropped
    for p in emitted:
        assert "self_audit" in p
        assert p["self_audit"]["gate"].startswith(("pass", "flag_"))


def test_cli_strict_emits_filtered_set_and_dropped_manifest(tmp_path):
    packets = [_packet()]  # counterevidence exists -> dropped in strict
    emitted, dropped = _run_cli(str(tmp_path), "strict", packets)
    assert len(emitted) == 0
    assert len(dropped) == 1 and dropped[0]["gate"] == "drop_paper_counterevidence"


def test_duplicate_packet_ids_both_audited(tmp_path):
    packets = [_packet(), _packet()]  # identical ids
    emitted, _ = _run_cli(str(tmp_path), "enrich", packets)
    assert len(emitted) == 2  # gate audits rows independently; dedup is step-② concern


def test_label_join_completeness_counted(tmp_path):
    labels = {"papers": [{"tasks": {"review_issue": [
        {"packet_id": "discovery-PaperX-0001", "label": "B"}]}}]}
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(json.dumps(labels))
    packets_path = tmp_path / "p.jsonl"
    rows_path = tmp_path / "r.jsonl"
    packets_path.write_text(json.dumps(_packet()) + "\n" +
                            json.dumps(_packet(packet_id="discovery-PaperX-0009")) + "\n")
    rows_path.write_text(json.dumps(_rows()[0]) + "\n")
    out_json = tmp_path / "out.json"
    G.main(["--packets-jsonl", str(packets_path), "--input-jsonl", str(rows_path),
            "--labels-json", str(labels_path), "--out-json", str(out_json)])
    report = json.loads(out_json.read_text())
    ev = report["summary"]["evaluation"]
    assert ev["label_join_missing"] == 1  # 0009 has no label
    assert "B" in ev["label_gate_matrix"]


def test_enrich_with_require_fields_blocks_invalid_not_emit(tmp_path):
    """P0 (GPT 2026-07-11): enrich + require-self-audit-fields must NOT emit the
    invalid packet to the Judge; it goes to the dropped/invalid manifest only."""
    emitted, dropped = _run_cli(str(tmp_path), "enrich", [_packet()], require_fields=True)
    assert emitted == [], "contract-invalid packets must not reach the Judge"
    assert len(dropped) == 1
    assert dropped[0]["gate"] == "invalid_missing_self_audit_fields"


def test_enrich_with_require_fields_emits_valid(tmp_path):
    p = _packet()
    p["issue_hypothesis"].update({
        "searched_sections": ["section-0001"],
        "absence_check_terms": ["gating module ablation"],
        "confidence": 0.8,
    })
    emitted, dropped = _run_cli(str(tmp_path), "enrich", [p], require_fields=True)
    assert len(emitted) == 1 and not dropped


if __name__ == "__main__":
    import tempfile
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                import pathlib
                with tempfile.TemporaryDirectory() as td:
                    fn(pathlib.Path(td))
            else:
                fn()
            print(f"✓ {name}")
            passed += 1
    print(f"\n{passed} tests passed")
