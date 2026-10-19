from copy import deepcopy
from pathlib import Path
import sqlite3
import pytest
from streamlit.testing.v1 import AppTest
from procureguard.case_store import CaseStore,VersionConflict
from procureguard.evidence import EvidenceRepository
from procureguard.investigation import investigate,snapshot_hash
from procureguard.lifecycle import dataset_namespace
from procureguard.orchestrator import audit
from procureguard.data_loader import parse_csv
from procureguard.schemas import SCHEMAS
from procureguard.evaluation import challenge_cases,verified_result,evaluate_challenge

ROOT=Path(__file__).resolve().parents[1]
CASES=list(challenge_cases(ROOT))


@pytest.mark.parametrize('case,data,identity',CASES,ids=[case['name'] for case,_,_ in CASES])
def test_frozen_challenge(case,data,identity):
    result=verified_result(data,identity,case['fault'])
    assert result['decision']==case['expected']


@pytest.fixture
def packet(dataset):
    return investigate(dataset,'PG103',EvidenceRepository(ROOT/'data/evidence'))


def test_recover_after_reopening_database(tmp_path,packet):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(packet,expected_version=0,request_key='first')
    restored=CaseStore(store.path).recover('PG103',packet.source_snapshot_hash)
    assert restored['result']==packet.to_dict() and restored['version']==1


def test_recover_uses_latest_review_revision(tmp_path,packet):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(packet,expected_version=0,request_key='first')
    store.review('PG103',expected_version=1,actor='ap_reviewer',action='request_recheck',rationale='Need revalidation')
    restored=store.recover('PG103',packet.source_snapshot_hash)
    assert restored['run_version']==1 and restored['version']==2


def test_different_source_snapshot_cannot_recover(tmp_path,packet):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(packet,expected_version=0,request_key='first')
    assert store.recover('PG103','different-data') is None


def test_recover_rejects_corrupt_packet(tmp_path,packet):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(packet,expected_version=0,request_key='first')
    with sqlite3.connect(store.path) as db:db.execute("UPDATE runs SET content='{}'")
    with pytest.raises(ValueError):store.recover('PG103',packet.source_snapshot_hash)


def test_lifecycle_persists_and_releases_other_invoice_capacity(tmp_path,dataset):
    store=CaseStore(tmp_path/'cases.sqlite');namespace=dataset_namespace(dataset)
    assert audit(dataset,'PG105').recommendation=='HOLD_FOR_REVIEW'
    store.set_lifecycle(dataset,'PG105B','rejected',expected_status='submitted',actor='ap_reviewer',rationale='Second submission rejected by demo reviewer')
    reopened=CaseStore(store.path).effective_data(dataset,namespace)
    assert audit(reopened,'PG105').recommendation=='READY_FOR_HUMAN_APPROVAL'
    assert audit(reopened,'PG105B').recommendation=='HOLD_FOR_REVIEW'
    assert store.verify_integrity()['valid']


def test_lifecycle_invalidates_previous_recommendation(tmp_path,dataset):
    store=CaseStore(tmp_path/'cases.sqlite');packet=investigate(dataset,'PG105',EvidenceRepository(ROOT/'data/evidence'))
    store.save(packet,expected_version=0,request_key='before')
    store.set_lifecycle(dataset,'PG105B','rejected',expected_status='submitted',actor='ap_reviewer',rationale='Reject second submission')
    updated=store.effective_data(dataset,dataset_namespace(dataset))
    assert store.recover('PG105',snapshot_hash(updated)) is None


def test_observer_cannot_change_lifecycle(tmp_path,dataset):
    with pytest.raises(PermissionError):CaseStore(tmp_path/'cases.sqlite').set_lifecycle(dataset,'PG105B','cancelled',expected_status='submitted',actor='faculty_observer',rationale='Forbidden')


def test_stale_lifecycle_change_rejected(tmp_path,dataset):
    store=CaseStore(tmp_path/'cases.sqlite')
    store.set_lifecycle(dataset,'PG105B','rejected',expected_status='submitted',actor='ap_reviewer',rationale='Reject')
    with pytest.raises(VersionConflict):store.set_lifecycle(dataset,'PG105B','cancelled',expected_status='submitted',actor='ap_reviewer',rationale='Stale tab')


def test_resubmission_reactivates_capacity(tmp_path,dataset):
    store=CaseStore(tmp_path/'cases.sqlite');namespace=dataset_namespace(dataset)
    store.set_lifecycle(dataset,'PG105B','cancelled',expected_status='submitted',actor='ap_reviewer',rationale='Cancelled')
    store.set_lifecycle(dataset,'PG105B','submitted',expected_status='cancelled',actor='ap_reviewer',rationale='Corrected submission received')
    assert audit(store.effective_data(dataset,namespace),'PG105').recommendation=='HOLD_FOR_REVIEW'


def test_duplicate_and_superseded_require_related_active_replacement(tmp_path,dataset):
    store=CaseStore(tmp_path/'cases.sqlite')
    with pytest.raises(ValueError):store.set_lifecycle(dataset,'PG105B','superseded',expected_status='submitted',actor='ap_reviewer',rationale='No replacement')
    with pytest.raises(ValueError):store.set_lifecycle(dataset,'PG105B','duplicate',expected_status='submitted',actor='ap_reviewer',rationale='Different invoice numbers',replacement='PG105')
    store.set_lifecycle(dataset,'PG105B','superseded',expected_status='submitted',actor='ap_reviewer',rationale='Replaced by first invoice',replacement='PG105')
    assert store.verify_integrity()['valid']


