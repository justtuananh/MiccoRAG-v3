import { chromium } from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';
import fs from 'node:fs';
const dir='/tmp/micco-evaluation-browser';
const auth=JSON.parse(fs.readFileSync(`${dir}/browser-auth.json`,'utf8'));
const results=[];
const browser=await chromium.launch({headless:true,executablePath:'/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});
try {
 for (const [role,user] of Object.entries(auth)) {
  const context=await browser.newContext();
  await context.addInitScript(token=>localStorage.setItem('docvault_token',token),user.token);
  const page=await context.newPage();
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const routes=['/dashboard','/documents','/workspaces','/processing-status','/chat','/expert','/knowledge','/admin','/departments','/approvals','/graph-knowledge'];
  for(const route of routes){
   const network=[];const fn=r=>{if(r.url().includes('/api/')&&r.status()>=400)network.push({path:new URL(r.url()).pathname,status:r.status()});};page.on('response',fn);
   let result={role,route};
   try{
    const r=await page.goto('http://127.0.0.1:18888'+route,{waitUntil:'networkidle',timeout:25000});
    const finalPath=new URL(page.url()).pathname;
    const expectedPath=(route==='/graph-knowledge'&&role!=='Admin')||(['/admin','/departments','/approvals'].includes(route)&&role==='Nhân viên')?'/dashboard':route;
    const root=await page.locator('#root').innerText();
    result={...result,http:r.status(),finalPath,expectedPath,mounted:root.length>20,expectedRoute:finalPath===expectedPath,apiErrors:network,pageErrors:[...errors]};
   }catch(e){result.error=e.message;}
   results.push(result);page.off('response',fn);
   fs.writeFileSync(`${dir}/browser-results.json`,JSON.stringify(results,null,2));
  }
  await context.close();
 }
 // Invalid token path: independent session, do not touch existing users.
 const c=await browser.newContext();await c.addInitScript(()=>localStorage.setItem('docvault_token','invalid-evaluation-token'));
 const p=await c.newPage();await p.goto('http://127.0.0.1:18888/documents',{waitUntil:'networkidle'});
 results.push({case:'invalid_token',finalPath:new URL(p.url()).pathname,tokenCleared:await p.evaluate(()=>!localStorage.getItem('docvault_token'))});
 await c.close();
}finally{await browser.close();fs.writeFileSync(`${dir}/browser-results.json`,JSON.stringify(results,null,2));}
console.log(JSON.stringify({executed:results.length,routeFailures:results.filter(x=>x.error||x.expectedRoute===false).length,apiErrors:results.filter(x=>x.apiErrors?.length).map(x=>({role:x.role,route:x.route,errors:x.apiErrors})),invalidToken:results.at(-1)}));
