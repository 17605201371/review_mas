#!/usr/bin/env python3
"""P0FIX3 Comprehensive Audit Script v2 - Fixed data extraction.

Key fix: read from evidence_map (not final_support, which is always empty).
Correct field names: support_role, support_source_bucket, locator_type, etc.
"""
import json, glob, csv, os, sys
from collections import Counter, defaultdict
from pathlib import Path

LOG_DIR = "smoke8_20260604_p0fix3_sameids_qwen35_t7_logs"
OUT_DIR = "p0fix3_audit_output"
os.makedirs(OUT_DIR, exist_ok=True)

def load_papers():
    papers = []
    for f in sorted(glob.glob(f"{LOG_DIR}/*.json")):
        d = json.load(open(f))
        papers.append(d)
    return papers

def get_support_items(rs):
    """Get support items from evidence_map (final_support is always empty)."""
    items = []
    for item in rs.get("evidence_map", []):
        if isinstance(item, dict):
            items.append(item)
    # Also check final_support just in case
    for item in rs.get("final_support", []):
        if isinstance(item, dict):
            items.append(item)
    return items

def safe(v, default=""):
    if v is None:
        return default
    return v

# ============================================================
# P0-1: Evidence Formation Audit
# ============================================================
def audit_p0_1_evidence_formation(papers):
    rows = []
    per_paper = []
    total_ev_worker_turns = 0
    total_qb_nonzero = 0
    total_payload_items = 0
    total_nonempty_payload = 0
    total_question_only = 0
    total_dead_loops = 0
    total_first_fallback = 0

    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        turns = d.get("turn_logs", [])
        pp = {
            "paper_id": pid,
            "first_verify_evidence_turn": None,
            "first_nonempty_payload_turn": None,
            "first_evidence_in_state_turn": None,
            "first_final_support_turn": None,
            "generated_by_evidence_agent": False,
            "generated_by_first_support_fallback": False,
            "ev_worker_turns": 0,
            "qb_nonzero_turns": 0,
            "payload_items": 0,
            "nonempty_payload_turns": 0,
            "question_only_turns": 0,
            "dead_loop": False,
            "first_fallback_turns": 0,
        }
        for t in turns:
            at = t.get("action_type", "")
            eat = t.get("effective_action_type", "")
            tid = t.get("turn_id", 0)
            qb = t.get("evidence_quote_bank_count", 0)
            pec = t.get("evidence_payload_evidence_count", 0)
            ni = len(t.get("new_items", []))
            agents = t.get("selected_agents", [])
            jps = t.get("evidence_json_parse_status", "")
            fff = t.get("first_support_fallback_turns", 0)
            sup_form = t.get("support_formation_pass_triggered", False)
            sup_form_reason = t.get("support_formation_pass_reason", "")

            has_ev_agent = any("Evidence" in a for a in agents)
            if has_ev_agent or "verify_evidence" in str(eat) or "gather_evidence" in str(eat):
                pp["ev_worker_turns"] += 1
                total_ev_worker_turns += 1

                if qb > 0:
                    pp["qb_nonzero_turns"] += 1
                    total_qb_nonzero += 1

                if pec > 0:
                    pp["payload_items"] += pec
                    total_payload_items += pec
                    pp["nonempty_payload_turns"] += 1
                    total_nonempty_payload += 1
                    if pp["first_nonempty_payload_turn"] is None:
                        pp["first_nonempty_payload_turn"] = tid
                    pp["generated_by_evidence_agent"] = True
                elif ni > 0:
                    ev_items = [it for it in t.get("new_items", []) if isinstance(it, dict) and it.get("type", "") in ("evidence", "support")]
                    if ev_items:
                        pp["payload_items"] += len(ev_items)
                        total_payload_items += len(ev_items)
                        pp["nonempty_payload_turns"] += 1
                        total_nonempty_payload += 1
                        if pp["first_nonempty_payload_turn"] is None:
                            pp["first_nonempty_payload_turn"] = tid
                        pp["generated_by_evidence_agent"] = True
                else:
                    pp["question_only_turns"] += 1
                    total_question_only += 1

                if pp["first_verify_evidence_turn"] is None:
                    pp["first_verify_evidence_turn"] = tid

            ss = t.get("state_snapshot", {})
            if isinstance(ss, dict):
                em = ss.get("evidence_map", [])
                if em and pp["first_evidence_in_state_turn"] is None:
                    pp["first_evidence_in_state_turn"] = tid
                fs = ss.get("final_support", [])
                if fs and pp["first_final_support_turn"] is None:
                    pp["first_final_support_turn"] = tid

            if "first_support_fallback" in str(sup_form_reason).lower() or fff:
                pp["first_fallback_turns"] += 1
                total_first_fallback += 1
                pp["generated_by_first_support_fallback"] = True

        rs_em = rs.get("evidence_map", [])
        rs_fs = rs.get("final_support", [])
        if not rs_em and not rs_fs:
            pp["dead_loop"] = True
            total_dead_loops += 1

        # Check evidence_map for first-support fallback items
        for item in get_support_items(rs):
            eid = item.get("evidence_id", "")
            if "first-support" in eid:
                pp["generated_by_first_support_fallback"] = True

        per_paper.append(pp)

    summary = {
        "evidence_agent_worker_turns": total_ev_worker_turns,
        "quote_bank_nonzero_turns": total_qb_nonzero,
        "payload_evidence_item_total": total_payload_items,
        "evidence_agent_nonempty_payload_turns": total_nonempty_payload,
        "evidence_agent_question_only_turns": total_question_only,
        "first_support_fallback_turns": total_first_fallback,
        "evidence_formation_dead_loop_count": total_dead_loops,
        "papers_count": len(papers),
    }

    verdict = "PASS"
    reasons = []
    if total_dead_loops > 0:
        verdict = "FAIL"
        reasons.append(f"dead_loop_count={total_dead_loops} > 0")
    if total_qb_nonzero > 0 and total_payload_items == 0:
        verdict = "FAIL"
        reasons.append("quote_bank has data but payload_evidence_item_total=0")
    qo_ratio = total_question_only / max(total_ev_worker_turns, 1)
    if qo_ratio > 0.8:
        verdict = "FAIL"
        reasons.append(f"question_only ratio={qo_ratio:.1%} > 80%")
    all_fallback = all(pp["generated_by_first_support_fallback"] and not pp["generated_by_evidence_agent"] for pp in per_paper if pp["ev_worker_turns"] > 0)
    if all_fallback and total_payload_items == 0:
        verdict = "FAIL"
        reasons.append("all evidence depends on fallback, none from Evidence Agent")

    summary["verdict"] = verdict
    summary["verdict_reasons"] = reasons
    summary["question_only_ratio"] = round(qo_ratio, 3)

    result = {"summary": summary, "per_paper": per_paper}
    with open(f"{OUT_DIR}/P0_EVIDENCE_FORMATION_AUDIT.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    with open(f"{OUT_DIR}/P0_EVIDENCE_FORMATION_AUDIT.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=per_paper[0].keys() if per_paper else [])
        w.writeheader()
        w.writerows(per_paper)

    lines = ["# P0-1: Evidence Formation Audit", "", f"**Verdict: {verdict}**", ""]
    if reasons:
        lines.append("Failure reasons:")
        for r in reasons:
            lines.append(f"- {r}")
        lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---|")
    for k, v in summary.items():
        if k not in ("verdict", "verdict_reasons", "question_only_ratio"):
            lines.append(f"| `{k}` | {v} |")
    lines.append(f"| `question_only_ratio` | {summary.get('question_only_ratio', 0)} |")
    lines.append("")
    lines.append("## Per-Paper")
    lines.append("")
    lines.append("| paper_id | ev_turns | qb_nonzero | payload_items | nonempty | question_only | first_payload | first_state | first_support | by_agent | by_fallback |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for pp in per_paper:
        lines.append(f"| {pp['paper_id']} | {pp['ev_worker_turns']} | {pp['qb_nonzero_turns']} | {pp['payload_items']} | {pp['nonempty_payload_turns']} | {pp['question_only_turns']} | {pp['first_nonempty_payload_turn']} | {pp['first_evidence_in_state_turn']} | {pp['first_final_support_turn']} | {pp['generated_by_evidence_agent']} | {pp['generated_by_first_support_fallback']} |")
    lines.append("")
    with open(f"{OUT_DIR}/P0_EVIDENCE_FORMATION_AUDIT.md", "w") as f:
        f.write("\n".join(lines))

    print(f"P0-1 Evidence Formation: {verdict} (payload_items={total_payload_items}, qo_ratio={qo_ratio:.1%}, fallback_turns={total_first_fallback})")
    return result


# ============================================================
# P0-2: First-Support Fallback Strong Audit
# ============================================================
def audit_p0_2_first_support_strong(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        claims_map = {}
        for c in rs.get("claims", []):
            if isinstance(c, dict):
                claims_map[c.get("claim_id", c.get("id", ""))] = c

        support_items = get_support_items(rs)
        for item in support_items:
            eid = item.get("evidence_id", "")
            strength = item.get("final_strength", item.get("strength", ""))
            # First-support items have evidence_id like "evidence-first-support-1-turn-2"
            if "first-support" in eid and strength == "strong":
                claim_id = item.get("claim_id", "")
                claim = claims_map.get(claim_id, {})
                quote_id = item.get("quote_id", "")
                raw_quote = item.get("raw_quote", "")
                if not raw_quote:
                    for qb in rs.get("evidence_quote_bank", []):
                        if isinstance(qb, dict) and qb.get("quote_id", "") == quote_id:
                            raw_quote = qb.get("raw_quote", qb.get("text", ""))
                            break

                # Check if this quote is used by other claims
                used_by_others = []
                for other in support_items:
                    if other.get("evidence_id") != eid:
                        oqid = other.get("quote_id", "")
                        if oqid and oqid == quote_id:
                            used_by_others.append(other.get("claim_id", ""))

                rows.append({
                    "paper_id": pid,
                    "claim_id": claim_id,
                    "claim_text": claim.get("claim_text", claim.get("text", ""))[:200],
                    "claim_type": claim.get("claim_type", claim.get("type", "")),
                    "evidence_id": eid,
                    "quote_id": quote_id,
                    "raw_quote": raw_quote[:300],
                    "source_locator": item.get("source_locator", ""),
                    "support_role": item.get("support_role", ""),
                    "support_source_bucket": item.get("support_source_bucket", ""),
                    "verified_source_bucket": item.get("verified_source_bucket", ""),
                    "semantic_alignment_score": item.get("semantic_alignment_score", ""),
                    "verified_grounding_label": item.get("verified_grounding_label", ""),
                    "semantic_grounding_label": item.get("semantic_grounding_label", ""),
                    "strength_promotion_from_medium_used": item.get("strength_promotion_from_medium_used", False),
                    "strength_promotion_reason": item.get("strength_promotion_reason", ""),
                    "initial_strength": item.get("initial_strength", ""),
                    "final_strength": strength,
                    "support_depth": item.get("support_depth", ""),
                    "used_by_other_claim_ids": ",".join(used_by_others),
                    "human_label": "",
                })

    with open(f"{OUT_DIR}/P0_FIRST_SUPPORT_STRONG_AUDIT.json", "w") as f:
        json.dump({"count": len(rows), "items": rows}, f, indent=2, ensure_ascii=False)
    if rows:
        with open(f"{OUT_DIR}/P0_FIRST_SUPPORT_STRONG_AUDIT.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

    lines = ["# P0-2: First-Support Fallback Strong Audit", "", f"**Count: {len(rows)}**", ""]
    lines.append("| paper_id | claim_id | claim_type | quote_id | support_role | locator | alignment | promotion_reason | used_by_others |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['claim_id'][:12]} | {r['claim_type']} | {r['quote_id'][:16]} | {r['support_role']} | {r['source_locator'][:40]} | {r['semantic_alignment_score']} | {r['strength_promotion_reason'][:40]} | {r['used_by_other_claim_ids'][:20]} |")
    lines.append("")
    lines.append("## Raw Quotes")
    lines.append("")
    for i, r in enumerate(rows):
        lines.append(f"### [{i+1}] {r['paper_id']} / {r['claim_id'][:12]}")
        lines.append(f"- **Claim**: {r['claim_text']}")
        lines.append(f"- **Quote**: {r['raw_quote']}")
        lines.append(f"- **Locator**: {r['source_locator']}")
        lines.append(f"- **Role**: {r['support_role']}, **Bucket**: {r['support_source_bucket']}")
        lines.append(f"- **Initial strength**: {r['initial_strength']} -> **Final**: {r['final_strength']}")
        lines.append(f"- **Promotion**: {r['strength_promotion_reason']}")
        lines.append("")
    with open(f"{OUT_DIR}/P0_FIRST_SUPPORT_STRONG_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P0-2 First-Support Strong: {len(rows)} items exported")
    return rows


# ============================================================
# P0-3: Medium->Strong Promotion Audit
# ============================================================
def audit_p0_3_promotion(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        claims_map = {}
        for c in rs.get("claims", []):
            if isinstance(c, dict):
                claims_map[c.get("claim_id", c.get("id", ""))] = c

        support_items = get_support_items(rs)
        for item in support_items:
            strength = item.get("final_strength", item.get("strength", ""))
            promo_used = item.get("strength_promotion_from_medium_used", False)
            promo_reason = item.get("strength_promotion_reason", "")
            initial = item.get("initial_strength", "")
            held_at_moderate = item.get("strength_promotion_held_at_moderate", False)

            # Items that were promoted from medium to strong
            if strength == "strong" and (promo_used or (initial == "medium" and "first-support" not in item.get("evidence_id", ""))):
                claim_id = item.get("claim_id", "")
                claim = claims_map.get(claim_id, {})
                quote_id = item.get("quote_id", "")
                raw_quote = item.get("raw_quote", "")
                if not raw_quote:
                    for qb in rs.get("evidence_quote_bank", []):
                        if isinstance(qb, dict) and qb.get("quote_id", "") == quote_id:
                            raw_quote = qb.get("raw_quote", qb.get("text", ""))
                            break

                rows.append({
                    "paper_id": pid,
                    "claim_id": claim_id,
                    "claim_text": claim.get("claim_text", claim.get("text", ""))[:200],
                    "claim_type": claim.get("claim_type", claim.get("type", "")),
                    "evidence_id": item.get("evidence_id", ""),
                    "raw_quote": raw_quote[:300],
                    "source_locator": item.get("source_locator", ""),
                    "support_role": item.get("support_role", ""),
                    "support_source_bucket": item.get("support_source_bucket", ""),
                    "support_depth": item.get("support_depth", ""),
                    "semantic_alignment_score": item.get("semantic_alignment_score", ""),
                    "initial_strength": initial,
                    "final_strength": strength,
                    "strength_promotion_from_medium_used": promo_used,
                    "strength_promotion_reason": promo_reason,
                    "strength_promotion_held_at_moderate": held_at_moderate,
                    "verified_claim_overlap_score": item.get("verified_claim_overlap_score", ""),
                    "support_quality": item.get("support_quality", ""),
                    "support_quality_adjustment": item.get("support_quality_adjustment", ""),
                    "human_label": "",
                })

    with open(f"{OUT_DIR}/P0_MEDIUM_TO_STRONG_PROMOTION_AUDIT.json", "w") as f:
        json.dump({"count": len(rows), "items": rows}, f, indent=2, ensure_ascii=False)
    if rows:
        with open(f"{OUT_DIR}/P0_MEDIUM_TO_STRONG_PROMOTION_AUDIT.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

    lines = ["# P0-3: Medium->Strong Promotion Audit", "", f"**Count: {len(rows)}**", ""]
    lines.append("| paper_id | claim_id | claim_type | support_role | depth | alignment | initial | promoted | reason | overlap |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['claim_id'][:12]} | {r['claim_type']} | {r['support_role']} | {r['support_depth']} | {r['semantic_alignment_score']} | {r['initial_strength']} | {r['strength_promotion_from_medium_used']} | {r['strength_promotion_reason'][:40]} | {r['verified_claim_overlap_score']} |")
    lines.append("")
    lines.append("## Raw Quotes")
    lines.append("")
    for i, r in enumerate(rows):
        lines.append(f"### [{i+1}] {r['paper_id']} / {r['claim_id'][:12]}")
        lines.append(f"- **Claim**: {r['claim_text']}")
        lines.append(f"- **Quote**: {r['raw_quote']}")
        lines.append(f"- **Depth**: {r['support_depth']}, **Role**: {r['support_role']}, **Bucket**: {r['support_source_bucket']}")
        lines.append(f"- **Initial**: {r['initial_strength']} -> **Final**: {r['final_strength']}, **Reason**: {r['strength_promotion_reason']}")
        lines.append(f"- **Quality**: {r['support_quality']}, **Adjustment**: {r['support_quality_adjustment']}")
        lines.append("")
    with open(f"{OUT_DIR}/P0_MEDIUM_TO_STRONG_PROMOTION_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P0-3 Promotion: {len(rows)} items exported")
    return rows


# ============================================================
# P0-4: Cross-Claim Quote Reuse & Independence Audit
# ============================================================
def audit_p0_4_quote_reuse(papers):
    quote_usage = defaultdict(list)
    all_support = []

    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        for item in get_support_items(rs):
            qid = item.get("quote_id", "")
            if qid:
                quote_usage[qid].append({
                    "paper_id": pid,
                    "claim_id": item.get("claim_id", ""),
                    "evidence_id": item.get("evidence_id", ""),
                    "strength": item.get("final_strength", item.get("strength", "")),
                    "support_role": item.get("support_role", ""),
                    "independence_group_id": item.get("independence_group_id", ""),
                })
            all_support.append(item)

    cross_claim = []
    same_claim = []
    for qid, usages in quote_usage.items():
        claim_ids = set(u["claim_id"] for u in usages)
        if len(usages) > 1:
            if len(claim_ids) == 1:
                same_claim.append({"quote_id": qid, "claim_id": list(claim_ids)[0], "count": len(usages), "usages": usages})
            else:
                cross_claim.append({"quote_id": qid, "claim_ids": list(claim_ids), "count": len(usages), "usages": usages})

    # Independence stats - use evidence_id + quote_id as independence group
    indep_groups = defaultdict(list)
    for item in all_support:
        # Build independence group from claim_id + source_locator + quote_id
        cid = item.get("claim_id", "")
        qid = item.get("quote_id", "")
        loc = item.get("source_locator", "")
        igid = item.get("independence_group_id", "")
        if not igid:
            # Fallback: build a composite key
            import hashlib
            raw = f"{cid}|{loc}|{qid}"
            igid = hashlib.md5(raw.encode()).hexdigest()[:12]
        if cid:
            indep_groups[igid].append(cid)

    claims_2plus = set()
    for igid, cids in indep_groups.items():
        unique_claims = set(cids)
        if len(unique_claims) >= 2:
            claims_2plus.update(unique_claims)

    # Check per-claim independence (different independence groups per claim)
    claim_indep = defaultdict(set)
    for item in all_support:
        cid = item.get("claim_id", "")
        qid = item.get("quote_id", "")
        loc = item.get("source_locator", "")
        igid = item.get("independence_group_id", "")
        if not igid:
            import hashlib
            raw = f"{cid}|{loc}|{qid}"
            igid = hashlib.md5(raw.encode()).hexdigest()[:12]
        if cid and igid:
            claim_indep[cid].add(igid)
    claims_2plus_indep = {cid for cid, igids in claim_indep.items() if len(igids) >= 2}

    summary = {
        "same_quote_same_claim_count": len(same_claim),
        "same_quote_cross_claim_count": len(cross_claim),
        "claims_with_2plus_independent_support": len(claims_2plus_indep),
        "total_unique_quotes_in_support": len(quote_usage),
        "total_final_support_items": len(all_support),
    }

    result = {"summary": summary, "cross_claim_reuse": cross_claim, "same_claim_multi": same_claim}
    with open(f"{OUT_DIR}/P0_CROSS_CLAIM_QUOTE_REUSE_AUDIT.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = ["# P0-4: Cross-Claim Quote Reuse & Independence Audit", ""]
    lines.append("## Summary")
    lines.append("")
    for k, v in summary.items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    if cross_claim:
        lines.append("## Cross-Claim Quote Reuse")
        lines.append("")
        for cc in cross_claim:
            lines.append(f"### Quote `{cc['quote_id']}` -> claims: {cc['claim_ids']}")
            for u in cc["usages"]:
                lines.append(f"  - paper={u['paper_id']} claim={u['claim_id'][:12]} ev={u['evidence_id'][:30]} str={u['strength']} role={u['support_role']}")
            lines.append("")
    if same_claim:
        lines.append("## Same Quote Same Claim (multi-turn)")
        lines.append("")
        for sc in same_claim:
            lines.append(f"- Quote `{sc['quote_id']}` used {sc['count']}x for claim `{sc['claim_id'][:12]}`")
        lines.append("")
    lines.append("## Independence")
    lines.append("")
    lines.append(f"`claims_with_2plus_independent_support = {len(claims_2plus_indep)}`")
    lines.append("")
    if claims_2plus_indep:
        for cid in claims_2plus_indep:
            lines.append(f"- claim `{cid}`: {len(claim_indep[cid])} independence groups")
    else:
        lines.append("**No claim has 2+ independent support groups.**")
        lines.append("")
        lines.append("> If claims_with_2plus_independent_support = 0:")
        lines.append("> P0fix3 can only be classified as 'P0 evidence formation fix',")
        lines.append("> NOT 'independent evidence optimization success'.")
    lines.append("")
    with open(f"{OUT_DIR}/P0_CROSS_CLAIM_QUOTE_REUSE_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P0-4 Quote Reuse: cross_claim={len(cross_claim)}, same_claim={len(same_claim)}, claims_2plus_indep={len(claims_2plus_indep)}")
    return result


# ============================================================
# P0-5: Empirical/Table/Figure Role Audit
# ============================================================
def audit_p0_5_empirical_role(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        claims_map = {}
        for c in rs.get("claims", []):
            if isinstance(c, dict):
                claims_map[c.get("claim_id", c.get("id", ""))] = c

        for item in get_support_items(rs):
            strength = item.get("final_strength", item.get("strength", ""))
            if strength != "strong":
                continue
            sr = item.get("support_role", "")
            sb = item.get("support_source_bucket", item.get("verified_source_bucket", ""))
            depth = item.get("support_depth", item.get("final_support_depth", ""))
            loc_type = item.get("locator_type", item.get("source_locator_type", ""))

            is_empirical = any(x in sr.lower() for x in ["empirical", "result", "experiment"]) or \
                           any(x in sb.lower() for x in ["empirical", "result", "experiment", "ablation"])
            is_table_fig = any(x in sr.lower() for x in ["table", "figure"]) or \
                           any(x in sb.lower() for x in ["table", "figure"]) or \
                           any(x in loc_type.lower() for x in ["table", "figure"])
            is_deep = depth == "deep"

            if is_empirical or is_table_fig or is_deep:
                claim_id = item.get("claim_id", "")
                claim = claims_map.get(claim_id, {})
                quote_id = item.get("quote_id", "")
                raw_quote = item.get("raw_quote", "")
                if not raw_quote:
                    for qb in rs.get("evidence_quote_bank", []):
                        if isinstance(qb, dict) and qb.get("quote_id", "") == quote_id:
                            raw_quote = qb.get("raw_quote", qb.get("text", ""))
                            break

                rows.append({
                    "paper_id": pid,
                    "claim_id": claim_id,
                    "claim_text": claim.get("claim_text", claim.get("text", ""))[:200],
                    "claim_type": claim.get("claim_type", claim.get("type", "")),
                    "evidence_id": item.get("evidence_id", ""),
                    "raw_quote": raw_quote[:300],
                    "source_locator": item.get("source_locator", ""),
                    "support_role": sr,
                    "support_source_bucket": sb,
                    "support_depth": depth,
                    "locator_type": loc_type,
                    "table_or_figure_flag": is_table_fig,
                    "result_or_experiment_flag": is_empirical,
                    "deep_support_flag": is_deep,
                    "semantic_alignment_score": item.get("semantic_alignment_score", ""),
                    "human_label": "",
                })

    with open(f"{OUT_DIR}/P0_EMPIRICAL_ROLE_AUDIT.json", "w") as f:
        json.dump({"count": len(rows), "items": rows}, f, indent=2, ensure_ascii=False)
    if rows:
        with open(f"{OUT_DIR}/P0_EMPIRICAL_ROLE_AUDIT.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

    lines = ["# P0-5: Empirical/Table/Figure Role Audit", "", f"**Count: {len(rows)}**", ""]
    lines.append("| paper_id | claim_id | claim_type | support_role | bucket | depth | loc_type | table_fig | empirical | deep |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['claim_id'][:12]} | {r['claim_type']} | {r['support_role']} | {r['support_source_bucket']} | {r['support_depth']} | {r['locator_type']} | {r['table_or_figure_flag']} | {r['result_or_experiment_flag']} | {r['deep_support_flag']} |")
    lines.append("")
    lines.append("## Raw Quotes")
    lines.append("")
    for i, r in enumerate(rows):
        lines.append(f"### [{i+1}] {r['paper_id']} / {r['claim_id'][:12]}")
        lines.append(f"- **Claim**: {r['claim_text']}")
        lines.append(f"- **Quote**: {r['raw_quote']}")
        lines.append(f"- **Role**: {r['support_role']}, **Bucket**: {r['support_source_bucket']}, **Depth**: {r['support_depth']}, **Locator**: {r['locator_type']}")
        lines.append("")
    with open(f"{OUT_DIR}/P0_EMPIRICAL_ROLE_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P0-5 Empirical Role: {len(rows)} items exported")
    return rows


# ============================================================
# P1-1: Recovery Funnel Audit
# ============================================================
def audit_p1_1_recovery(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        for t in d.get("turn_logs", []):
            if not t.get("recovery_attempted", False):
                continue
            rows.append({
                "paper_id": pid,
                "turn_id": t.get("turn_id", 0),
                "target_claim_id": t.get("recovery_target_id", t.get("target_claim_id", "")),
                "target_type": t.get("recovery_target_type", ""),
                "target_quality": t.get("target_quality_label", ""),
                "target_gate_label": t.get("recovery_target_gate_label", t.get("target_gate_label", "")),
                "supporting_evidence_ids": str(t.get("supporting_evidence_ids", []))[:100],
                "failure_code": t.get("recovery_failure_code", ""),
                "failure_message": (t.get("recovery_failure_message", "") or "")[:200],
                "validated": t.get("recovery_patch_validated", t.get("recovery_validated", False)),
                "committed": t.get("recovery_patch_committed", t.get("recovery_committed", False)),
                "state_mutation_applied": t.get("recovery_layer_state_mutation_applied", False),
                "hygiene_delta_improved": t.get("recovery_layer_hygiene_delta_improved", False),
                "effective_repair": t.get("recovery_effective_repair", False),
                "safe_resolution": t.get("recovery_safe_resolution", False),
                "patch_operation": t.get("recovery_patch_operation", ""),
                "human_label": "",
            })

    fc_counter = Counter(r["failure_code"] for r in rows if r["failure_code"])
    gate_counter = Counter(r["target_gate_label"] for r in rows)
    validated = sum(1 for r in rows if r["validated"])
    committed = sum(1 for r in rows if r["committed"])
    effective = sum(1 for r in rows if r["effective_repair"])
    safe_res = sum(1 for r in rows if r.get("safe_resolution", False))

    summary = {
        "recovery_attempted": len(rows),
        "recovery_patch_validated": validated,
        "recovery_patch_committed": committed,
        "recovery_effective_repair": effective,
        "recovery_safe_resolution": safe_res,
        "failure_code_histogram": dict(fc_counter),
        "target_gate_histogram": dict(gate_counter),
    }

    result = {"summary": summary, "turns": rows}
    with open(f"{OUT_DIR}/P1_RECOVERY_TARGET_FUNNEL_AUDIT.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    if rows:
        with open(f"{OUT_DIR}/P1_RECOVERY_TARGET_FUNNEL_AUDIT.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

    lines = ["# P1-1: Recovery Funnel Audit", ""]
    lines.append("## Summary")
    lines.append(f"- recovery_attempted: {len(rows)}")
    lines.append(f"- validated: {validated}")
    lines.append(f"- committed: {committed}")
    lines.append(f"- effective_repair: {effective}")
    lines.append(f"- safe_resolution: {safe_res}")
    lines.append(f"- failure_codes: {dict(fc_counter)}")
    lines.append(f"- target_gates: {dict(gate_counter)}")
    lines.append("")
    lines.append("## Turn Details")
    lines.append("")
    lines.append("| paper_id | turn | target | gate | failure_code | validated | committed | effective | safe | operation |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['turn_id']} | {r['target_claim_id'][:12]} | {r['target_gate_label']} | {r['failure_code']} | {r['validated']} | {r['committed']} | {r['effective_repair']} | {r['safe_resolution']} | {r['patch_operation'][:30]} |")
    lines.append("")
    with open(f"{OUT_DIR}/P1_RECOVERY_TARGET_FUNNEL_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P1-1 Recovery: {len(rows)} turns, validated={validated}, committed={committed}, effective={effective}, safe={safe_res}")
    return result


# ============================================================
# P1-2: Gap Lifecycle Audit
# ============================================================
def audit_p1_2_gap_lifecycle(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})

        for gap in rs.get("evidence_gaps", []):
            if not isinstance(gap, dict):
                continue
            rows.append({
                "paper_id": pid,
                "gap_id": gap.get("gap_id", gap.get("id", "")),
                "question_text": (gap.get("question", gap.get("question_text", "")) or "")[:200],
                "related_claim_ids": str(gap.get("related_claim_ids", [])),
                "related_evidence_ids": str(gap.get("related_evidence_ids", [])),
                "related_flaw_ids": str(gap.get("related_flaw_ids", [])),
                "status": gap.get("status", "open"),
                "resolution_reason": gap.get("resolution_reason", ""),
                "targetless": len(gap.get("related_claim_ids", [])) == 0,
            })

        for uq in rs.get("unresolved_questions", []):
            if not isinstance(uq, dict):
                continue
            rows.append({
                "paper_id": pid,
                "gap_id": uq.get("question_id", uq.get("id", "")),
                "question_text": (uq.get("question", uq.get("text", "")) or "")[:200],
                "related_claim_ids": str(uq.get("related_claim_ids", [])),
                "related_evidence_ids": str(uq.get("related_evidence_ids", [])),
                "related_flaw_ids": str(uq.get("related_flaw_ids", [])),
                "status": uq.get("status", "open"),
                "resolution_reason": uq.get("resolution_reason", uq.get("deferred_reason", "")),
                "targetless": len(uq.get("related_claim_ids", [])) == 0,
            })

    status_counter = Counter(r["status"] for r in rows)
    targetless = sum(1 for r in rows if r["targetless"])
    resolved = sum(1 for r in rows if r["status"] == "resolved")
    deferred = sum(1 for r in rows if r["status"] == "deferred")

    summary = {
        "total_gaps": len(rows),
        "status_histogram": dict(status_counter),
        "targetless_count": targetless,
        "resolved_count": resolved,
        "deferred_count": deferred,
    }

    result = {"summary": summary, "gaps": rows}
    with open(f"{OUT_DIR}/P1_GAP_LIFECYCLE_TRANSITION_AUDIT.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = ["# P1-2: Gap Lifecycle Audit", ""]
    lines.append("## Summary")
    lines.append(f"- total: {len(rows)}")
    lines.append(f"- statuses: {dict(status_counter)}")
    lines.append(f"- targetless: {targetless}")
    lines.append("")
    lines.append("| paper_id | gap_id | status | targetless | related_claims | question |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['gap_id'][:16]} | {r['status']} | {r['targetless']} | {r['related_claim_ids'][:40]} | {r['question_text'][:80]} |")
    lines.append("")
    with open(f"{OUT_DIR}/P1_GAP_LIFECYCLE_TRANSITION_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P1-2 Gaps: {len(rows)} total, resolved={resolved}, deferred={deferred}, targetless={targetless}")
    return result


# ============================================================
# P1-3: Zero-Real Paper Audit
# ============================================================
def audit_p1_3_zero_real(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        
        # Check evidence_map for strong items (not final_support which is always empty)
        support_items = get_support_items(rs)
        strong_items = [it for it in support_items 
                       if it.get("final_strength", it.get("strength", "")) == "strong"]
        has_real_strong = len(strong_items) > 0
        
        if has_real_strong:
            continue

        claims = rs.get("claims", [])
        primary_claims = [c for c in claims if isinstance(c, dict) and c.get("is_primary", c.get("primary", False))]
        if not primary_claims:
            primary_claims = claims[:3]

        turns = d.get("turn_logs", [])
        ev_turns = sum(1 for t in turns if any("Evidence" in a for a in t.get("selected_agents", [])))
        qb_size = len(rs.get("evidence_quote_bank", []))
        
        # Gather evidence_map details
        em = rs.get("evidence_map", [])
        em_strengths = [it.get("final_strength", it.get("strength", "")) for it in em if isinstance(it, dict)]

        rows.append({
            "paper_id": pid,
            "primary_claim_count": len(primary_claims),
            "primary_claim_texts": [c.get("claim_text", c.get("text", ""))[:150] for c in primary_claims if isinstance(c, dict)],
            "evidence_agent_turns": ev_turns,
            "quote_bank_size": qb_size,
            "evidence_map_size": len(em),
            "evidence_map_strengths": em_strengths,
            "strong_count": len(strong_items),
            "flaw_candidates_size": len(rs.get("flaw_candidates", [])),
            "unresolved_questions_size": len(rs.get("unresolved_questions", [])),
            "evidence_gaps_size": len(rs.get("evidence_gaps", [])),
            "dialogue_summary": (rs.get("dialogue_summary", "") or "")[:300],
            "human_label": "",
        })

    with open(f"{OUT_DIR}/P1_ZERO_REAL_CASE_AUDIT.json", "w") as f:
        json.dump({"count": len(rows), "papers": rows}, f, indent=2, ensure_ascii=False)

    lines = ["# P1-3: Zero-Real Paper Audit", "", f"**Count: {len(rows)} zero-real papers**", ""]
    for r in rows:
        lines.append(f"## {r['paper_id']}")
        lines.append(f"- primary_claims: {r['primary_claim_count']}")
        lines.append(f"- evidence_agent_turns: {r['evidence_agent_turns']}")
        lines.append(f"- quote_bank_size: {r['quote_bank_size']}")
        lines.append(f"- evidence_map_size: {r['evidence_map_size']}")
        lines.append(f"- evidence_map_strengths: {r['evidence_map_strengths']}")
        lines.append(f"- strong_count: {r['strong_count']}")
        lines.append(f"- unresolved_questions: {r['unresolved_questions_size']}")
        lines.append(f"- dialogue_summary: {r['dialogue_summary']}")
        lines.append("")
        lines.append("### Primary Claims")
        for ct in r["primary_claim_texts"]:
            lines.append(f"- {ct}")
        lines.append("")
    with open(f"{OUT_DIR}/P1_ZERO_REAL_CASE_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P1-3 Zero-Real: {len(rows)} papers")
    return rows


# ============================================================
# P2-1: Negative Evidence & Contested Audit
# ============================================================
def audit_p2_1_negative(papers):
    neg_rows = []
    contested_rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})

        for fc in rs.get("flaw_candidates", []):
            if not isinstance(fc, dict):
                continue
            neg_rows.append({
                "paper_id": pid,
                "flaw_id": fc.get("flaw_id", fc.get("id", "")),
                "flaw_text": (fc.get("flaw_text", fc.get("text", "")) or "")[:300],
                "flaw_type": fc.get("flaw_type", fc.get("type", "")),
                "status": fc.get("status", ""),
                "negative_evidence_id": fc.get("negative_evidence_id", ""),
                "claim_id": fc.get("related_claim_id", fc.get("claim_id", "")),
                "severity": fc.get("severity", ""),
            })

        for item in get_support_items(rs):
            if item.get("contested", False):
                contested_rows.append({
                    "paper_id": pid,
                    "claim_id": item.get("claim_id", ""),
                    "evidence_id": item.get("evidence_id", ""),
                    "strength": item.get("final_strength", item.get("strength", "")),
                    "contested_status": item.get("contested_status", "contested"),
                })

    result = {"negative_flaws": neg_rows, "contested_support": contested_rows}
    with open(f"{OUT_DIR}/P2_NEGATIVE_CONTESTED_AUDIT.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    lines = ["# P2-1: Negative Evidence & Contested Audit", ""]
    lines.append(f"## Negative Flaws: {len(neg_rows)}")
    lines.append("")
    for r in neg_rows:
        lines.append(f"### {r['paper_id']} / {r['flaw_id'][:16]}")
        lines.append(f"- **Type**: {r['flaw_type']}, **Status**: {r['status']}, **Severity**: {r['severity']}")
        lines.append(f"- **Text**: {r['flaw_text']}")
        lines.append("")
    lines.append(f"## Contested Support: {len(contested_rows)}")
    lines.append("")
    for r in contested_rows:
        lines.append(f"- {r['paper_id']} / {r['claim_id'][:12]} / {r['evidence_id'][:20]} strength={r['strength']}")
    lines.append("")
    with open(f"{OUT_DIR}/P2_NEGATIVE_CONTESTED_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P2-1 Negative: {len(neg_rows)} flaws, {len(contested_rows)} contested")
    return result


# ============================================================
# P2-2: Locator Quality Audit
# ============================================================
def audit_p2_2_locator(papers):
    rows = []
    for d in papers:
        pid = d.get("paper_id", "?")
        rs = d.get("review_state", {})
        for item in get_support_items(rs):
            locator = item.get("source_locator", "")
            if not locator:
                continue
            loc_type = item.get("locator_type", item.get("source_locator_type", ""))
            loc_conf = item.get("locator_confidence", item.get("source_locator_confidence", ""))
            rows.append({
                "paper_id": pid,
                "evidence_id": item.get("evidence_id", ""),
                "claim_id": item.get("claim_id", ""),
                "raw_quote": (item.get("raw_quote", "") or "")[:200],
                "source_locator": locator,
                "locator_type": loc_type,
                "locator_confidence": loc_conf,
                "support_role": item.get("support_role", ""),
                "support_source_bucket": item.get("support_source_bucket", ""),
                "final_strength": item.get("final_strength", item.get("strength", "")),
                "verified_locator_quality": item.get("verified_locator_quality", ""),
                "human_label": "",
            })

    with open(f"{OUT_DIR}/P2_LOCATOR_QUALITY_AUDIT.json", "w") as f:
        json.dump({"count": len(rows), "items": rows}, f, indent=2, ensure_ascii=False)
    if rows:
        with open(f"{OUT_DIR}/P2_LOCATOR_QUALITY_AUDIT.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)

    lines = ["# P2-2: Locator Quality Audit", "", f"**Count: {len(rows)}**", ""]
    lines.append("| paper_id | evidence_id | locator_type | confidence | role | bucket | strength | locator |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['paper_id']} | {r['evidence_id'][:30]} | {r['locator_type']} | {r['locator_confidence']} | {r['support_role']} | {r['support_source_bucket']} | {r['final_strength']} | {r['source_locator'][:50]} |")
    lines.append("")
    with open(f"{OUT_DIR}/P2_LOCATOR_QUALITY_AUDIT.md", "w") as f:
        f.write("\n".join(lines))
    print(f"P2-2 Locator: {len(rows)} items")
    return rows


# ============================================================
# Final Report
# ============================================================
def generate_final_report(papers, results):
    p01 = results["p0_1"]
    p02 = results["p0_2"]
    p03 = results["p0_3"]
    p04 = results["p0_4"]
    p05 = results["p0_5"]
    p11 = results["p1_1"]
    p12 = results["p1_2"]
    p13 = results["p1_3"]
    p21 = results["p2_1"]
    p22 = results["p2_2"]

    lines = ["# P0FIX3 Comprehensive Audit Report", ""]
    lines.append("## Executive Summary")
    lines.append("")

    red_flags = []
    yellow_flags = []
    green_flags = []

    # P0-1 checks
    s = p01["summary"]
    if s["verdict"] == "FAIL":
        red_flags.append(f"P0-1 Evidence Formation: FAIL - {s['verdict_reasons']}")
    else:
        green_flags.append("P0-1 Evidence Formation dead loop eliminated")

    # P0-2 checks
    if len(p02) == 0:
        green_flags.append("P0-2 No first-support fallback strong items (all from normal path)")
    else:
        yellow_flags.append(f"P0-2 {len(p02)} first-support fallback strong items need human review")

    # P0-3 checks
    if len(p03) > 0:
        yellow_flags.append(f"P0-3 {len(p03)} medium->strong promotion items need human review")
        promoted_count = sum(1 for r in p03 if r.get("strength_promotion_from_medium_used"))
        if promoted_count > len(p03) * 0.8:
            yellow_flags.append("P0-3 >80% of strong from promotion, moderate layer absorbed")

    # P0-4 checks
    claims_2plus = p04["summary"]["claims_with_2plus_independent_support"]
    if claims_2plus == 0:
        yellow_flags.append("P0-4 claims_with_2plus_independent_support = 0, cannot claim independent evidence optimization")
    else:
        green_flags.append(f"P0-4 {claims_2plus} claims have 2+ independent support")

    cross = len(p04.get("cross_claim_reuse", []))
    if cross > 0:
        yellow_flags.append(f"P0-4 {cross} cross-claim quote reuse cases need review")

    # P0-5 checks
    if len(p05) > 0:
        green_flags.append(f"P0-5 {len(p05)} empirical/table/figure strong items verified")
    else:
        yellow_flags.append("P0-5 No empirical/table/figure strong items found")

    # P1-1 checks
    rec_s = p11["summary"]
    if rec_s["recovery_effective_repair"] <= 1:
        yellow_flags.append(f"P1-1 recovery_effective_repair={rec_s['recovery_effective_repair']}, still low")

    # P1-2 checks
    gap_s = p12["summary"]
    if gap_s["targetless_count"] > gap_s["total_gaps"] * 0.5:
        yellow_flags.append(f"P1-2 {gap_s['targetless_count']}/{gap_s['total_gaps']} gaps are targetless")

    # P1-3 checks
    if len(p13) > 0:
        yellow_flags.append(f"P1-3 {len(p13)} zero-real papers remain")

    # P2-1 checks
    neg_count = len(p21["negative_flaws"])
    contested_count = len(p21["contested_support"])
    if neg_count > 0:
        green_flags.append(f"P2-1 {neg_count} flaw candidates detected")
    if contested_count == 0:
        green_flags.append("P2-1 No contested support items")

    # P2-2 checks
    if len(p22) > 0:
        green_flags.append(f"P2-2 {len(p22)} locator items exported for review")
    else:
        yellow_flags.append("P2-2 No locator items found")

    lines.append("### Decision")
    lines.append("")
    if red_flags:
        lines.append("**RED: Rollback or redo required**")
        lines.append("")
        for f in red_flags:
            lines.append(f"- {f}")
    elif len(yellow_flags) <= 3:
        lines.append("**YELLOW: Keep experiment branch, pending minor reviews**")
        lines.append("")
    else:
        lines.append("**YELLOW: Keep experiment branch, do not replace baseline**")
        lines.append("")

    lines.append("")
    if green_flags:
        lines.append("### Green Flags (Pass)")
        lines.append("")
        for f in green_flags:
            lines.append(f"- {f}")
        lines.append("")
    if yellow_flags:
        lines.append("### Yellow Flags (Warnings)")
        lines.append("")
        for f in yellow_flags:
            lines.append(f"- {f}")
        lines.append("")
    if red_flags:
        lines.append("### Red Flags (Failures)")
        lines.append("")
        for f in red_flags:
            lines.append(f"- {f}")
        lines.append("")

    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Audit Item | Key Metric | Value |")
    lines.append("|---|---|---|")
    lines.append(f"| P0-1 Evidence Formation | verdict | {p01['summary']['verdict']} |")
    lines.append(f"| P0-1 | payload_evidence_item_total | {p01['summary']['payload_evidence_item_total']} |")
    lines.append(f"| P0-1 | question_only_ratio | {p01['summary'].get('question_only_ratio', 'N/A')} |")
    lines.append(f"| P0-2 First-Support Strong | count | {len(p02)} |")
    lines.append(f"| P0-3 Medium->Strong | count | {len(p03)} |")
    lines.append(f"| P0-4 Cross-Claim Reuse | cross_claim_count | {len(p04.get('cross_claim_reuse', []))} |")
    lines.append(f"| P0-4 Independence | claims_with_2plus_indep | {claims_2plus} |")
    lines.append(f"| P0-5 Empirical Role | count | {len(p05)} |")
    lines.append(f"| P1-1 Recovery | attempted/effective | {rec_s['recovery_attempted']}/{rec_s['recovery_effective_repair']} |")
    lines.append(f"| P1-2 Gaps | total/targetless | {gap_s['total_gaps']}/{gap_s['targetless_count']} |")
    lines.append(f"| P1-3 Zero-Real | papers | {len(p13)} |")
    lines.append(f"| P2-1 Negative | flaws | {len(p21['negative_flaws'])} |")
    lines.append(f"| P2-1 Contested | count | {len(p21['contested_support'])} |")
    lines.append(f"| P2-2 Locator | items | {len(p22)} |")
    lines.append("")

    lines.append("## Key Conclusions")
    lines.append("")
    lines.append(f"1. **P0 dead loop fixed**: {'YES' if p01['summary']['verdict'] == 'PASS' else 'NO'}")
    lines.append(f"2. **Fallback strong trustworthy**: NEEDS HUMAN REVIEW ({len(p02)} items)")
    lines.append(f"3. **Medium->Strong promotion**: NEEDS HUMAN REVIEW ({len(p03)} items)")
    lines.append(f"4. **Independent evidence goal achieved**: {'YES' if claims_2plus > 0 else 'NO (claims_with_2plus_independent_support=0)'}")
    lines.append(f"5. **Empirical/deep metrics authentic**: NEEDS HUMAN REVIEW ({len(p05)} items)")
    lines.append(f"6. **Recovery still functional**: effective_repair={rec_s['recovery_effective_repair']}")
    lines.append(f"7. **Gaps genuinely cleaned**: resolved={gap_s['resolved_count']}, targetless={gap_s['targetless_count']}")
    lines.append(f"8. **P0fix3 as new baseline**: {'CONDITIONAL (pending human review)' if not red_flags else 'NO (red flags)'}")
    lines.append("")

    with open(f"{OUT_DIR}/P0FIX3_COMPREHENSIVE_AUDIT_REPORT.md", "w") as f:
        f.write("\n".join(lines))

    decision = {
        "color": "RED" if red_flags else ("YELLOW" if yellow_flags else "GREEN"),
        "green_flags": green_flags,
        "yellow_flags": yellow_flags,
        "red_flags": red_flags,
        "claims_2plus_independent_support": claims_2plus,
        "can_be_baseline": len(red_flags) == 0,
        "classification": "P0 evidence formation fix" if claims_2plus == 0 else "P0 evidence formation fix + independent evidence optimization",
    }
    with open(f"{OUT_DIR}/P0FIX3_AUDIT_DECISION.json", "w") as f:
        json.dump(decision, f, indent=2, ensure_ascii=False)
    with open(f"{OUT_DIR}/P0FIX3_AUDIT_DECISION.md", "w") as f:
        f.write("\n".join(lines[:20]))

    print(f"\nFinal Decision: {decision['color']}")
    print(f"Classification: {decision['classification']}")
    print(f"Can be baseline: {decision['can_be_baseline']}")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    papers = load_papers()
    print(f"Loaded {len(papers)} papers from {LOG_DIR}")
    print()

    results = {}
    results["p0_1"] = audit_p0_1_evidence_formation(papers)
    results["p0_2"] = audit_p0_2_first_support_strong(papers)
    results["p0_3"] = audit_p0_3_promotion(papers)
    results["p0_4"] = audit_p0_4_quote_reuse(papers)
    results["p0_5"] = audit_p0_5_empirical_role(papers)
    results["p1_1"] = audit_p1_1_recovery(papers)
    results["p1_2"] = audit_p1_2_gap_lifecycle(papers)
    results["p1_3"] = audit_p1_3_zero_real(papers)
    results["p2_1"] = audit_p2_1_negative(papers)
    results["p2_2"] = audit_p2_2_locator(papers)

    print()
    generate_final_report(papers, results)
    print(f"\nAll outputs written to {OUT_DIR}/")
