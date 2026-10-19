"""Execute the regression suite and frozen development challenge, with actual saved demos."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from procureguard.evaluation import evaluate_challenge
from procureguard.data_loader import load_dataset
from procureguard.evidence import EvidenceRepository
from procureguard.investigation import investigate,snapshot_hash
from procureguard.case_store import CaseStore
from procureguard.lifecycle import dataset_namespace


def main():
    run=subprocess.run([sys.executable,str(ROOT/'scripts/validate_v2.py')],cwd=ROOT)
    if run.returncode:raise SystemExit(run.returncode)
    base=json.loads((ROOT/'reports/validation_v2.json').read_text(encoding='utf-8'))
    challenge=evaluate_challenge(ROOT)
    data=load_dataset(ROOT/'data/synthetic');repository=EvidenceRepository(ROOT/'data/evidence')
    scratch=ROOT/'build/v3-evidence';scratch.mkdir(parents=True,exist_ok=True)
    # Unique DB records a fresh demonstration without overwriting existing user history.
    from uuid import uuid4
    store=CaseStore(scratch/(uuid4().hex+'.sqlite'))
    before=investigate(data,'PG104',repository)
    store.save(before,expected_version=0,request_key='missing')
    store.review('PG104',expected_version=1,actor='ap_reviewer',action='request_recheck',rationale='Obtain the delayed warehouse receipt')
    after=investigate(data,'PG104',repository,released=True)
    store.save(after,expected_version=2,request_key='resumed')
    recovered=CaseStore(store.path).recover('PG104',snapshot_hash(data))
    resume={'before':before.final['recommendation'],'after':after.final['recommendation'],
            'current_revision':recovered['version'],'same_run_reopened':recovered['result']['final']['run_id']==after.final['run_id'],
            'history':store.history('PG104'),'source_unchanged':before.source_snapshot_hash==after.source_snapshot_hash,
            'packet_before':before.to_dict(),'packet_after':after.to_dict()}
    ledger_before=investigate(data,'PG105',repository)
    store.set_lifecycle(data,'PG105B','rejected',expected_status='submitted',actor='ap_reviewer',rationale='Reject the second synthetic submission after human review')
    updated=store.effective_data(data,dataset_namespace(data))
    ledger_after=investigate(updated,'PG105',repository)
    lifecycle={'before':ledger_before.final['recommendation'],'after':ledger_after.final['recommendation'],
               'excluded_invoice':'PG105B','classification':updated.invoices['PG105B']['lifecycle_status'],
               'history':store.history('PG105B'),'integrity':store.verify_integrity(),
               'packet_before':ledger_before.to_dict(),'packet_after':ledger_after.to_dict()}
    live_path=ROOT/'reports/live_planner_run.json'
    live=json.loads(live_path.read_text(encoding='utf-8')) if live_path.exists() else None
    live_summary={k:live[k] for k in ('executed_at','model','agreement','live_choices','fallbacks','boundary')} if live else None
    if live_summary:live_summary['case_count']=len(live['cases'])
    report={'executed_at':datetime.now(timezone.utc).isoformat(),'regression_tests':base['tests'],
            'regression_scenarios':{'agreement':base['agreement'],'total':base['scenarios']},
            'challenge_sha256':hashlib.sha256((ROOT/'data/challenge_v3.json').read_bytes()).hexdigest(),
            'challenge':challenge,'live_model':live_summary,'case_recovery':resume,'lifecycle_demo':lifecycle}
    (ROOT/'reports/validation_v3.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (ROOT/'reports/evolving_case_demo.json').write_text(json.dumps({'resume':resume,'lifecycle':lifecycle},indent=2),encoding='utf-8')
    metrics=challenge['metrics']
    final=next(m for m in metrics if m['mode']=='Historical audit with critic')
    print('Challenge results:',json.dumps(metrics,indent=2))
    print('Restored packet:',resume['same_run_reopened'],'Lifecycle transition:',lifecycle['before'],'to',lifecycle['after'])
    if final['exact_agreement']!=challenge['case_count'] or not resume['same_run_reopened'] or not lifecycle['integrity']['valid']:
        raise SystemExit('v3 validation did not pass')


if __name__=='__main__':main()
