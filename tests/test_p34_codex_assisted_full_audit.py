from scripts.p34_codex_assisted_full_audit import _evidence_disagreement_label


def test_local_evidence_disagreement_is_conservative():
    assert _evidence_disagreement_label("supports", "uncertain") == "uncertain"
    assert _evidence_disagreement_label("partially_supports", "uncertain") == "partially_supports"
    assert _evidence_disagreement_label("unrelated", "supports") == "unrelated"
    assert _evidence_disagreement_label("contradicts", "supports") == "contradicts"
