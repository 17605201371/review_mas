from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalize_patch_source(value: Any) -> str:
    raw = str(value or "").strip()
    if raw == "salvaged":
        return "system_salvaged"
    if raw in {"model_generated", "system_salvaged"}:
        return raw
    return "none"


def group_map(meta: Dict[str, Any]) -> Dict[str, str]:
    ids = list(meta.get("ids", []))
    mapping: Dict[str, str] = {}
    for idx, paper_id in enumerate(ids):
        if idx < 4:
            mapping[paper_id] = "canonical_success_sensitive"
        elif idx < 7:
            mapping[paper_id] = "hardest_drift_prone"
        else:
            mapping[paper_id] = "recovery_support"
    return mapping


def row_summary(row: Dict[str, Any], bucket: str) -> Dict[str, Any]:
    turns = list(row.get("turn_logs", []))
    target_switch_count = 0
    last_targets = None
    sticky_applied_count = 0
    sticky_reused_count = 0
    sticky_released_count = 0
    sticky_release_reasons: Dict[str, int] = {}
    patch_emitted_count = 0
    patch_committed_count = 0
    model_generated_commit_count = 0
    system_salvaged_commit_count = 0
    failure_counts: Dict[str, int] = {}
    for turn in turns:
        target_sig = (
            tuple(turn.get("target_claim_ids", []) or []),
            tuple(turn.get("target_flaw_ids", []) or []),
            tuple(turn.get("target_evidence_ids", []) or []),
            tuple(turn.get("target_hypotheses", []) or []),
        )
        if any(target_sig):
            if last_targets is not None and target_sig != last_targets:
                target_switch_count += 1
            last_targets = target_sig
        if bool(turn.get("sticky_target_applied", False)):
            sticky_applied_count += 1
        if bool(turn.get("sticky_target_reused", False)):
            sticky_reused_count += 1
        if bool(turn.get("sticky_target_released", False)):
            sticky_released_count += 1
        reason = str(turn.get("sticky_release_reason") or "").strip()
        if reason:
            sticky_release_reasons[reason] = sticky_release_reasons.get(reason, 0) + 1
        if bool(turn.get("recovery_patch_emitted", turn.get("recovery_emitted", False))):
            patch_emitted_count += 1
        if bool(turn.get("recovery_patch_committed", turn.get("recovery_committed", False))):
            patch_committed_count += 1
            source = normalize_patch_source(turn.get("recovery_patch_source"))
            if source == "model_generated":
                model_generated_commit_count += 1
            elif source == "system_salvaged":
                system_salvaged_commit_count += 1
        code = str(turn.get("recovery_failure_code") or "").strip()
        if code:
            failure_counts[code] = failure_counts.get(code, 0) + 1

    return {
        "paper_id": row.get("paper_id", ""),
        "bucket": bucket,
        "reward": float(row.get("reward", 0.0) or 0.0),
        "decision_correct": float(row.get("decision_correct", 0.0) or 0.0),
        "target_switch_count": target_switch_count,
        "sticky_target_applied_count": sticky_applied_count,
        "sticky_target_reused_count": sticky_reused_count,
        "sticky_target_released_count": sticky_released_count,
        "sticky_release_reasons": sticky_release_reasons,
        "rows_with_any_commit": int(patch_committed_count > 0),
        "patch_emitted_count": patch_emitted_count,
        "patch_committed_count": patch_committed_count,
        "model_generated_commit_count": model_generated_commit_count,
        "system_salvaged_commit_count": system_salvaged_commit_count,
        "NO_EFFECT_PATCH": failure_counts.get("NO_EFFECT_PATCH", 0),
        "BLOCKED_BY_POLICY": failure_counts.get("BLOCKED_BY_POLICY", 0),
        "top_failure": max(failure_counts.items(), key=lambda item: item[1])[0] if failure_counts else "none",
        "sticky_fields_present": any("sticky_target_id" in turn for turn in turns),
        "sticky_triggered": sticky_applied_count > 0,
        "stuck_warning": bool(turns and turns[-1].get("phase_after_action") == "recovery"),
    }


