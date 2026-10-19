"""Author a fixed extension challenge BEFORE implementing the v3 fixes.

This file never imports the audit engine. Expected decisions are explicit.
It is a development challenge, authored by the same development assistant,
not an independent field or held-out performance claim.
"""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'data/challenge_v3.json'
BASE = {
    'vendors': [{'vendor_id':'VC','name':'Fictional Cedar Works','status':'active','bank_token':'DEMO-CEDAR'}],
    'purchase_orders': [{'po_id':'POC','vendor_id':'VC','item_id':'IC','quantity':'12','unit_price':'25.00','currency':'INR'}],
    'goods_receipts': [{'grn_id':'GC','po_id':'POC','item_id':'IC','quantity':'12'}],
    'invoices': [{'invoice_id':'C1','invoice_number':'DEMO-C1','vendor_id':'VC','po_id':'POC','item_id':'IC','quantity':'6','unit_price':'25.00','declared_total':'150.00','currency':'INR','bank_token':'DEMO-CEDAR','invoice_date':'2026-10-17','lifecycle_status':'submitted'}],
}
PEER = dict(BASE['invoices'][0], invoice_id='C2', invoice_number='DEMO-C2')


def case(name, expected, changes=(), *, peer=None, fault=None):
    return {'name':name,'expected':expected,'changes':list(changes),'peer':peer,'fault':fault}


def main():
    if TARGET.exists():
        raise SystemExit('The challenge is already frozen; refusing to change it')
    ready, hold, missing = 'READY_FOR_HUMAN_APPROVAL','HOLD_FOR_REVIEW','INSUFFICIENT_DATA'
    rows = [
        case('clean unfamiliar identifiers',ready),
        case('ordered capacity equality',ready,[['invoices',0,'quantity','12'],['invoices',0,'declared_total','300.00']]),
        case('unit tolerance equality',ready,[['invoices',0,'unit_price','25.01'],['invoices',0,'declared_total','150.06']]),
        case('unit tolerance exceeded',hold,[['invoices',0,'unit_price','25.02'],['invoices',0,'declared_total','150.12']]),
        case('line total wrong',hold,[['invoices',0,'declared_total','160.00']]),
        case('receipt missing',missing,[['goods_receipts',None,None,[]]]),
        case('unknown order',missing,[['invoices',0,'po_id','ABSENT']]),
        case('unknown vendor',missing,[['invoices',0,'vendor_id','ABSENT']]),
        case('bank anomaly',hold,[['invoices',0,'bank_token','DEMO-CHANGED']]),
        case('inactive supplier',hold,[['vendors',0,'status','inactive']]),
        case('zero quantity',missing,[['invoices',0,'quantity','0']]),
        case('nonfinite money',missing,[['invoices',0,'unit_price','NaN']]),
        case('active peer exhausts capacity',hold,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=PEER),
        case('recorded peer counts',hold,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=dict(PEER,lifecycle_status='recorded')),
        case('rejected peer does not count',ready,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=dict(PEER,lifecycle_status='rejected')),
        case('cancelled peer does not count',ready,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=dict(PEER,lifecycle_status='cancelled')),
        case('duplicate copy does not count',ready,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=dict(PEER,lifecycle_status='duplicate')),
        case('superseded peer does not count',ready,[['invoices',0,'quantity','7'],['invoices',0,'declared_total','175.00']],peer=dict(PEER,lifecycle_status='superseded')),
        case('rejected current submission stays held',hold,[['invoices',0,'lifecycle_status','rejected']]),
        case('invalid lifecycle cannot pass',missing,[['invoices',0,'lifecycle_status','paid']]),
        case('active exact duplicate is held',hold,peer=dict(PEER,invoice_number='DEMO-C1')),
        case('rejected prior number may be resubmitted',ready,peer=dict(PEER,invoice_number='DEMO-C1',lifecycle_status='rejected')),
        case('invalid active peer blocks capacity',missing,peer=dict(PEER,quantity='oops')),
        case('corrupt matcher omits price',hold,[['invoices',0,'unit_price','30.00'],['invoices',0,'declared_total','180.00']],fault='omit_amounts'),
        case('corrupt matcher omits arithmetic',hold,[['invoices',0,'declared_total','180.00']],fault='omit_amounts'),
    ]
    payload={'frozen_at':datetime.now(timezone.utc).isoformat(),'purpose':'Frozen development challenge, not held-out or field data','target_invoice':'C1','base':BASE,'cases':rows}
    raw=(json.dumps(payload,indent=2)+'\n').encode()
    TARGET.write_bytes(raw)
    (ROOT/'data/challenge_v3.sha256').write_text(hashlib.sha256(raw).hexdigest()+'\n',encoding='ascii')
    print(f'Frozen {len(rows)} cases: {hashlib.sha256(raw).hexdigest()}')


if __name__=='__main__': main()
