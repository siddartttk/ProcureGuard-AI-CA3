"""Independent implementation: never calls matcher/risk tools or trusts their numbers."""
from decimal import Decimal
from ..schemas import row_errors, ACTIVE_STATUSES, EXCLUDED_STATUSES
from ..state import Finding


class CriticAgent:
    """Goal: detect omissions, unsupported findings, altered values and contradictions."""

    def expected(self, data, i, p):
        expected = []
        def add(code, **ev):
            severity = 'missing' if code.startswith('MISSING_') or code == 'INVALID_DATA' else 'review'
            expected.append(Finding(code, severity, {k: str(v) for k, v in ev.items()}))
        # Schema parsing is shared infrastructure; all audit comparisons below are independent.
        invalid = [f'invoice: {e}' for e in row_errors('invoices', i)]
        vendor, po = data.vendors.get(i.get('vendor_id')), data.purchase_orders.get(i.get('po_id'))
        for table, row in [('vendors', vendor), ('purchase_orders', po)]:
            if row is not None:
                invalid += [f'{table}: {e}' for e in row_errors(table, row)]
        for g in data.goods_receipts.values():
            if g.get('po_id') == i.get('po_id'):
                invalid += [f'goods_receipts:{g["grn_id"]}: {e}' for e in row_errors('goods_receipts', g)]
        if invalid:
            add('INVALID_DATA', errors='; '.join(sorted(invalid)))
            return expected
        q, price, total = [Decimal(i[k]) for k in ('quantity', 'unit_price', 'declared_total')]
        active = i.get('lifecycle_status', 'submitted') in ACTIVE_STATUSES
        if not active:
            add('INACTIVE_SUBMISSION', invoice_id=i['invoice_id'], lifecycle_status=i['lifecycle_status'])
        if vendor is None:
            add('MISSING_VENDOR', vendor_id=i['vendor_id'])
        if po is None:
            add('MISSING_PO', po_id=i['po_id'])
        else:
            if i['vendor_id'] != po['vendor_id']:
                add('VENDOR_MISMATCH', invoice_vendor=i['vendor_id'], po_vendor=po['vendor_id'])
            if i['item_id'] != po['item_id']:
                add('ITEM_MISMATCH', invoice_item=i['item_id'], po_item=po['item_id'])
            receipts = [g for g in data.goods_receipts.values() if g['po_id'] == i['po_id'] and g['item_id'] == i['item_id']]
            if not receipts:
                add('MISSING_GRN', po_id=i['po_id'], item_id=i['item_id'])
            else:
                delivered = Decimal(0)
                for g in receipts:
                    delivered += Decimal(g['quantity'])
                if q > delivered:
                    add('EXCESS_RECEIVED', invoiced=q, received=delivered)
            if q > Decimal(po['quantity']):
                add('EXCESS_ORDERED', invoiced=q, ordered=Decimal(po['quantity']))
            difference = price - Decimal(po['unit_price'])
            if difference < -p.price_tolerance or difference > p.price_tolerance:
                add('PRICE_MISMATCH', invoice_price=price, po_price=Decimal(po['unit_price']), tolerance=p.price_tolerance)
            elif abs(difference * q) > p.line_exposure_tolerance:
                add('LINE_EXPOSURE', invoice_line=(q * price).quantize(Decimal('0.01')),
                    authorised_line=(q * Decimal(po['unit_price'])).quantize(Decimal('0.01')),
                    tolerance=p.line_exposure_tolerance)
            related = [r for r in data.invoices.values() if r.get('po_id') == i['po_id']
                       and r.get('item_id') == i['item_id'] and r.get('vendor_id') == i['vendor_id']
                       and r.get('lifecycle_status', 'submitted') not in EXCLUDED_STATUSES]
            if active and len(related) > 1:
                identities = ', '.join(sorted(r['invoice_id'] for r in related))
                if any(row_errors('invoices', r) for r in related):
                    add('MISSING_LEDGER_CONTEXT', invoice_ids=identities)
                else:
                    obligations = {}
                    for r in related:
                        obligations.setdefault(r['invoice_number'], set()).add(tuple(Decimal(r[k]) for k in ('quantity','unit_price','declared_total')))
                    ambiguous = any(len(values) > 1 for values in obligations.values())
                    if ambiguous:
                        add('MISSING_LEDGER_CONTEXT', invoice_ids=identities)
                    booked = sum((next(iter(values))[0] for values in obligations.values()), Decimal(0))
                    limit = Decimal(po['quantity'])
                    if receipts and delivered < limit:
                        limit = delivered
                    if not ambiguous and booked > limit:
                        add('CUMULATIVE_EXCESS', committed=booked, capacity=limit, invoice_ids=identities)
        expected_total = (q * price).quantize(Decimal('0.01'))
        if total < expected_total - p.total_tolerance or total > expected_total + p.total_tolerance:
            add('TOTAL_MISMATCH', declared=total, calculated=expected_total, tolerance=p.total_tolerance)
        matches = []
        for candidate in data.invoices.values():
            if active and candidate.get('lifecycle_status', 'submitted') not in EXCLUDED_STATUSES and (candidate['vendor_id'], candidate['invoice_number']) == (i['vendor_id'], i['invoice_number']):
                matches.append(candidate['invoice_id'])
        if len(matches) > 1:
            add('DUPLICATE', invoice_ids=', '.join(sorted(matches)))
        if vendor:
            if vendor['bank_token'] != i['bank_token']:
                add('BANK_CHANGE', invoice_bank=i['bank_token'], master_bank=vendor['bank_token'])
            if vendor['status'] == 'inactive':
                add('INACTIVE_VENDOR', vendor_id=vendor['vendor_id'], status=vendor['status'])
        exposure = total if total > expected_total else expected_total
        if exposure >= p.high_value:
            add('HIGH_VALUE', amount=exposure, threshold=p.high_value)
        codes = sorted(f.code for f in expected if f.severity == 'review')
        if len(codes) >= 2:
            add('COMPOUND_RISK', contributing_codes=', '.join(codes))
        return expected

    def run(self, state, data, invoice, policy):
        expected = self.expected(data, invoice, policy)
        canonical = lambda rows: sorted((f.code, f.severity, tuple(sorted(f.evidence.items()))) for f in rows)
        state.verified = canonical(expected) == canonical(state.findings)
        expected_codes, actual_codes = {f.code for f in expected}, {f.code for f in state.findings}
        check = {'attempt': state.attempts, 'passed': state.verified,
                 'checked': 'Schema, record links, exact amounts, receipt sums, all risk rules, evidence and severity',
                 'missing_codes': sorted(expected_codes - actual_codes),
                 'unsupported_codes': sorted(actual_codes - expected_codes),
                 'evidence_equal': state.verified,
                 'expected_findings': [dict(code=f.code, severity=f.severity, evidence=f.evidence) for f in expected]}
        state.verifications.append(check)
        state.event('Critic', 'independent_recomputation', 'Recompute and compare complete evidence',
                    'Verified' if state.verified else 'Contradiction detected', 'Every investigation attempt',
                    'Decision' if state.verified else 'Planner recheck gate')
        return state.verified