def aggregate(rows: List[Dict[str, Any]], groups: Dict[str, str]) -> Dict[str, Any]:
    summaries = [row_summary(row, groups.get(row.get("paper_id", ""), "unknown")) for row in rows]
    release_counts: Dict[str, int] = {}
    for item in summaries:
        for code, count in item["sticky_release_reasons"].items():
            release_counts[code] = release_counts.get(code, 0) + count
    applied = sum(item["sticky_target_applied_count"] for item in summaries)
    reused = sum(item["sticky_target_reused_count"] for item in summaries)
    return {
        "rows": len(summaries),
        "summaries": summaries,
        "target_switch_count": sum(item["target_switch_count"] for item in summaries),
        "sticky_target_applied_count": applied,
        "sticky_target_reuse_rate": round(reused / max(applied, 1), 4),
        "sticky_target_reused_count": reused,
        "sticky_target_released_count": sum(item["sticky_target_released_count"] for item in summaries),
        "sticky_release_reasons": release_counts,
        "patch_emitted_count": sum(item["patch_emitted_count"] for item in summaries),
        "patch_committed_count": sum(item["patch_committed_count"] for item in summaries),
        "rows_with_any_commit": sum(item["rows_with_any_commit"] for item in summaries),
        "NO_EFFECT_PATCH": sum(item["NO_EFFECT_PATCH"] for item in summaries),
        "BLOCKED_BY_POLICY": sum(item["BLOCKED_BY_POLICY"] for item in summaries),
        "model_generated_commit_count": sum(item["model_generated_commit_count"] for item in summaries),
        "system_salvaged_commit_count": sum(item["system_salvaged_commit_count"] for item in summaries),
        "avg_reward": round(sum(item["reward"] for item in summaries) / max(len(summaries), 1), 4),
        "decision_correct_rate": round(sum(item["decision_correct"] for item in summaries) / max(len(summaries), 1), 4),
        "sticky_fields_present_on_all_rows": all(item["sticky_fields_present"] for item in summaries),
        "sticky_triggered_rows": sum(1 for item in summaries if item["sticky_triggered"]),
        "stuck_warning_rows": sum(1 for item in summaries if item["stuck_warning"]),
    }


def find_row(summaries: Sequence[Dict[str, Any]], paper_id: str) -> Dict[str, Any]:
    for item in summaries:
        if item["paper_id"] == paper_id:
            return item
    return {"paper_id": paper_id, "target_switch_count": 0, "sticky_target_applied_count": 0, "patch_emitted_count": 0, "patch_committed_count": 0, "rows_with_any_commit": 0, "top_failure": "missing", "reward": 0.0}


