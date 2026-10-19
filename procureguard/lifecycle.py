"""Procurement lifecycle, separate from recommendations and payment approval."""
from copy import deepcopy
from .schemas import INVOICE_STATUSES
from .case_store import checksum

TRANSITIONS = {
    'submitted': {'recorded','rejected','cancelled','duplicate','superseded'},
    'recorded': {'rejected','cancelled','superseded'},
    'rejected': {'submitted'}, 'cancelled': {'submitted'},
    'duplicate': {'submitted'}, 'superseded': {'submitted'},
}


def dataset_namespace(data):
    # Call with the original bundle, not its SQLite overlay. Explicit and implicit
    # submitted defaults are equivalent; distinct imported lifecycle baselines are not.
    original = {name: deepcopy(getattr(data,name)) for name in ('vendors','purchase_orders','goods_receipts','invoices')}
    for row in original['invoices'].values():
        row.setdefault('lifecycle_status','submitted')
    return checksum(original)


def validate_transition(data, invoice_id, new_status, replacement=None):
    if invoice_id not in data.invoices or new_status not in INVOICE_STATUSES:
        raise ValueError('Unknown invoice or lifecycle status')
    old = data.invoices[invoice_id].get('lifecycle_status','submitted')
    if old not in TRANSITIONS:
        raise ValueError('The current lifecycle is invalid; correct the source data first')
    if new_status not in TRANSITIONS[old]:
        raise ValueError(f'Unsupported lifecycle transition: {old} to {new_status}')
    if new_status in ('duplicate','superseded'):
        target = data.invoices.get(replacement)
        if replacement == invoice_id or target is None or target.get('lifecycle_status','submitted') not in ('submitted','recorded'):
            raise ValueError('Choose a different active replacement invoice')
        source = data.invoices[invoice_id]
        if any(target[k] != source[k] for k in ('vendor_id','po_id','item_id')):
            raise ValueError('Replacement must refer to the same supplier, PO and item')
        if new_status == 'duplicate' and target['invoice_number'] != source['invoice_number']:
            raise ValueError('Duplicate classification requires the same supplier invoice number')
    return old
