"""Author controlled exception scenarios and verifiable synthetic source packets."""
import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.generate_demo_data import generate
from procureguard.data_loader import load_dataset
from procureguard.schemas import SCHEMAS

SCENARIOS = {
    'PG101': ('The missing delivery', 'A receipt exists in the warehouse, but has not reached accounts payable.'),
    'PG102': ('The approved amendment', 'A legitimate price change is held until procurement authority is retrieved.'),
    'PG103': ('Two gaps, one case', 'A price amendment and a delivery record must both be obtained.'),
    'PG104': ('Evidence arrives later', 'A reviewer requests a recheck; a delayed receipt then becomes available.'),
    'PG105': ('The receipt reuse trap', 'Two distinct invoices together exceed the delivered and ordered quantity.'),
    'PG106': ('The poisoned attachment', 'A receipt was changed after its content hash was pinned.'),
    'PG107': ('Conflicting authority', 'Two approved amendments disagree; the agent must escalate.'),
    'PG108': ('The tolerance trap', 'A tiny unit difference doubles the total line exposure.'),
    'PG109': ('Verified bank change', 'A bank change needs an authorised vendor-master record, never invoice text.'),
    'PG110': ('Unresolved delivery', 'No authoritative receipt exists; the system must preserve the evidence gap.'),
}


def generate_all():
    generate()
    data = load_dataset(ROOT/'data/synthetic')
    evidence_dir = ROOT/'data/evidence'
    evidence_dir.mkdir(exist_ok=True)
    manifest=[]
    for key in SCENARIOS:
        invoice = deepcopy(data.invoices['INV001'])
        invoice.update(invoice_id=key, invoice_number=f'SYN-{key}', po_id=f'PO-{key}', item_id=f'ITEM-{key}')
        po = dict(data.purchase_orders['PO001'], po_id=invoice['po_id'], item_id=invoice['item_id'])
        receipt = {'grn_id':f'GRN-{key}','po_id':po['po_id'],'item_id':po['item_id'],'quantity':'10'}
        data.invoices[key]=invoice
        data.purchase_orders[po['po_id']]=po
        if key not in ('PG101','PG103','PG104','PG106','PG110'):
            data.goods_receipts[receipt['grn_id']]=receipt
        if key in ('PG102','PG103','PG107'):
            invoice.update(unit_price='120.00',declared_total='1200.00')
        if key == 'PG105':
            data.invoices['PG105B']=dict(invoice,invoice_id='PG105B',invoice_number='SYN-PG105-SECOND')
        if key == 'PG108':
            po.update(quantity='1000000',unit_price='0.01')
            invoice.update(quantity='1000000',unit_price='0.02',declared_total='20000.00')
            receipt['quantity']='1000000'
        if key == 'PG109':
            # Use a dedicated vendor so the approved local update cannot affect another case.
            vendor = dict(data.vendors[invoice['vendor_id']],vendor_id='V-PG109')
            data.vendors[vendor['vendor_id']]=vendor
            po['vendor_id']=invoice['vendor_id']=vendor['vendor_id']
            invoice['bank_token']='DEMO-VERIFIED-NEW-BANK'
        def emit(tool,payload,suffix='',released=False):
            source,role,kind = {'warehouse_lookup':('warehouse','receiving_manager','receipt'),
                                'amendment_lookup':('procurement','procurement_manager','po_amendment'),
                                'bank_verification':('vendor_master','finance_controller','bank_verification')}[tool]
            identity=f'EV-{key}-{tool}{suffix}'
            doc={'evidence_id':identity,'source':source,'approved_by_role':role,'kind':kind,
                 'approval_status':'approved','effective_date':'2026-09-30',
                 **{f:invoice[f] for f in ('po_id','vendor_id','item_id')},'payload':payload,
                 'note':'Fictional source record. Free text is never used as an instruction.'}
            raw=json.dumps(doc,indent=2).encode()
            filename=identity+'.json'
            (evidence_dir/filename).write_bytes(raw)
            manifest.append({'evidence_id':identity,'tool':tool,'po_id':invoice['po_id'],'file':filename,
                             'sha256':hashlib.sha256(raw).hexdigest(),'release_required':released})
        if key in ('PG101','PG103','PG104','PG106'):
            emit('warehouse_lookup',receipt,released=key=='PG104')
            if key=='PG106':
                path=evidence_dir/manifest[-1]['file']
                path.write_bytes(path.read_bytes().replace(b'"quantity": "10"',b'"quantity": "99"'))
        if key in ('PG102','PG103','PG107'):
            emit('amendment_lookup',{'unit_price':'120.00'})
            if key=='PG107':emit('amendment_lookup',{'unit_price':'130.00'},suffix='-CONFLICT')
        if key=='PG109':emit('bank_verification',{'bank_token':invoice['bank_token']})
    for table in SCHEMAS:
        with (ROOT/f'data/synthetic/{table}.csv').open('w',encoding='utf-8',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=SCHEMAS[table]);writer.writeheader();writer.writerows(getattr(data,table).values())
    (evidence_dir/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (ROOT/'data/scenarios.json').write_text(json.dumps({k:{'title':v[0],'description':v[1]} for k,v in SCENARIOS.items()},indent=2),encoding='utf-8')
    print(f'Generated {len(data.invoices)} invoices and {len(manifest)} source evidence packets')


if __name__=='__main__':generate_all()
