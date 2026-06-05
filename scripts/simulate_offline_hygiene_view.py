import json, re
from pathlib import Path

RESULTS = Path('outputs/results_main/review_infer/evidence_binding_v1_mixed16.jsonl')
DATASET = Path('outputs/subsets/state_hygiene_mixed_v2.parquet')
OUT_JSON = Path('outputs/results_main/review_infer/binding_v1_offline_hygiene_view_results.json')
OUT_MD = Path('docs/experiments/BINDING_V1_OFFLINE_HYGIENE_VIEW_SIMULATION.md')
CASE_MD = Path('docs/experiments/BINDING_V1_OFFLINE_HYGIENE_CASE_TABLE.md')

SUPPORT_STANCES={'supports','partially_supports'}
META_TERMS=('fallback','could not bind','verify whether','locate a concrete','check whether','excerpt','cuts off','ensure the evidence','resolve the','unable to','cannot verify')

def norm_gold(x):
    if x is None: return None
    s=str(x).strip().lower()
    if 'accept' in s or s in {'1','true'}: return 'accept'
    if 'reject' in s or s in {'0','false'}: return 'reject'
    return None

def load_gold():
    if not DATASET.exists():
        return {}
    gold = {}
    try:
        import pyarrow.parquet as pq
        table = pq.read_table(DATASET)
        cols = {name: table[name].to_pylist() for name in table.column_names}
        n = table.num_rows
        for i in range(n):
            pid = None
            for key in ('paper_id', 'id', 'task_id'):
                if key in cols and cols[key][i] is not None:
                    pid = cols[key][i]
                    break
            g = None
            for key in ('gold_decision', 'ground_truth_decision', 'decision', 'label'):
                if key in cols and cols[key][i] is not None:
                    g = norm_gold(cols[key][i])
                    if g:
                        break
            env = cols.get('env_kwargs', [None] * n)[i] if 'env_kwargs' in cols else None
            if g is None and isinstance(env, dict):
                g = norm_gold(env.get('ground_truth_decision') or env.get('gold_decision'))
            if pid and g:
                gold[str(pid)] = g
    except Exception as exc:
        print(f'warning: could not load gold labels from parquet: {exc}')
    return gold

def open_unresolved(state):
    return [q for q in state.get('unresolved_questions',[]) or [] if (q.get('status') or 'open')=='open']

def is_meta(text):
    low=str(text or '').lower()
    return any(t in low for t in META_TERMS)

def real_claim_ids(state):
    return {str(c.get('claim_id') or c.get('id')) for c in state.get('claims',[]) or [] if not str(c.get('claim_id') or c.get('id') or '').startswith('claim-fallback')}

def real_strong_support(state):
    claims=real_claim_ids(state)
    per={}
    total=0
    for e in state.get('evidence_map',[]) or []:
        cid=str(e.get('claim_id') or '')
        if cid in claims and e.get('binding_status')=='bound_real_claim' and e.get('strength')=='strong' and e.get('stance') in SUPPORT_STANCES:
            total+=1; per[cid]=per.get(cid,0)+1
    return total,per

def stale_gap_count(state, support_per_claim):
    stale=[]; kept=[]
    for gap in state.get('evidence_gaps',[]) or []:
        text=str(gap or '')
        if 'claim-fallback' in text:
            stale.append(text); continue
        hit=False
        for cid,count in support_per_claim.items():
            if count>0 and cid in text:
                hit=True; break
        (stale if hit else kept).append(text)
    return stale, kept

def conflict_counts(state, support_per_claim):
    stale=[]; kept=[]
    for c in state.get('conflict_notes',[]) or []:
        ctype=str(c.get('conflict_type') or '')
        note=str(c.get('note') or '').lower()
        cid=str(c.get('claim_id') or '')
        if ctype.startswith('fallback') or (cid and support_per_claim.get(cid,0)>=1 and ('fallback' in note or 'evidence-fallback' in note)):
            stale.append(c); continue
        kept.append(c)
    return stale, kept

def flaw_counts(state):
    confirmed=major=critical=grounded=ungrounded=fallback=0
    for f in state.get('flaw_candidates',[]) or []:
        status=f.get('status') or 'candidate'
        fid=str(f.get('flaw_id') or '')
        ev=f.get('evidence_ids') or []
        if fid.startswith('flaw-fallback') or f.get('source') in {'fallback','system_meta'}:
            fallback+=1
            continue
        if not ev:
            ungrounded+=1
            continue
        grounded+=1
        if status not in {'downgraded','retracted'}:
            if f.get('severity')=='critical': critical+=1
            if f.get('severity')=='major': major+=1
            if status=='confirmed': confirmed+=1
    return {'confirmed':confirmed,'major':major,'critical':critical,'grounded':grounded,'ungrounded':ungrounded,'fallback':fallback}

