from procureguard.orchestrator import audit
from procureguard.agents.critic import CriticAgent
from procureguard.policies import Policy
from procureguard.state import AuditState, Finding


def test_critic_detects_omitted_price_issue(dataset):
    state=AuditState('INV013')
    assert not CriticAgent().run(state,dataset,dataset.invoices['INV013'],Policy())
    assert state.verifications[0]['missing_codes'] == ['PRICE_MISMATCH']


def test_critic_detects_tampered_amount(dataset):
    s=audit(dataset,'INV013')
    s.findings[0].evidence['invoice_price']='999.00'
    assert not CriticAgent().run(s,dataset,dataset.invoices['INV013'],Policy())


def test_critic_detects_false_severity(dataset):
    s=audit(dataset,'INV013'); f=s.findings[0]
    s.findings=[Finding(f.code,'missing',f.evidence)]
    assert not CriticAgent().run(s,dataset,dataset.invoices['INV013'],Policy())


def test_critic_detects_duplicate_findings(dataset):
    s=audit(dataset,'INV013'); s.findings.append(s.findings[0])
    assert not CriticAgent().run(s,dataset,dataset.invoices['INV013'],Policy())


def test_critic_catches_corrupted_matcher(monkeypatch,dataset):
    from procureguard import tools
    monkeypatch.setitem(tools.MATCH_TOOLS,'amount_comparison',lambda *args: [])
    s=audit(dataset,'INV013')
    assert not s.verified and s.attempts == 1 and s.recommendation == 'HOLD_FOR_REVIEW'
    assert all(not x['passed'] for x in s.verifications)


def test_critic_catches_disabled_screen(monkeypatch,dataset):
    from procureguard import tools
    monkeypatch.setattr(tools,'screen',lambda *args: [])
    s=audit(dataset,'INV017')
    assert s.recommendation == 'HOLD_FOR_REVIEW' and not s.verified


def test_one_time_fault_corrected(dataset):
    s=audit(dataset,'INV001',demo_fault='once')
    assert s.attempts == 1 and [v['passed'] for v in s.verifications] == [False,True]
    assert s.recommendation == 'READY_FOR_HUMAN_APPROVAL'


def test_persistent_fault_bounded_hold(dataset):
    s=audit(dataset,'INV001',demo_fault='persistent')
    assert s.attempts == 1 and len(s.verifications) == 2
    assert s.recommendation == 'HOLD_FOR_REVIEW' and not s.verified


def test_no_retry_policy(dataset):
    s=audit(dataset,'INV001',Policy(max_rechecks=0),demo_fault='once')
    assert s.attempts == 0 and len(s.verifications) == 1 and s.recommendation == 'HOLD_FOR_REVIEW'
