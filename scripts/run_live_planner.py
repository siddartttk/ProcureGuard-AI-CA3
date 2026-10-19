"""Record a real installed Ollama run. Never download models or substitute mock results."""
import argparse
import json
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from procureguard.planning import OllamaPlannerModel
from procureguard.data_loader import load_dataset
from procureguard.evidence import EvidenceRepository
from procureguard.investigation import investigate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',default='qwen2.5-coder:7b')
    args=parser.parse_args()
    installed=OllamaPlannerModel.available_models()
    if args.model not in installed:raise SystemExit('Selected model is not installed; no model will be downloaded')
    data=load_dataset(ROOT/'data/synthetic');repository=EvidenceRepository(ROOT/'data/evidence')
    expected={'PG103':'READY_FOR_HUMAN_APPROVAL','PG106':'HOLD_FOR_REVIEW','PG107':'HOLD_FOR_REVIEW','PG109':'READY_FOR_HUMAN_APPROVAL'}
    cases=[]
    for identity,label in expected.items():
        result=investigate(data,identity,repository,model=OllamaPlannerModel(args.model))
        live=sum(bool(s.get('planner_record',{}).get('live_inference')) for s in result.steps)
        fallbacks=sum(bool(s.get('fallback')) for s in result.steps)
        cases.append({'invoice_id':identity,'expected':label,'actual':result.final['recommendation'],
                      'agreement':result.final['recommendation']==label,'live_choices':live,'fallbacks':fallbacks,
                      'steps':result.steps,'elapsed_ms':result.elapsed_ms,'packet':result.to_dict()})
        print(identity,result.final['recommendation'],'live choices:',live,'fallbacks:',fallbacks,flush=True)
    report={'executed_at':datetime.now(timezone.utc).isoformat(),'model':args.model,'installed_models':installed,
            'endpoint':'http://127.0.0.1:11434','cases':cases,'agreement':sum(c['agreement'] for c in cases),
            'live_choices':sum(c['live_choices'] for c in cases),'fallbacks':sum(c['fallbacks'] for c in cases),
            'boundary':'Real local model inference on four known synthetic scenarios. No model-superiority or field-performance claim. No model download or paid API.'}
    (ROOT/'reports/live_planner_run.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if report['fallbacks'] or not report['live_choices']:raise SystemExit('Live demo incomplete; recorded fallbacks remain labelled')


if __name__=='__main__':main()
