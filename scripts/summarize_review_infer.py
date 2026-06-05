import argparse
import json
from collections import Counter
from pathlib import Path


MODES = ("s1", "s2", "s3", "s4")
NARRATIVE_LIST_FIELDS = (
    "new_items",
    "downgraded_items",
    "retracted_items",
    "conflicts_detected",
    "reason_for_revision",
)


def load_rows(path: Path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def mean(values):
    return sum(values) / len(values) if values else 0.0


def count_decisions(rows):
    counts = {"accept": 0, "reject": 0, "undecided": 0}
    for row in rows:
        decision = row.get("final_decision") or (row.get("review_state") or {}).get("final_decision", "undecided")
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def count_turn_field(rows, field):
    counts = Counter()
    for row in rows:
        for item in row.get("turn_logs", []):
            value = item.get(field)
            if value in (None, ""):
                continue
            counts[str(value)] += 1
    return dict(counts)


def count_turn_list_field(rows, field):
    counts = Counter()
    for row in rows:
        for item in row.get("turn_logs", []):
            for value in item.get(field, []) or []:
                if value in (None, ""):
                    continue
                counts[str(value)] += 1
    return dict(counts)


def count_auto_finalized(rows):
    return sum(1 for row in rows for item in row.get("turn_logs", []) if item.get("auto_finalized"))


def summarize_mode(path: Path):
    rows = load_rows(path)
    rewards = [float(row.get("reward", 0.0)) for row in rows]
    turn_counts = [len(row.get("turn_logs", [])) for row in rows]
    claim_counts = [len((row.get("review_state") or {}).get("claims", [])) for row in rows]
    evidence_counts = [len((row.get("review_state") or {}).get("evidence_map", [])) for row in rows]
    flaw_counts = [len((row.get("review_state") or {}).get("flaw_candidates", [])) for row in rows]
    unresolved_counts = [len((row.get("review_state") or {}).get("unresolved_questions", [])) for row in rows]
    empty_finalize_rows = 0
    for row in rows:
        state = row.get("review_state") or {}
        if (
            (row.get("final_decision") or state.get("final_decision")) != "undecided"
            and len(state.get("claims", [])) == 0
            and len(state.get("evidence_map", [])) == 0
            and len(state.get("flaw_candidates", [])) == 0
        ):
            empty_finalize_rows += 1

    narrative_counts = {field: count_turn_list_field(rows, field) for field in NARRATIVE_LIST_FIELDS}
    narrative_turn_rows = {
        f"{field}_turns": sum(
            1 for row in rows for item in row.get("turn_logs", []) if item.get(field)
        )
        for field in NARRATIVE_LIST_FIELDS
    }

    return {
        "rows": len(rows),
        "avg_reward": mean(rewards),
        "avg_turns": mean(turn_counts),
        "avg_claims": mean(claim_counts),
        "avg_evidence": mean(evidence_counts),
        "avg_flaws": mean(flaw_counts),
        "avg_unresolved": mean(unresolved_counts),
        "nonempty_claim_rows": sum(1 for count in claim_counts if count > 0),
        "nonempty_evidence_rows": sum(1 for count in evidence_counts if count > 0),
        "nonempty_flaw_rows": sum(1 for count in flaw_counts if count > 0),
        "finalize_with_empty_state_rows": empty_finalize_rows,
        "auto_finalized_turns": count_auto_finalized(rows),
        "action_type_counts": count_turn_field(rows, "action_type"),
        "effective_action_type_counts": count_turn_field(rows, "effective_action_type"),
        "policy_source_counts": count_turn_field(rows, "policy_source"),
        "decisions": count_decisions(rows),
        **narrative_turn_rows,
        "narrative_value_counts": narrative_counts,
    }


def print_table(summary_by_mode):
    header = (
        f"{'mode':<4} {'rows':>4} {'avg_reward':>10} {'avg_turns':>9} "
        f"{'avg_claims':>10} {'avg_evidence':>12} {'avg_flaws':>10} "
        f"{'claim_rows':>10} {'evid_rows':>9} {'flaw_rows':>9} {'empty_fin':>10} {'auto_fin':>9} "
        f"{'accept':>7} {'reject':>7} {'undecided':>10}"
    )
    print(header)
    print("-" * len(header))
    for mode in MODES:
        item = summary_by_mode.get(mode, {})
        decisions = item.get("decisions", {})
        print(
            f"{mode:<4} {item.get('rows', 0):>4} {item.get('avg_reward', 0.0):>10.4f} "
            f"{item.get('avg_turns', 0.0):>9.2f} {item.get('avg_claims', 0.0):>10.2f} "
            f"{item.get('avg_evidence', 0.0):>12.2f} {item.get('avg_flaws', 0.0):>10.2f} "
            f"{item.get('nonempty_claim_rows', 0):>10} {item.get('nonempty_evidence_rows', 0):>9} "
            f"{item.get('nonempty_flaw_rows', 0):>9} {item.get('finalize_with_empty_state_rows', 0):>10} {item.get('auto_finalized_turns', 0):>9} "
            f"{decisions.get('accept', 0):>7} {decisions.get('reject', 0):>7} {decisions.get('undecided', 0):>10}"
        )


def main():
    parser = argparse.ArgumentParser(description="Summarize review inference jsonl outputs.")
    parser.add_argument("--input-dir", default="outputs/review_infer")
    parser.add_argument("--suffix", default="_5.jsonl")
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--save-json", default=None)
    args = parser.parse_args()

    if args.input_file:
        input_path = Path(args.input_file)
        summary = summarize_mode(input_path)
        mode_name = input_path.stem
        summary_by_mode = {mode_name: summary}
        print(json.dumps(summary_by_mode, ensure_ascii=False, indent=2))
    else:
        input_dir = Path(args.input_dir)
        summary_by_mode = {}
        for mode in MODES:
            summary_by_mode[mode] = summarize_mode(input_dir / f"{mode}{args.suffix}")
        print_table(summary_by_mode)

    if args.save_json:
        output_path = Path(args.save_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary_by_mode, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
