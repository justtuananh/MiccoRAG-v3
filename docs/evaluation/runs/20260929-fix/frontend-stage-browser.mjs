import { chromium } from '/usr/lib/node_modules/openclaw/node_modules/playwright-core/index.mjs';
import { readFileSync, writeFileSync } from 'node:fs';

const auth = JSON.parse(readFileSync('/tmp/micco-stage-browser-auth.json', 'utf8'));
const base = 'http://127.0.0.1:15174';
const routes = ['/dashboard', '/documents', '/workspaces', '/processing-status', '/chat', '/expert', '/knowledge', '/admin', '/departments', '/approvals', '/graph-knowledge'];
const browser = await chromium.launch({ headless: true, executablePath: '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell' });
const report = { checked_at: new Date().toISOString(), base, routes: [], faults: [], ux: [] };

async function contextFor(role, options = {}) {
  const context = await browser.newContext(options);
  await context.addInitScript(token => localStorage.setItem('docvault_token', token), auth[role].token);
  return context;
}

try {
  for (const role of process.env.ONLY_FAULTS ? [] : Object.keys(auth)) {
    const context = await contextFor(role);
    const page = await context.newPage();
    for (const route of routes) {
      const apiErrors = [];
      const pageErrors = [];
      const onResponse = response => {
        if (response.url().includes('/api/') && response.status() >= 400) apiErrors.push({ path: new URL(response.url()).pathname, status: response.status() });
      };
      const onPageError = error => pageErrors.push(error.message);
      page.on('response', onResponse);
      page.on('pageerror', onPageError);
      const item = { role, route };
      try {
        const response = await page.goto(base + route, { waitUntil: 'domcontentloaded', timeout: 25000 });
        await page.waitForTimeout(600);
        const finalPath = new URL(page.url()).pathname;
        const adminOnly = ['/admin', '/departments', '/graph-knowledge'].includes(route);
        const privileged = route === '/approvals';
        const expected = (adminOnly && role !== 'Admin') || (privileged && role === 'Nhân viên') ? '/dashboard' : route;
        Object.assign(item, { http: response?.status(), finalPath, expected, routePass: finalPath === expected, mounted: (await page.locator('#root').innerText()).length > 20, apiErrors, pageErrors });
      } catch (error) {
        item.error = String(error);
      }
      report.routes.push(item);
      page.off('response', onResponse);
      page.off('pageerror', onPageError);
    }
    await context.close();
  }

  for (const scenario of ['complete', 'truncated', 'explicit_error', 'http_503']) {
    const context = await contextFor('Giám đốc');
    const page = await context.newPage();
    let streamPosts = 0;
    let fallbackPosts = 0;
    await page.route('**/api/v1/rag/chat/**', async route => {
      if (route.request().url().endsWith('/history')) return route.fulfill({ status: 200, contentType: 'application/json', body: '{"messages":[]}' });
      if (!route.request().url().endsWith('/stream')) {
        if (route.request().method() === 'POST') fallbackPosts++;
        return route.continue();
      }
      streamPosts++;
      const marker = `STAGE_${scenario.toUpperCase()}_ANSWER`;
      const token = `event: token\ndata: ${JSON.stringify({ text: marker })}\n\n`;
      const end = scenario === 'complete' ? `event: complete\ndata: ${JSON.stringify({ answer: marker, sources: [] })}\n\n`
        : scenario === 'explicit_error' ? 'event: error\ndata: {"message":"STAGE_CONTROLLED_ERROR"}\n\n' : '';
      await route.fulfill({ status: scenario === 'http_503' ? 503 : 200, contentType: 'text/event-stream', body: scenario === 'http_503' ? 'STAGE_SERVICE_UNAVAILABLE' : token + end });
    });
    await page.goto(base + '/chat', { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => {
      const input = document.querySelector('textarea');
      return input && !input.disabled;
    });
    await page.getByText('Chat với', { exact: false }).first().waitFor();
    const input = page.locator('textarea').first();
    await input.fill(`Câu hỏi kiểm tra ${scenario}`);
    await input.press('Enter');
    await page.waitForTimeout(1200);
    const body = await page.locator('body').innerText();
    report.faults.push({ scenario, streamPosts, fallbackPosts, answerShown: body.includes(`STAGE_${scenario.toUpperCase()}_ANSWER`), partialWarning: body.includes('có thể chưa đầy đủ'), errorShown: body.includes('STAGE_CONTROLLED_ERROR') || body.includes('STAGE_SERVICE_UNAVAILABLE'), inputEnabled: !(await input.isDisabled()), tail: body.slice(-450) });
    await context.close();
  }

  const mobileContext = await contextFor('Nhân viên', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto(base + '/documents', { waitUntil: 'domcontentloaded' });
  await mobilePage.waitForTimeout(1000);
  report.ux.push({ case: 'mobile_documents', viewportWidth: 390,
    pageWidth: await mobilePage.evaluate(() => document.documentElement.scrollWidth),
    searchVisible: await mobilePage.getByPlaceholder('Tìm kiếm...').isVisible().catch(() => false),
    rootTextLength: (await mobilePage.locator('#root').innerText()).length });
  await mobileContext.close();

  const desktopContext = await contextFor('Admin');
  const desktopPage = await desktopContext.newPage();
  await desktopPage.goto(base + '/documents', { waitUntil: 'domcontentloaded' });
  await desktopPage.waitForTimeout(1000);
  const search = desktopPage.getByPlaceholder('Tìm kiếm...');
  const searchVisible = await search.isVisible();
  if (searchVisible) {
    await search.focus();
    await search.fill('___KHONG_TON_TAI___');
  }
  report.ux.push({ case: 'desktop_document_search', searchVisible,
    focused: await search.evaluate(element => element === document.activeElement).catch(() => false),
    emptyVisible: (await desktopPage.locator('body').innerText()).includes('Không tìm thấy') });
  await desktopPage.keyboard.press('Tab');
  report.ux.push({ case: 'keyboard_tab', focusedTag: await desktopPage.evaluate(() => document.activeElement?.tagName), focusedName: await desktopPage.evaluate(() => document.activeElement?.getAttribute('aria-label') || document.activeElement?.getAttribute('title') || '') });
  const themeButton = desktopPage.getByRole('button', { name: 'Toggle dark mode' });
  const beforeDark = await desktopPage.locator('html').evaluate(el => el.classList.contains('dark'));
  await themeButton.click();
  const afterDark = await desktopPage.locator('html').evaluate(el => el.classList.contains('dark'));
  report.ux.push({ case: 'theme', beforeDark, afterDark, toggled: beforeDark !== afterDark });
  await desktopContext.close();
} finally {
  await browser.close();
  writeFileSync('/root/MiccoRAG/evaluation/runs/20260929-fix/' + (process.env.ONLY_FAULTS ? 'frontend-stage-faults-mobile.json' : 'frontend-stage-browser.json'), JSON.stringify(report, null, 2));
}

console.log(JSON.stringify({ routes: report.routes.length, routeFailures: report.routes.filter(r => r.routePass === false || r.error).length, pageErrors: report.routes.filter(r => r.pageErrors?.length).length, apiErrors: report.routes.filter(r => r.apiErrors?.length).length, faults: report.faults, ux: report.ux }));
