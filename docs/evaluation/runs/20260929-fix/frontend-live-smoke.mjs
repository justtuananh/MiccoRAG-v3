import { chromium } from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const auth = JSON.parse(readFileSync('/tmp/micco-live-browser-auth.json', 'utf8'));
const base = 'http://127.0.0.1:18888';
const routes = ['/workspaces', '/documents', '/chat', '/admin'];
const browser = await chromium.launch({ headless: true, executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell' });
const results = [];
let mobile;
try {
  for (const role of ['Admin', 'Giám đốc', 'Phó giám đốc', 'Trưởng phòng', 'Nhân viên']) {
    const context = await browser.newContext();
    await context.addInitScript(token => localStorage.setItem('docvault_token', token), auth[role].token);
    const page = await context.newPage();
    for (const route of routes) {
      const pageErrors = [];
      const apiErrors = [];
      const onPageError = error => pageErrors.push(error.message);
      const onResponse = response => {
        if (response.url().includes('/api/') && response.status() >= 400)
          apiErrors.push({ path: new URL(response.url()).pathname, status: response.status() });
      };
      page.on('pageerror', onPageError);
      page.on('response', onResponse);
      const item = { role, route };
      try {
        const response = await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(700);
        const finalPath = new URL(page.url()).pathname;
        const expectedPath = route === '/admin' && role !== 'Admin' ? '/dashboard' : route;
        const rootTextLength = (await page.locator('#root').innerText()).length;
        Object.assign(item, { http: response?.status(), finalPath, expectedPath, routePass: finalPath === expectedPath, mounted: rootTextLength > 20, pageErrors, apiErrors });
      } catch (error) {
        item.error = String(error);
      }
      results.push(item);
      page.off('pageerror', onPageError);
      page.off('response', onResponse);
    }
    await context.close();
  }

  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await context.addInitScript(token => localStorage.setItem('docvault_token', token), auth['Nhân viên'].token);
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(base + '/documents', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(700);
  mobile = {
    viewportWidth: 390,
    pageWidth: await page.evaluate(() => document.documentElement.scrollWidth),
    searchVisible: await page.getByRole('textbox', { name: 'Tìm kiếm tài liệu' }).isVisible(),
    pageErrors,
  };
  await context.close();
} finally {
  await browser.close();
}

const report = {
  checked_at: new Date().toISOString(),
  gateway: base,
  read_only: true,
  results,
  mobile,
  passed: results.filter(item => item.http === 200 && item.routePass && item.mounted && !item.pageErrors.length && !item.apiErrors.length).length,
  total: results.length,
};
writeFileSync('/root/MiccoRAG/evaluation/runs/20260929-fix/frontend-live-smoke.json', JSON.stringify(report, null, 2));
console.log(JSON.stringify({ passed: report.passed, total: report.total, failures: report.results.filter(item => item.http !== 200 || !item.routePass || !item.mounted || item.pageErrors?.length || item.apiErrors?.length || item.error), mobile }));
if (report.passed !== report.total || mobile.pageWidth > 390 || !mobile.searchVisible || mobile.pageErrors.length) process.exitCode = 1;
