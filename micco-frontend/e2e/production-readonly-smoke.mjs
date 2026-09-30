import { readFileSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

// Run only against the deployed gateway after receiving a short-lived token file.
// The token, document metadata, response bodies, and request headers are never logged.
const base = process.env.PROD_SMOKE_BASE || 'http://127.0.0.1:18888';
const tokenFile = process.env.PROD_SMOKE_TOKEN_FILE;
const output = process.env.PROD_SMOKE_OUTPUT || '/root/MiccoRAG/evaluation/runs/20260930-remediation/frontend-production-readonly-smoke.json';
const preferredDocId = process.env.PROD_SMOKE_DOC_ID;
if (!tokenFile) throw new Error('PROD_SMOKE_TOKEN_FILE is required');
const token = readFileSync(tokenFile, 'utf8').trim();
if (!token || /\s/.test(token)) throw new Error('Token file does not contain one JWT');
const currentHtml = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
const currentAsset = currentHtml.match(/\/assets\/(index-[\w-]+\.js)/)?.[1];
if (!currentAsset) throw new Error('Current frontend build asset is unavailable');

const checks = [];
const pageErrorKinds = [];
let nonReadRequests = 0;
let runtimeMode = 'unknown';
const record = (name, pass, status) => checks.push({ name, pass: Boolean(pass), ...(status === undefined ? {} : { status }) });
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome' });

try {
  // Anonymous checks use an isolated browser context without stored credentials.
  const anonymous = await browser.newContext();
  const anonPage = await anonymous.newPage();
  anonPage.on('pageerror', error => pageErrorKinds.push(error.name || 'Error'));
  await anonPage.goto(`${base}/login`, { waitUntil: 'domcontentloaded' });
  const deployedAsset = await anonPage.locator('script[src*="/assets/index-"]').first().getAttribute('src', { timeout: 1000 }).catch(() => null);
  if (deployedAsset) {
    runtimeMode = 'built_static';
    record('deployed frontend matches current build', deployedAsset.endsWith(`/${currentAsset}`));
  } else {
    runtimeMode = 'vite_dev';
    const hasViteClient = await anonPage.locator('script[src="/@vite/client"]').count() > 0;
    const hasCurrentEntry = await anonPage.locator('script[src="/src/main.jsx"]').count() > 0;
    record('deployed frontend serves current Vite source entry', hasViteClient && hasCurrentEntry);
  }
  record('anonymous login page', new URL(anonPage.url()).pathname === '/login' && await anonPage.getByRole('heading', { name: 'Đăng nhập' }).first().isVisible());
  await anonPage.goto(`${base}/documents`, { waitUntil: 'domcontentloaded' });
  await anonPage.waitForURL('**/login', { timeout: 15000 });
  record('anonymous protected route redirects', new URL(anonPage.url()).pathname === '/login');
  await anonymous.close();

  // JWT injection exercises the actual deployed session restore path. It does not
  // claim to test password login. All API requests still go to the real gateway.
  const context = await browser.newContext();
  await context.addInitScript(value => localStorage.setItem('docvault_token', value), token);
  const page = await context.newPage();
  page.on('pageerror', error => pageErrorKinds.push(error.name || 'Error'));
  page.on('request', request => {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method())) nonReadRequests += 1;
  });
  await page.goto(`${base}/documents`, { waitUntil: 'domcontentloaded' });
  await page.waitForURL('**/documents', { timeout: 15000 });

  const readApi = path => page.evaluate(async path => {
    const authorization = `Bearer ${localStorage.getItem('docvault_token') || ''}`;
    const response = await fetch(path, { headers: { Authorization: authorization }, cache: 'no-store' });
    return { status: response.status, body: response.ok ? await response.json() : null };
  }, path);

  const me = await readApi('/api/auth/me');
  record('authenticated real API me', me.status === 200 && Number.isInteger(me.body?.id) && typeof me.body?.role === 'string', me.status);
  const listing = await readApi('/api/documents');
  const documents = Array.isArray(listing.body) ? listing.body : Array.isArray(listing.body?.items) ? listing.body.items : [];
  record('authenticated real API documents', listing.status === 200 && Array.isArray(documents), listing.status);
  record('authenticated documents page', new URL(page.url()).pathname === '/documents' && await page.getByRole('textbox', { name: 'Tìm kiếm tài liệu' }).isVisible());

  const preferred = preferredDocId && /^\d+$/.test(preferredDocId) ? Number(preferredDocId) : null;
  const candidate = preferred || documents.find(item => item.effective_from && Number.isInteger(item.id))?.id || documents.find(item => Number.isInteger(item.id))?.id;
  if (candidate) {
    const detail = await readApi(`/api/documents/${candidate}`);
    record('readable document detail API', detail.status === 200 && detail.body?.id === candidate, detail.status);
    const duplicate = await readApi(`/api/documents/${candidate}/duplicate-check`);
    record('real duplicate check API', duplicate.status === 200 && typeof duplicate.body?.checked === 'boolean', duplicate.status);

    await page.goto(`${base}/documents/${candidate}`, { waitUntil: 'domcontentloaded' });
    const heading = page.locator('h1').first();
    await heading.waitFor({ timeout: 15000 });
    record('source detail renders', new URL(page.url()).pathname === `/documents/${candidate}` && await heading.isVisible());
    const dateRow = page.getByText('Ngày hiệu lực', { exact: true }).first();
    const dateVisible = await dateRow.isVisible();
    const expectedDateVisible = !detail.body?.effective_from || await page.getByText(String(detail.body.effective_from), { exact: true }).first().isVisible();
    record('source effective date shown', dateVisible && expectedDateVisible);
    const panel = page.getByRole('region', { name: 'Kiểm tra nội dung trùng' });
    const panelVisible = await panel.isVisible();
    let copyVisible = false;
    if (duplicate.body?.checked && duplicate.body.match_type === 'exact') copyVisible = await panel.getByText('Nội dung phần chữ trùng', { exact: false }).isVisible();
    else if (duplicate.body?.checked && duplicate.body.match_type === 'similar') copyVisible = await panel.getByText('Nội dung phần chữ gần giống', { exact: false }).isVisible();
    else if (duplicate.body?.checked) copyVisible = await panel.getByText('Không phát hiện trùng phần chữ', { exact: false }).isVisible();
    else copyVisible = await panel.getByText('Chưa có kết quả kiểm tra', { exact: false }).isVisible();
    record('source duplicate panel reflects real result', panelVisible && copyVisible);
  } else {
    record('readable document available for detail smoke', false);
  }

  await page.getByRole('button', { name: 'Menu tài khoản' }).click();
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await page.waitForURL('**/login', { timeout: 15000 });
  record('real logout clears token and protected view', await page.evaluate(() => !localStorage.getItem('docvault_token')) && new URL(page.url()).pathname === '/login');
  await context.close();
} catch (error) {
  record('smoke runner completed', false, error?.name || 'Error');
} finally {
  await browser.close();
}

const report = {
  checked_at: new Date().toISOString(),
  scope: 'Deployed gateway, real API, supplied JWT; read-only browser navigation, GET checks, and real logout button. Password login was not exercised. Vite dev mode checks the source entry and UI behavior; source hash equality is verified separately by deployment manifest.',
  runtime_mode: runtimeMode,
  checks,
  page_error_kinds: pageErrorKinds,
  non_read_request_count: nonReadRequests,
  pass: checks.every(check => check.pass) && pageErrorKinds.length === 0 && nonReadRequests === 0,
};
writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
console.log(JSON.stringify(report));
if (!report.pass) process.exitCode = 1;
