import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from procureguard.case_store import CaseStore,VersionConflict
from procureguard.investigation import investigate
from procureguard.evidence import EvidenceRepository

@pytest.fixture
def result(dataset):
    return investigate(dataset,'PG103',EvidenceRepository(Path(__file__).resolve().parents[1]/'data/evidence'))

def test_persistent_snapshot_and_idempotency(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite')
    assert store.save(result,expected_version=0,request_key='request-1')==1
    assert store.save(result,expected_version=0,request_key='request-1')==1
    reloaded=CaseStore(store.path)
    assert reloaded.load('PG103')==result.to_dict()
    assert reloaded.verify_integrity()['valid'] and len(reloaded.history('PG103'))==1

def test_idempotency_key_content_mismatch_rejected(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one');result.budget=0
    with pytest.raises(ValueError):store.save(result,expected_version=1,request_key='one')

def test_stale_save_rejected(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one')
    with pytest.raises(VersionConflict):store.save(result,expected_version=0,request_key='two')

def test_two_concurrent_saves_have_one_winner(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite')
    def save(key):
        try:return store.save(result,expected_version=0,request_key=key)
        except VersionConflict:return 'conflict'
    with ThreadPoolExecutor(2) as pool:outcomes=list(pool.map(save,['one','two']))
    assert sorted(map(str,outcomes))==['1','conflict'] and store.verify_integrity()['valid']

def test_observer_cannot_review(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one')
    with pytest.raises(PermissionError):store.review('PG103',expected_version=1,actor='faculty_observer',action='confirm_recommendation',rationale='Reviewed')

def test_review_revision_prevents_stale_review(tmp_path,result):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one')
    assert store.review('PG103',expected_version=1,actor='ap_reviewer',action='request_recheck',rationale='Need another source check')==2
    assert store.current('PG103')['status']=='RECHECK_REQUESTED'
    with pytest.raises(VersionConflict):store.review('PG103',expected_version=1,actor='ap_reviewer',action='confirm_recommendation',rationale='Stale tab')
    assert store.save(result,expected_version=2,request_key='two')==3

@pytest.mark.parametrize('rationale',['',' ', 'x'*1001])
def test_bad_review_rationale_rejected(tmp_path,result,rationale):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one')
    with pytest.raises(ValueError):store.review('PG103',expected_version=1,actor='ap_reviewer',action='confirm_recommendation',rationale=rationale)

@pytest.mark.parametrize('target',['event','snapshot'])
def test_audit_tampering_detected(tmp_path,result,target):
    store=CaseStore(tmp_path/'cases.sqlite');store.save(result,expected_version=0,request_key='one')
    with sqlite3.connect(store.path) as db:
        if target=='event':db.execute("UPDATE events SET payload='{}' WHERE seq=1")
        else:db.execute("UPDATE runs SET content='{}' WHERE case_id='PG103'")
    assert not store.verify_integrity()['valid']
