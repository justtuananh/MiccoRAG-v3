import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:5174';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
});
const results = [];
const payload = '<img src=x onerror="window.__xss=1"><svg onload="window.__xss=2"></svg><a href="javascript:window.__xss=3">mở</a>';
const docs = [
  { id: 11, name: 'Quy trình mua sắm.pdf', type: 'PDF', category: 'Quy trình', tags: ['mua sắm'], status: 'indexed', approval_status: 'approved', department_id: 1, created_at: '2026-09-29T08:00:00' },
  { id: 12, name: 'Báo cáo kỹ thuật.docx', type: 'DOCX', category: 'Báo cáo', tags: ['kỹ thuật'], status: 'failed', approval_status: 'approved', department_id: 2, created_at: '2026-09-28T08:00:00' },
];

async function fixture(role = 'Admin') {
  const context = await browser.newContext();
  await context.addInitScript(() => localStorage.setItem('docvault_token', 'fixture-token'));
  let chatPosts = 0;
  await context.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const json = value => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(value) });
    if (path === '/api/auth/me') return json({ id: 1, name: 'Tester', role });
    if (path === '/api/auth/departments') return json([{ id: 1, name: 'Phòng A' }, { id: 2, name: 'Phòng B' }]);
    if (path === '/api/documents') {
      const params = new URL(request.url()).searchParams;
      if (params.get('type') === 'PDF') await new Promise(resolve => setTimeout(resolve, 400));
      return json(docs.filter(doc =>
        (!params.get('type') || doc.type === params.get('type')) &&
        (!params.get('category') || doc.category === params.get('category')) &&
        (!params.get('department_id') || String(doc.department_id) === params.get('department_id'))));
    }
    if (path === '/api/approvals/count') return json({ count: 1 });
    if (path === '/api/v1/workspaces') return json([{ id: 1, name: 'KB thử', document_count: 1, indexed_count: 1 }]);
    if (path === '/api/v1/workspaces/1/suggested-questions') return json([]);
    if (path === '/api/v1/rag/chat/1/history') return json({ messages: [
      { id: 'u1', role: 'user', content: payload },
      { id: 'a1', role: 'assistant', content: `Nội dung ${payload} [ doc:2 ]`, sources: [{ index: 'doc:2', document_id: 2, source_file: '\" onmouseover=\"window.__xss=4' }] },
      { id: 'a2', role: 'assistant', content: 'Tham khảo [ a3x9 ]', sources: [{ index: 'a3x9', document_id: 3, source_file: 'Tên mới.pdf', formatted: 'Tên cũ.pdf' }] },
    ] });
    if (path === '/api/v1/documents/3/markdown') return route.fulfill({ status: 200, contentType: 'text/plain', body: 'Nội dung tài liệu đổi tên' });
    if (path === '/api/v1/rag/chat/1/stream') {
      chatPosts++;
      return route.fulfill({ status: 200, contentType: 'text/event-stream', body: 'event: token\ndata: {"text":"Câu trả lời dở"}\n\n' });
    }
    if (path === '/api/v1/rag/chat/1') {
      chatPosts++;
      return json({ answer: 'Unexpected retry' });
    }
    if (path === '/api/approvals/pending') return json({ documents: [], knowledge: [{ id: 7, title: 'Mục thử', owner: 'Tester', content_text: 'x', visibility: 'public' }] });
    if (path === '/api/approvals/knowledge/7/preview') return json({ content_html: `<h2>Hồ sơ</h2>${payload}` });
    return json([]);
  });
  return { context, getChatPosts: () => chatPosts };
}

async function check(name, fn) {
  try { results.push({ name, pass: await fn() }); }
  catch (error) { results.push({ name, pass: false, error: String(error) }); }
}