def write_subset_doc(root: Path, meta: Dict[str, Any], groups: Dict[str, str]) -> None:
    lines = [
        '# P25.1 Iteration Subset',
        '',
        '- fixed_subset: `outputs/results_main/review_infer/p25_1_iteration_subset.parquet`',
        '- fixed_count: 10',
        '- note: target sticky round reuses the exact same subset as the retained explicit recovery-phase baseline.',
        '',
        '## Fixed Cases',
    ]
    reasons = meta.get('reasons', {})
    for paper_id in meta.get('ids', []):
        lines.append(f"- `{paper_id}` [{groups.get(paper_id, 'unknown')}]: {reasons.get(paper_id, '')}")
    root.joinpath('P25_1_ITERATION_SUBSET.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_protocol_doc(root: Path) -> None:
    lines = [
        '# Target Sticky Protocol V2',
        '',
        '## Scope',
        '- This round only changes the sticky insertion point, moving target control into manager policy fallback before target sanitize.',
        '- Manager architecture, validator/lifecycle, reward, salvage behavior, blocked calibration, and benchmark scope stay frozen.',
        '',
        '## Control Point',
        '- Sticky now acts inside `review_manager_policy.apply_manager_policy_fallback()` after `payload["target_claim_ids"]` is formed and before `_sanitize_targets_for_action()` runs.',
        '- The rule only applies to claim targets in recovery-oriented turns and reuses the active sticky target when no stronger grounded contradiction points to a new claim.',
        '- Sticky state persistence stays in `ReviewState`; only the insertion point changes.',
        '- Turn-log event fields are split: persistent sticky fields come from state, while `sticky_target_applied / reused / released / target_switch_blocked_by_sticky` come from the current payload.',
        '',
        '## Sticky Rules',
        '- Only claim-level sticky is supported.',
        '- One active sticky target may be reused across the next recovery continuation turn through `sticky_target_turns_remaining`.',
        '',
        '## Release Conditions',
        '- `patch_committed`',
        '- `blocked_terminal`',
        '- `stronger_counterevidence`',
        '- `target_unresolvable`',
        '- `phase_exit`',
        '- `forced_release`',
    ]
    root.joinpath('TARGET_STICKY_PROTOCOL_V2.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_sanity_doc(root: Path, baseline: Dict[str, Any], sticky: Dict[str, Any], sticky_path: Path, sticky_log: Path) -> None:
    lines = [
        '# P25.1 Target Sticky V2 Sanity',
        '',
        '## Runtime Artifacts',
        '- current retained baseline jsonl: `outputs/results_main/review_infer/p25_1_iter_recovery_phase_v1.jsonl`',
        f'- target sticky v2 jsonl: `{sticky_path}`',
        f'- target sticky v2 log: `{sticky_log}`',
        '',
        '## Field Presence',
        f"- sticky fields present on all sticky rows: {sticky['sticky_fields_present_on_all_rows']}",
        f"- sticky triggered rows: {sticky['sticky_triggered_rows']}",
        f"- stuck warning rows: {sticky['stuck_warning_rows']}",
        '',
        '## Release Reasons',
    ]
    for key, value in sorted(sticky['sticky_release_reasons'].items()):
        lines.append(f'- {key}: {value}')
    if not sticky['sticky_release_reasons']:
        lines.append('- none')
    root.joinpath('P25_1_TARGET_STICKY_V2_SANITY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_compare_doc(root: Path, baseline: Dict[str, Any], sticky: Dict[str, Any], groups: Dict[str, str]) -> None:
    lines = [
        '# P25.1 Target Sticky V2 Compare',
        '',
        '## Aggregate Compare',
        '| Metric | Current retained baseline | Target sticky v2 |',
        '| --- | ---: | ---: |',
    ]
    for key in [
        'target_switch_count',
        'sticky_target_applied_count',
        'sticky_target_reuse_rate',
        'patch_emitted_count',
        'patch_committed_count',
        'rows_with_any_commit',
        'NO_EFFECT_PATCH',
        'BLOCKED_BY_POLICY',
        'model_generated_commit_count',
        'system_salvaged_commit_count',
        'avg_reward',
        'decision_correct_rate',
    ]:
        lines.append(f'| {key} | {baseline.get(key, 0)} | {sticky.get(key, 0)} |')
    lines.extend([
        '',
        '## Per-Case Snapshot',
        '| paper_id | bucket | baseline target switches | sticky target switches | sticky applied | baseline committed | sticky committed | baseline top failure | sticky top failure |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |',
    ])
    for paper_id in sorted(groups):
        left = find_row(baseline['summaries'], paper_id)
        right = find_row(sticky['summaries'], paper_id)
        lines.append(
            f"| {paper_id} | {groups.get(paper_id, 'unknown')} | {left['target_switch_count']} | {right['target_switch_count']} | {right['sticky_target_applied_count']} | {left['patch_committed_count']} | {right['patch_committed_count']} | {left['top_failure']} | {right['top_failure']} |"
        )
    root.joinpath('P25_1_TARGET_STICKY_V2_COMPARE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_decision_doc(root: Path, baseline: Dict[str, Any], sticky: Dict[str, Any], groups: Dict[str, str]) -> None:
    checks = {
        'target_switch_down': sticky['target_switch_count'] < baseline['target_switch_count'],
        'rows_with_any_commit_not_down': sticky['rows_with_any_commit'] >= baseline['rows_with_any_commit'],
        'patch_committed_not_down': sticky['patch_committed_count'] >= baseline['patch_committed_count'],
    }
    guard_checks = {
        'no_effect_not_worse': sticky['NO_EFFECT_PATCH'] <= baseline['NO_EFFECT_PATCH'],
        'no_stuck_warning': sticky['stuck_warning_rows'] == 0,
    }
    canonical_ids = [paper_id for paper_id, bucket in groups.items() if bucket == 'canonical_success_sensitive']
    canonical_regressions: List[str] = []
    for paper_id in canonical_ids:
        left = find_row(baseline['summaries'], paper_id)
        right = find_row(sticky['summaries'], paper_id)
        if right['patch_committed_count'] < left['patch_committed_count'] or right['reward'] + 0.05 < left['reward']:
            canonical_regressions.append(paper_id)
    guard_checks['canonical_not_large_regression'] = len(canonical_regressions) < 2
    keep = sum(1 for value in checks.values() if value) >= 2 and all(guard_checks.values())
    lines = [
        '# P25.1 Target Sticky V2 Decision',
        '',
        f"- decision: {'KEEP' if keep else 'ROLLBACK'}",
        '',
        '## Primary Checks',
    ]
    for key, value in checks.items():
        lines.append(f'- {key}: {value}')
    lines.extend(['', '## Guard Checks'])
    for key, value in guard_checks.items():
        lines.append(f'- {key}: {value}')
    lines.extend([
        '',
        '## Canonical Regression Watch',
        f"- flagged canonical ids: {', '.join(canonical_regressions) if canonical_regressions else 'none'}",
        '',
        '## Interpretation',
        f"- target_switch_count: baseline={baseline['target_switch_count']}, sticky_v2={sticky['target_switch_count']}",
        f"- patch_emitted_count: baseline={baseline['patch_emitted_count']}, sticky_v2={sticky['patch_emitted_count']}",
        f"- patch_committed_count: baseline={baseline['patch_committed_count']}, sticky_v2={sticky['patch_committed_count']}",
        f"- rows_with_any_commit: baseline={baseline['rows_with_any_commit']}, sticky_v2={sticky['rows_with_any_commit']}",
        f"- NO_EFFECT_PATCH: baseline={baseline['NO_EFFECT_PATCH']}, sticky_v2={sticky['NO_EFFECT_PATCH']}",
        f"- BLOCKED_BY_POLICY: baseline={baseline['BLOCKED_BY_POLICY']}, sticky_v2={sticky['BLOCKED_BY_POLICY']}",
        '',
        '## Next Step Gate',
        '- Only if this decision is KEEP should the next restrained iteration consider a lightweight manager rule.',
        '- If this decision is ROLLBACK, revert target sticky instead of stacking more control logic.',
    ])
    root.joinpath('P25_1_TARGET_STICKY_V2_DECISION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-jsonl', required=True)
    parser.add_argument('--sticky-jsonl', required=True)
    parser.add_argument('--subset-meta', required=True)
    parser.add_argument('--sticky-log', required=True)
    parser.add_argument('--docs-root', default='.')
    args = parser.parse_args()

    docs_root = Path(args.docs_root).resolve()
    meta = json.loads(Path(args.subset_meta).read_text())
    groups = group_map(meta)
    baseline = aggregate(load_jsonl(Path(args.baseline_jsonl)), groups)
    sticky = aggregate(load_jsonl(Path(args.sticky_jsonl)), groups)

    write_subset_doc(docs_root, meta, groups)
    write_protocol_doc(docs_root)
    write_sanity_doc(docs_root, baseline, sticky, Path(args.sticky_jsonl), Path(args.sticky_log))
    write_compare_doc(docs_root, baseline, sticky, groups)
    write_decision_doc(docs_root, baseline, sticky, groups)
    print(json.dumps({
        'baseline': {k: v for k, v in baseline.items() if k != 'summaries'},
        'sticky': {k: v for k, v in sticky.items() if k != 'summaries'},
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
