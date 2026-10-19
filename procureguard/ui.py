"""A case-oriented Streamlit workbench over executed, persisted investigations."""
import html
import json
import os
from collections import Counter
from pathlib import Path
from uuid import uuid4
import pandas as pd
import streamlit as st
from .data_loader import load_dataset, parse_csv, from_tables
from .schemas import SCHEMAS
from .orchestrator import audit
from .investigation import investigate, snapshot_hash
from .planning import MockPlannerModel, OllamaPlannerModel
from .evidence import EvidenceRepository
from .case_store import CaseStore, VersionConflict
from .lifecycle import dataset_namespace, TRANSITIONS

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'READY_FOR_HUMAN_APPROVAL':'Ready for review', 'HOLD_FOR_REVIEW':'Held for review',
          'INSUFFICIENT_DATA':'Waiting for evidence'}
CSS = '''<style>
.stApp {background:#f4f6fa;color:#182940} .block-container{max-width:1440px;padding-top:2rem;padding-bottom:4rem}
section[data-testid="stSidebar"]{background:#101e33} section[data-testid="stSidebar"] *{color:#e3ebf5}
section[data-testid="stSidebar"] [data-baseweb="select"] *{color:#182940}
section[data-testid="stSidebar"] h1{font-size:1.75rem!important;letter-spacing:-.035em}
section[data-testid="stSidebar"] button *{color:#182940!important}
h1,h2,h3{font-family:Arial,sans-serif!important;letter-spacing:-.04em;color:#14243d}
h1{font-size:2.8rem!important} .pg-hero{background:#101e33;color:#eff4fb;padding:38px 42px;border-radius:16px;margin-bottom:24px}
.pg-hero h1{color:#eff4fb!important;font-size:3.25rem!important;margin:10px 0 16px;max-width:850px;line-height:1.05}
.pg-hero p{color:#b9c8dc;font-size:1.05rem;max-width:800px;line-height:1.6}.pg-kicker{font:700 .74rem Arial;letter-spacing:.18em;color:#c3ed7c}
.pg-pill{font:600 .8rem Arial;border:1px solid #35465d;border-radius:30px;padding:8px 12px;display:inline-block;margin-right:10px;color:#eff4fb}
div[data-testid="stMetric"]{background:#fff;border:1px solid #dce3ec;border-radius:12px;padding:20px}
div[data-testid="stMetricValue"]{font-family:Arial;color:#14243d;font-weight:700;font-size:1.65rem}
.pg-step{border-left:3px solid #239b91;background:white;border-radius:0 9px 9px 0;padding:16px 20px;margin:10px 0}
.pg-step strong{color:#14243d}.pg-step span{font-size:.8rem;text-transform:uppercase;color:#12746c;letter-spacing:.08em}
.pg-step p{margin:5px 0 0;color:#526278}.stButton button[kind="primary"]{background:#166f66;border:none}
.pg-rule{height:1px;background:#dce3ec;margin:22px 0} .pg-small{color:#62738a;font-size:.88rem}
</style>'''


def load_demo():
    base = load_dataset(ROOT/'data/synthetic')
    st.session_state.base_data = base
    st.session_state.dataset_namespace = dataset_namespace(base)
    st.session_state.data = database_for(st.session_state.dataset_namespace).effective_data(base,st.session_state.dataset_namespace)
    st.session_state.results = {}
    st.session_state.baselines = {}
    st.session_state.versions = {}
    st.session_state.selected_id = 'PG103'
    st.session_state.is_demo = True


def store():
    return database_for(st.session_state.dataset_namespace)


def database_for(namespace):
    return CaseStore(os.environ.get('PROCUREGUARD_DB_PATH', str(ROOT/f'runtime/cases-{namespace[:12]}.sqlite')))


def scenarios():
    return json.loads((ROOT/'data/scenarios.json').read_text(encoding='utf-8'))


def go_case(identity):
    st.session_state.selected_id = identity
    st.session_state.page = 'Investigate a case'


