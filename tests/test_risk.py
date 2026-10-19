from procureguard.orchestrator import audit
from procureguard.tools import duplicate
from procureguard.policies import Policy


def codes(s): return {f.code for f in s.findings}


def test_duplicate_both_submissions_held(dataset):
    for identity in ('INV011','INV012'):
        s = audit(dataset,identity)
        assert codes(s) == {'DUPLICATE'} and s.recommendation == 'HOLD_FOR_REVIEW'


def test_same_number_other_vendor_valid(dataset):
    dataset.invoices['INV002']['invoice_number'] = dataset.invoices['INV001']['invoice_number']
    assert not duplicate(dataset,dataset.invoices['INV001'],Policy())


def test_changed_bank_evidence(dataset):
    f = audit(dataset,'INV017').findings[0]
    assert f.code == 'BANK_CHANGE'
    assert f.evidence['invoice_bank'] == 'DEMO-UNEXPECTED-TOKEN'


def test_inactive_vendor(dataset):
    assert codes(audit(dataset,'INV018')) == {'INACTIVE_VENDOR'}


def test_high_value_inclusive_boundary(dataset):
    assert codes(audit(dataset,'INV019')) == {'HIGH_VALUE'}


def test_high_value_below_boundary(dataset):
    i = dataset.invoices['INV019']; i['unit_price']='9999.99'; i['declared_total']='99999.90'
    dataset.purchase_orders['PO019']['unit_price']='9999.99'
    assert not audit(dataset,'INV019').findings


def test_compound_score_is_explained(dataset):
    s = audit(dataset,'INV022')
    assert codes(s) == {'PRICE_MISMATCH','BANK_CHANGE','COMPOUND_RISK'}
    assert s.risk_score == 70


def test_invalid_invoice_is_not_review_ready(dataset):
    assert audit(dataset,'INV023').recommendation == 'INSUFFICIENT_DATA'


def test_blank_required_field(dataset):
    assert codes(audit(dataset,'INV031')) == {'INVALID_DATA'}
