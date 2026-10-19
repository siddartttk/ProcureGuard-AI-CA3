import csv
import json
from pathlib import Path
import pytest
from procureguard.orchestrator import audit
from procureguard.data_loader import parse_csv, from_tables
from procureguard.schemas import SCHEMAS
from procureguard.reporting import record_review, report_json
from procureguard.policies import Policy
from data.generate_demo_data import generate


def test_dynamic_routes(dataset):
    a,b,c=[audit(dataset,x) for x in ('INV001','INV022','INV016')]
    assert 'Risk' not in [e['agent'] for e in a.trace]
    assert 'Risk' in [e['agent'] for e in b.trace]
    assert 'missing_evidence' in [e['tool'] for e in c.trace]
    assert 'missing_evidence' not in [e['tool'] for e in a.trace]


def test_all_valid_invoices_receive_mandatory_screen(dataset):
    for identity in dataset.invoices:
        s=audit(dataset,identity)
        if not any(f.code=='INVALID_DATA' for f in s.findings):
            assert 'mandatory_risk_screen' in [e['tool'] for e in s.trace]


def test_trace_contract_and_sequence(dataset):
    s=audit(dataset,'INV022')
    assert [e['sequence'] for e in s.trace] == list(range(1,len(s.trace)+1))
    assert all(all(e[k] for k in ('timestamp','agent','tool','action','outcome','condition','next_step','input_summary')) for e in s.trace)


def test_missing_and_risk_preserved(dataset):
    dataset.invoices['INV016']['bank_token']='DEMO-ALTERED'
    s=audit(dataset,'INV016')
    assert {f.code for f in s.findings} == {'MISSING_GRN','BANK_CHANGE'}
    assert s.recommendation == 'INSUFFICIENT_DATA' and s.verified


def test_no_automatic_payment_and_review_log(dataset,tmp_path):
    s=audit(dataset,'INV001'); before=s.recommendation
    e=record_review(s,'confirm_recommendation','Evidence examined in classroom demo',tmp_path/'review.jsonl')
    assert not s.payment_executed and not e['payment_executed'] and e['simulation']
    assert e['actor']=='demo_reviewer' and s.recommendation == before
    assert json.loads((tmp_path/'review.jsonl').read_text()) == e


def test_payment_action_not_supported(dataset,tmp_path):
    with pytest.raises(ValueError): record_review(audit(dataset,'INV001'),'pay','test',tmp_path/'review.jsonl')


def test_review_requires_rationale(dataset,tmp_path):
    with pytest.raises(ValueError): record_review(audit(dataset,'INV001'),'confirm_recommendation',' ',tmp_path/'review.jsonl')


def test_export_contains_real_evidence(dataset):
    parsed=json.loads(report_json(audit(dataset,'INV022')))
    assert parsed['invoice_id']=='INV022' and parsed['verified']
    assert len(parsed['findings']) == 3 and parsed['trace'][-1]['agent']=='Decision'


def test_unknown_invoice_handled(dataset):
    with pytest.raises(ValueError,match='Unknown invoice'): audit(dataset,'ABSENT')


def test_malformed_csv_rejected():
    with pytest.raises(ValueError): parse_csv('invoice_id,bad\nfoo,bar','invoices')


def test_extra_columns_rejected():
    header=','.join(SCHEMAS['vendors'])
    with pytest.raises(ValueError): parse_csv(header+'\nV1,Name,active,BANK,EXTRA','vendors')


def test_duplicate_primary_keys_rejected(dataset):
    tables={name:list(getattr(dataset,name).values()) for name in SCHEMAS}
    tables['invoices'].append(tables['invoices'][0])
    with pytest.raises(ValueError,match='duplicate primary key'): from_tables(tables)


def test_generation_reproducible(tmp_path):
    a,b=generate(tmp_path/'a'),generate(tmp_path/'b')
    assert all(p.read_bytes()==(b/p.name).read_bytes() for p in a.glob('*.csv'))


def test_full_corpus_answer_key(dataset):
    key=Path(__file__).resolve().parents[1]/'data/synthetic/expected_outcomes.csv'
    for row in csv.DictReader(key.open(encoding='utf-8')):
        s=audit(dataset,row['invoice_id'])
        assert s.recommendation == row['expected_decision'], row
        assert {f.code for f in s.findings} == set(filter(None,row['expected_codes'].split(';'))), row
        assert s.verified, row


def test_answer_key_unavailable_to_agents(dataset):
    assert set(vars(dataset)) == {'vendors','purchase_orders','goods_receipts','invoices','errors'}


def test_policy_rejects_unbounded_retry():
    with pytest.raises(ValueError): Policy(max_rechecks=10)


def test_schema_error_cannot_reach_ready(dataset):
    dataset.invoices['INV001']['currency']='USD'
    assert audit(dataset,'INV001').recommendation == 'INSUFFICIENT_DATA'
