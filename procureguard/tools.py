"""Reusable matching and risk tools. No tool can execute a payment."""
from decimal import Decimal
from .data_loader import Dataset
from .policies import Policy
from .schemas import row_errors, number, ACTIVE_STATUSES, EXCLUDED_STATUSES
from .state import Finding


def finding(code: str, **evidence: object) -> Finding:
    severity = 'missing' if code.startswith('MISSING_') or code == 'INVALID_DATA' else 'review'
    return Finding(code, severity, {k: str(v) for k, v in evidence.items()})


def context_errors(data: Dataset, invoice: dict) -> list[str]:
    """Revalidate originals on every run, including referenced source rows."""
    errors = [f'invoice: {e}' for e in row_errors('invoices', invoice)]
    for table, field in [('vendors', 'vendor_id'), ('purchase_orders', 'po_id')]:
        record = getattr(data, table).get(invoice.get(field))
        if record is not None:
            errors.extend(f'{table}: {e}' for e in row_errors(table, record))
    for receipt in data.goods_receipts.values():
        if receipt.get('po_id') == invoice.get('po_id'):
            errors.extend(f'goods_receipts:{receipt["grn_id"]}: {e}' for e in row_errors('goods_receipts', receipt))
    return sorted(errors)


def schema_check(data: Dataset, invoice: dict, policy: Policy) -> list[Finding]:
    errors = context_errors(data, invoice)
    return [finding('INVALID_DATA', errors='; '.join(errors))] if errors else []


def links(data: Dataset, i: dict, policy: Policy) -> list[Finding]:
    out = []
    if i.get('lifecycle_status', 'submitted') not in ACTIVE_STATUSES:
        out.append(finding('INACTIVE_SUBMISSION', invoice_id=i['invoice_id'], lifecycle_status=i['lifecycle_status']))
    vendor, po = data.vendors.get(i['vendor_id']), data.purchase_orders.get(i['po_id'])
    if vendor is None:
        out.append(finding('MISSING_VENDOR', vendor_id=i['vendor_id']))
    if po is None:
        out.append(finding('MISSING_PO', po_id=i['po_id']))
    else:
        if po['vendor_id'] != i['vendor_id']:
            out.append(finding('VENDOR_MISMATCH', invoice_vendor=i['vendor_id'], po_vendor=po['vendor_id']))
        if po['item_id'] != i['item_id']:
            out.append(finding('ITEM_MISMATCH', invoice_item=i['item_id'], po_item=po['item_id']))
        if not any(g['po_id'] == i['po_id'] and g['item_id'] == i['item_id'] for g in data.goods_receipts.values()):
            out.append(finding('MISSING_GRN', po_id=i['po_id'], item_id=i['item_id']))
    return out