try {
  const { context, getChatPosts } = await fixture();
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));
  await page.goto(`${base}/chat`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Nội dung', { exact: false }).first().waitFor();
  await check('chat history payload does not execute', async () => (await page.evaluate(() => window.__xss)) === undefined);
  await check('chat history creates no injected image or SVG', async () => await page.locator('.markdown-content img, .markdown-content svg').count() === 0);
  await check('citation title stays inside attribute', async () => await page.locator('.citation').first().getAttribute('title') === 'Nguồn: \" onmouseover=\"window.__xss=4');
  await check('renamed source uses current filename and citation ID', async () =>
    await page.locator('.citation').last().getAttribute('title') === 'Nguồn: Tên mới.pdf' &&
    await page.getByText('Tên mới.pdf', { exact: true }).count() > 0 &&
    await page.getByText('Tên cũ.pdf', { exact: true }).count() === 0);
  await page.locator('.citation').last().click();
  await page.getByText('Nội dung tài liệu đổi tên').waitFor();
  await check('citation opens document by ID after rename', async () =>
    await page.getByText('Tên mới.pdf', { exact: true }).count() > 0);
  await page.goto(`${base}/chat`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Nội dung', { exact: false }).first().waitFor();
  await page.locator('textarea').first().fill('Câu thử stream');
  await page.locator('textarea').first().press('Enter');
  await page.getByRole('alert').getByText('Nội dung phía trên có thể chưa đầy đủ.', { exact: false }).waitFor();
  await check('truncated stream shows partial warning and does not resend', async () => getChatPosts() === 1 && await page.getByText('Câu trả lời dở').count() > 0);
  await check('chat has no page error', async () => pageErrors.length === 0);

  await page.goto(`${base}/approvals`, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'Tri thức' }).click();
  await page.getByRole('button', { name: 'Xem trước' }).click();
  await page.getByRole('heading', { name: 'Hồ sơ' }).waitFor();
  await check('approval preview payload does not execute', async () => (await page.evaluate(() => window.__xss)) === undefined);
  await check('approval preview strips event handlers and javascript links', async () => {
    const preview = page.locator('.prose').last();
    return await preview.locator('img[onerror], svg, a[href^="javascript:"]').count() === 0;
  });

  await page.goto(`${base}/documents`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Quy trình mua sắm.pdf').first().waitFor();
  const documentSearch = page.getByRole('textbox', { name: 'Tìm kiếm tài liệu' });
  await documentSearch.fill('quy trinh');
  await check('Vietnamese filename search ignores accents', async () =>
    await page.getByText('Quy trình mua sắm.pdf').count() > 0 && await page.getByText('Báo cáo kỹ thuật.docx').count() === 0);
  await documentSearch.fill('');
  await page.getByRole('button', { name: 'Bộ lọc' }).click();
  await page.getByRole('combobox', { name: 'Lọc theo loại tệp' }).selectOption('DOCX');
  await page.getByText('Báo cáo kỹ thuật.docx').first().waitFor();
  await check('type filter removes rows from previous request', async () => await page.getByText('Quy trình mua sắm.pdf').count() === 0);
  await page.getByRole('combobox', { name: 'Lọc theo loại tệp' }).selectOption('PDF');
  await page.getByRole('combobox', { name: 'Lọc theo loại tệp' }).selectOption('DOCX');
  await page.waitForTimeout(500);
  await check('late response from old filter cannot overwrite newer rows', async () =>
    await page.getByText('Báo cáo kỹ thuật.docx').count() > 0 && await page.getByText('Quy trình mua sắm.pdf').count() === 0);
  await page.getByRole('combobox', { name: 'Lọc theo loại tệp' }).selectOption('All');
  await page.getByRole('combobox', { name: 'Lọc theo danh mục' }).selectOption('Quy trình');
  await page.getByText('Quy trình mua sắm.pdf').first().waitFor();
  await check('category filter scopes rows', async () => await page.getByText('Báo cáo kỹ thuật.docx').count() === 0);
  await page.getByRole('combobox', { name: 'Lọc theo danh mục' }).selectOption('All');
  await page.getByRole('textbox', { name: 'Lọc theo thẻ' }).fill('mua sam');
  await check('tag filter matches Vietnamese accents', async () =>
    await page.getByText('Quy trình mua sắm.pdf').count() > 0 && await page.getByText('Báo cáo kỹ thuật.docx').count() === 0);
  await page.getByRole('textbox', { name: 'Lọc theo thẻ' }).fill('');
  await page.getByRole('combobox', { name: 'Lọc theo trạng thái' }).selectOption('failed');
  await check('status filter shows failed document only', async () =>
    await page.getByText('Báo cáo kỹ thuật.docx').count() > 0 && await page.getByText('Quy trình mua sắm.pdf').count() === 0);
  await page.getByRole('combobox', { name: 'Lọc theo trạng thái' }).selectOption('All');
  await page.getByRole('button', { name: 'Phòng A' }).click();
  await check('department filter scopes visible rows', async () =>
    await page.getByText('Quy trình mua sắm.pdf').count() > 0 && await page.getByText('Báo cáo kỹ thuật.docx').count() === 0);
  await documentSearch.fill('không có tài liệu nào khớp');
  await check('empty result state is explicit', async () => await page.getByText('Không tìm thấy tài liệu').count() > 0);
  await context.close();

  const restricted = await fixture('Giám đốc');
  const restrictedPage = await restricted.context.newPage();
  await restrictedPage.goto(`${base}/admin`, { waitUntil: 'domcontentloaded' });
  await restrictedPage.waitForURL('**/dashboard');
  await check('executive cannot open admin route or menu', async () =>
    await restrictedPage.getByRole('link', { name: 'Quản trị' }).count() === 0);
  await restricted.context.close();
} finally {
  await browser.close();
}

const report = { checked_at: new Date().toISOString(), base, results, passed: results.filter(r => r.pass).length, total: results.length };
if (process.env.E2E_EVIDENCE) writeFileSync(process.env.E2E_EVIDENCE, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (report.passed !== report.total) process.exitCode = 1;
