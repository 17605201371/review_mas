#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

ACCEPT_REJECT = {"accept", "reject"}
REAL_CLAIM_PREFIX_BLOCKLIST = ("claim-fallback", "claim-general")
NEGATIVE_STANCES = {"contradicts", "contradict", "refutes", "missing"}
POSITIVE_STANCES = {"supports", "support", "partially_supports", "partial_support"}

CRITERIA = {
    "novelty": re.compile(r"\b(novel|novelty|original|incremental|prior work|related work|contribution)\b", re.I),
    "significance": re.compile(r"\b(significance|impact|importance|important|minor contribution|weak contribution|useful|meaningful)\b", re.I),
    "soundness": re.compile(r"\b(sound|soundness|method|methodology|algorithm|assumption|theory|valid|invalid|flaw|objective|optimization)\b", re.I),
    "empirical": re.compile(r"\b(empirical|experiment|evaluation|baseline|ablation|dataset|metric|result|table|figure|benchmark)\b", re.I),
    "clarity": re.compile(r"\b(clear|clarity|presentation|readability|reproducib|implementation|detail|code|hyperparameter|unclear)\b", re.I),
}
CORE_CRITERIA = {"novelty", "significance", "soundness", "empirical"}

PAPER_GROUNDING_RE = re.compile(
    r"\b(method|algorithm|experiment|evaluation|baseline|dataset|metric|result|table|figure|ablation|"
    r"architecture|assumption|proof|theorem|model|framework|comparison|benchmark)\b",
    re.I,
)
META_RE = re.compile(
    r"\b(excerpt|truncat|provided text|full text|not provided|insufficient context|cannot verify|"
    r"unable to verify|fallback|parse|raw output|agent|system|review limitation|not assessable)\b",
    re.I,
)
HARD_NEG_RE = re.compile(
    r"\b(major|serious|critical|significant concern|main concern|weakness|flaw|insufficient|not enough|"
    r"lack|lacks|missing|unclear|questionable|not convincing|limited|fails|does not|cannot|"
    r"no ablation|no baseline|no comparison|unsupported|unsubstantiated)\b",
    re.I,
)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def is_real_claim_id(claim_id: Any) -> bool:
    cid = norm(claim_id)
    return bool(cid) and not cid.startswith(REAL_CLAIM_PREFIX_BLOCKLIST)


def pred_decision(row: Dict[str, Any]) -> str:
    state = row.get("review_state") or {}
    value = norm(row.get("final_decision") or state.get("final_decision"))
    return value if value in ACCEPT_REJECT else "undecided"


def infer_gold(row: Dict[str, Any]) -> str:
    explicit = norm(row.get("gold_decision") or row.get("ground_truth_decision") or row.get("label"))
    if explicit in ACCEPT_REJECT:
        return explicit
    pred = pred_decision(row)
    try:
        correct = float(row.get("accept_reject_correct", row.get("decision_correct")))
    except (TypeError, ValueError):
        return "unknown"
    if pred not in ACCEPT_REJECT:
        return "unknown"
    return pred if correct >= 0.5 else ("accept" if pred == "reject" else "reject")


def issue_text(issue: Any) -> str:
    if isinstance(issue, dict):
        fields = [
            issue.get("title"),
            issue.get("description"),
            issue.get("flaw"),
            issue.get("question"),
            issue.get("rationale"),
            issue.get("reason"),
            issue.get("status"),
            issue.get("severity"),
        ]
        return " ".join(str(x or "") for x in fields)
    return str(issue or "")


def evidence_ids(issue: Any) -> List[str]:
    if not isinstance(issue, dict):
        return []
    ids = issue.get("evidence_ids") or issue.get("supporting_evidence_ids") or issue.get("evidence_id") or []
    if isinstance(ids, str):
        ids = [ids]
    return [str(x) for x in ids if x]


