from decimal import Decimal
import pytest
from procureguard.orchestrator import audit
from procureguard.policies import Policy
from procureguard.schemas import number
from procureguard.tools import amounts, quantities


def codes(state): return {f.code for f in state.findings}


def test_clean_invoice(dataset):
    state = audit(dataset, 'INV001')
    assert state.recommendation == 'READY_FOR_HUMAN_APPROVAL'
    assert state.verified and not state.findings


def test_price_tool_exact_decimal(dataset):
    i = dataset.invoices['INV013']
    f = amounts(dataset, i, Policy())[0]
    assert f.code == 'PRICE_MISMATCH'
    assert f.evidence == {'invoice_price':'120.00','po_price':'100.00','tolerance':'0.01'}


def test_quantity_above_received(dataset):
    found = quantities(dataset, dataset.invoices['INV014'], Policy())
    assert found[0].code == 'EXCESS_RECEIVED'
    assert found[0].evidence == {'invoiced':'10','received':'8'}


def test_quantity_above_ordered(dataset):
    assert codes(audit(dataset,'INV015')) == {'EXCESS_ORDERED'}


def test_split_receipts_are_summed(dataset):
    assert audit(dataset,'INV032').recommendation == 'READY_FOR_HUMAN_APPROVAL'


def test_other_item_receipt_not_counted(dataset):
    dataset.goods_receipts['GRN014']['item_id'] = 'UNRELATED'
    state = audit(dataset,'INV014')
    assert 'MISSING_GRN' in codes(state)
    assert state.recommendation == 'INSUFFICIENT_DATA'


def test_missing_po(dataset):
    assert codes(audit(dataset,'INV020')) == {'MISSING_PO'}


def test_missing_receipt(dataset):
    state = audit(dataset,'INV016')
    assert state.recommendation == 'INSUFFICIENT_DATA'
    assert codes(state) == {'MISSING_GRN'}


def test_vendor_po_mapping(dataset):
    assert codes(audit(dataset,'INV021')) == {'VENDOR_MISMATCH'}


def test_unknown_vendor(dataset):
    state = audit(dataset,'INV029')
    assert 'MISSING_VENDOR' in codes(state)
    assert state.recommendation == 'INSUFFICIENT_DATA'


def test_wrong_item(dataset):
    assert codes(audit(dataset,'INV030')) == {'ITEM_MISMATCH','MISSING_GRN'}


def test_arithmetic_mismatch(dataset):
    f = audit(dataset,'INV026').findings[0]
    assert f.code == 'TOTAL_MISMATCH' and f.evidence['calculated'] == '1000.00'


def test_price_tolerance_equality(dataset):
    assert audit(dataset,'INV024').recommendation == 'READY_FOR_HUMAN_APPROVAL'


def test_price_outside_tolerance(dataset):
    assert codes(audit(dataset,'INV025')) == {'PRICE_MISMATCH'}


def test_total_tolerance_equality(dataset):
    assert audit(dataset,'INV027').recommendation == 'READY_FOR_HUMAN_APPROVAL'


def test_total_outside_tolerance(dataset):
    assert codes(audit(dataset,'INV028')) == {'TOTAL_MISMATCH'}


def test_configured_zero_tolerance(dataset):
    assert 'PRICE_MISMATCH' in codes(audit(dataset,'INV024',Policy(price_tolerance=Decimal('0'))))


@pytest.mark.parametrize('bad',['NaN','Infinity','-1','0','1e999999','1.001','oops'])
def test_invalid_money_rejected(bad):
    with pytest.raises(ValueError): number(bad)


def test_fractional_quantity_rejected():
    with pytest.raises(ValueError): number('1.5',quantity=True)


def test_bad_source_po_cannot_pass(dataset):
    dataset.purchase_orders['PO001']['unit_price'] = 'NaN'
    s = audit(dataset,'INV001')
    assert s.verified and s.recommendation == 'INSUFFICIENT_DATA'
    assert codes(s) == {'INVALID_DATA'}
