"""Reproduce fictional cases without randomness or external data (fixed scenario seed)."""
import csv
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate(output: Path = ROOT / 'data' / 'synthetic'):
    output.mkdir(parents=True, exist_ok=True)
    vendors = [dict(vendor_id=f'V{i:02}', name=f'Fictional {name} Supplies', status='inactive' if i == 4 else 'active', bank_token=f'DEMO-BANK-{i:02}')
               for i, name in enumerate(['Aster', 'Cobalt', 'Juniper', 'Mistral'], 1)]
    pos, grns, invoices, outcomes = [], [], [], []
    labels = {**{i: 'clean' for i in range(1, 11)}, 11:'duplicate first submission', 12:'duplicate repeated submission',
              13:'incorrect unit price', 14:'quantity above receipts', 15:'quantity above order', 16:'missing receipt',
              17:'unexpected bank token', 18:'inactive vendor', 19:'high value', 20:'missing purchase order',
              21:'incorrect supplier mapping', 22:'price and bank anomalies', 23:'invalid negative quantity',
              24:'price tolerance equality', 25:'price just outside tolerance', 26:'incorrect declared total',
              27:'total tolerance equality', 28:'total just outside tolerance', 29:'unknown vendor',
              30:'incorrect item mapping', 31:'blank bank field', 32:'aggregate split receipts'}
    missing = {16,20,23,29,30,31}
    clean = {*range(1,11),24,27,32}
    # This key is declarative and separate. No expected outcome is computed with audit code.
    expected_codes = {11:'DUPLICATE',12:'DUPLICATE',13:'PRICE_MISMATCH',14:'EXCESS_RECEIVED',15:'EXCESS_ORDERED',
      16:'MISSING_GRN',17:'BANK_CHANGE',18:'INACTIVE_VENDOR',19:'HIGH_VALUE',20:'MISSING_PO',21:'VENDOR_MISMATCH',
      22:'BANK_CHANGE;COMPOUND_RISK;PRICE_MISMATCH',23:'INVALID_DATA',25:'PRICE_MISMATCH',26:'TOTAL_MISMATCH',
      28:'TOTAL_MISMATCH',29:'MISSING_VENDOR;VENDOR_MISMATCH',30:'ITEM_MISMATCH;MISSING_GRN',31:'INVALID_DATA'}
    for n in range(1,33):
        vendor = f'V{1 + (n % 3):02}'
        if n in (11,12): vendor = 'V01'
        if n == 18: vendor = 'V04'
        po = dict(po_id=f'PO{n:03}',vendor_id=vendor,item_id=f'ITEM{n:03}',quantity='10',unit_price='100.00',currency='INR')
        grn = dict(grn_id=f'GRN{n:03}',po_id=po['po_id'],item_id=po['item_id'],quantity='10')
        inv = dict(invoice_id=f'INV{n:03}',invoice_number=f'DEMO-2026-{n:03}',vendor_id=vendor,po_id=po['po_id'],
                   item_id=po['item_id'],quantity='10',unit_price='100.00',declared_total='1000.00',currency='INR',
                   bank_token=f'DEMO-BANK-{int(vendor[1:]):02}',invoice_date='2026-10-01')
        if n in (11,12): inv['invoice_number'] = 'DEMO-DUP-011'
        if n in (13,22): inv['unit_price'] = '120.00'
        if n == 14: grn['quantity'] = '8'
        if n == 15: po['quantity'] = '8'
        if n in (17,22): inv['bank_token'] = 'DEMO-UNEXPECTED-TOKEN'
        if n == 19: po['unit_price'] = inv['unit_price'] = '10000.00'
        if n == 20: inv['po_id'] = 'PO-ABSENT'
        if n == 21:
            inv['vendor_id'] = 'V02' if vendor != 'V02' else 'V03'
            inv['bank_token'] = f'DEMO-BANK-{int(inv["vendor_id"][1:]):02}'
        if n == 23: inv['quantity'] = '-2'
        if n == 24: inv['unit_price'] = '100.01'
        if n == 25: inv['unit_price'] = '100.02'
        if n == 29: inv['vendor_id'] = 'V-ABSENT'
        if n == 30: inv['item_id'] = 'ITEM-WRONG'
        if n == 31: inv['bank_token'] = ''
        inv['declared_total'] = str((Decimal(inv['quantity']) * Decimal(inv['unit_price'])).quantize(Decimal('0.01')))
        if n == 26: inv['declared_total'] = '1005.00'
        if n == 27: inv['declared_total'] = '1000.01'
        if n == 28: inv['declared_total'] = '1000.02'
        if n == 32:
            grn['quantity'] = '4'
            grns.append(dict(grn_id='GRN032B',po_id=po['po_id'],item_id=po['item_id'],quantity='6'))
        pos.append(po)
        if n != 16: grns.append(grn)
        invoices.append(inv)
        outcomes.append(dict(invoice_id=inv['invoice_id'],scenario=labels[n],expected_decision='INSUFFICIENT_DATA' if n in missing else 'READY_FOR_HUMAN_APPROVAL' if n in clean else 'HOLD_FOR_REVIEW',expected_codes=expected_codes.get(n,'')))
    for filename, rows in [('vendors',vendors),('purchase_orders',pos),('goods_receipts',grns),('invoices',invoices),('expected_outcomes',outcomes)]:
        with (output / f'{filename}.csv').open('w',newline='',encoding='utf-8') as handle:
            writer = csv.DictWriter(handle,fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    return output


if __name__ == '__main__':
    print(generate())
