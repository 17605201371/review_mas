#!/usr/bin/env python3
"""Recovery layer distribution audit (4-layer taxonomy).

This script counts how many recovery turns reached each of the four
explicit layers introduced by ``_compute_recovery_layer_fields`` in
``agent_system/environments/env_package/review/state.py``:

  1. ``patch_validated``         — validator accepted the patch.
  2. ``patch_committed``         — validator wrote the patch to the per-turn
                                   recovery patch log.
  3. ``state_mutation_applied``  — committing the patch produced a real
                                   status-field transition in the
                                   ReviewState (the legacy
                                   ``recovery_success`` semantic).
  4. ``hygiene_delta_improved``  — a state mutation that materially reduces
                                   ReviewState inconsistency (currently
                                   identical to layer 3 because every
                                   ``COMMIT_TRANSITION`` is by construction
                                   inconsistency-reducing).

Why this script?  Earlier audits collapsed the four layers into a single
``recovery_committed`` counter, which mixed validator-level acceptance with
real state repair.  External reviews flagged this as a paper-level
statistics risk because a turn could log
``recovery_patch_committed=True`` while ``recovery_success=False``.  The
new fields (``recovery_layer*`` / ``recovery_effective_repair``) make the
distinction explicit, and this audit stratifies the per-turn outcomes
accordingly.

The script is backwards compatible with V16 turn logs (which were emitted
before the new fields were wired in): when the explicit fields are
missing, it derives them from ``recovery_validated`` /
``recovery_committed`` / ``recovery_commit_applied`` and from the
``revision_events`` field that was always persisted on the turn log.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


# ---------------------------------------------------------------------------
# Loading helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _as_bool(value: Any) -> bool:
    return bool(value) if value is not None else False


# ---------------------------------------------------------------------------
# Layer derivation (forward-compatible with the new fields)
# ---------------------------------------------------------------------------

def _has_status_revision_event(turn: Dict[str, Any]) -> bool:
    events = turn.get("revision_events") or []
    for event in events:
        if not isinstance(event, dict):
            continue
        if str(event.get("field") or "").strip().lower() != "status":
            continue
        new_value = str(event.get("new_value") or event.get("after") or "").strip().lower()
        if not new_value or new_value == "none":
            continue
        return True
    return False


def derive_recovery_layer(turn: Dict[str, Any]) -> Dict[str, Any]:
    """Return the 4-layer taxonomy for a single turn log entry.

    Honours the new ``recovery_layer*`` fields when present and otherwise
    reconstructs them from the legacy fields and ``revision_events``.
    """
    if turn.get("recovery_layer") or "recovery_layer_validated" in turn:
        return {
            "validated": _as_bool(turn.get("recovery_layer_validated")),
            "committed": _as_bool(turn.get("recovery_layer_committed")),
            "state_mutation_applied": _as_bool(
                turn.get("recovery_layer_state_mutation_applied")
            ),
            "hygiene_delta_improved": _as_bool(
                turn.get("recovery_layer_hygiene_delta_improved")
            ),
            "effective_repair": _as_bool(turn.get("recovery_effective_repair")),
            "layer": str(turn.get("recovery_layer") or ""),
        }

    attempted = _as_bool(turn.get("recovery_attempted"))
    validated = _as_bool(
        turn.get("recovery_validated") or turn.get("recovery_patch_validated")
    )
    committed = _as_bool(
        turn.get("recovery_committed") or turn.get("recovery_patch_committed")
    )
    state_mutation_applied = _as_bool(
        turn.get("recovery_commit_applied") or turn.get("recovery_success")
    )
    hygiene_delta_improved = bool(
        state_mutation_applied and _has_status_revision_event(turn)
    )
    if hygiene_delta_improved:
        layer = "hygiene_delta_improved"
    elif state_mutation_applied:
        layer = "state_mutation_applied"
    elif committed:
        layer = "patch_committed"
    elif validated:
        layer = "patch_validated"
    elif attempted:
        layer = "attempted"
    else:
        layer = ""
    return {
        "validated": validated,
        "committed": committed,
        "state_mutation_applied": state_mutation_applied,
        "hygiene_delta_improved": hygiene_delta_improved,
        "effective_repair": hygiene_delta_improved,
        "layer": layer,
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _iter_recovery_turns(rows: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for row in rows:
        for turn in row.get("turn_logs") or []:
            if _as_bool(turn.get("recovery_attempted")):
                yield {"paper_id": row.get("paper_id"), "turn": turn}


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    layer_counts: Counter[str] = Counter()
    cumulative: Counter[str] = Counter()
    source_layer_counts: Dict[str, Counter[str]] = {}
    per_paper: Dict[str, Counter[str]] = {}
    examples: Dict[str, List[Dict[str, Any]]] = {
        "patch_validated": [],
        "patch_committed": [],
        "state_mutation_applied": [],
        "hygiene_delta_improved": [],
    }

    for entry in _iter_recovery_turns(rows):
        turn = entry["turn"]
        paper_id = str(entry["paper_id"] or "")
        derived = derive_recovery_layer(turn)
        layer = derived["layer"] or "attempted"
        layer_counts[layer] += 1

        # Cumulative counts: every higher layer also implies the lower ones.
        if derived["validated"]:
            cumulative["patch_validated"] += 1
        if derived["committed"]:
            cumulative["patch_committed"] += 1
        if derived["state_mutation_applied"]:
            cumulative["state_mutation_applied"] += 1
        if derived["hygiene_delta_improved"]:
            cumulative["hygiene_delta_improved"] += 1

        source = str(turn.get("recovery_patch_source") or "unknown")
        source_layer_counts.setdefault(source, Counter())[layer] += 1

        per_paper.setdefault(paper_id, Counter())[layer] += 1

        bucket = examples.get(layer)
        if bucket is not None and len(bucket) < 3:
            bucket.append({
                "paper_id": paper_id,
                "turn_id": int(turn.get("turn_id") or 0),
                "patch_source": source,
                "old_status": str(turn.get("old_status") or ""),
                "new_status": str(turn.get("new_status") or ""),
                "recovery_failure_code": str(turn.get("recovery_failure_code") or ""),
                "recovery_target_id": str(turn.get("recovery_target_id") or ""),
            })

    return {
        "recovery_turn_total": sum(layer_counts.values()),
        "layer_terminal_counts": dict(layer_counts),
        "layer_cumulative_counts": dict(cumulative),
        "patch_source_layer_counts": {
            source: dict(counts) for source, counts in source_layer_counts.items()
        },
        "per_paper_layer_counts": {
            paper_id: dict(counts) for paper_id, counts in per_paper.items()
        },
        "examples": examples,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

LAYER_ORDER = [
    "attempted",
    "patch_validated",
    "patch_committed",
    "state_mutation_applied",
    "hygiene_delta_improved",
]


def render_markdown(args: argparse.Namespace, summary: Dict[str, Any], paper_count: int) -> str:
    lines: List[str] = []
    lines.append("# Recovery Layer Distribution Audit v1\n")
    lines.append(f"- input: `{args.input}`")
    lines.append(f"- papers: {paper_count}")
    lines.append(f"- recovery turns total: {summary['recovery_turn_total']}\n")

    lines.append("## 4-layer taxonomy")
    lines.append(
        "Each recovery turn is classified by the highest layer it reached."
    )
    lines.append("")
    lines.append("- `patch_validated`         — validator accepted the patch")
    lines.append("- `patch_committed`         — validator wrote the patch to the per-turn log")
    lines.append("- `state_mutation_applied`  — committing the patch produced a status-field revision")
    lines.append("- `hygiene_delta_improved`  — state mutation that reduces inconsistency")
    lines.append("- (lower) `attempted`       — patch was generated but did not validate\n")

    lines.append("## Terminal layer (highest stage reached per turn)")
    for layer in LAYER_ORDER:
        if layer in summary["layer_terminal_counts"]:
            lines.append(f"- `{layer}`: {summary['layer_terminal_counts'][layer]}")
    lines.append("")

    lines.append("## Cumulative layer (turns reaching at least this stage)")
    for layer in LAYER_ORDER[1:]:  # skip "attempted"
        if layer in summary["layer_cumulative_counts"]:
            lines.append(f"- `{layer}`: {summary['layer_cumulative_counts'][layer]}")
    lines.append("")

    lines.append("## Patch source × terminal layer")
    for source, counts in sorted(summary["patch_source_layer_counts"].items()):
        breakdown = ", ".join(
            f"{layer}={counts.get(layer, 0)}" for layer in LAYER_ORDER if counts.get(layer)
        )
        lines.append(f"- `{source}`: {breakdown}")
    lines.append("")

    lines.append("## Examples (up to 3 per layer)")
    for layer in ("patch_validated", "patch_committed", "state_mutation_applied", "hygiene_delta_improved"):
        bucket = summary["examples"].get(layer) or []
        if not bucket:
            continue
        lines.append(f"### `{layer}`")
        for entry in bucket:
            lines.append(
                f"- `{entry['paper_id']}` turn {entry['turn_id']} "
                f"target=`{entry['recovery_target_id']}` "
                f"source=`{entry['patch_source']}` "
                f"transition=`{entry['old_status']}->{entry['new_status']}` "
                f"code=`{entry['recovery_failure_code']}`"
            )
        lines.append("")

    lines.append("## Interpretation")
    cumulative = summary["layer_cumulative_counts"]
    committed = cumulative.get("patch_committed", 0)
    state_mut = cumulative.get("state_mutation_applied", 0)
    hygiene = cumulative.get("hygiene_delta_improved", 0)
    if committed and state_mut < committed:
        gap = committed - state_mut
        lines.append(
            f"- {gap}/{committed} validator-committed patch(es) did NOT actually mutate "
            "the ReviewState; paper-level success counters should use "
            "`recovery_effective_repair` (= `hygiene_delta_improved`) rather than "
            "`recovery_patch_committed`."
        )
    if state_mut and hygiene < state_mut:
        lines.append(
            f"- {state_mut - hygiene} state mutation(s) did not trigger the "
            "hygiene-delta heuristic; this is reserved for future stricter "
            "definitions and is currently expected to be 0."
        )
    if not committed:
        lines.append(
            "- No validator-committed recovery turns observed.  This audit "
            "still reports validated patches and any out-of-band hygiene mutations."
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        help="Path to a per-paper turn-log jsonl (e.g. mainline V16 / V17 result).",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Where to write the structured audit summary.",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Where to write the human-readable Markdown audit.",
    )
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    summary = aggregate(rows)
    summary["input"] = args.input
    summary["paper_count"] = len(rows)

    Path(args.output_json).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    Path(args.output_md).write_text(
        render_markdown(args, summary, paper_count=len(rows)),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
