import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});
const results=[];
async function test(name,fn){try{await fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,error:String(e)});}}
for (const role of ['Admin','Trưởng phòng']) {
 const ctx=await browser.newContext({viewport:{width:390,height:844}});const posts=[];
 await ctx.addInitScript(()=>localStorage.setItem('docvault_token','fixture'));
 await ctx.route('**/api/**',async route=>{
  const r=route.request(),path=new URL(r.url()).pathname;let body=[];
  if(path==='/api/auth/me')body={id:1,name:'Fixture',role,department_id:1};
  if(path==='/api/approvals/count')body={count:2};
  if(path==='/api/approvals/pending')body={documents:[{id:1,name:'Tài liệu cần duyệt '+ 'Tên dài '.repeat(35),approval_status:'pending',visibility:'public',effective_from:'2026-01-01'}],knowledge:[{id:2,title:'Tri thức cần duyệt',approval_status:'pending_dept',visibility:'public',effective_from:'2026-01-01'}]};
  if(r.method()==='POST'){posts.push({path,body:r.postDataJSON()});body={processing_started:false};}
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(body)});
 });
 const p=await ctx.newPage();await p.goto('http://127.0.0.1:15174/approvals');await p.getByRole('button',{name:'Phê duyệt',exact:true}).first().waitFor();
 await test(role+' approval requires dates and Admin reason',async()=>{
  await p.getByRole('button',{name:'Phê duyệt',exact:true}).first().click();const modal=p.getByRole('dialog',{name:'Xác nhận ngày hiệu lực'});await modal.waitFor();
  const submit=modal.getByRole('button',{name:'Phê duyệt',exact:true});
  await modal.getByLabel('Ngày hiệu lực *',{exact:true}).fill('');if(!await submit.isDisabled())throw Error('Missing date accepted');
  await modal.getByLabel('Ngày hiệu lực *',{exact:true}).fill('2026-01-01');
  if(role==='Admin'){if(!await submit.isDisabled())throw Error('Missing reason accepted');await modal.getByLabel('Lý do xử lý thay cấp duyệt *').fill('Kiểm thử thay người duyệt');}
  await modal.getByLabel('Ngày hết hiệu lực (nếu có)').fill('2025-12-31');if(!await submit.isDisabled())throw Error('Invalid interval accepted');
  await modal.getByLabel('Ngày hết hiệu lực (nếu có)').fill('2026-12-31');
  for(let i=0;i<12;i++){await p.keyboard.press('Tab');if(!await modal.evaluate(el=>el.contains(document.activeElement)))throw Error('Focus escaped modal');}
  await submit.click();await modal.waitFor({state:'hidden'});
  const sent=posts.at(-1);if(sent.body.effective_from!=='2026-01-01'||(role==='Admin'&&!sent.body.reason))throw Error('Incorrect approval payload');
 });
 for(const tab of ['Tài liệu','Tri thức'])await test(role+' rejects '+tab+' only with a reason',async()=>{
  await p.getByRole('button',{name:new RegExp('^'+tab)}).click();await p.getByRole('button',{name:'Từ chối',exact:true}).first().click();const modal=p.getByRole('dialog',{name:'Từ chối nội dung'});await modal.waitFor();const submit=modal.getByRole('button',{name:'Từ chối',exact:true});
  if(!await submit.isDisabled())throw Error('Empty rejection accepted');await modal.locator('textarea').fill('Cần bổ sung nguồn');await submit.click();await modal.waitFor({state:'hidden'});
  if(!JSON.stringify(posts.at(-1).body).includes('Cần bổ sung nguồn'))throw Error('Reason missing');
 });
 await test(role+' long title fits mobile',async()=>{if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error('Horizontal overflow');});
 await ctx.close();
}
await browser.close();const report={scope:'Chromium forms at 390px with deterministic API fixtures; backend approval semantics tested separately.',results};writeFileSync('/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-approval-forms.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(results.some(x=>!x.pass))process.exitCode=1;
