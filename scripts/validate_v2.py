"""Reproduce tests, known scenario outcomes, baseline comparisons and workload timing."""
import csv
import json
import os
import platform
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from procureguard.data_loader import load_dataset
from procureguard.evidence import EvidenceRepository
from procureguard.investigation import investigate

# Declarative expectations are outside the runtime input and planner context.
EXPECTED={'PG101':'READY_FOR_HUMAN_APPROVAL','PG102':'READY_FOR_HUMAN_APPROVAL',
          'PG103':'READY_FOR_HUMAN_APPROVAL','PG104':'INSUFFICIENT_DATA','PG105':'HOLD_FOR_REVIEW',
          'PG105B':'HOLD_FOR_REVIEW','PG106':'HOLD_FOR_REVIEW','PG107':'HOLD_FOR_REVIEW',
          'PG108':'HOLD_FOR_REVIEW','PG109':'READY_FOR_HUMAN_APPROVAL','PG110':'INSUFFICIENT_DATA'}


def main():
    reports=ROOT/'reports';reports.mkdir(exist_ok=True)
    scratch=ROOT/'build'/('validation-'+uuid4().hex[:8]);scratch.mkdir(parents=True)
    env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    env['TEMP']=env['TMP']=str(scratch)
    command=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',f'--basetemp={scratch / "pytest"}',f'--junitxml={reports / "pytest-results.xml"}']
    run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True)
    (reports/'pytest-output.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    print(run.stdout)
    if not (reports/'pytest-results.xml').exists():raise SystemExit('No fresh test report produced')
    tests=[]
    for row in ET.parse(reports/'pytest-results.xml').findall('.//testcase'):
        status='failed' if row.find('failure') is not None or row.find('error') is not None else 'skipped' if row.find('skipped') is not None else 'passed'
        tests.append({'test':row.get('classname')+'.'+row.get('name'),'status':status,'seconds':float(row.get('time','0'))})
    data=load_dataset(ROOT/'data/synthetic');repository=EvidenceRepository(ROOT/'data/evidence')
    comparisons=[];packets=[]
    def evaluate(identity,expected,scenario,released=False):
        result=investigate(data,identity,repository,released=released)
        comparisons.append({'Case':identity+(' / resumed' if released else ''),'Scenario':scenario,
                            'Rules-only baseline':result.initial['recommendation'],'With evidence':result.final['recommendation'],
                            'Expected':expected,'Agreement':result.final['recommendation']==expected,
                            'Evidence lookups':len(result.steps),'Verified':result.final['verified']})
        packets.append(result.to_dict())
    with (ROOT/'data/synthetic/expected_outcomes.csv').open() as handle:
        for row in csv.DictReader(handle):evaluate(row['invoice_id'],row['expected_decision'],row['scenario'])
    catalog=json.loads((ROOT/'data/scenarios.json').read_text())
    for identity,expected in EXPECTED.items():evaluate(identity,expected,catalog.get(identity,catalog['PG105'])['title'])
    evaluate('PG104','READY_FOR_HUMAN_APPROVAL','Delayed receipt now available',released=True)
    timings=[]
    for _ in range(5):
        start=perf_counter()
        for identity in EXPECTED:investigate(data,identity,repository)
        timings.append((perf_counter()-start)*1000)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
            'planner':'Offline mock planner; no live Ollama inference included',
            'tests':{'total':len(tests),'passed':sum(t['status']=='passed' for t in tests),
                     'failed':sum(t['status']=='failed' for t in tests),'skipped':sum(t['status']=='skipped' for t in tests),'cases':tests},
            'invoices':len(data.invoices),'scenarios':len(comparisons),'operational_scenarios':12,
            'agreement':sum(r['Agreement'] for r in comparisons),
            'resolved':sum(r['Rules-only baseline']!='READY_FOR_HUMAN_APPROVAL' and r['With evidence']=='READY_FOR_HUMAN_APPROVAL' for r in comparisons),
            'comparisons':comparisons,'timing':{'workload':'11 operational investigations per run; five runs',
               'samples_ms':[round(t,3) for t in timings],'median_ms':round(statistics.median(timings),3),
               'minimum_ms':round(min(timings),3),'maximum_ms':round(max(timings),3)},
            'limitations':['Known synthetic scenarios, not independently authored held-out or field data',
                           'No measured human-review time, organisational savings or LLM superiority claim',
                           'Baseline shares accounting rules; comparison isolates access to authorised evidence',
                           'Role identity and upstream approval metadata are simulated; event hashes are not immutable storage']}
    (reports/'validation_v2.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (reports/'investigation_packets.json').write_text(json.dumps(packets,indent=2),encoding='utf-8')
    with (reports/'scenario_comparison.csv').open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(comparisons[0]));writer.writeheader();writer.writerows(comparisons)
    doc=['# Executed validation','',f"{report['tests']['passed']}/{report['tests']['total']} tests passed; {report['tests']['failed']} failures/errors; {report['tests']['skipped']} skipped.",
         f"Executed {report['generated_at']} using Python {report['python']}.",'',
         f"{report['agreement']}/{report['scenarios']} known scenario decisions agree: 32 original regression scenarios and 12 operational scenarios (including a delayed-evidence resume). The operational dataset contains {report['invoices']} invoices.",'',
         f"{report['resolved']} initially blocked scenario runs became ready for human review after authorised evidence acquisition. This includes PG104 before and after evidence availability as two explicit scenarios.",'',
         '## What the comparison establishes','',
         'The same deterministic accounting checker is used in the baseline and evidence workflow. The difference is access to verified warehouse, procurement and vendor-master evidence. This demonstrates exception resolution beyond initial flags; it does not establish that multiple agents or an LLM outperform a simpler implementation.','',
         '## Workload timing','',json.dumps(report['timing'],indent=2),'',
         '## Limits','']+['- '+s for s in report['limitations']]+['',
         '## Evidence files','',
         'reports/pytest-output.txt and pytest-results.xml record actual execution. validation_v2.json, scenario_comparison.csv and investigation_packets.json contain results, comparisons, before/after state, source snapshots and tool traces.','',
         '## Reproduce','', 'Run `python scripts/validate_v2.py` after installing requirements-tested.txt. Never quote an old report as evidence of modified code.']
    (ROOT/'docs/validation_report.md').write_text('\n'.join(doc)+'\n',encoding='utf-8')
    print(f"Scenario agreement {report['agreement']}/{report['scenarios']}; evidence-driven resolutions {report['resolved']}")
    if run.returncode or report['agreement']!=report['scenarios']:raise SystemExit(1)


if __name__=='__main__':main()
