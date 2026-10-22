import { chromium } from 'playwright';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:5176';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
});
const context = await browser.newContext();
await context.addInitScript(() => localStorage.setItem('docvault_token', 'synthetic-fixture-token'));
const results = [];
const checks = {
  91: { checked: true, match_type: 'exact', similarity: null, match: { id: 321, name: 'Tài liệu nguồn.txt' }, scope: 'workspace' },
  92: { checked: true, match_type: 'exact', similarity: null, match: null, scope: 'workspace' },
  93: { checked: true, match_type: 'similar', similarity: 0.87, match: { id: 322, name: 'Nội dung gần giống.txt' }, scope: 'workspace' },
  94: { checked: true, match_type: null, similarity: null, match: null, scope: 'workspace' },
};
const json = (route, data, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
await context.route('**/api/**', async route => {
  const path = new URL(route.request().url()).pathname;
  if (path === '/api/auth/me') return json(route, { id: 1, name: 'Synthetic Admin', role: 'Admin', is_active: true });
  if (path === '/api/approvals/count') return json(route, { count: 0 });
  const match = path.match(/^\/api\/documents\/(\d+)(?:\/(duplicate-check|versions))?$/);
  if (match) {
    const id = Number(match[1]);
    if (match[2] === 'duplicate-check') {
      if (id === 95) return json(route, { detail: 'Not found' }, 404);
      return json(route, checks[id] || { checked: false, match_type: null, match: null, scope: 'workspace' });
    }
    if (match[2] === 'versions') return json(route, []);
    return json(route, { id, name: `Synthetic document ${id}`, type: 'bin', size: 10, status: 'failed', approval_status: 'approved', visibility: 'public', created_at: '2026-09-30T08:00:00' });
  }
  return json(route, []);
});

async function check(name, fn) {
  try { results.push({ name, pass: Boolean(await fn()) }); }
  catch (error) { results.push({ name, pass: false, error: String(error) }); }
}

try {
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));

  await page.goto(`${base}/documents/91`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Nội dung phần chữ trùng với tài liệu khác', { exact: false }).waitFor();
  await check('exact duplicate links to readable match', async () =>
    await page.getByRole('link', { name: 'Xem tài liệu liên quan: Tài liệu nguồn.txt' }).getAttribute('href') === '/documents/321');

  await page.goto(`${base}/documents/92`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Bạn không có quyền xem tài liệu liên quan.').waitFor();
  await check('inaccessible exact match has no name or link', async () =>
    await page.getByText('Tài liệu nguồn.txt').count() === 0 && await page.getByRole('link', { name: /Xem tài liệu liên quan/ }).count() === 0);

  await page.goto(`${base}/documents/93`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Nội dung phần chữ gần giống', { exact: false }).waitFor();
  await check('similar content remains advisory with percentage', async () =>
    await page.getByText('87%', { exact: false }).count() > 0 && await page.getByText('hệ thống không tự gộp', { exact: false }).count() > 0);

  await page.goto(`${base}/documents/94`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Không phát hiện trùng phần chữ trong kho này.').waitFor();
  await check('checked no-match names narrow text scope', async () => await page.getByText('Không phát hiện trùng phần chữ trong kho này.').count() === 1);

  await page.goto(`${base}/documents/95`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Chưa có kết quả kiểm tra phần chữ').waitFor();
  await check('404 does not claim duplicate check complete', async () => await page.getByText('Không phát hiện trùng phần chữ trong kho này.').count() === 0);
  await check('duplicate panel has no runtime errors', async () => errors.length === 0);
} finally {
  await context.close();
  await browser.close();
}

console.log(JSON.stringify(results));
if (results.some(result => !result.pass)) process.exitCode = 1;