def run_case(identity, released=False):
    database = store()
    version = database.current(identity)['version']
    model = OllamaPlannerModel() if st.session_state.planner_mode == 'Ollama local planner' else MockPlannerModel()
    with st.spinner('Planning evidence lookups, checking authority and independently validating the case…'):
        result = investigate(st.session_state.data, identity, EvidenceRepository(ROOT/'data/evidence'),
                             model=model, released=released, budget=st.session_state.tool_budget)
        saved_version = database.save(result, expected_version=version, request_key=str(uuid4()))
        st.session_state.results[identity] = result.to_dict()
        st.session_state.versions[identity] = saved_version


def center():
    st.markdown('''<div class="pg-hero"><div class="pg-kicker">PROCUREGUARD AI · ACCOUNTS PAYABLE</div>
    <h1>Turn invoice exceptions<br>into verified decisions.</h1>
    <p>An agent chooses the missing evidence. Deterministic controls check the numbers and authority. A human owns the final review.</p>
    <span class="pg-pill">Evidence resolution</span><span class="pg-pill">Independent critic</span><span class="pg-pill">Versioned case history</span></div>''',unsafe_allow_html=True)
    left,right = st.columns([3,1])
    with left: st.subheader('A queue with a clear next action')
    with right:
        if st.button('Audit loaded invoices',type='primary',width='stretch'):
            st.session_state.baselines={i:audit(st.session_state.data,i).to_dict() for i in st.session_state.data.invoices}
    results = list(st.session_state.baselines.values())
    counts=Counter(r['recommendation'] for r in results)
    cols=st.columns(4)
    for col,label,value in zip(cols,['Invoices audited','Ready for review','Held for review','Evidence gaps'],
                               [len(results),counts['READY_FOR_HUMAN_APPROVAL'],counts['HOLD_FOR_REVIEW'],counts['INSUFFICIENT_DATA']]):
        col.metric(label,value)
    st.caption(f'{len(st.session_state.data.invoices)} synthetic invoices loaded. Audit metrics describe the initial records before evidence resolution.')
    st.subheader('Three cases that explain the system')
    cards=[('PG103','01 / RESOLVE','Two gaps. One verified outcome.','Find a procurement amendment and a warehouse receipt. Watch the plan change after each observation.'),
           ('PG105','02 / PROTECT','One receipt cannot pay twice.','Distinct invoice numbers still consume the same order capacity. Cumulative controls keep both cases held.'),
           ('PG106','03 / CHALLENGE','A document is not authority.','A modified receipt fails its pinned hash check. The agent escalates instead of trusting the attachment.')]
    for col,(identity,kicker,title,description) in zip(st.columns(3),cards):
        with col:
            with st.container(border=True):
                st.caption(kicker);st.subheader(title);st.write(description)
                st.button('Open '+identity,key='open_'+identity,on_click=go_case,args=(identity,),width='stretch')
    if results:
        st.subheader('Review queue')
        queue=[]
        for r in results:
            row=st.session_state.data.invoices[r['invoice_id']]
            queue.append({'Invoice':r['invoice_id'],'PO':row['po_id'],'Amount (INR)':row['declared_total'],
                          'Status':LABELS[r['recommendation']],'Blocking controls':', '.join(f['code'] for f in r['findings']) or 'None'})
        st.dataframe(pd.DataFrame(queue),hide_index=True,width='stretch')
    with st.expander('Load another synthetic CSV bundle'):
        files={name:st.file_uploader(name.replace('_',' ').title(),type='csv',key='upload_'+name) for name in SCHEMAS}
        if st.button('Validate and load bundle'):
            if not all(files.values()):st.error('Select all four CSV tables.')
            else:
                try:
                    base=from_tables({n:parse_csv(f.getvalue().decode('utf-8-sig'),n) for n,f in files.items()})
                    st.session_state.base_data=base
                    st.session_state.dataset_namespace=dataset_namespace(base)
                    st.session_state.data=store().effective_data(base,st.session_state.dataset_namespace)
                    st.session_state.results={};st.session_state.baselines={};st.session_state.is_demo=False
                    st.session_state.versions={}
                    st.session_state.selected_id=next(iter(st.session_state.data.invoices));st.rerun()
                except (ValueError,UnicodeError,KeyError) as exc:st.error(str(exc))
        st.caption('The trusted evidence repository contains only bundled fictional records. Uploaded records are audited without access to those source adapters.')


