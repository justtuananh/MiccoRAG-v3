import { chromium } from 'playwright';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:5176';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
});
const results = [];
const context = await browser.newContext();
await context.addInitScript(() => localStorage.setItem('docvault_token', 'synthetic-fixture-token'));
let processingCalls = 0;
let processingMode = 'initial';
const userSearches = [];
const logSearches = [];
const requestedPaths = [];
const statusItem = {
  id: 91, name: 'synthetic-processing.txt', status: 'parsing', chunk_count: 0,
  uploader_name: 'Synthetic user', department_name: 'Synthetic department',
  file_type: 'txt', file_size: 32, created_at: '2026-09-30T08:00:00',
};
const json = (route, data, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(data) });
await context.route('**/api/**', async route => {
  const url = new URL(route.request().url());
  requestedPaths.push(url.pathname);
  if (url.pathname === '/api/auth/me') return json(route, { id: 1, name: 'Synthetic Admin', role: 'Admin', is_active: true });
  if (url.pathname === '/api/approvals/count') return json(route, { count: 0 });
  if (url.pathname === '/api/documents/processing-status') {
    processingCalls++;
    if (processingMode === 'fail') return json(route, { detail: 'Synthetic outage' }, 503);
    return json(route, { items: processingMode === 'initial' ? [statusItem] : [], counts: { all: 0, processing: 0, indexed: 0, failed: 0 } });
  }
  if (url.pathname === '/api/admin/stats') return json(route, { totalUsers: 1, totalDocuments: 0, totalKnowledge: 0, totalDepartments: 0, storageUsed: '0 KB', activeSessions: 0 });
  if (url.pathname === '/api/admin/users') {
    userSearches.push(url.searchParams.get('search') || '');
    return json(route, { users: [], total: 0, page: 1, page_size: 10 });
  }
  if (url.pathname === '/api/admin/chat-logs') {
    logSearches.push(url.searchParams.get('search') || '');
    return json(route, { logs: [], total: 0, page: 1, page_size: 10 });
  }
  return json(route, []);
});

async function check(name, test) {
  try { results.push({ name, pass: Boolean(await test()) }); }
  catch (error) { results.push({ name, pass: false, error: String(error) }); }
}

try {
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  await page.goto(`${base}/processing-status`, { waitUntil: 'domcontentloaded' });
  try { await page.getByText('synthetic-processing.txt').waitFor({ timeout: 8000 }); }
  catch (error) { throw new Error(`Processing fixture did not load: url=${page.url()} paths=${requestedPaths.join(',')} body=${(await page.locator('body').innerText()).slice(0, 400)} errors=${pageErrors.join('|')} cause=${error}`); }
  processingMode = 'fail';
  await page.getByRole('button', { name: 'Làm mới' }).click();
  await page.getByRole('alert').getByText('Không thể tải trạng thái xử lý.', { exact: false }).waitFor();
  await check('failed refresh is visible and retains labeled stale data', async () =>
    await page.getByText('synthetic-processing.txt').count() === 1 &&
    await page.getByText('Chưa cập nhật', { exact: true }).count() === 1 &&
    await page.getByText('dữ liệu cũ', { exact: false }).count() > 0);
  processingMode = 'recovered';
  await page.getByRole('button', { name: 'Thử lại' }).click();
  await page.getByText('Không có tài liệu nào đang xử lý').waitFor();
  await check('retry clears failure and accepts successful empty state', async () =>
    await page.getByRole('alert').count() === 0 && await page.getByText('synthetic-processing.txt').count() === 0);

  await page.goto(`${base}/admin`, { waitUntil: 'domcontentloaded' });
  const userInput = page.getByPlaceholder('Tìm kiếm người dùng...');
  await userInput.waitFor();
  await userInput.fill('synthetic-user-filter');
  await page.getByRole('button', { name: 'Lịch sử hệ thống' }).click();
  await page.getByPlaceholder('Tìm kiếm log (IP, câu hỏi, phương thức)...').fill('synthetic-log-filter');
  await page.waitForTimeout(600);
  await check('user and log debounces run independently', async () =>
    userSearches.includes('synthetic-user-filter') && logSearches.includes('synthetic-log-filter'));
  await check('both pages avoid runtime errors', async () => pageErrors.length === 0);
} finally {
  await context.close();
  await browser.close();
}

console.log(JSON.stringify(results));
if (results.some(result => !result.pass)) process.exitCode = 1;