def related_claim_ids(issue: Any) -> List[str]:
    if not isinstance(issue, dict):
        return []
    ids = issue.get("related_claim_ids") or issue.get("claim_ids") or issue.get("target_claim_ids") or issue.get("claim_id") or []
    if isinstance(ids, str):
        ids = [ids]
    return [str(x) for x in ids if x]


def criterion_hits(text: str) -> List[str]:
    hits = [name for name, pattern in CRITERIA.items() if pattern.search(text or "")]
    return hits or ["unspecified"]


def is_core_criterion(criteria: Iterable[str]) -> bool:
    return bool(set(criteria) & CORE_CRITERIA)


def evidence_lookup(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(ev.get("evidence_id") or ""): ev
        for ev in state.get("evidence_map", []) or []
        if isinstance(ev, dict) and ev.get("evidence_id")
    }


def evidence_text(ev: Dict[str, Any]) -> str:
    return " ".join(str(ev.get(k) or "") for k in ("evidence", "source", "rationale", "binding_rationale", "support_quality_reason"))


def evidence_is_negative(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in NEGATIVE_STANCES or norm(ev.get("strength")) == "missing"


def evidence_is_positive_strong(ev: Dict[str, Any]) -> bool:
    return norm(ev.get("stance")) in POSITIVE_STANCES and norm(ev.get("strength")) == "strong"


def evidence_is_real_grounded(ev: Dict[str, Any]) -> bool:
    return is_real_claim_id(ev.get("claim_id")) and norm(ev.get("source")) != "fallback-extraction"


def linked_real_negative_evidence(ids: Iterable[str], ev_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for evid in ids:
        ev = ev_map.get(str(evid))
        if ev and evidence_is_real_grounded(ev) and evidence_is_negative(ev):
            out.append(ev)
    return out


def collect_system_negative_candidates(state: Dict[str, Any]) -> Dict[str, Any]:
    ev_map = evidence_lookup(state)
    negative_evidence = []
    weak_negative_evidence = []
    for ev in ev_map.values():
        if not evidence_is_real_grounded(ev):
            continue
        if evidence_is_negative(ev):
            text = evidence_text(ev)
            criteria = criterion_hits(text)
            item = {
                "evidence_id": ev.get("evidence_id"),
                "claim_id": ev.get("claim_id"),
                "criteria": criteria,
                "text": text[:260],
            }
            if is_core_criterion(criteria) and PAPER_GROUNDING_RE.search(text):
                negative_evidence.append(item)
            else:
                weak_negative_evidence.append(item)

    grounded_flaws = []
    weak_flaws = []
    meta_flaws = []
    for flaw in state.get("flaw_candidates", []) or []:
        if not isinstance(flaw, dict):
            continue
        text = issue_text(flaw)
        criteria = criterion_hits(text)
        linked_neg = linked_real_negative_evidence(evidence_ids(flaw), ev_map)
        has_any_real_evidence = any(evidence_is_real_grounded(ev_map.get(eid, {})) for eid in evidence_ids(flaw))
        status = norm(flaw.get("status")) or "candidate"
        severity = norm(flaw.get("severity")) or "unknown"
        item = {
            "flaw_id": flaw.get("flaw_id") or flaw.get("id") or "",
            "status": status,
            "severity": severity,
            "criteria": criteria,
            "evidence_ids": evidence_ids(flaw),
            "related_claim_ids": related_claim_ids(flaw),
            "text": text[:260],
        }
        if META_RE.search(text):
            meta_flaws.append(item)
        elif linked_neg and status == "confirmed" and severity in {"major", "critical"} and is_core_criterion(criteria):
            grounded_flaws.append(item)
        elif has_any_real_evidence or (PAPER_GROUNDING_RE.search(text) and is_core_criterion(criteria)):
            weak_flaws.append(item)

    paper_unresolved = []
    weak_unresolved = []
    meta_unresolved = []
    for item in (state.get("unresolved_questions") or []) + (state.get("evidence_gaps") or []):
        text = issue_text(item)
        criteria = criterion_hits(text)
        linked_neg = linked_real_negative_evidence(evidence_ids(item), ev_map)
        row = {
            "criteria": criteria,
            "evidence_ids": evidence_ids(item),
            "related_claim_ids": related_claim_ids(item),
            "text": text[:260],
        }
        if META_RE.search(text):
            meta_unresolved.append(row)
        elif linked_neg and is_core_criterion(criteria):
            paper_unresolved.append(row)
        elif PAPER_GROUNDING_RE.search(text) and HARD_NEG_RE.search(text):
            weak_unresolved.append(row)

    real_strong = 0
    real_nonabs = 0
    for ev in ev_map.values():
        if evidence_is_positive_strong(ev) and evidence_is_real_grounded(ev):
            real_strong += 1
            source_text = norm(ev.get("source")) + " " + norm(ev.get("support_source_bucket")) + " " + evidence_text(ev).lower()
            if "abstract" not in source_text:
                real_nonabs += 1

    trusted_blocker_count = len(negative_evidence) + len(grounded_flaws) + len(paper_unresolved)
    weak_blocker_count = len(weak_negative_evidence) + len(weak_flaws) + len(weak_unresolved)
    return {
        "negative_evidence": negative_evidence,
        "weak_negative_evidence": weak_negative_evidence,
        "grounded_flaws": grounded_flaws,
        "weak_flaws": weak_flaws,
        "meta_flaws": meta_flaws,
        "paper_unresolved": paper_unresolved,
        "weak_unresolved": weak_unresolved,
        "meta_unresolved": meta_unresolved,
        "system_trusted_negative_blocker_count": trusted_blocker_count,
        "system_weak_negative_candidate_count": weak_blocker_count,
        "real_strong_support_total": real_strong,
        "non_abstract_support_total": real_nonabs,
    }


def table_row(cols: Iterable[Any]) -> str:
    return "| " + " | ".join(str(c).replace("\n", " ") for c in cols) + " |"


def summarize_group(rows: List[Dict[str, Any]], tag: str) -> Dict[str, Any]:
    subset = [r for r in rows if r["tag"] == tag]
    return {
        "rows": len(subset),
        "trusted_blocker_rows": sum(1 for r in subset if r["system_trusted_negative_blocker_count"] > 0),
        "weak_candidate_rows": sum(1 for r in subset if r["system_weak_negative_candidate_count"] > 0),
        "oracle_core_hard_rows": sum(1 for r in subset if r.get("oracle_core_hard_weakness")),
        "formation_gap_rows": sum(1 for r in subset if r.get("negative_formation_gap")),
        "avg_real_strong": round(sum(r["real_strong_support_total"] for r in subset) / len(subset), 3) if subset else 0,
        "avg_weak_candidates": round(sum(r["system_weak_negative_candidate_count"] for r in subset) / len(subset), 3) if subset else 0,
    }


def render_schema() -> str:
    return """# Negative Evidence Formation / Flaw Confirmation v1 Schema

## 定位

本轮是离线 formation audit，不改 runtime、不改 final decision、不使用 reviewer comments 作为模型输入。

## 核心对象

- `system_trusted_negative_blocker`: 已绑定真实 claim、非 fallback evidence、核心 criterion 相关，并能解释 empirical/soundness/novelty/significance 负向判断的 blocker。
- `system_weak_negative_candidate`: 有 paper/criterion 语言，但缺少真实负向 evidence 或确认生命周期，只能作为 report warning / human review signal。
- `negative_formation_gap`: oracle-style reviewer comments 指出 core hard weakness，但系统没有 trusted negative blocker。

## 进入 trusted blocker 的最小条件

1. 负向 evidence 必须绑定真实 claim，且不是 `fallback-extraction`。
2. flaw 必须是 `confirmed` 且 `major/critical`，并有真实负向 evidence 支撑。
3. unresolved 只有在绑定真实负向 evidence 且关联核心 criterion 时才可视为 paper-grounded blocker。
4. meta / excerpt / fallback / system limitation 不得作为 reject blocker。

## 本轮约束

该 schema 只用于决定下一轮是否值得做 Negative Evidence Formation / Flaw Confirmation pass，不直接进入最终推荐。
"""


def render_audit(summary: Dict[str, Any]) -> str:
    lines = [
        "# Negative Evidence Formation / Flaw Confirmation v1 Audit",
        "",
        "## 结论",
        "",
        "当前 9B dry-run 的 false accept 不是 positive support 太多这么简单，而是系统缺少能与人工 hard weakness 对齐的可信负向 blocker。系统侧多数负向信号仍停留在 weak candidate / unresolved / meta burden，不能安全用于 final decision。",
        "",
        "## Group Summary",
        "",
        table_row(["group", "rows", "trusted_blocker_rows", "weak_candidate_rows", "oracle_core_hard_rows", "formation_gap_rows", "avg_real_strong", "avg_weak_candidates"]),
        table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for group, data in summary["group_summaries"].items():
        lines.append(table_row([group, data["rows"], data["trusted_blocker_rows"], data["weak_candidate_rows"], data["oracle_core_hard_rows"], data["formation_gap_rows"], data["avg_real_strong"], data["avg_weak_candidates"]]))
    lines += [
        "",
        "## Criterion Gap",
        "",
        table_row(["criterion", "formation_gap_count"]),
        table_row(["---", "---:"]),
    ]
    for criterion, count in summary["formation_gap_criteria"].most_common():
        lines.append(table_row([criterion, count]))
    lines += [
        "",
        "## 解释",
        "",
        "- `trusted_blocker_rows` 很低，说明系统目前缺少 paper-grounded negative evidence / confirmed flaw。",
        "- `weak_candidate_rows` 高，说明系统不是完全看不到负面线索，而是缺少确认、绑定和 criterion linkage。",
        "- reviewer comments 只作为离线 oracle-style 参照；它不能直接变成 reject rule，因为 recovered accept 中也存在 hard weakness comments。",
    ]
    return "\n".join(lines)


def render_case_table(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Negative Evidence Formation Case Table v1",
        "",
        table_row([
            "paper_id",
            "gold",
            "sim4",
            "tag",
            "trusted",
            "weak",
            "oracle_core_hard",
            "gap",
            "oracle_hard_criteria",
            "system_blocker_criteria",
            "real_strong",
            "non_abs",
            "next_action",
        ]),
        table_row(["---", "---", "---", "---", "---:", "---:", "---", "---", "---", "---", "---:", "---:", "---"]),
    ]
    interesting = [r for r in rows if r["tag"] in {"false_accept", "recovered_accept"}]
    for r in interesting:
        lines.append(table_row([
            r["paper_id"],
            r["gold_decision"],
            r["sim4_label"],
            r["tag"],
            r["system_trusted_negative_blocker_count"],
            r["system_weak_negative_candidate_count"],
            int(bool(r.get("oracle_core_hard_weakness"))),
            int(bool(r.get("negative_formation_gap"))),
            ",".join(r.get("oracle_hard_criteria", [])),
            ",".join(r.get("system_blocker_criteria", [])),
            r["real_strong_support_total"],
            r["non_abstract_support_total"],
            r["next_action"],
        ]))
    return "\n".join(lines)


def render_decision(summary: Dict[str, Any]) -> str:
    false_accept = summary["group_summaries"].get("false_accept", {})
    recovered = summary["group_summaries"].get("recovered_accept", {})
    return f"""# Negative Evidence Formation v1 Decision

## 决策

下一步应做 **Negative Evidence Formation / Flaw Confirmation v1 小样本 pass**，而不是继续调 final decision 阈值或重启 sticky/throttle。

## 依据

- false accept: `{false_accept.get('rows', 0)}` 行。
- false accept 中 trusted blocker 行数: `{false_accept.get('trusted_blocker_rows', 0)}`。
- false accept 中 formation gap 行数: `{false_accept.get('formation_gap_rows', 0)}`。
- recovered accept 中同样存在 oracle hard weakness: `{recovered.get('oracle_core_hard_rows', 0)}`，所以 reviewer comments 不能直接作为 reject rule。

## 下一刀

实现一个小样本 negative evidence / flaw confirmation pass：

1. 只围绕 empirical / soundness / novelty / significance 四个核心 criterion。
2. 输入只能用 paper text、当前 ReviewState、claim/evidence/flaw，不使用 reviewer comments。
3. 输出结构化 `negative_evidence_items` 和 `flaw_confirmation_items`。
4. 只有真实 claim 绑定、非 fallback、paper-grounded、criterion-linked 的负向证据才能成为 trusted blocker。
5. 先在 false accept + recovered accept 的 10 条 diagnostic subset 上跑，不进入正式主试验。

## 暂时不做

- 不把 weak negative candidate 当 reject blocker。
- 不用 unresolved/meta count 直接 reject。
- 不改 final decision 阈值。
- 不做 9B full rerun。

## 成功标准

- false accept 中至少形成部分 trusted negative blocker。
- recovered accept 不被同样规则大面积误伤。
- trusted blocker 能指向具体 criterion、claim/evidence 或 paper excerpt。
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", default="outputs/results_main/review_infer/mainline_final_v1_9b_fulltest39_dryrun.jsonl")
    parser.add_argument("--criterion-sim", default="outputs/results_main/review_infer/criterion_grounded_decision_sim_v1_9b_fulltest39_dryrun.json")
    parser.add_argument("--oracle-audit", default="outputs/results_main/review_infer/oracle_negative_evidence_formation_audit_v1_9b_fulltest39.json")
    parser.add_argument("--output-json", default="outputs/results_main/review_infer/negative_evidence_formation_v1_9b_fulltest39.json")
    parser.add_argument("--doc-dir", default="docs/experiments/mainline_current")
    args = parser.parse_args()

    rows = load_jsonl(Path(args.jsonl))
    criterion = load_json(Path(args.criterion_sim))
    oracle = load_json(Path(args.oracle_audit))

    sim_by_id = {r.get("paper_id"): r for r in criterion.get("case_rows", [])}
    oracle_by_id = {r.get("paper_id"): r for r in oracle.get("case_rows", [])}

    out_rows: List[Dict[str, Any]] = []
    formation_gap_criteria: Counter[str] = Counter()
    system_criteria_counter: Counter[str] = Counter()

    for row in rows:
        pid = row.get("paper_id")
        state = row.get("review_state") or {}
        sim = sim_by_id.get(pid, {})
        oracle_row = oracle_by_id.get(pid, {})
        system = collect_system_negative_candidates(state)

        sim4_label = sim.get("sim4_label") or oracle_row.get("sim4_label") or "unknown"
        gold = sim.get("gold_decision") or oracle_row.get("gold_decision") or infer_gold(row)
        tag = "other"
        if gold == "reject" and sim4_label == "accept_like":
            tag = "false_accept"
        elif gold == "accept" and sim4_label == "accept_like":
            tag = "recovered_accept"
        elif gold == "accept":
            tag = "false_reject_or_unrecovered_accept"

        system_criteria = set()
        for bucket in ("negative_evidence", "weak_negative_evidence", "grounded_flaws", "weak_flaws", "paper_unresolved", "weak_unresolved"):
            for item in system[bucket]:
                system_criteria.update(item.get("criteria", []))
        for criterion_name in system_criteria:
            system_criteria_counter[criterion_name] += 1

        oracle_hard_criteria = sorted((oracle_row.get("oracle_hard_criterion_counts") or {}).keys())
        oracle_core_hard = bool(oracle_row.get("oracle_core_hard_weakness"))
        gap = bool(oracle_core_hard and system["system_trusted_negative_blocker_count"] == 0)
        if gap:
            for criterion_name in oracle_hard_criteria or ["unspecified"]:
                formation_gap_criteria[criterion_name] += 1

        next_action = "none"
        if tag == "false_accept" and gap:
            next_action = "target_negative_evidence_pass"
        elif tag == "recovered_accept" and gap:
            next_action = "protect_with_discriminative_confirmation"
        elif system["system_trusted_negative_blocker_count"] > 0:
            next_action = "inspect_trusted_blocker_precision"

        out_rows.append({
            "paper_id": pid,
            "gold_decision": gold,
            "current_decision": pred_decision(row),
            "sim4_label": sim4_label,
            "tag": tag,
            "system_trusted_negative_blocker_count": system["system_trusted_negative_blocker_count"],
            "system_weak_negative_candidate_count": system["system_weak_negative_candidate_count"],
            "system_blocker_criteria": sorted(system_criteria),
            "negative_evidence_count": len(system["negative_evidence"]),
            "weak_negative_evidence_count": len(system["weak_negative_evidence"]),
            "grounded_flaw_count": len(system["grounded_flaws"]),
            "weak_flaw_count": len(system["weak_flaws"]),
            "paper_unresolved_count": len(system["paper_unresolved"]),
            "weak_unresolved_count": len(system["weak_unresolved"]),
            "meta_flaw_count": len(system["meta_flaws"]),
            "meta_unresolved_count": len(system["meta_unresolved"]),
            "real_strong_support_total": sim.get("real_strong_support_total", system["real_strong_support_total"]),
            "non_abstract_support_total": sim.get("non_abstract_support_total", system["non_abstract_support_total"]),
            "oracle_core_hard_weakness": oracle_core_hard,
            "oracle_hard_weakness_count": oracle_row.get("oracle_hard_weakness_count", 0),
            "oracle_hard_criteria": oracle_hard_criteria,
            "negative_formation_gap": gap,
            "next_action": next_action,
            "examples": {
                "negative_evidence": system["negative_evidence"][:2],
                "weak_negative_evidence": system["weak_negative_evidence"][:2],
                "grounded_flaws": system["grounded_flaws"][:2],
                "weak_flaws": system["weak_flaws"][:2],
                "paper_unresolved": system["paper_unresolved"][:2],
                "weak_unresolved": system["weak_unresolved"][:2],
            },
        })

    summary = {
        "input_jsonl": args.jsonl,
        "criterion_sim_json": args.criterion_sim,
        "oracle_audit_json": args.oracle_audit,
        "rows": len(out_rows),
        "group_summaries": {
            "false_accept": summarize_group(out_rows, "false_accept"),
            "recovered_accept": summarize_group(out_rows, "recovered_accept"),
            "false_reject_or_unrecovered_accept": summarize_group(out_rows, "false_reject_or_unrecovered_accept"),
            "other": summarize_group(out_rows, "other"),
        },
        "formation_gap_criteria": dict(formation_gap_criteria),
        "system_blocker_criteria": dict(system_criteria_counter),
        "case_rows": out_rows,
    }

    output_json = Path(args.output_json)
    write_json(output_json, summary)

    doc_dir = Path(args.doc_dir)
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V1_SCHEMA.md", render_schema())
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V1_AUDIT.md", render_audit({
        **summary,
        "formation_gap_criteria": formation_gap_criteria,
        "system_blocker_criteria": system_criteria_counter,
    }))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V1_CASE_TABLE.md", render_case_table(out_rows))
    write_md(doc_dir / "NEGATIVE_EVIDENCE_FORMATION_V1_DECISION.md", render_decision(summary))

    print(json.dumps({
        "json": str(output_json),
        "docs": [
            "NEGATIVE_EVIDENCE_FORMATION_V1_SCHEMA.md",
            "NEGATIVE_EVIDENCE_FORMATION_V1_AUDIT.md",
            "NEGATIVE_EVIDENCE_FORMATION_V1_CASE_TABLE.md",
            "NEGATIVE_EVIDENCE_FORMATION_V1_DECISION.md",
        ],
        "group_summaries": summary["group_summaries"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
