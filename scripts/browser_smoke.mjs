import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const modules=process.env.RUNTIME_NODE_MODULES;
if(!modules)throw new Error('Set RUNTIME_NODE_MODULES to the bundled Node package directory.');
const {chromium}=await import(pathToFileURL(path.join(modules,'playwright/index.mjs')).href);
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1100},deviceScaleFactor:1});
const consoleErrors=[];page.on('pageerror',error=>consoleErrors.push(error.message));
const captures=[];
async function shot(name){
 await page.locator('[data-testid="stMain"]').evaluate(el=>{el.scrollTop=0;});
 await page.locator('[data-testid="stMain"]').getByRole('heading').first().scrollIntoViewIfNeeded();
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 await page.screenshot({path:'docs/screenshots/'+name});captures.push(name);
}
async function select(label,value){
 const input=page.getByRole('combobox',{name:new RegExp('\\. '+label+'$')});
 await input.fill(value);await page.getByRole('option',{name:new RegExp('^'+value+'(?: ·|$)')}).click();
}
async function openLifecycle(){
 const label=page.getByText('Invoice lifecycle and ledger allocation',{exact:true});
 const details=label.locator('xpath=ancestor::details[1]');
 if(!await details.evaluate(el=>el.open))await label.click();
}
await fs.mkdir('docs/screenshots',{recursive:true});
await page.goto(process.env.PROCUREGUARD_URL||'http://127.0.0.1:8513');
await page.getByRole('button',{name:'Audit loaded invoices',exact:true}).click();
await page.getByText('Review queue',{exact:true}).waitFor();
await shot('01_command_center.png');
await page.getByRole('button',{name:'Open PG103',exact:true}).click();
await page.getByRole('button',{name:'Run investigation',exact:true}).click();
await page.getByRole('button',{name:'Download complete evidence packet',exact:true}).waitFor();
await shot('02_resolved_case.png');
await page.locator('[data-testid="stHorizontalBlock"]').filter({has:page.getByText('Before investigation',{exact:true})}).last().screenshot({path:'build/ui_decision_crop.png'});
await page.getByRole('tab',{name:'Agent trace',exact:true}).click();
await page.getByText('amendment_lookup',{exact:true}).waitFor();
await page.setViewportSize({width:1600,height:1600});
await shot('03_adaptive_plan.png');
await page.setViewportSize({width:1600,height:1100});
await page.getByRole('tab',{name:'Evidence provenance',exact:true}).click();
await page.getByText('Verified source record and exact values',{exact:true}).waitFor();
await shot('04_provenance.png');
await page.reload();
await page.getByText('Investigate a case',{exact:true}).first().click();
await page.getByText(/Reopened saved investigation revision/).waitFor();
await page.getByRole('combobox',{name:'Selected PG103 · Two gaps, one case. Case',exact:true}).waitFor();
await shot('09_recovered_case.png');
await select('Case','PG105B');
await openLifecycle();
await select('New lifecycle classification','rejected');
await page.getByLabel('Lifecycle rationale',{exact:true}).fill('Reject the second fictional submission after checking the capacity evidence.');
await page.getByRole('button',{name:'Record lifecycle classification',exact:true}).click();
await page.getByText('Current classification: rejected',{exact:false}).waitFor();
await shot('07_lifecycle.png');
await select('Case','PG105');
await page.getByRole('button',{name:'Run investigation',exact:true}).click();
await page.getByRole('button',{name:'Download complete evidence packet',exact:true}).waitFor();
await page.getByText('Required controls passed. A human review is still required.',{exact:true}).waitFor();
await shot('08_revalidated_allocation.png');
// Explicitly restore the active commitment for the next classroom rehearsal.
await select('Case','PG105B');
await openLifecycle();
await page.getByLabel('Lifecycle rationale',{exact:true}).fill('Resubmit the fictional record to restore the starting demo branch.');
await page.getByRole('button',{name:'Record lifecycle classification',exact:true}).click();
await page.getByText('Current classification: submitted',{exact:false}).waitFor();
await page.getByText('Evidence & controls',{exact:true}).first().click();
await page.getByText('Trust boundaries',{exact:true}).waitFor();
await shot('05_controls.png');
await page.getByText('Validation lab',{exact:true}).first().click();
await page.getByText('Rules-only baseline versus evidence resolution',{exact:true}).waitFor();
await page.getByText('Real local model demonstration',{exact:true}).waitFor();
await shot('06_validation.png');
await page.getByText('Frozen challenge and ablation',{exact:true}).scrollIntoViewIfNeeded();
await page.screenshot({path:'docs/screenshots/10_challenge_comparison.png'});captures.push('10_challenge_comparison.png');
const report={captured_at:new Date().toISOString(),screenshots:captures.length,captures,recovery_verified:true,lifecycle_transition_verified:true,streamlit_exceptions:await page.locator('[data-testid="stException"]').count(),consoleErrors};
await fs.writeFile('reports/browser_smoke.json',JSON.stringify(report,null,2));
await browser.close();console.log(report);
if(report.streamlit_exceptions||consoleErrors.length)process.exitCode=1;
