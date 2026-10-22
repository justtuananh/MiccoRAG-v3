import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://b06.fixture/documents/104' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.localStorage = dom.window.localStorage;
globalThis.requestAnimationFrame = callback => { queueMicrotask(() => callback(0)); return 1; };
globalThis.cancelAnimationFrame = () => {};
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { default: React, act } = await import('react');
const { createRoot } = await import('react-dom/client');
const { MemoryRouter, Routes, Route } = await import('react-router-dom');
const vite = await createServer({ configFile: false, server: { middlewareMode: true }, esbuild: { jsx: 'automatic' } });
const { default: DocumentView } = await vite.ssrLoadModule('/src/pages/DocumentView.jsx');
const { AuthContext } = await vite.ssrLoadModule('/src/context/authContextCore.js');
const originalFetch = globalThis.fetch;
after(async () => { globalThis.fetch = originalFetch; await vite.close(); dom.window.close(); });

async function renderDetail({ status = 'rejected', note = 'Thiếu căn cứ.\nBổ sung ngày hiệu lực.', denied = false } = {}) {
  const host = document.createElement('div');
  document.body.append(host);
  const calls = [];
  const fixtureFetch = async (url, options = {}) => {
    assert.equal(options.method || 'GET', 'GET');
    calls.push(url);
    if (url === '/api/documents/104') {
      return new Response(JSON.stringify(denied ? { detail: 'Permission denied' } : {
        id: 104, name: 'B06-fixture.txt', type: 'TXT', size: '10 B', owner: 'Owner', uploader_id: 5,
        department: 'Kỹ thuật', visibility: 'internal', approval_status: status,
        approval_note: note, status: status === 'approved' ? 'indexed' : status,
        created_at: '2026-10-22T01:00:00', tags: [],
      }), { status: denied ? 403 : 200 });
    }
    if (url.endsWith('/versions')) return new Response('[]');
    if (url.endsWith('/duplicate-check')) return new Response('null');
    if (url.endsWith('/preview')) return new Response(JSON.stringify({ supported: true, content: 'Synthetic preview' }));
    assert.fail(`Unexpected request: ${url}`);
  };
  globalThis.fetch = fixtureFetch;
  const root = createRoot(host);
  await act(async () => root.render(React.createElement(MemoryRouter, { initialEntries: ['/documents/104'] },
    React.createElement(AuthContext.Provider, { value: { user: { id: 5, role: 'Nhân viên' }, authFetch: fixtureFetch } },
      React.createElement(Routes, null,
        React.createElement(Route, { path: '/documents/:id', element: React.createElement(DocumentView) }),
        React.createElement(Route, { path: '/documents', element: React.createElement('p', null, 'Documents list') }))))));
  return { host, calls, cleanup: async () => { await act(async () => root.unmount()); host.remove(); } };
}

test('owner sees the persisted rejection reason on initial detail and a fresh reload', async () => {
  for (let load = 0; load < 2; load++) {
    const ui = await renderDetail();
    try {
      const reason = ui.host.querySelector('[aria-label="Lý do từ chối"]');
      assert.ok(reason, 'rejected detail has a clearly labelled reason');
      assert.ok(reason.textContent.includes('Thiếu căn cứ.\nBổ sung ngày hiệu lực.'));
      assert.doesNotMatch(ui.host.textContent, /đang chờ phê duyệt/);
      assert.match(ui.host.textContent, /đã từ chối tài liệu này/);
      assert.ok(ui.calls.includes('/api/documents/104'));
    } finally { await ui.cleanup(); }
  }
});

for (const note of [null, '', '   ']) {
  test(`rejected legacy document with ${JSON.stringify(note)} note has an explicit fallback`, async () => {
    const ui = await renderDetail({ note });
    try {
      assert.match(ui.host.querySelector('[aria-label="Lý do từ chối"]')?.textContent || '', /Chưa có lý do từ chối/);
    } finally { await ui.cleanup(); }
  });
}

for (const status of ['pending', 'approved']) {
  test(`${status} detail does not mislabel an approval note as a rejection`, async () => {
    const ui = await renderDetail({ status, note: 'Normal approval metadata' });
    try {
      assert.equal(ui.host.querySelector('[aria-label="Lý do từ chối"]'), null);
      assert.doesNotMatch(ui.host.textContent, /Normal approval metadata|đã từ chối tài liệu này/);
      assert.match(ui.host.textContent, status === 'approved' ? /đã phê duyệt tài liệu này/ : /đang chờ phê duyệt/);
    } finally { await ui.cleanup(); }
  });
}

test('rejection reason renders as text, including markup and long content', async () => {
  const note = '<img src=x onerror=alert(1)>\n' + 'Bổ sung căn cứ '.repeat(40);
  const ui = await renderDetail({ note });
  try {
    const reason = ui.host.querySelector('[aria-label="Lý do từ chối"]');
    assert.ok(reason?.textContent.includes(note));
    assert.equal(reason.querySelector('img,script'), null);
  } finally { await ui.cleanup(); }
});

test('denied detail redirects without displaying the rejection reason', async () => {
  const ui = await renderDetail({ denied: true });
  try {
    assert.match(ui.host.textContent, /Documents list/);
    assert.equal(ui.host.querySelector('[aria-label="Lý do từ chối"]'), null);
    assert.doesNotMatch(ui.host.textContent, /Thiếu căn cứ/);
  } finally { await ui.cleanup(); }
});
