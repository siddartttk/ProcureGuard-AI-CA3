"""Offline development evaluation. Unverified baselines never serve runtime decisions."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from .data_loader import from_tables
from .orchestrator import audit
from .policies import Policy
from . import tools


def challenge_cases(root: Path):
    raw=(root/'data/challenge_v3.json').read_bytes()
    expected=(root/'data/challenge_v3.sha256').read_text(encoding='ascii').strip()
    if hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('Frozen challenge changed: integrity check failed')
    document=json.loads(raw)
    for case in document['cases']:
        tables=deepcopy(document['base'])
        for table,index,key,value in case['changes']:
            if index is None:tables[table]=deepcopy(value)
            else:tables[table][index][key]=value
        if case['peer'] is not None:tables['invoices'].append(deepcopy(case['peer']))
        yield case,from_tables(tables),document['target_invoice']


def producer_baseline(data,identity,*,history,fault=None):
    """Evaluation-only candidate outcome with no independent critic claim."""
    data=deepcopy(data)
    if not history:data.invoices={identity:data.invoices[identity]}
    invoice=data.invoices[identity];p=Policy()
    findings=tools.schema_check(data,invoice,p)
    if not findings:
        for name,tool in tools.MATCH_TOOLS.items():
            if fault=='omit_amounts' and name=='amount_comparison':continue
            findings.extend(tool(data,invoice,p))
        for tool in tools.RISK_TOOLS.values():findings.extend(tool(data,invoice,p))
        findings.extend(tools.compound(findings))
    decision='INSUFFICIENT_DATA' if any(f.severity=='missing' for f in findings) else 'HOLD_FOR_REVIEW' if findings else 'READY_FOR_HUMAN_APPROVAL'
    return {'decision':decision,'codes':[f.code for f in findings],'critic_interventions':0,'independently_verified':False}


def verified_result(data,identity,fault=None):
    original=tools.MATCH_TOOLS['amount_comparison']
    try:
        if fault=='omit_amounts':tools.MATCH_TOOLS['amount_comparison']=lambda *args:[]
        result=audit(data,identity)
    finally:tools.MATCH_TOOLS['amount_comparison']=original
    return {'decision':result.recommendation,'codes':[f.code for f in result.findings],
            'critic_interventions':sum(not v['passed'] for v in result.verifications),
            'independently_verified':result.verified}


def evaluate_challenge(root):
    rows=[]
    for case,data,identity in challenge_cases(root):
        modes={
            'Single-invoice producer baseline':producer_baseline(data,identity,history=False,fault=case['fault']),
            'Historical producer baseline':producer_baseline(data,identity,history=True,fault=case['fault']),
            'Historical audit with critic':verified_result(data,identity,case['fault']),
        }
        for mode,result in modes.items():
            rows.append({'case':case['name'],'mode':mode,'expected':case['expected'],**result,
                         'fault_injection':case['fault'] or 'none','agreement':result['decision']==case['expected']})
    metrics=[]
    for mode in dict.fromkeys(r['mode'] for r in rows):
        subset=[r for r in rows if r['mode']==mode]
        true_flags=sum(r['expected']!='READY_FOR_HUMAN_APPROVAL' and r['decision']!='READY_FOR_HUMAN_APPROVAL' for r in subset)
        missed=sum(r['expected']!='READY_FOR_HUMAN_APPROVAL' and r['decision']=='READY_FOR_HUMAN_APPROVAL' for r in subset)
        false_flags=sum(r['expected']=='READY_FOR_HUMAN_APPROVAL' and r['decision']!='READY_FOR_HUMAN_APPROVAL' for r in subset)
        metrics.append({'mode':mode,'cases':len(subset),'exact_agreement':sum(r['agreement'] for r in subset),
                        'missed_actionable_cases':missed,'incorrect_ready':missed,'false_holds_or_gaps':false_flags,
                        'flag_precision':true_flags/(true_flags+false_flags) if true_flags+false_flags else None,
                        'flag_recall':true_flags/(true_flags+missed) if true_flags+missed else None,
                        'critic_interventions':sum(r['critic_interventions'] for r in subset)})
    return {'rows':rows,'metrics':metrics,'case_count':len(rows)//3,
            'boundary':'Frozen development challenge authored by the same assistant before v3 changes. Two cases deliberately corrupt the matcher. Not independently held-out or field data. Unverified producer baselines are evaluation-only.'}
