import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const base = process.env.E2E_BASE_URL || 'http://127.0.0.1:15175';
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_PATH || '/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell',
});

try {
  const context = await browser.newContext();
  await context.addInitScript(() => localStorage.setItem('docvault_token', 'synthetic-chat-fixture'));
  const requests = [];
  await context.route('**/api/**', route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const json = body => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (path === '/api/auth/me') return json({ id: 1, name: 'Synthetic user', role: 'Nhân viên' });
    if (path === '/api/v1/workspaces') return json([
      { id: 1, name: 'KB A', document_count: 1, indexed_count: 1 },
      { id: 2, name: 'KB B', document_count: 1, indexed_count: 1 },
    ]);
    if (/^\/api\/v1\/workspaces\/\d+\/suggested-questions$/.test(path)) return json([]);
    if (/^\/api\/v1\/rag\/chat\/\d+\/history$/.test(path)) return json({ messages: [] });
    const stream = path.match(/^\/api\/v1\/rag\/chat\/(\d+)\/stream$/);
    if (stream) {
      const body = request.postDataJSON();
      requests.push({ workspaceId: Number(stream[1]), ...body });
      const answer = `Reply ${requests.length}`;
      return route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body: `event: complete\ndata: ${JSON.stringify({ answer, sources: [] })}\n\n`,
      });
    }
    return json([]);
  });

  const page = await context.newPage();
  await page.goto(`${base}/chat`, { waitUntil: 'domcontentloaded' });
  const input = page.locator('textarea').first();
  const send = async (question, answer) => {
    await input.fill(question);
    await input.press('Enter');
    await page.getByText(answer, { exact: true }).waitFor();
    await page.waitForFunction(() => !document.querySelector('textarea')?.disabled);
  };

  await send('First question', 'Reply 1');
  await send('Second question', 'Reply 2');
  assert.equal(requests[0].workspaceId, 1);
  assert.equal(requests[0].history, undefined);
  assert.equal(requests[1].history, undefined);

  await page.getByRole('button', { name: 'KB A' }).first().click();
  await page.getByRole('button', { name: 'KB B' }).click();
  await send('Other workspace', 'Reply 3');
  assert.equal(requests[2].workspaceId, 2);
  assert.equal(requests[2].history, undefined);

  console.log('Chat browser test passed: requests use the selected workspace and leave history to the server.');
  await context.close();
} finally {
  await browser.close();
}
