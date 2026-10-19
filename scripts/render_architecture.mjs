import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const rt='C:/Users/sidda/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {chromium}=await import(pathToFileURL(rt+'/playwright/index.mjs').href);
const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const page=await browser.newPage({viewport:{width:2200,height:1800},deviceScaleFactor:2});
await page.setContent('<html><body style="margin:40px;background:#fff"><div id="diagram"></div></body></html>');
await page.addScriptTag({path:'build/diagram/node_modules/mermaid/dist/mermaid.min.js'});
const source=await fs.readFile('docs/architecture.mmd','utf8');
const svg=await page.evaluate(async source=>{
  mermaid.initialize({startOnLoad:false,theme:'base',themeVariables:{fontFamily:'Arial',fontSize:'20px',primaryColor:'#E8F0F6',primaryTextColor:'#0B2545',primaryBorderColor:'#087F8C',lineColor:'#45627B'},flowchart:{htmlLabels:false,curve:'linear',nodeSpacing:32,rankSpacing:55,useMaxWidth:false}});
  const {svg}=await mermaid.render('pgarchitecture',source);document.getElementById('diagram').innerHTML=svg;return svg;
},source);
await fs.writeFile('docs/architecture.svg',svg);
await page.locator('#diagram svg').screenshot({path:'docs/architecture.png'});
console.log(await page.locator('#diagram svg').boundingBox());
await browser.close();