def amounts(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    out = []
    price, qty, total = number(i['unit_price']), number(i['quantity'], quantity=True), number(i['declared_total'])
    calculated = (price * qty).quantize(Decimal('0.01'))
    if abs(total - calculated) > p.total_tolerance:
        out.append(finding('TOTAL_MISMATCH', declared=total, calculated=calculated, tolerance=p.total_tolerance))
    po = data.purchase_orders.get(i['po_id'])
    if po and abs(price - number(po['unit_price'])) > p.price_tolerance:
        out.append(finding('PRICE_MISMATCH', invoice_price=price, po_price=number(po['unit_price']), tolerance=p.price_tolerance))
    elif po and abs((price - number(po['unit_price'])) * qty) > p.line_exposure_tolerance:
        out.append(finding('LINE_EXPOSURE', invoice_line=calculated,
                           authorised_line=(number(po['unit_price']) * qty).quantize(Decimal('0.01')),
                           tolerance=p.line_exposure_tolerance))
    return out


def quantities(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    out = []
    qty = number(i['quantity'], quantity=True)
    po = data.purchase_orders.get(i['po_id'])
    if po and qty > number(po['quantity'], quantity=True):
        out.append(finding('EXCESS_ORDERED', invoiced=qty, ordered=number(po['quantity'], quantity=True)))
    receipts = [g for g in data.goods_receipts.values() if g['po_id'] == i['po_id'] and g['item_id'] == i['item_id']]
    received = sum((number(g['quantity'], quantity=True) for g in receipts), Decimal(0))
    if po and receipts and qty > received:
        out.append(finding('EXCESS_RECEIVED', invoiced=qty, received=received))
    peers = [r for r in data.invoices.values() if r.get('po_id') == i['po_id']
             and r.get('item_id') == i['item_id'] and r.get('vendor_id') == i['vendor_id']
             and r.get('lifecycle_status', 'submitted') not in EXCLUDED_STATUSES]
    if po and i.get('lifecycle_status', 'submitted') in ACTIVE_STATUSES and len(peers) > 1:
        if any(row_errors('invoices', r) for r in peers):
            out.append(finding('MISSING_LEDGER_CONTEXT', invoice_ids=', '.join(sorted(r['invoice_id'] for r in peers))))
        else:
            groups = {}
            for r in peers:
                groups.setdefault(r['invoice_number'], []).append(r)
            if any(len({tuple(number(r[k], quantity=k == 'quantity') for k in ('quantity','unit_price','declared_total')) for r in group}) > 1 for group in groups.values()):
                return out + [finding('MISSING_LEDGER_CONTEXT', invoice_ids=', '.join(sorted(r['invoice_id'] for r in peers)))]
            committed = sum((number(group[0]['quantity'], quantity=True) for group in groups.values()), Decimal(0))
            capacity = min(number(po['quantity'], quantity=True), received) if receipts else number(po['quantity'], quantity=True)
            if committed > capacity:
                out.append(finding('CUMULATIVE_EXCESS', committed=committed, capacity=capacity,
                                   invoice_ids=', '.join(sorted(r['invoice_id'] for r in peers))))
    return out


def duplicate(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    # Exact, case-sensitive vendor + stripped invoice number. Both submissions are held.
    if i.get('lifecycle_status', 'submitted') not in ACTIVE_STATUSES:
        return []
    ids = sorted(r['invoice_id'] for r in data.invoices.values()
                 if r['vendor_id'] == i['vendor_id'] and r['invoice_number'] == i['invoice_number']
                 and r.get('lifecycle_status', 'submitted') not in EXCLUDED_STATUSES)
    return [finding('DUPLICATE', invoice_ids=', '.join(ids))] if len(ids) > 1 else []


def bank(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    v = data.vendors.get(i['vendor_id'])
    return [finding('BANK_CHANGE', invoice_bank=i['bank_token'], master_bank=v['bank_token'])] if v and i['bank_token'] != v['bank_token'] else []


def status(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    v = data.vendors.get(i['vendor_id'])
    return [finding('INACTIVE_VENDOR', vendor_id=v['vendor_id'], status=v['status'])] if v and v['status'] != 'active' else []


def high_value(data: Dataset, i: dict, p: Policy) -> list[Finding]:
    amount = max(number(i['declared_total']), (number(i['unit_price']) * number(i['quantity'], quantity=True)).quantize(Decimal('0.01')))
    return [finding('HIGH_VALUE', amount=amount, threshold=p.high_value)] if amount >= p.high_value else []


MATCH_TOOLS = {'record_links': links, 'amount_comparison': amounts, 'quantity_comparison': quantities}
RISK_TOOLS = {'duplicate_search': duplicate, 'bank_comparison': bank, 'vendor_status': status, 'value_threshold': high_value}


def screen(data: Dataset, i: dict, p: Policy) -> dict[str, list[Finding]]:
    """Run each mandatory check once; retain its evidence for risk assessment."""
    results = {name: tool(data, i, p) for name, tool in RISK_TOOLS.items()}
    return {name: findings for name, findings in results.items() if findings}


def compound(findings: list[Finding]) -> list[Finding]:
    codes = sorted(f.code for f in findings if f.severity == 'review' and f.code != 'COMPOUND_RISK')
    return [finding('COMPOUND_RISK', contributing_codes=', '.join(codes))] if len(codes) >= 2 else []
