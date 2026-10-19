import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {pathToFileURL} from 'node:url';
const runtime=path.join(os.homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies');
const modules=process.env.RUNTIME_NODE_MODULES||path.join(runtime,'node/node_modules');
const skill=process.env.PRESENTATION_SKILL_DIR||path.join(os.homedir(),'.codex/plugins/cache/openai-primary-runtime/presentations/26.1015.12040/skills/presentations');
process.env.RUNTIME_NODE_MODULES=modules;
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(modules,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation,resolvePresentationFont,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const root=process.cwd(),build=path.join(root,'build/deck');
await fs.mkdir(build,{recursive:true});await fs.mkdir('presentation/slide_previews',{recursive:true});
const report=JSON.parse(await fs.readFile('reports/validation_v2.json','utf8'));
const v3=JSON.parse(await fs.readFile('reports/validation_v3.json','utf8'));
const font=resolvePresentationFont({fontFamily:'Arial'});
const p=Presentation.create({slideSize:{width:1280,height:720}});p.theme.defaultFont=font;
const C={navy:'#101E33',paper:'#F4F6FA',ink:'#172A42',muted:'#5D6D82',lime:'#C3ED7C',teal:'#167F74',mint:'#DEF1E8',coral:'#ED8C77',line:'#D8E0EA',white:'#FFFFFF'};
function rect(s,x,y,w,h,fill,line='none',radius=0){return s.shapes.add({geometry:radius?'roundRect':'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:line==='none'?0:1},borderRadius:radius});}
function txt(s,value,x,y,w,h,size=26,color=C.ink,bold=false,name='text'){
 const sh=s.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=value;sh.text.insets=0;sh.text.style={typeface:font,fontSize:size,color,bold};return sh;
}
function slide(title,notes,{dark=false,backup=false}={}){
 const s=p.slides.add();s.background.fill=dark?C.navy:C.paper;s.hidden=backup;
 if(title)txt(s,title,64,58,1140,114,46,dark?C.white:C.ink,true,'title');
 const n=p.slides.items.length;
 txt(s,backup?'TECHNICAL BACKUP':String(n).padStart(2,'0'),backup?985:1160,666,backup?235:55,24,16,dark?C.lime:C.muted);
 s.speakerNotes.text=notes;return s;
}
function line(s,x,y,w,color=C.line){rect(s,x,y,w,1.5,color);}
function box(s,label,x,y,w=220,h=82,dark=false){
 const sh=rect(s,x,y,w,h,dark?C.navy:C.mint,dark?'none':C.teal,8);
 txt(s,label,x+16,y+14,w-32,h-20,20,dark?C.white:C.ink,true);return sh;
}
function link(s,a,b,from='right',to='left',label='',x=0,y=0){
 s.shapes.connect(a,b,{kind:'elbow',fromSide:from,toSide:to,line:{fill:C.teal,width:2},tail:{type:'arrow'}});
 if(label)txt(s,label,x,y,240,28,18,C.teal);
}
function table(s,values,x,y,width,height,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:widths,values});
 t.borders.assign({fill:C.line,width:1,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.navy:(r%2?C.white:C.paper);
  cell.text.style={typeface:font,fontSize:size,color:r===0?C.white:C.ink,bold:r===0};
 }
 return t;
}
// 01. A quiet, bold opening with an editable source-to-decision illustration.
let s=slide('',`0:00–0:15, Rishi. We are Rishi Dwivedi and Siddarth Singh Kushwah from AIML-C, SIT Pune. ProcureGuard is an agentic accounts-payable exception-resolution proof of concept. It retrieves authorised evidence and produces recommendations for human review. No payment is executed.`,{dark:true});
txt(s,'PROCUREGUARD AI',64,65,640,45,25,C.lime,true);
txt(s,'Evidence before\ndecisions.',64,175,800,230,82,C.white,true,'title');
txt(s,'Agentic invoice exception resolution',68,438,740,48,30,'#B7C7DB');
txt(s,'Rishi Dwivedi  /  24070126152\nSiddarth Singh Kushwah  /  24070126174',68,551,740,74,22,C.white);
txt(s,'AIML-C, SIT Pune',68,640,640,30,20,'#B7C7DB');
rect(s,905,170,296,370,'#182B45','none',14);
txt(s,'SOURCE RECORDS',929,197,248,30,18,C.lime,true);
for(const [i,label] of ['Order amendment','Warehouse receipt','Vendor verification'].entries()){
 rect(s,929,247+i*58,248,42,'#223B57','none',6);txt(s,label,944,257+i*58,220,26,20,C.white);
}
line(s,929,446,248,'#41566F');txt(s,'Verified recommendation',929,470,248,54,23,C.lime,true);

// 02. The business problem, with no invented savings or fraud statistics.
s=slide('A flag starts another investigation.',`0:15–0:45, Rishi. In accounts payable, a reviewer matches invoices to purchase orders and receipts, then checks supplier details. A flag does not tell procurement which amendment to retrieve or receiving which receipt is missing. Our domain is procurement and finance operations. We focus on the evidence search and accountable handoff after a mismatch. Three-way matching itself is established enterprise functionality. Source: https://learn.microsoft.com/en-us/dynamics365/finance/accounts-payable/accounts-payable-invoice-matching`);
txt(s,'The records are separated.',64,197,530,45,30,C.teal,true);
const sources=['Invoice','Purchase order','Goods receipt','Vendor master'];
for(let i=0;i<sources.length;i++){line(s,64,270+i*65,470);txt(s,sources[i],64,283+i*65,470,40,27);}
rect(s,613,198,3,380,C.line);
txt(s,'The reviewer still has to ask:',674,197,540,48,30,C.ink,true);
txt(s,'Which evidence is missing?',674,292,535,50,30);
txt(s,'Who can authorise this change?',674,388,535,70,30);
txt(s,'What happens when sources disagree?',674,494,535,76,30);
txt(s,'Business goal: fewer unresolved handoffs and a traceable reason for every recommendation.',64,606,1120,55,24,C.teal,true);

// 03. A precise, editable example tied to the actual PG103 data.
s=slide('One invoice. Two missing facts.',`0:45–1:10, Rishi. Case PG103 bills 10 units at INR 120. The original PO says INR 100 and no receipt has reached accounts payable. The planner first retrieves a procurement-approved amendment, then observes that the receipt is still missing and chooses the warehouse lookup. The critic independently checks the revised source snapshot. The invoice itself is unchanged. The outcome is ready for human review, not approval or payment. Evidence: reports/investigation_packets.json, PG103.`);
txt(s,'PG103  /  Invoice amount INR 1,200',64,184,1140,48,28,C.teal,true);
table(s,[['Evidence','Initial records','Accepted source record'],['PO unit price','INR 100; invoice bills INR 120','Approved amendment: INR 120'],['Goods received','No matching receipt','Warehouse receipt: 10 units'],['Recommendation','Waiting for evidence','Ready for human review']],64,252,1152,276,[235,430,487],23);
const stages=['Observe gaps','Retrieve amendment','Retrieve receipt','Verify revised evidence'];
for(let i=0;i<4;i++){
 txt(s,String(i+1).padStart(2,'0'),64+i*290,567,55,40,27,C.teal,true);
 txt(s,stages[i],64+i*290,607,265,48,23,C.ink,true);
}

// 04. Compact architecture; full tool/data mapping appears in the appendix.
s=slide('The planner chooses evidence. Controls decide.',`1:10–1:50, Rishi. The matching and risk agents always perform mandatory checks. The critic recomputes the findings separately. When a gap is resolvable, the resolution planner selects a permitted evidence tool. The evidence agent checks hashes, scope, effective dates and authority before applying a source update to a local snapshot. The loop reassesses the findings, with at most three lookups. The decision coordinator and human reviewer receive the final state. Planner implementations are an offline mock and optional local Ollama; arithmetic never depends on the model. Modules: investigation.py, planning.py, agents/evidence_agent.py, tools.py, agents/critic.py, case_store.py.`);
const input=box(s,'UI + operational\nCSV records',64,213);
const controls=box(s,'Matching + risk\nRun all checks',350,213,220,82,true);
const critic=box(s,'Independent critic\nRecheck evidence',636,213,220,82,true);
const decision=box(s,'Decision coordinator\nReady / hold / missing',922,213,294,82,true);
const authority=box(s,'Approved sources\nPO / GRN / vendor',64,441,220,100);
const executor=box(s,'Evidence agent\nVerify and apply',350,441,220,100,true);
const planner=box(s,'Planner\nChoose evidence',636,441,220,100,true);
const human=box(s,'Human review\nNo payment execution',922,441,294,100);
link(s,input,controls);link(s,controls,critic);link(s,critic,decision);
link(s,critic,planner,'bottom','top','resolvable gap',666,355);
link(s,planner,executor,'left','right');link(s,authority,executor);
link(s,executor,controls,'top','bottom','reassess snapshot',365,355);
link(s,decision,human,'bottom','top','final recommendation',942,355);
txt(s,'SQLite state: snapshots, case revisions, lifecycle and source-hash recovery',64,604,1120,48,25,C.teal,true);

// 05. Real application evidence, cropped only for projector readability.
s=slide('Live: resolve, reopen and revalidate.',`1:50–3:10, Siddarth. Run PG103 and inspect successive tool choices and accepted source records. Refresh the browser, reopen the case and show that the stored run ID is unchanged: no lookup was repeated. PG105 is initially held for cumulative quantity. Classify PG105B as rejected or cancelled with a rationale, then re-investigate PG105 and show the released capacity. PG105B itself remains held. Use offline mode for predictable pacing; the real local-model demonstration is separately recorded with requests and responses. This screenshot is from an actual application run.`,{dark:false});
const screenshot=await fs.readFile('presentation/evidence/ui_decision_crop.png');
s.images.add({blob:screenshot.buffer.slice(screenshot.byteOffset,screenshot.byteOffset+screenshot.byteLength),contentType:'image/png',alt:'Actual PG103 before-and-after decision from the running Streamlit application',fit:'contain',position:{left:64,top:204,width:1152,height:190}});
txt(s,'01  Acquire the right evidence',64,447,535,46,29,C.teal,true);
txt(s,'Amendment, then warehouse receipt',64,512,535,42,27,C.ink,true);
txt(s,'The next tool follows the remaining gap.',64,565,535,65,25,C.muted);
txt(s,'02  Reopen the saved investigation',682,447,535,46,29,C.teal,true);
txt(s,'Same run ID after a fresh session',682,512,535,42,27,C.ink,true);
txt(s,'Changed lifecycle requires revalidation.',682,565,535,65,25,C.muted);
txt(s,'Executed case PG103. Original invoice unchanged. Human review required.',64,640,1110,32,22,C.muted);

// 06. Three implemented challenges, not hypothetical marketing claims.
s=slide('The system also knows when to stop.',`3:10–3:40, Siddarth. PG105 and PG105B bill 20 units against capacity of 10, even though invoice numbers differ; both are held. PG106 has a modified receipt and fails the pinned hash. PG107 has two authorised amendments with different prices and escalates. These controls are exercised in tests. Hashes are checked against a trusted local manifest; this is not a digital signature or proof that a real delivery happened.`,{dark:true});
const checks=[['Lifecycle-aware capacity','Inactive copies excluded','REVALIDATE AFTER REVIEW'],['Changed attachment','Pinned hash does not match','EVIDENCE BLOCKED'],['Conflicting authority','INR 120 / INR 130','HUMAN RESOLUTION']];
for(let i=0;i<3;i++){
 const x=64+i*394;
 txt(s,String(i+1).padStart(2,'0'),x,205,130,90,74,C.lime,true);
 txt(s,checks[i][0],x,327,350,76,32,C.white,true);
 txt(s,checks[i][1],x,430,350,76,26,'#B7C7DB');
 line(s,x,538,330,'#41566F');txt(s,checks[i][2],x,565,350,55,21,C.coral,true);
}

// 07. An editable chart and precise boundaries on what the measurements prove.
s=slide('Measured on fixed development cases.',`3:40–4:15, Siddarth. ${report.tests.passed} automated tests passed and all 44 regression/operational decisions agree. The frozen extension challenge has 25 cases. Single-invoice, historical producer and critic-enabled modes agreed on 19, 23 and 25 decisions. Incorrect ready counts were 6, 2 and 0. Two deliberate matcher omissions exercise fault containment. The same development assistant authored the fixtures before v3 implementation; these are not independently held-out cases. The installed local model completed four known cases, five actual tool selections and zero fallback. This demonstrates live execution, not model superiority. Sources: reports/validation_v3.json, live_planner_run.json and pytest-results.xml.`);
txt(s,String(report.tests.passed),64,186,320,92,76,C.teal,true);txt(s,'automated tests passed',64,285,350,55,25,C.ink,true);
txt(s,'25/25',470,186,350,92,76,C.ink,true);txt(s,'frozen challenge decisions',470,285,350,55,25,C.ink,true);
txt(s,`${v3.live_model.agreement}/${v3.live_model.case_count}`,952,186,230,92,76,C.teal,true);txt(s,'real local-model cases',882,285,330,72,25,C.ink,true);
line(s,64,372,1152);
const chart=s.charts.add('bar',{position:{left:64,top:403,width:730,height:220},categories:['One invoice','History','History + critic'],
 series:[{name:'Correct decisions out of 25',values:v3.challenge.metrics.map(m=>m.exact_agreement),fill:C.teal}],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:100},
 xAxis:{textStyle:{fontSize:22,fill:C.ink}},
 yAxis:{min:0,max:25,majorUnit:5,textStyle:{fontSize:18,fill:C.muted},majorGridlines:{fill:C.line,width:1}},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:25,bold:true,fill:C.ink}},chartFill:'none',plotAreaFill:'none'});
applyPresentationChartFont(chart,{fontFamily:font});
txt(s,'25 frozen development cases\nIncorrect ready: 6 / 2 / 0\nTwo injected producer faults',846,431,370,150,25,C.muted);
txt(s,'Known development cases. No field-accuracy, reviewer-time or financial-savings claim.',64,640,1115,33,21,C.muted);

// 08. Close with an honest product boundary and a concrete next stage.
s=slide('A traceable handoff to a human.',`4:15–4:45, Siddarth. The PoC implements cumulative reconciliation, an evidence loop, independent verification, saved-case reopening and human lifecycle classification. A real installed local model selected tools in four recorded synthetic scenarios. Upstream sources and reviewer identities remain simulated. Next steps are independent unseen evaluation, authenticated sources, multi-line and tax workflows. No payment capability exists. Both team members should understand the planner and accounting boundary. End the eight-slide presentation here; separate architecture and policy documents support questions.`,{dark:true});
txt(s,'Evidence-backed recommendations.\nHuman-owned decisions.',64,196,1152,165,54,C.white,true);
const closing=[['IMPLEMENTED','Case recovery and lifecycle\nIndependent accounting critic\nRecorded real model planning'],['SIMULATED','Warehouse and procurement sources\nSelectable reviewer identities\nNo payment capability'],['NEXT','Independent unseen evaluation\nAuthenticated, signed sources\nMulti-line and tax workflows']];
for(let i=0;i<3;i++){
 const x=64+i*394;line(s,x,413,340,'#41566F');txt(s,closing[i][0],x,442,350,38,19,C.lime,true);txt(s,closing[i][1],x,494,350,130,24,'#B7C7DB');
}

// 09. Complete architecture and evaluation isolation; hidden in slideshow.
s=slide('Architecture: tools, state and trust boundaries',`Technical backup. Six specialist roles: Planner (audit routing and resolution choice), Matching, Risk assessment, Evidence executor/verifier, Independent Critic, Decision coordinator. Agents are logical software components sharing structured state, not six separate LLMs or operating-system processes. Mandatory controls always run. The independent critic does not call matching/risk tool implementations. Evidence retrieval reads only pinned synthetic files. Runtime Dataset never contains expected outcomes. Reports contain original and effective snapshots for reproducibility.`,{backup:true});
const nodes={};
nodes.ui=box(s,'Streamlit UI\nInvoice selection',64,190,245,94);
nodes.audit=box(s,'Matching + risk\nAmounts / capacity',352,190,260,94,true);
nodes.critic=box(s,'Independent critic\nRecompute accounting',655,190,260,94,true);
nodes.decision=box(s,'Decision coordinator\nRecommendation gate',958,190,258,94,true);
nodes.sources=box(s,'Source adapters\nGRN / PO / vendor',64,355,245,94);
nodes.evidence=box(s,'Evidence agent\nHash / scope / authority',352,355,260,94,true);
nodes.plan=box(s,'Planner\nMock or local Ollama',655,355,260,94,true);
nodes.human=box(s,'Human review\nRationale / version',958,355,258,94);
link(s,nodes.ui,nodes.audit);link(s,nodes.audit,nodes.critic);link(s,nodes.critic,nodes.decision);
link(s,nodes.critic,nodes.plan,'bottom','top');link(s,nodes.plan,nodes.evidence,'left','right');link(s,nodes.sources,nodes.evidence);
link(s,nodes.evidence,nodes.audit,'top','bottom');link(s,nodes.decision,nodes.human,'bottom','top');
const csv=box(s,'Operational CSV\nInvoices / PO / GRN / vendors',64,520,245,94);
const state=box(s,'Investigation state\nSource / effective records',352,520,260,94);
const sqlite=box(s,'SQLite case store\nRevisions / event hashes',655,520,260,94);
const evalbox=box(s,'Separate evaluation\nAnswer key / tests / results',958,520,258,94);
link(s,csv,nodes.audit,'top','left');link(s,state,sqlite);link(s,nodes.human,sqlite,'bottom','top');
txt(s,'Bounded control: eligible tool allowlist, at most three evidence lookups, one accounting recheck.',64,626,1140,34,22,C.teal,true);

// 10. Editable policy table.
s=slide('Policy PG-2.0 and failure outcomes',`Technical backup. These are illustrative policies, not accounting advice or a legal compliance claim. Quantities are positive whole units and INR values use Decimal. Cumulative capacity is a conservative group hold across every loaded active invoice against the same order, vendor and item. There is no settlement ledger or automatic allocation. The line exposure guard applies to a unit difference that otherwise fits the unit tolerance, preventing many small per-unit differences from accumulating into a large line discrepancy.`,{backup:true});
table(s,[['Control','Policy','Outcome'],['Unit price / arithmetic','Inclusive INR 0.01 tolerance','Mismatch requires review'],['Line exposure','INR 1 cap on tolerated unit differences','Hold material line differences'],['Cumulative quantity','All loaded commitments fit PO and GRN','Hold overcommitted group'],['High value','Exposure at least INR 100,000','Human review'],['Evidence or critic conflict','No bypass; at most one accounting recheck','Hold unresolved verification'],['Missing authoritative evidence','Stop after allowed lookups or budget','Request evidence and owner']],64,190,1152,420,[255,562,335],21);

// 11. Editable agent contracts.
s=slide('Agent responsibilities and collaboration',`Technical backup. The resolution planner is instantiated through a swappable model interface in planning.py, with a deterministic offline mock and a local Ollama JSON-schema implementation. The controller validates its proposed action independently of model output. Evidence application is atomic on a copied snapshot. Matching and risk findings feed the critic. The decision coordinator never calls a payment tool; none exists. The actual local-model execution is recorded in reports/live_planner_run.json; protocol stubs also exercise failure handling.`,{backup:true});
table(s,[['Role','Input and responsibility','Observable output'],['Planner','Findings, attempted tools, remaining budget','Allowed next tool and brief action summary'],['Matching agent','Invoice, PO and receipt source snapshot','Schema, links, amounts and capacity findings'],['Risk agent','Retained mandatory screening evidence','Risk flags and compound severity'],['Evidence agent','Selected tool and trusted source repository','Accepted / missing / rejected / conflicting records'],['Independent critic','Effective originals and proposed findings','Complete evidence comparison and verification'],['Decision coordinator','Verified findings and evidence gate','Ready / hold / insufficient; never payment']],64,190,1152,420,[250,540,362],21);

// 12. Reproducibility and sources are accessible without extending the timed talk.
s=slide('Reproduction, evaluation limits and sources',`Technical backup. Install Python 3.11+ and requirements-tested.txt. Run python -m streamlit run app.py. Run python scripts/validate_v3.py to regenerate actual results. Regenerate synthetic records with python data/generate_cases.py. Optional local model setup is documented in README; the benchmark uses the offline mock. Domain reference: https://learn.microsoft.com/en-us/dynamics365/finance/accounts-payable/accounts-payable-invoice-matching . Local structured-output protocol reference: https://ollama.com/blog/structured-outputs . Agent/workflow terminology reference: https://www.anthropic.com/engineering/building-effective-agents . No third-party photographs or generated UI screenshots are used.`,{backup:true});
txt(s,'Run the app',64,197,485,44,29,C.teal,true);txt(s,'python -m streamlit run app.py',64,257,540,50,25,C.ink);
txt(s,'Reproduce the evidence',64,348,540,44,29,C.teal,true);txt(s,'python scripts/validate_v3.py',64,408,540,50,25,C.ink);
txt(s,'Known limits',678,197,540,44,29,C.teal,true);
txt(s,'Synthetic cases known during development\nSmall actual model demo; no field validation\nLocal hashes are not immutable audit storage\nSingle-line INR records; no tax or credit-note engine',678,259,540,220,25,C.ink);
line(s,64,527,1152);
txt(s,'References',64,553,260,35,23,C.teal,true);
txt(s,'Microsoft Learn: Accounts payable invoice matching\nOllama: Structured outputs\nAnthropic: Building effective agents',350,550,866,100,22,C.muted);

const candidate=path.join(build,'candidate-v3.pptx');
for(let i=0;i<p.slides.items.length;i++){
 const blob=await p.export({slide:p.slides.items[i],format:'png',scale:1});
 await fs.writeFile(`presentation/slide_previews/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await blob.arrayBuffer()));
 if(i===8)await fs.writeFile('docs/architecture_overview.png',new Uint8Array(await blob.arrayBuffer()));
}
p.slides.keep([0,1,2,3,4,5,6,7]);
await (await PresentationFile.exportPptx(p)).save(candidate);
const receiptPath=path.join(build,'final-validation-'+Date.now()+'.json');
const finalized=await finalizePresentation({workspaceDir:root,candidatePath:candidate,
 finalPath:path.join(root,process.env.PPTX_OUTPUT||'presentation/ProcureGuard_AI_CA3_Improved.pptx'),
 pythonExecutable:process.env.RUNTIME_PYTHON||path.join(runtime,'python/python.exe'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',
             '--require-native-table-slide','3'],
 requiredNativeTableOwnerSlides:[3],requiredNativeChartOwnerSlides:[7],explicitTotalSlideCount:8,
 nativeChartTargetApplication:'powerpoint',materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath});
await fs.copyFile(receiptPath,'reports/presentation_validation.json');
await fs.writeFile('presentation/slide_outline.json',JSON.stringify({main_slides:8,hidden_backup_slides:0,total:8,validation:report.generated_at},null,2));
console.log({finalPath:finalized.finalPath,slides:8});
