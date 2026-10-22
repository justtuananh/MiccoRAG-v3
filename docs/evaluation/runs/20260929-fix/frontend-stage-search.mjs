import { chromium } from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const auth = JSON.parse(readFileSync('/tmp/micco-stage-browser-auth.json', 'utf8'));
const browser = await chromium.launch({ headless: true, executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell' });
const context = await browser.newContext();
await context.addInitScript(token => localStorage.setItem('docvault_token', token), auth.Admin.token);
const page = await context.newPage();
const documentRequests = [];
page.on('request', request => {
  const path = new URL(request.url());
  if (path.pathname === '/api/documents') documentRequests.push(path.search);
});
try {
  await page.goto('http://127.0.0.1:15174/documents', { waitUntil: 'domcontentloaded' });
  await page.getByPlaceholder('Tìm kiếm...').fill('quy trinh');
  await page.waitForTimeout(400);
  const rowCount = await page.locator('tbody tr').count();
  const summary = await page.locator('body').innerText();
  const result = { query: 'quy trinh', matchingRows: rowCount, summaryShowsThree: summary.includes('trong số 3 tài liệu'), serverSearchParameterSent: documentRequests.some(query => query.includes('search=')), pass: rowCount === 3 && !documentRequests.some(query => query.includes('search=')) };
  writeFileSync('/root/MiccoRAG/evaluation/runs/20260929-fix/frontend-stage-search.json', JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
  if (!result.pass) process.exitCode = 1;
} finally {
  await browser.close();
}