@pytest.mark.parametrize('tamper',["UPDATE cases SET status='READY_FOR_REVIEW'","UPDATE lifecycle SET status='recorded'","DELETE FROM lifecycle"])
def test_metadata_tampering_is_detected(tmp_path,dataset,tamper):
    store=CaseStore(tmp_path/'cases.sqlite')
    store.set_lifecycle(dataset,'PG105B','cancelled',expected_status='submitted',actor='ap_reviewer',rationale='Cancelled')
    with sqlite3.connect(store.path) as db:db.execute(tamper)
    assert not store.verify_integrity()['valid']


def test_duplicate_copies_do_not_inflate_other_capacity(dataset):
    first=dataset.invoices['PG105'];first.update(quantity='5',declared_total='500.00')
    dataset.invoices['PG105B'].update(quantity='5',declared_total='500.00')
    dataset.invoices['COPY']=dict(first,invoice_id='COPY')
    # First invoice and its copy are duplicates, but the distinct second obligation fits.
    assert audit(dataset,'PG105B').recommendation=='READY_FOR_HUMAN_APPROVAL'
    assert any(f.code=='DUPLICATE' for f in audit(dataset,'PG105').findings)


def test_conflicting_duplicate_values_block_ledger_confidence(dataset):
    dataset.invoices['COPY']=dict(dataset.invoices['PG105'],invoice_id='COPY',quantity='9',declared_total='900.00')
    assert audit(dataset,'PG105B').recommendation=='INSUFFICIENT_DATA'


def test_unknown_peer_lifecycle_cannot_silently_release_capacity(dataset):
    dataset.invoices['PG105B']['lifecycle_status']='unknown'
    result=audit(dataset,'PG105')
    assert result.verified and result.recommendation=='INSUFFICIENT_DATA'
    assert 'MISSING_LEDGER_CONTEXT' in {f.code for f in result.findings}


def test_csv_accepts_optional_lifecycle_column():
    header=','.join(SCHEMAS['invoices']+['lifecycle_status'])
    raw=header+'\nX,N,V,P,I,1,2.00,2.00,INR,DEMO,2026-10-01,rejected\n'
    assert parse_csv(raw,'invoices')[0]['lifecycle_status']=='rejected'


def test_fresh_browser_session_restores_packet(tmp_path,monkeypatch):
    monkeypatch.setenv('PROCUREGUARD_DB_PATH',str(tmp_path/'ui.sqlite'))
    original=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    original.sidebar.radio[0].set_value('Investigate a case').run()
    next(b for b in original.button if b.label=='Run investigation').click().run()
    run_id=original.session_state.results['PG103']['final']['run_id']
    fresh=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    fresh.sidebar.radio[0].set_value('Investigate a case').run()
    assert not fresh.exception
    assert fresh.session_state.results['PG103']['final']['run_id']==run_id
    assert fresh.session_state.versions['PG103']==1


def test_challenge_ablation_shows_critic_stops_corrupt_producer():
    report=evaluate_challenge(ROOT)
    metrics={r['mode']:r for r in report['metrics']}
    assert metrics['Historical audit with critic']['incorrect_ready']==0
    assert metrics['Historical producer baseline']['incorrect_ready']>=2
    assert metrics['Historical audit with critic']['critic_interventions']>=2


def test_distinct_imported_lifecycle_baselines_have_distinct_namespaces(dataset):
    changed=deepcopy(dataset);changed.invoices['PG105B']['lifecycle_status']='rejected'
    assert dataset_namespace(dataset)!=dataset_namespace(changed)


def test_other_browser_lifecycle_change_invalidates_displayed_packet(tmp_path,monkeypatch,dataset):
    path=tmp_path/'ui.sqlite';monkeypatch.setenv('PROCUREGUARD_DB_PATH',str(path))
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Investigate a case').run()
    app.selectbox[0].set_value('PG105').run()
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert app.session_state.results['PG105']['final']['recommendation']=='HOLD_FOR_REVIEW'
    CaseStore(path).set_lifecycle(dataset,'PG105B','rejected',expected_status='submitted',actor='ap_reviewer',rationale='Action in another browser')
    app.run()
    assert not app.exception and 'PG105' not in app.session_state.results
    next(b for b in app.button if b.label=='Run investigation').click().run()
    assert app.session_state.results['PG105']['final']['recommendation']=='READY_FOR_HUMAN_APPROVAL'


def test_ui_records_lifecycle_and_persists_after_restore(tmp_path,monkeypatch):
    monkeypatch.setenv('PROCUREGUARD_DB_PATH',str(tmp_path/'ui.sqlite'))
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    app.sidebar.radio[0].set_value('Investigate a case').run()
    app.selectbox[0].set_value('PG105B').run()
    next(s for s in app.selectbox if s.label=='New lifecycle classification').set_value('cancelled').run()
    next(t for t in app.text_input if t.label=='Lifecycle rationale').set_value('Cancelled fictional duplicate order').run()
    next(b for b in app.button if b.label=='Record lifecycle classification').click().run()
    assert not app.exception and app.session_state.data.invoices['PG105B']['lifecycle_status']=='cancelled'
    next(b for b in app.button if b.label=='Restore demo records').click().run()
    assert app.session_state.data.invoices['PG105B']['lifecycle_status']=='cancelled'