def case_page():
    st.title('Investigate a case')
    catalog=scenarios()
    identities=list(st.session_state.data.invoices)
    selected=st.session_state.get('selected_id',identities[0])
    if selected not in identities:selected=identities[0]
    identity=st.selectbox('Case',identities,index=identities.index(selected),key='selected_id',
                          format_func=lambda k:k+' · '+catalog.get(k,{}).get('title','Invoice investigation'))
    spec=catalog.get(identity)
    if spec:st.write(spec['description'])
    invoice=st.session_state.data.invoices[identity]
    a,b,c=st.columns(3)
    a.metric('Invoice amount',f"INR {invoice['declared_total']}")
    b.metric('Purchase order',invoice['po_id'])
    current=store().current(identity)
    c.metric('Case revision',current['version'])
    released=st.checkbox('Make the delayed warehouse receipt available (simulation)',value=False,key='released_'+identity) if identity=='PG104' else False
    with st.expander('Original invoice and source records'):
        columns=st.columns(2)
        columns[0].json(invoice)
        columns[1].json(st.session_state.data.purchase_orders.get(invoice['po_id'],{}))
        st.caption('The original invoice is never edited. Approved evidence changes a per-investigation snapshot only.')
    if st.button('Run investigation',type='primary'):
        if not st.session_state.is_demo:
            # Reject accidental crossover into a bundled case with the same IDs.
            class EmptyRepository:
                def lookup(self,*args,**kwargs):
                    from .evidence import EvidenceResult
                    return EvidenceResult('not_found','No connected evidence source for uploaded data',[],[])
            database=store();version=database.current(identity)['version']
            result=investigate(st.session_state.data,identity,EmptyRepository(),budget=st.session_state.tool_budget)
            st.session_state.results[identity]=result.to_dict()
            st.session_state.versions[identity]=database.save(result,expected_version=version,request_key=str(uuid4()))
            st.rerun()
        else:
            try:
                run_case(identity,released)
                st.rerun()
            except (ValueError,OSError) as exc:st.error(str(exc))
    result=st.session_state.results.get(identity)
    source_hash=snapshot_hash(st.session_state.data)
    if result is None or result['source_snapshot_hash'] != source_hash:
        try:
            restored=store().recover(identity,source_hash)
        except (ValueError,OSError) as exc:
            st.error(f'Cannot reopen stored evidence safely: {exc}');return
        result=restored['result'] if restored else None
        if restored:
            st.session_state.results[identity]=result
            st.session_state.versions[identity]=restored['version']
            st.caption(f'Reopened saved investigation revision {restored["run_version"]}. Current case revision: {restored["version"]}. No tools were rerun.')
        else:
            st.session_state.results.pop(identity,None)
    with st.expander('Invoice lifecycle and ledger allocation'):
        status=invoice.get('lifecycle_status','submitted')
        st.write(f'**Current classification:** {status}')
        st.caption('Submitted and recorded invoices consume capacity. Rejected, cancelled, duplicate and superseded copies are excluded. Recorded means a procurement commitment, not payment approval. Changes require a rationale and invalidate affected recommendations.')
        target=st.selectbox('New lifecycle classification',sorted(TRANSITIONS.get(status,{'submitted'})),key='life_target_'+identity)
        replacement=None
        if target in ('duplicate','superseded'):
            choices=[k for k,r in st.session_state.data.invoices.items() if k!=identity and r.get('lifecycle_status','submitted') in ('submitted','recorded') and all(r[f]==invoice[f] for f in ('vendor_id','po_id','item_id'))]
            if choices:replacement=st.selectbox('Active replacement invoice',choices,key='life_replacement_'+identity)
            else:st.warning('No active replacement matches this supplier, PO and item.')
        actor=st.selectbox('Lifecycle demo role',['ap_reviewer','faculty_observer'],key='life_actor_'+identity)
        rationale=st.text_input('Lifecycle rationale',max_chars=1000,key='life_reason_'+identity)
        if st.button('Record lifecycle classification',key='life_save_'+identity,disabled=target in ('duplicate','superseded') and replacement is None):
            try:
                store().set_lifecycle(st.session_state.base_data,identity,target,expected_status=status,actor=actor,rationale=rationale,replacement=replacement)
                st.session_state.data=store().effective_data(st.session_state.base_data,st.session_state.dataset_namespace)
                st.session_state.results={};st.session_state.baselines={};st.session_state.versions={}
                st.rerun()
            except (ValueError,PermissionError,OSError) as exc:st.error(str(exc))
    if result is None:
        st.info('Run this case to see the initial decision, selected tools, evidence and final recommendation. Saved packets for changed source records require revalidation.');return
    initial,final=result['initial'],result['final']
    st.divider()
    a,b,c=st.columns([2,2,1])
    a.metric('Before investigation',LABELS[initial['recommendation']])
    b.metric('After investigation',LABELS[final['recommendation']])
    c.metric('Evidence lookups',f"{len([s for s in result['steps'] if s['tool']!='stop'])} / {result['budget']}")
    if final['recommendation']=='READY_FOR_HUMAN_APPROVAL':st.success('Required controls passed. A human review is still required.')
    elif final['verified']:st.warning(final['explanation'])
    else:st.error('Verification gate blocked this case. Conflicting evidence cannot clear an invoice.')
    if any(s.get('fallback') for s in result['steps']):st.warning('The local model was unavailable or returned an invalid action. The recorded fallback used the offline mock planner.')
    tabs=st.tabs(['Decision & next actions','Agent trace','Evidence provenance','Case history'])
    with tabs[0]:
        resolved=sorted({f['code'] for f in initial['findings']}-{f['code'] for f in final['findings']})
        if resolved:st.write('**Resolved controls:** '+', '.join(resolved))
        if final['findings']:
            st.dataframe([{'Control':f['code'],'Severity':f['severity'],'Evidence':json.dumps(f['evidence'])} for f in final['findings']],hide_index=True,width='stretch')
        if result['next_actions']:st.dataframe(result['next_actions'],hide_index=True,width='stretch')
        else:st.write('**Next owner:** Accounts payable reviewer. Inspect the verified evidence packet and record a review.')
        st.caption('Severity scores are illustrative policy weights, not fraud probabilities. No payment function exists.')
    with tabs[1]:
        st.write('**Planner:** '+result['planner_mode'])
        for step in result['steps']:
            st.markdown(f'<div class="pg-step"><span>Step {step["step"]} · {html.escape(step["status"])}</span><br><strong>{html.escape(step["tool"])}</strong><p>{html.escape(step["summary"])}</p><p>{html.escape(step.get("reason",""))}</p></div>',unsafe_allow_html=True)
            if step.get('fallback'):st.caption(step['fallback'])
            if step.get('planner_record'):
                with st.expander('Actual local model request and response'):
                    st.json(step['planner_record'])
        if not result['steps']:st.info('No permitted evidence lookup is needed or can safely resolve this case.')
        st.write('**Independent final verification:** '+('Passed' if final['verified'] else 'Blocked'))
        with st.expander('Accounting tool events and critic comparisons'):
            st.dataframe(final['trace'],hide_index=True,width='stretch');st.json(final['verifications'])
    with tabs[2]:
        if result['evidence']:
            st.dataframe([{'Evidence':d['evidence_id'],'Source':d['source'],'Authority':d['approved_by_role'],
                           'Effective date':d['effective_date'],'SHA-256':d['sha256']} for d in result['evidence']],hide_index=True,width='stretch')
        else:st.info('No additional evidence was accepted.')
        if result['evidence']:
            selected=st.selectbox('Open source evidence',[d['evidence_id'] for d in result['evidence']],key='evidence_'+identity)
            document=next(d for d in result['evidence'] if d['evidence_id']==selected)
            with st.expander('Verified source record and exact values',expanded=True):
                st.json(document)
                st.write('**Original invoice:**');st.json(result['source_snapshot']['invoices'][identity])
                st.write('**Effective purchase order:**');st.json(result['effective_snapshot']['purchase_orders'].get(invoice['po_id'],{}))
        st.caption('Hashes detect content changes against the trusted local manifest. The manifest and approval metadata are simulated source authority, not digital signatures.')
        st.code('Source snapshot: '+result['source_snapshot_hash']+'\nEffective snapshot: '+result['effective_snapshot_hash'],language=None)
    with tabs[3]:
        history=store().history(identity)
        if history:st.dataframe(history,hide_index=True,width='stretch')
        st.json(store().verify_integrity())
        revisions=store().revisions(identity)
        if revisions:
            version=st.selectbox('Inspect saved investigation revision',revisions,key='history_'+identity)
            previous=store().load(identity,version)
            st.download_button('Download selected revision',json.dumps(previous,indent=2),f'{identity}_revision_{version}.json','application/json')
        st.caption('SQLite transactions, optimistic case revisions and event hashes are implemented. A database administrator can rewrite local storage; external anchoring and production identity are future work.')
    st.download_button('Download complete evidence packet',json.dumps(result,indent=2),identity+'_evidence_packet.json','application/json')
    with st.expander('Human review simulation'):
        st.caption('These demo roles are selectable and are not authenticated identities. Confirming a recommendation cannot approve a payment.')
        actor=st.selectbox('Demo role',['ap_reviewer','faculty_observer'])
        action=st.selectbox('Review action',['confirm_recommendation','request_recheck'])
        rationale=st.text_area('Review rationale',max_chars=1000)
        if st.button('Record review'):
            try:
                store().review(identity,expected_version=st.session_state.versions[identity],actor=actor,action=action,rationale=rationale)
                st.session_state.versions[identity]=store().current(identity)['version']
                st.success('Review recorded. For a recheck, provide the requested source evidence and run the investigation again to create a new revision.')
            except (ValueError,PermissionError) as exc:st.error(str(exc))


