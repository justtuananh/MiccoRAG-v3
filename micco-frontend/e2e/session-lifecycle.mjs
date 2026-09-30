import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});
const base='http://127.0.0.1:15174';const results=[];
async function run(name,fn){try{await fn();results.push({name,pass:true});}catch(e){results.push({name,pass:false,error:String(e)});}}
const ctx=await browser.newContext();
await ctx.route('**/api/**',route=>{
 const p=new URL(route.request().url()).pathname;
 if(!route.request().headers().authorization?.includes('fixture-token'))return route.fulfill({status:401,contentType:'application/json',body:'{"detail":"unauthorized"}'});
 let data=[];
 if(p==='/api/auth/me')data={id:1,name:'Fixture',role:'Nhân viên'};
 if(p==='/api/dashboard/stats')data={total_documents:0,total_knowledge:0,total_storage:'0 KB',recent_documents:[],department_stats:[],activity_chart:[]};
 return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
});
const page=await ctx.newPage();await page.goto(base+'/login');
const login=async()=>{await page.evaluate(()=>localStorage.setItem('docvault_token','fixture-token'));await page.goto(base+'/documents');await page.waitForURL('**/documents');await page.getByRole('textbox',{name:'Tìm kiếm tài liệu'}).waitFor();};
await run('reload restores authenticated session',async()=>{await login();await page.reload({waitUntil:'domcontentloaded'});await page.getByRole('textbox',{name:'Tìm kiếm tài liệu'}).waitFor();});
await run('back navigation preserves authorized route',async()=>{await page.goto(base+'/knowledge');await page.goBack({waitUntil:'domcontentloaded'});await page.getByRole('textbox',{name:'Tìm kiếm tài liệu'}).waitFor();});
await run('logout in another tab clears current session',async()=>{const second=await ctx.newPage();await second.goto(base+'/documents');await second.evaluate(()=>localStorage.removeItem('docvault_token'));await page.waitForURL('**/login');await second.close();});
await run('restored page with missing token redirects',async()=>{await login();await page.evaluate(()=>{localStorage.removeItem('docvault_token');window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));});await page.waitForURL('**/login');});
await run('reload after token loss stays logged out',async()=>{await page.reload({waitUntil:'domcontentloaded'});if(new URL(page.url()).pathname!='/login')throw Error('Protected route persisted');});
await run('late auth failure does not erase a newer token',async()=>{
 await login();let finish;const pending=new Promise(resolve=>{finish=resolve;});let entered;const started=new Promise(resolve=>{entered=resolve;});
 await page.route('**/api/auth/me',async route=>{entered();await pending;await route.fulfill({status:401,contentType:'application/json',body:'{}'});},{times:1});
 await page.evaluate(()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})));await started;
 await page.evaluate(()=>localStorage.setItem('docvault_token','replacement-token'));finish();
 await page.waitForTimeout(150);if(await page.evaluate(()=>localStorage.getItem('docvault_token'))!=='replacement-token')throw Error('New token cleared by old failure');
});
await run('late API failure does not revoke a newer session',async()=>{
 await login();let finish;const pending=new Promise(resolve=>{finish=resolve;});let entered;const started=new Promise(resolve=>{entered=resolve;});
 await page.route('**/api/race',async route=>{entered();await pending;await route.fulfill({status:401,contentType:'application/json',body:'{}'});},{times:1});
 await page.evaluate(async()=>{const {ragFetch}=await import('/src/utils/api.js');window.raceRequest=ragFetch('/api/race');});await started;
 await page.evaluate(()=>localStorage.setItem('docvault_token','replacement-token'));finish();await page.evaluate(()=>window.raceRequest.then(()=>null));
 if(await page.evaluate(()=>localStorage.getItem('docvault_token'))!=='replacement-token')throw Error('New token cleared by old API failure');
});
await ctx.close();await browser.close();const report={scope:'Browser with deterministic authenticated API fixtures; pageshow restoration simulated, native bfcache eviction not claimed.',results};writeFileSync('/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-session.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));if(results.some(x=>!x.pass))process.exitCode=1;
