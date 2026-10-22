import {chromium} from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';
import fs from 'node:fs';
const auth=JSON.parse(fs.readFileSync('/tmp/micco-evaluation-browser/browser-auth.json','utf8'));
const browser=await chromium.launch({headless:true,executablePath:'/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});
const results=[];
try{
 for (const scenario of ['complete','truncated','explicit_error','http_503']) {
  const context=await browser.newContext(); await context.addInitScript(t=>localStorage.setItem('docvault_token',t),auth['Giám đốc'].token);
  const page=await context.newPage();let intercepted=0;
  await page.route('**/api/v1/rag/chat/*/stream',async route=>{
   intercepted++;
   const marker=`EVAL_${scenario.toUpperCase()}_ANSWER`;
   const token=`event: token\ndata: ${JSON.stringify({text:marker})}\n\n`;
   const end=scenario==='complete'?`event: complete\ndata: ${JSON.stringify({answer:marker,sources:[],related_entities:[]})}\n\n`:scenario==='explicit_error'?`event: error\ndata: ${JSON.stringify({message:'EVAL_CONTROLLED_ERROR'})}\n\n`:'';
   await route.fulfill({status:scenario==='http_503'?503:200,contentType:'text/event-stream',body:scenario==='http_503'?'EVAL_SERVICE_UNAVAILABLE':token+end});
  });
  await page.goto('http://127.0.0.1:18888/chat',{waitUntil:'networkidle'});
  const input=page.locator('textarea').first();await input.fill('Câu hỏi kiểm tra giao diện '+scenario);await input.press('Enter');
  await page.waitForTimeout(1000);
  const body=await page.locator('body').innerText();
  results.push({scenario,intercepted,markerShown:body.includes(`EVAL_${scenario.toUpperCase()}_ANSWER`),errorShown:body.includes('EVAL_CONTROLLED_ERROR')||body.includes('⚠️')||body.includes('Có lỗi xảy ra'),inputDisabled:await input.isDisabled(),tail:body.slice(-850),serverMutation:false});
  await context.close();
 }
}finally{await browser.close();fs.writeFileSync('evaluation/runs/20260929/browser-fault-results.json',JSON.stringify(results,null,2));}
console.log(JSON.stringify(results.map(({tail,...x})=>x)));
