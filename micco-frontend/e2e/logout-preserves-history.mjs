import assert from 'node:assert/strict';
import { writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:15174';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
});
const checks = [];
const context = await browser.newContext();
const history = { messages: [
  { id: 'u1', role: 'user', content: 'Câu hỏi đã lưu' },
  { id: 'a1', role: 'assistant', content: 'Câu trả lời đã lưu' },
] };
let historyReads = 0;
let deleteCalls = 0;
const pageErrors = [];

try {
  await context.addInitScript(() => {
    if (!sessionStorage.getItem('fixture-logged-out')) localStorage.setItem('docvault_token', 'fixture-token');
  });
  await context.route('**/api/**', route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === 'DELETE') deleteCalls += 1;
    const json = data => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    if (path === '/api/auth/me') return json({ id: 1, name: 'Fixture', role: 'Nhân viên' });
    if (path === '/api/approvals/count') return json({ count: 0 });
    if (path === '/api/v1/workspaces') return json([{ id: 1, name: 'KB thử', document_count: 1, indexed_count: 1 }]);
    if (path === '/api/v1/workspaces/1/suggested-questions') return json([]);
    if (path === '/api/v1/rag/chat/1/history') { historyReads += 1; return json(history); }
    return json([]);
  });

  const page = await context.newPage();
  page.on('pageerror', error => pageErrors.push(error.name || 'Error'));
  await page.goto(`${base}/chat`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Câu hỏi đã lưu', { exact: true }).waitFor();
  await page.getByText('Câu trả lời đã lưu', { exact: true }).waitFor();
  checks.push({ name: 'persisted history visible before logout', pass: true });

  await page.getByRole('button', { name: 'Menu tài khoản' }).click();
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await page.waitForURL('**/login');
  const tokenCleared = await page.evaluate(() => !localStorage.getItem('docvault_token'));
  checks.push({ name: 'real logout button clears client token', pass: tokenCleared });
  checks.push({ name: 'logout sends no history DELETE', pass: deleteCalls === 0 });

  // Re-establish the same synthetic session; password login is covered elsewhere.
  await page.evaluate(() => {
    sessionStorage.setItem('fixture-logged-out', '1');
    localStorage.setItem('docvault_token', 'fixture-token');
  });
  await page.goto(`${base}/chat`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Câu hỏi đã lưu', { exact: true }).waitFor();
  await page.getByText('Câu trả lời đã lưu', { exact: true }).waitFor();
  checks.push({ name: 'server history remains after signing in again', pass: historyReads >= 2 && deleteCalls === 0 });
  checks.push({ name: 'no page errors', pass: pageErrors.length === 0 });
} finally {
  await context.close();
  await browser.close();
}

assert.ok(checks.every(check => check.pass), JSON.stringify(checks));
const report = { scope: 'Browser fixture with persisted server history; real logout button, synthetic JWT restore, no password-login claim.', checks, delete_calls: deleteCalls, history_reads: historyReads, page_error_kinds: pageErrors };
writeFileSync('/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-logout-history.json', JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