def derive_decision(state):
    strong,per=real_strong_support(state)
    stale_gaps, kept_gaps=stale_gap_count(state,per)
    stale_conf, kept_conf=conflict_counts(state,per)
    fl=flaw_counts(state)
    unresolved=open_unresolved(state)
    meta_unres=[q for q in unresolved if is_meta(q.get('question',''))]
    paper_unres=[q for q in unresolved if q not in meta_unres]
    # conservative derived view: only real strong support counts; fallback/meta negatives are removed from blockers.
    blockers=[]
    if fl['critical']>0: blockers.append('critical_flaw')
    if fl['major']>=2: blockers.append('major_flaws>=2')
    if len(paper_unres)>=6: blockers.append('paper_unresolved>=6')
    if len(kept_conf)>=4: blockers.append('conflicts>=4')
    if blockers:
        decision='reject'
    elif strong>=2 and fl['major']==0 and len(paper_unres)<=3:
        decision='accept'
    else:
        decision='reject'
    return {
        'decision':decision,'real_strong_support':strong,'support_per_claim':per,
        'stale_gap_count':len(stale_gaps),'kept_gap_count':len(kept_gaps),
        'meta_unresolved_count':len(meta_unres),'paper_unresolved_count':len(paper_unres),
        'stale_conflict_count':len(stale_conf),'kept_conflict_count':len(kept_conf),
        **{f'flaw_{k}':v for k,v in fl.items()},
        'blockers':blockers,
    }

def f1(tp,fp,fn):
    return 0.0 if 2*tp+fp+fn==0 else 2*tp/(2*tp+fp+fn)

def summarize(rows,gold):
    labels=[gold.get(pid) for pid,_ in rows if gold.get(pid)]
    pred=[m['decision'] for pid,m in rows if gold.get(pid)]
    acc=sum(a==b for a,b in zip(labels,pred))/len(labels) if labels else None
    tp_a=sum(p=='accept' and g=='accept' for p,g in zip(pred,labels)); fp_a=sum(p=='accept' and g=='reject' for p,g in zip(pred,labels)); fn_a=sum(p=='reject' and g=='accept' for p,g in zip(pred,labels))
    tp_r=sum(p=='reject' and g=='reject' for p,g in zip(pred,labels)); fp_r=sum(p=='reject' and g=='accept' for p,g in zip(pred,labels)); fn_r=sum(p=='accept' and g=='reject' for p,g in zip(pred,labels))
    return {'labeled_rows':len(labels),'accuracy':acc,'accept_recall':(tp_a/(tp_a+fn_a) if tp_a+fn_a else None),'reject_recall':(tp_r/(tp_r+fn_r) if tp_r+fn_r else None),'macro_f1':(f1(tp_a,fp_a,fn_a)+f1(tp_r,fp_r,fn_r))/2 if labels else None,'predicted_accept_count':sum(p=='accept' for p in pred),'false_accept_ids':[pid for (pid,m),g,p in zip(rows,labels,pred) if p=='accept' and g=='reject'],'recovered_accept_ids':[pid for (pid,m),g,p in zip(rows,labels,pred) if p=='accept' and g=='accept']}

gold=load_gold()
rows=[]; original=[]
for line in RESULTS.read_text().splitlines():
    if not line.strip(): continue
    r=json.loads(line); pid=str(r.get('paper_id') or r.get('task_id'))
    st=r.get('review_state') or {}
    m=derive_decision(st); rows.append((pid,m))
    original.append((pid, {'decision': r.get('final_decision') or st.get('final_decision') or 'reject'}))
summary={'source':str(RESULTS),'rows':len(rows),'derived':summarize(rows,gold),'original':summarize(original,gold),'aggregate':{}}
for key in ['real_strong_support','stale_gap_count','kept_gap_count','meta_unresolved_count','paper_unresolved_count','stale_conflict_count','kept_conflict_count','flaw_major','flaw_critical','flaw_grounded','flaw_ungrounded','flaw_fallback']:
    summary['aggregate'][key]=sum(m[key] for _,m in rows)
summary['case_rows']=[{'paper_id':pid,'gold':gold.get(pid),**m} for pid,m in rows]
OUT_JSON.parent.mkdir(parents=True,exist_ok=True); OUT_JSON.write_text(json.dumps(summary,indent=2,ensure_ascii=False))

md=[]
md.append('# Binding v1 Offline Hygiene View Simulation\n')
md.append('Input: `outputs/results_main/review_infer/evidence_binding_v1_mixed16.jsonl`. This is an offline derived-view simulation only: no model rerun and no live state mutation.\n')
md.append('## Summary\n')
for k,v in summary['original'].items(): md.append(f'- original_{k}: {v}\n')
for k,v in summary['derived'].items(): md.append(f'- derived_{k}: {v}\n')
md.append('\n## Aggregate Hygiene Signals\n')
for k,v in summary['aggregate'].items(): md.append(f'- {k}: {v}\n')
md.append('\n## Decision\n')
md.append('Offline hygiene is the right next diagnostic because runtime hygiene changed the trajectory and reduced positive support. This simulation isolates the final-view effect on the fixed Binding v1 state.\n')
OUT_MD.write_text(''.join(md))

case=[]
case.append('# Binding v1 Offline Hygiene Case Table\n\n')
case.append('| paper_id | gold | derived | real_strong | paper_unresolved | meta_unresolved | kept_conflicts | stale_conflicts | major_flaws | blockers |\n')
case.append('|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n')
for row in summary['case_rows']:
    case.append(f"| {row['paper_id']} | {row.get('gold')} | {row['decision']} | {row['real_strong_support']} | {row['paper_unresolved_count']} | {row['meta_unresolved_count']} | {row['kept_conflict_count']} | {row['stale_conflict_count']} | {row['flaw_major']} | {','.join(row['blockers']) or '-'} |\n")
CASE_MD.write_text(''.join(case))
print(json.dumps(summary['derived'],indent=2))
print('wrote', OUT_JSON, OUT_MD, CASE_MD)
