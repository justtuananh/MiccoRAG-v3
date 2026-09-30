import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});const rows=[];
const base='http://127.0.0.1:15174';
const doc={id:1,name:'Tài liệu thử '+ 'Tên dài '.repeat(15)+'.txt',original_filename:'fixture.txt',type:'TXT',file_type:'txt',status:'indexed',approval_status:'approved',owner:'Fixture',uploader_id:1,workspace_id:1,effective_from:'2026-01-01',size:100,tags:[]};
async function check(name,fn){try{await fn();rows.push({case:name,pass:true});}catch(e){rows.push({case:name,pass:false,error:String(e)});}writeFileSync('/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-modal-keyboard.json',JSON.stringify({scope:'Keyboard, Escape, dialog semantics and viewport checks with deterministic API fixtures; not a full WCAG certification.',rows},null,2));console.log(name,rows.at(-1).pass);}
const ctx=await browser.newContext({viewport:{width:390,height:844}});await ctx.addInitScript(()=>localStorage.setItem('docvault_token','fixture'));
await ctx.route('**/api/**',route=>{const path=new URL(route.request().url()).pathname;let body=[];
 if(path==='/api/auth/me')body={id:1,name:'Fixture',role:'Admin',email:'fixture@example.invalid'};
 if(path==='/api/approvals/count')body={count:0};
 if(path==='/api/documents')body=[doc];
 if(path==='/api/documents/1')body=doc;
 if(path.endsWith('/preview'))return route.fulfill({status:200,contentType:'text/plain',body:'Synthetic document'});
 if(path==='/api/v1/workspaces'||path==='/api/v1/workspaces/summary')body=[{id:1,name:'Fixture workspace',visibility:'private',owner_id:1,document_count:1,search_mode:'vector_only'}];
 if(path==='/api/auth/departments'||path==='/api/admin/departments')body=[{id:1,name:'Fixture department',kind:'standard',user_count:0}];
 if(path.includes('/history'))body={messages:[]};
 if(path.includes('system-prompt'))body={prompt:'Fixture prompt'};
 return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(body)});
});
const page=await ctx.newPage();page.setDefaultTimeout(6000);
async function verify(label){const modal=page.getByRole('dialog',{name:label,exact:true});await modal.waitFor();
 for(let i=0;i<18;i++){await page.keyboard.press(i%4===0?'Shift+Tab':'Tab');if(!await modal.evaluate(el=>el.contains(document.activeElement)))throw Error('Focus escaped');}
 const bounds=await modal.boundingBox();if(bounds.x< -1||bounds.width>391)throw Error('Dialog exceeds viewport');
 await page.keyboard.press('Escape');await modal.waitFor({state:'hidden'});
}
await check('document upload dialog',async()=>{await page.goto(base+'/documents');await page.getByRole('button',{name:'Tải lên tài liệu',exact:true}).click();await verify('Tải lên tài liệu');});
await check('document row deletion dialog',async()=>{await page.goto(base+'/documents');await page.locator('button:has(svg.lucide-ellipsis),button:has(svg.lucide-more-horizontal)').first().click();await page.getByRole('button',{name:'Xóa',exact:true}).first().click();await verify('Xóa tài liệu');});
await check('document bulk deletion dialog',async()=>{await page.goto(base+'/documents');await page.getByTitle('Chọn tất cả',{exact:true}).click();await page.getByRole('button',{name:/Xóa \d+ mục/}).click();await verify('Xóa các tài liệu đã chọn');});
for(const [button,label] of [['Chia sẻ','Chia sẻ tài liệu'],['Xóa tài liệu','Xóa tài liệu'],['Phiên bản mới','Tải lên phiên bản mới']])await check('document detail '+label,async()=>{await page.goto(base+'/documents/1');await page.getByRole('button',{name:button,exact:true}).click();await verify(label);});
await check('workspace create dialog',async()=>{await page.goto(base+'/workspaces');await page.getByRole('button',{name:'Tạo mới',exact:true}).first().click();await verify('Tạo hoặc sửa kho tri thức');});
await check('department dialog',async()=>{await page.goto(base+'/departments');await page.getByRole('button',{name:/Thêm phòng ban/}).click();await verify('Thông tin phòng ban');});
await check('chat prompt dialog',async()=>{await page.goto(base+'/chat');await page.getByRole('button',{name:'Chỉnh sửa System Prompt',exact:true}).click();await verify('Cấu hình hướng dẫn trả lời');});
await check('workspace deletion dialog',async()=>{await page.goto(base+'/workspaces');await page.getByRole('button',{name:'Thao tác kho tri thức'}).first().click();await page.getByRole('button',{name:'Xóa',exact:true}).click();await verify('Xóa kho tri thức');});
await check('mobile navigation dialog',async()=>{await page.goto(base+'/documents');await page.getByRole('button',{name:'Mở menu điều hướng'}).click();await verify('Điều hướng');});
await check('profile dialog',async()=>{await page.goto(base+'/documents');await page.getByRole('button',{name:'Menu tài khoản'}).click();await page.getByRole('button',{name:'Thông tin cá nhân'}).click();await verify('Cập nhật thông tin cá nhân');});
// Isolated render of shared modal components, preserving their actual forms and focus behavior.
await ctx.route('**/__modal_fixture__',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><html><head></head><body><main id="fixture"></main></body></html>'}));
for(const [file,exp,props,label] of [
 ['components/knowledge/KnowledgeForm.jsx','default',{},'Soạn tri thức'],
 ['components/admin/UserModal.jsx','default',{open:true},'Thông tin tài khoản'],
 ['components/admin/LogsTable.jsx','LogDetailModal',{log:{id:1,question:'Long question '.repeat(40),answer:'Synthetic answer',method:'vector_only',response_time:1}},'Chi tiết nhật ký'],
 ['components/shared/ConfirmDeleteModal.jsx','default',{title:'Xóa thử',description:'Khôi phục trong 30 ngày'},'Xác nhận xóa'],
])await check(label,async()=>{await page.goto(base+'/__modal_fixture__');await page.evaluate(async({file,exp,props})=>{
 const Refresh=(await import('/@react-refresh')).default;Refresh.injectIntoGlobalHook(window);window.$RefreshReg$=()=>{};window.$RefreshSig$=()=>type=>type;window.__vite_plugin_react_preamble_installed__=true;await import('/src/index.css');const React=(await import('/node_modules/.vite/deps/react.js')).default;const ReactDOM=await import('/node_modules/.vite/deps/react-dom_client.js');const {createRoot}=ReactDOM.default || ReactDOM;const Component=(await import('/src/'+file))[exp];const root=createRoot(document.getElementById('fixture'));root.render(React.createElement(Component,{...props,onClose:()=>root.unmount(),onSave:async()=>{},onConfirm:async()=>{}}));
 },{file,exp,props});await verify(label);});
await browser.close();if(rows.some(r=>!r.pass))process.exitCode=1;