def controls():
    st.title('Evidence & controls')
    st.write('A model may choose a permitted lookup. It cannot create source evidence, change an invoice, bypass accounting checks or execute a payment.')
    st.subheader('Trust boundaries')
    st.dataframe([
        {'Boundary':'Planner output','Enforcement':'Schema + eligible-tool allowlist + maximum three lookups; visible fallback'},
        {'Boundary':'Source evidence','Enforcement':'Pinned content hash + order/vendor/item scope + effective date + approval role'},
        {'Boundary':'Accounting','Enforcement':'Decimal comparisons + line exposure + cumulative commitments + independent critic'},
        {'Boundary':'Human review','Enforcement':'Version conflict checks + reviewer role + required rationale; identity is simulated'},
        {'Boundary':'Storage','Enforcement':'SQLite transaction + idempotency key + hash chain + source/effective snapshots'},
    ],hide_index=True,width='stretch')
    st.subheader('Evidence register')
    repo=EvidenceRepository(ROOT/'data/evidence')
    st.dataframe(pd.DataFrame(repo.manifest),hide_index=True,width='stretch')
    st.subheader('Policy PG-2.0')
    st.write('INR and single-line invoices. Inclusive unit tolerance ₹0.01, arithmetic tolerance ₹0.01, and a ₹1.00 line-exposure cap. High value begins at ₹100,000. Only submitted and recorded invoices consume capacity. Exact duplicate copies count as one obligation, while conflicting duplicate values block ledger confidence. Inactive submissions cannot become ready. Lifecycle classification is a simulated human action and is independent of payment approval.')
    st.subheader('Boundaries of this PoC')
    st.write('All data and source systems are fictional. No OCR, tax engine, credit-note lifecycle, ERP connector, production authentication or payment execution. The optional local language model is limited to evidence-tool choice. Default execution uses an explicit mock planner. A signed external source, audited user directory and separately authored field evaluation are deployment requirements.')


