import { writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:15174';
const browser = await chromium.launch({ headless: true, executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell' });
const context = await browser.newContext();
const checks = [];
const pageErrors = [];
let aCountReads = 0;
let releaseOldResponse;
let releaseBResponse;
let notifyOldRequest;
let notifyBRequest;
const oldRequestStarted = new Promise(resolve => { notifyOldRequest = resolve; });
const bRequestStarted = new Promise(resolve => { notifyBRequest = resolve; });

try {
  await context.addInitScript(() => localStorage.setItem('docvault_token', 'token-A'));
  await context.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const bearer = request.headers().authorization || '';
    const reply = data => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(data) });
    if (path === '/api/auth/me') {
      const id = bearer.endsWith('token-B') ? 2 : bearer.endsWith('token-C') ? 3 : 1;
      return reply({ id, name: `User ${id}`, role: 'Admin', is_active: true });
    }
    if (path === '/api/approvals/count') {
      if (bearer.endsWith('token-A')) {
        aCountReads += 1;
        if (aCountReads === 1) return reply({ count: 3, last_requester: 'A requester' });
        notifyOldRequest();
        await new Promise(resolve => { releaseOldResponse = resolve; });
        return reply({ count: 9, last_requester: 'Old A requester' });
      }
      if (bearer.endsWith('token-B')) {
        notifyBRequest();
        await new Promise(resolve => { releaseBResponse = resolve; });
        return reply({ count: 4, last_requester: 'B requester' });
      }
      return reply({ count: 6, last_requester: 'C requester' });
    }
    if (path === '/api/documents') return reply([]);
    if (path === '/api/dashboard/stats') return reply({});
    return reply([]);
  });

  const page = await context.newPage();
  page.on('pageerror', error => pageErrors.push(error.name || 'Error'));
  const badge = value => page.locator('a[href="/approvals"]').filter({ hasText: 'Phê duyệt' }).getByText(String(value), { exact: true });
  const toast = page.getByText('Yêu cầu phê duyệt mới!', { exact: true });
  await page.goto(`${base}/documents`, { waitUntil: 'domcontentloaded' });
  await badge(3).waitFor();
  checks.push({ name: 'first privileged user count shown', pass: true });

  // The 15-second poll starts while A is active; its response remains in flight.
  await Promise.race([oldRequestStarted, new Promise((_, reject) => setTimeout(() => reject(new Error('poll timeout')), 22000))]);
  await page.evaluate(() => {
    localStorage.setItem('docvault_token', 'token-B');
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
  });
  await bRequestStarted;
  checks.push({ name: 'account switch clears old count while new result waits', pass: await badge(3).count() === 0 && await toast.count() === 0 });
  releaseBResponse();
  await badge(4).waitFor();

  releaseOldResponse();
  await page.waitForTimeout(300);
  checks.push({ name: 'late A response cannot overwrite B count or requester', pass: await badge(4).count() > 0 && await badge(9).count() === 0 && await toast.count() === 0 });

  await page.getByRole('button', { name: 'Menu tài khoản' }).click();
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await page.waitForURL('**/login');
  checks.push({ name: 'logout removes switched account token', pass: await page.evaluate(() => !localStorage.getItem('docvault_token')) });

  // Reuse the mounted provider so stale approval state would create a toast.
  await page.evaluate(() => {
    localStorage.setItem('docvault_token', 'token-C');
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
  });
  await badge(6).waitFor();
  checks.push({ name: 'new session starts without old approval toast', pass: await toast.count() === 0 });
  checks.push({ name: 'no runtime page errors', pass: pageErrors.length === 0 });
} finally {
  if (releaseOldResponse) releaseOldResponse();
  if (releaseBResponse) releaseBResponse();
  await context.close();
  await browser.close();
}

const report = { scope: 'Browser fixture with two account switches and delayed approval count; no production API.', checks, page_error_kinds: pageErrors, pass: checks.every(check => check.pass) };
writeFileSync('/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-approval-session-isolation.json', JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report));
if (!report.pass) process.exitCode = 1;
