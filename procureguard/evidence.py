"""Read-only synthetic source adapters with pinned hashes and scoped authority checks."""
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from .schemas import row_errors, number

AUTHORITIES = {'warehouse_lookup': ('warehouse', 'receiving_manager', 'receipt'),
               'amendment_lookup': ('procurement', 'procurement_manager', 'po_amendment'),
               'bank_verification': ('vendor_master', 'finance_controller', 'bank_verification')}


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


@dataclass
class EvidenceResult:
    status: str
    reason: str
    accepted: list
    rejected: list


class EvidenceRepository:
    """The manifest is the trusted demo boundary, not a cryptographic signature service."""
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        raw = (self.directory / 'manifest.json').read_bytes()
        if len(raw) > 2_000_000:
            raise ValueError('Evidence manifest too large')
        self.manifest = json.loads(raw)
        if not isinstance(self.manifest, list) or len(self.manifest) > 500:
            raise ValueError('Invalid evidence manifest')

    def lookup(self, tool: str, invoice: dict, *, released: bool = False):
        if tool not in AUTHORITIES:
            raise ValueError('Tool is not allowlisted')
        source, authority, kind = AUTHORITIES[tool]
        accepted, rejected = [], []
        for entry in self.manifest:
            if entry.get('tool') != tool or entry.get('po_id') != invoice['po_id']:
                continue
            if entry.get('release_required') and not released:
                continue
            identity = entry.get('evidence_id', 'unknown')
            try:
                path = (self.directory / entry['file']).resolve()
                if not path.is_relative_to(self.directory) or not path.is_file():
                    raise ValueError('Unsafe evidence path')
                raw = path.read_bytes()
                if len(raw) > 100_000 or digest_bytes(raw) != entry['sha256']:
                    raise ValueError('Pinned content hash mismatch')
                document = json.loads(raw)
                if document['evidence_id'] != identity:
                    raise ValueError('Evidence identity mismatch')
                if document['source'] != source or document['approved_by_role'] != authority:
                    raise ValueError('Source or approval authority mismatch')
                if document['kind'] != kind or document['approval_status'] != 'approved':
                    raise ValueError('Evidence is unapproved or has the wrong type')
                for field in ('vendor_id', 'po_id', 'item_id'):
                    if document[field] != invoice[field]:
                        raise ValueError(f'Evidence scope mismatch: {field}')
                if date.fromisoformat(document['effective_date']) > date.fromisoformat(invoice['invoice_date']):
                    raise ValueError('Evidence is not effective for this invoice date')
                payload = document['payload']
                if not isinstance(payload, dict):
                    raise ValueError('Evidence payload must be structured data')
                if tool == 'warehouse_lookup':
                    errors = row_errors('goods_receipts', payload)
                    if payload.get('po_id') != invoice['po_id'] or payload.get('item_id') != invoice['item_id']:
                        errors.append('Receipt does not match the invoice scope')
                    if errors:
                        raise ValueError('; '.join(errors))
                elif tool == 'amendment_lookup':
                    number(payload['unit_price'])
                    if set(payload) != {'unit_price'}:
                        raise ValueError('Amendments may change only unit price')
                else:
                    if set(payload) != {'bank_token'} or not isinstance(payload['bank_token'], str) or not 1 <= len(payload['bank_token']) <= 120:
                        raise ValueError('Invalid approved bank token')
                accepted.append({**document, 'sha256': entry['sha256']})
            except (ValueError, KeyError, TypeError, OSError) as exc:
                rejected.append({'evidence_id': identity, 'reason': str(exc)})
        # Distinct receipts can accumulate. A PO/master update needs one unambiguous value.
        if tool != 'warehouse_lookup' and len({json.dumps(d['payload'], sort_keys=True) for d in accepted}) > 1:
            return EvidenceResult('conflict', 'Authorised sources disagree; human resolution required', accepted, rejected)
        if accepted and rejected:
            return EvidenceResult('conflict', 'Conflicting or rejected source records require human review', accepted, rejected)
        if accepted:
            return EvidenceResult('accepted', f'{len(accepted)} scoped source record(s) verified', accepted, rejected)
        return EvidenceResult('rejected' if rejected else 'not_found',
                              'Evidence failed verification' if rejected else 'No approved evidence is currently available', [], rejected)


def apply_evidence(data, invoice, tool, documents):
    """Change only the investigation snapshot. Never change the original invoice."""
    before_invoice = dict(invoice)
    for document in documents:
        payload = document['payload']
        if tool == 'warehouse_lookup':
            identity = payload['grn_id']
            if identity in data.goods_receipts and data.goods_receipts[identity] != payload:
                raise ValueError('Receipt ID conflicts with an existing source record')
            data.goods_receipts[identity] = dict(payload)
        elif tool == 'amendment_lookup':
            data.purchase_orders[invoice['po_id']]['unit_price'] = payload['unit_price']
        elif tool == 'bank_verification':
            data.vendors[invoice['vendor_id']]['bank_token'] = payload['bank_token']
    if invoice != before_invoice:
        raise AssertionError('Invoice immutability violated')