def validation():
    st.title('Validation lab')
    path=ROOT/'reports/validation_v2.json'
    if not path.exists():st.info('Run scripts/validate_v2.py to generate executed validation evidence.');return
    report=json.loads(path.read_text(encoding='utf-8'))
    a,b,c,d=st.columns(4)
    a.metric('Tests passed',report['tests']['passed'])
    b.metric('Tests failed / errors',report['tests']['failed'])
    c.metric('Scenario decisions',f"{report['agreement']} / {report['scenarios']}")
    d.metric('Unresolved → ready',report['resolved'])
    st.caption('Executed '+report['generated_at']+'. Known synthetic cases; these results do not establish real-world fraud accuracy or reviewer time savings.')
    st.subheader('Rules-only baseline versus evidence resolution')
    st.dataframe(report['comparisons'],hide_index=True,width='stretch')
    st.write('The baseline is the same mandatory accounting checker without evidence lookup. This comparison isolates the effect of acquiring authorised evidence; it does not establish that an LLM outperforms rules or that multiple agents are necessary.')
    st.subheader('Measured engine workload')
    st.json(report['timing'])
    st.caption('Local execution only. Model startup, UI rendering, human work and organisational savings are not included. No reviewer-time claim is made.')
    with st.expander('Executed automated tests'):st.dataframe(report['tests']['cases'],hide_index=True,width='stretch')
    st.download_button('Download validation evidence',json.dumps(report,indent=2),'validation_v2.json','application/json')
    v3_path=ROOT/'reports/validation_v3.json'
    if v3_path.exists():
        v3=json.loads(v3_path.read_text(encoding='utf-8'))
        st.subheader('Frozen challenge and ablation')
        st.dataframe(v3['challenge']['metrics'],hide_index=True,width='stretch')
        st.caption(v3['challenge']['boundary'])
        with st.expander('Challenge results, including deliberate matcher faults'):
            st.dataframe(v3['challenge']['rows'],hide_index=True,width='stretch')
        st.subheader('Real local model demonstration')
        live=v3.get('live_model')
        if live:
            st.write(f'Model: **{live["model"]}**. Recorded: {live["executed_at"]}. {live["agreement"]}/{live["case_count"]} case decisions matched, {live["live_choices"]} live selections, {live["fallbacks"]} fallbacks.')
            st.caption('This is a recorded demonstration on known synthetic cases, not a model-superiority benchmark. Default app execution remains offline.')
        else:st.info('No completed live model run has been recorded.')
        st.download_button('Download v3 validation and comparisons',json.dumps(v3,indent=2),'validation_v3.json','application/json')


