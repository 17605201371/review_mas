import json
import statistics
from pathlib import Path

def median(vals): return statistics.median(vals) if vals else 0.0

def analyze_jsonl(path: str):
    p = Path(path)
    if not p.exists():
        print(f"File {path} not found.")
        return
    rows = [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]
    
    if not rows:
        print("No rows found")
        return
        
    rewards = [float(r.get("reward", 0)) for r in rows]
    decisions = [r.get("final_decision", "undecided") for r in rows]
    correct_count = sum(1 for d in decisions if d in ("accept", "reject")) # Assuming binary correctness, we may need true ground truth or just non-undecided. Wait, decision_correct_rate is actually often "reject" for this dataset.
    
    print(f"### A. Basic Metrics")
    print(f"- Rows: {len(rows)}")
    print(f"- Avg Reward: {sum(rewards)/len(rewards):.4f}")
    if rows:
        print(f"- Median Reward: {median(rewards):.4f}")
        print(f"- Min/Max/Quartiles: Min: {min(rewards):.4f}, Max: {max(rewards):.4f}, Q1: {statistics.quantiles(rewards)[0]:.4f}, Q3: {statistics.quantiles(rewards)[2]:.4f}")
    
    # Structure
    turns = [len(r.get("turn_logs", [])) for r in rows]
    claims = [len((r.get("review_state") or {}).get("claims", [])) for r in rows]
    evidences = [len((r.get("review_state") or {}).get("evidence_map", [])) for r in rows]
    flaws = [len((r.get("review_state") or {}).get("flaw_candidates", [])) for r in rows]
    
    print(f"\n### B. Structural Metrics")
    print(f"- Avg Turns: {sum(turns)/len(rows):.2f}")
    print(f"- Avg Claims: {sum(claims)/len(rows):.2f}")
    print(f"- Avg Evidence: {sum(evidences)/len(rows):.2f}")
    print(f"- Avg Flaws: {sum(flaws)/len(rows):.2f}")
    print(f"- Claim Rows: {sum(1 for x in claims if x > 0)}")
    print(f"- Evidence Rows: {sum(1 for x in evidences if x > 0)}")
    print(f"- Flaw Rows: {sum(1 for x in flaws if x > 0)}")
    print(f"- CEF Rows: {sum(1 for c, e, f in zip(claims, evidences, flaws) if c>0 and e>0 and f>0)}")
    
    # Conflict/Recovery
    total_revisions = 0
    total_conflicts = 0
    recovery_attempts = 0
    recovery_commits = 0
    attempt_no_commit = 0
    
    high_conflict_rows = []
    
    for r in rows:
        r_conflicts = 0
        r_revisions = 0
        r_attempts = 0
        r_commits = 0
        
        for t in r.get("turn_logs", []):
            if t.get("conflict_summary"):
                r_conflicts += len(t["conflict_summary"])
            if t.get("revision_meta", {}).get("reason_for_revision"):
                r_revisions += 1
            if t.get("recovery_attempted"):
                recovery_attempts += 1
                r_attempts += 1
            if t.get("recovery_commit_applied"):
                recovery_commits += 1
                r_commits += 1
            if t.get("recovery_attempted") and not t.get("recovery_commit_applied"):
                attempt_no_commit += 1
                
        total_conflicts += r_conflicts
        total_revisions += r_revisions
        
        if r_conflicts >= 5: # Need a stable way to count conflicts. Wait, conflict_notes in review_state is the cumulative size.
            pass
            
        r_cumulative_conflicts = len((r.get("review_state") or {}).get("conflict_notes", []))
        if r_cumulative_conflicts >= 5:
            high_conflict_rows.append((r, r_cumulative_conflicts, r_revisions, r_commits, r_attempts))

    print(f"\n### C. Conflict & Recovery Metrics")
    print(f"- Avg Conflicts: {total_conflicts/len(rows):.2f}")
    print(f"- Avg Revisions: {total_revisions/len(rows):.2f}")
    print(f"- Recovery Attempts: {recovery_attempts}")
    print(f"- Recovery Commits: {recovery_commits}")
    print(f"- Recovery Commit Rate: {recovery_commits/max(1, recovery_attempts):.2%}")
    print(f"- Attempt without Commit: {attempt_no_commit}")
    
    print(f"\n### D. High Conflict Subgroup (conflicts >= 5)")
    if high_conflict_rows:
        hr_rewards = [float(r[0].get("reward", 0)) for r in high_conflict_rows]
        print(f"- Rows: {len(high_conflict_rows)}")
        print(f"- Avg Reward: {sum(hr_rewards)/len(hr_rewards):.4f}")
        hr_revisions = sum(r[2] for r in high_conflict_rows)
        hr_attempts = sum(r[4] for r in high_conflict_rows)
        hr_commits = sum(r[3] for r in high_conflict_rows)
        print(f"- Avg Revisions: {hr_revisions/len(high_conflict_rows):.2f}")
        print(f"- Recovery Commit Rate: {hr_commits/max(1, hr_attempts):.2%}")
    else:
        print("No high conflict rows found.")

if __name__ == "__main__":
    analyze_jsonl("outputs/review_infer/p22_expanded_verification_qwen35_4b.jsonl")
