import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { readSSEStream } from '../src/utils/api.js';
import { isAdminRole, isPrivilegedRole } from '../src/utils/roles.js';

const dom = new JSDOM('<!doctype html><html><body></body></html>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
const { sanitizeHtml, escapeHtml } = await import('../src/utils/sanitizeHtml.js');

test('approval HTML keeps formatting but removes scripts, handlers and unsafe URLs', () => {
  const clean = sanitizeHtml('<h2>Hồ sơ</h2><img src=x onerror="alert(1)"><a href="javascript:alert(2)">mở</a><svg onload="alert(3)"></svg><script>alert(4)</script>');
  const container = dom.window.document.createElement('div');
  container.innerHTML = clean;
  assert.equal(container.querySelector('h2')?.textContent, 'Hồ sơ');
  assert.equal(container.querySelector('script,svg'), null);
  assert.equal(container.querySelector('img')?.hasAttribute('onerror'), false);
  assert.equal(container.querySelector('a')?.hasAttribute('href'), false);
});

test('chat content and citation attributes cannot break out of HTML', () => {
  const hostile = '\"><img src=x onerror=alert(1)>';
  const clean = sanitizeHtml(`<button title="${escapeHtml(hostile)}">${escapeHtml(hostile)}</button>`);
  const container = dom.window.document.createElement('div');
  container.innerHTML = clean;
  assert.equal(container.querySelectorAll('img').length, 0);
  assert.equal(container.querySelector('button')?.getAttribute('title'), hostile);
});

test('protected image placeholders keep only identifiers needed for authenticated fetch', () => {
  const clean = sanitizeHtml('<img data-image-doc-id="42" data-image-id="a-b" src="javascript:alert(1)" onload="alert(2)">');
  const container = dom.window.document.createElement('div');
  container.innerHTML = clean;
  const image = container.querySelector('img');
  assert.equal(image?.dataset.imageDocId, '42');
  assert.equal(image?.dataset.imageId, 'a-b');
  assert.equal(image?.hasAttribute('src'), false);
  assert.equal(image?.hasAttribute('onload'), false);
});

function sseResponse(parts) {
  const encoder = new TextEncoder();
  return new Response(new ReadableStream({
    start(controller) {
      for (const part of parts) controller.enqueue(encoder.encode(part));
      controller.close();
    },
  }), { headers: { 'content-type': 'text/event-stream' } });
}

test('SSE EOF after tokens reports partial answer, never completion', async () => {
  const events = [];
  await readSSEStream(sseResponse(['event: token\ndata: {"text":"dở"}\n\n']), {
    onChunk: chunk => events.push(chunk.event),
    onDone: () => events.push('done'),
    onError: () => events.push('error'),
  });
  assert.deepEqual(events, ['token', 'error']);
});

test('SSE completion and explicit error have separate terminal states', async () => {
  for (const [terminal, expected] of [
    ['event: complete\ndata: {"answer":"đủ"}\n\n', ['token', 'complete', 'done']],
    ['event: error\ndata: {"message":"hỏng"}\n\n', ['token', 'error']],
  ]) {
    const events = [];
    await readSSEStream(sseResponse(['event: token\ndata: {"text":"dở"}\n\n', terminal]), {
      onChunk: chunk => events.push(chunk.event),
      onDone: () => events.push('done'),
      onError: () => events.push('error'),
    });
    assert.deepEqual(events, expected);
  }
});

test('only Admin can enter management routes; executive roles retain privileged read workflow', () => {
  for (const role of ['Trưởng phòng', 'Giám đốc', 'Phó giám đốc', 'Nhân viên', undefined]) {
    assert.equal(isAdminRole(role), false);
  }
  assert.equal(isAdminRole('Admin'), true);
  assert.equal(isPrivilegedRole('Giám đốc'), true);
  assert.equal(isPrivilegedRole('Phó giám đốc'), true);
});