def main():
    st.set_page_config(page_title='ProcureGuard AI · Evidence Resolution',page_icon='🛡️',layout='wide')
    st.markdown(CSS,unsafe_allow_html=True)
    if 'data' not in st.session_state:load_demo()
    if 'versions' not in st.session_state:st.session_state.versions={}
    integrity=store().verify_integrity()
    if not integrity['valid']:
        st.error('Local case storage failed its integrity check: '+integrity['reason'])
        st.stop()
    latest=store().effective_data(st.session_state.base_data,st.session_state.dataset_namespace)
    if snapshot_hash(latest) != snapshot_hash(st.session_state.data):
        st.session_state.data=latest
        st.session_state.results={};st.session_state.baselines={};st.session_state.versions={}
    st.sidebar.title('ProcureGuard AI')
    st.sidebar.caption('EVIDENCE RESOLUTION WORKBENCH')
    page=st.sidebar.radio('Workspace',['Command center','Investigate a case','Evidence & controls','Validation lab'],key='page')
    st.sidebar.divider()
    st.sidebar.selectbox('Planner',['Offline mock planner','Ollama local planner'],key='planner_mode')
    if st.session_state.planner_mode=='Ollama local planner':
        st.sidebar.caption('Local model: '+os.environ.get('PROCUREGUARD_OLLAMA_MODEL','qwen2.5-coder:7b'))
        if st.sidebar.button('Check installed local models'):
            try:st.sidebar.write(OllamaPlannerModel.available_models())
            except (OSError,ValueError) as exc:st.sidebar.warning(f'Local service unavailable: {type(exc).__name__}')
    st.sidebar.slider('Maximum evidence lookups',min_value=0,max_value=3,value=3,key='tool_budget')
    st.sidebar.caption('Offline mode needs no model download. Ollama mode requires a running local model.')
    st.sidebar.divider()
    st.sidebar.caption('Rishi Dwivedi · 24070126152\n\nSiddarth Singh Kushwah · 24070126174\n\nAIML-C · SIT Pune')
    if st.sidebar.button('Restore demo records'):
        load_demo();st.rerun()
    st.sidebar.caption('Synthetic data · Human review required\n\nSaved case history survives a UI reset.')
    {'Command center':center,'Investigate a case':case_page,'Evidence & controls':controls,'Validation lab':validation}[page]()
