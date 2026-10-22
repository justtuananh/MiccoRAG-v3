import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

// Render the real page and event handlers; only the network boundary is synthetic.
const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://b04.fixture/documents' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.FormData = dom.window.FormData;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { default: React, act } = await import('react');
const { createRoot } = await import('react-dom/client');
const { MemoryRouter } = await import('react-router-dom');
// Vite transforms JSX in middleware mode without opening a listening server.
const vite = await createServer({
  configFile: false, server: { middlewareMode: true },
  esbuild: { jsx: 'automatic' },
});
const { default: Documents } = await vite.ssrLoadModule('/src/pages/Documents.jsx');
const { AuthContext } = await vite.ssrLoadModule('/src/context/authContextCore.js');
after(async () => { await vite.close(); dom.window.close(); });

async function mountUpload() {
  const host = document.createElement('div');
  document.body.append(host);
  const root = createRoot(host);
  const uploads = [];
  const authFetch = async (url, options) => {
    if (url === '/api/documents/upload') {
      uploads.push(options);
      return new Response(JSON.stringify({ detail: 'Fixture stopped before persistence' }), { status: 400 });
    }
    assert.ok(['/api/documents', '/api/auth/departments'].includes(url), url);
    return new Response('[]');
  };
  await act(async () => root.render(React.createElement(MemoryRouter, { initialEntries: ['/documents'] },
    React.createElement(AuthContext.Provider, {
      value: { user: { id: 1, role: 'Nhân viên' }, authFetch, refreshApprovals() {} },
    }, React.createElement(Documents)))));
  await act(async () => host.querySelector('[aria-label="Tải lên tài liệu"]').click());
  const date = host.querySelector('input[type="date"]');
  await act(async () => {
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(date, '2026-10-22');
    date.dispatchEvent(new window.Event('input', { bubbles: true }));
    date.dispatchEvent(new window.Event('change', { bubbles: true }));
  });
  const submit = () => [...host.querySelectorAll('button')].find(button => /^Tải lên\s/.test(button.textContent));
  const select = async (method, files) => act(async () => {
    const input = host.querySelector('#file-input-upload');
    if (method === 'picker') {
      Object.defineProperty(input, 'files', { configurable: true, value: files });
      input.dispatchEvent(new window.Event('change', { bubbles: true }));
    } else {
      const event = new window.Event('drop', { bubbles: true, cancelable: true });
      Object.defineProperty(event, 'dataTransfer', { value: { files } });
      input.parentElement.dispatchEvent(event);
    }
  });
  const remove = async name => act(async () => {
    const row = [...host.querySelectorAll('p')].find(p => p.textContent === name)?.parentElement.parentElement;
    assert.ok(row, `staged row for ${name}`);
    row.querySelector('button').click();
  });
  const cleanup = async () => { await act(async () => root.unmount()); host.remove(); };
  return { host, uploads, select, remove, submit, cleanup };
}

for (const method of ['picker', 'drop']) {
  test(`${method}: empty file blocks upload; removal and valid reselection recover`, async () => {
    const ui = await mountUpload();
    try {
      await ui.select(method, [new window.File([], 'empty.txt')]);
      assert.equal(ui.submit().disabled, true);
      assert.match(ui.host.textContent, /[Tt]ệp rỗng/);
      await act(async () => ui.submit().click());
      assert.equal(ui.uploads.length, 0);
      await ui.remove('empty.txt');
      assert.doesNotMatch(ui.host.textContent, /[Tt]ệp rỗng/);
      assert.equal(ui.submit().disabled, true); // No files remain.
      await ui.select(method, [new window.File(['valid'], 'empty.txt')]);
      assert.equal(ui.submit().disabled, false);
      assert.doesNotMatch(ui.host.textContent, /[Tt]ệp rỗng/);
    } finally { await ui.cleanup(); }
  });

  test(`${method}: mixed files block the whole upload until the empty file is removed`, async () => {
    const ui = await mountUpload();
    try {
      await ui.select(method, [new window.File(['valid'], 'valid.txt'), new window.File([], 'bad.md')]);
      assert.equal(ui.submit().disabled, true);
      assert.match(ui.host.textContent, /[Tt]ệp rỗng/);
      assert.match(ui.host.textContent, /valid.txt/);
      assert.match(ui.host.textContent, /bad.md/);
      assert.equal(ui.submit().disabled, true);
      await act(async () => ui.submit().click());
      assert.equal(ui.uploads.length, 0);
      await ui.select(method, [new window.File(['more'], 'more.txt')]);
      assert.equal(ui.submit().disabled, true); // Adding a valid file cannot hide the bad one.
      assert.match(ui.host.textContent, /[Tt]ệp rỗng/);
      await ui.remove('bad.md');
      assert.doesNotMatch(ui.host.textContent, /[Tt]ệp rỗng/);
      assert.equal(ui.submit().disabled, false);
      await act(async () => ui.submit().click());
      assert.equal(ui.uploads.length, 1); // Real submit handler reaches the network again.
      assert.deepEqual(ui.uploads[0].body.getAll('files').map(file => file.name), ['valid.txt', 'more.txt']);
    } finally { await ui.cleanup(); }
  });
}

// Real File.size values around the backend's inclusive 50 * 1024 * 1024 limit.
const boundaryFiles = new Map([52_428_800, 52_428_801, 53_477_376].map(size => [
  size, new window.File([new Uint8Array(size)], `boundary-${size}.txt`),
]));

for (const method of ['picker', 'drop']) {
  test(`${method}: exact 50 MiB is accepted and the copy states the actual per-file limit`, async () => {
    const ui = await mountUpload();
    try {
      await ui.select(method, [boundaryFiles.get(52_428_800)]);
      assert.equal(ui.submit().disabled, false);
      assert.equal(ui.host.querySelector('[role="alert"]'), null);
      assert.match(ui.host.textContent, /50 MiB/);
      assert.match(ui.host.textContent, /52\.428\.800 byte/);
      // The limit applies per file, not to the combined selection.
      await ui.select(method, [boundaryFiles.get(52_428_800)]);
      assert.equal(ui.submit().disabled, false);
    } finally { await ui.cleanup(); }
  });

  for (const size of [52_428_801, 53_477_376]) {
    test(`${method}: ${size} bytes blocks single/mixed uploads and removal recovers`, async () => {
      const ui = await mountUpload();
      const oversized = boundaryFiles.get(size);
      try {
        await ui.select(method, [oversized]);
        assert.equal(ui.submit().disabled, true);
        const error = () => ui.host.querySelector('[role="alert"]')?.textContent || '';
        assert.ok(error().includes(oversized.name));
        assert.match(error(), /50 MiB/);
        assert.match(error(), /52\.428\.800 byte/);
        assert.ok(error().includes(size.toLocaleString('vi-VN')), 'actual byte size is unambiguous at limit + 1');
        await act(async () => ui.submit().click());
        assert.equal(ui.uploads.length, 0);
        await ui.select(method, [new window.File(['valid'], 'valid-small.txt')]);
        assert.equal(ui.submit().disabled, true);
        assert.ok(error().includes(oversized.name));
        await act(async () => ui.submit().click());
        assert.equal(ui.uploads.length, 0);
        await ui.remove(oversized.name);
        assert.equal(ui.submit().disabled, false);
        assert.equal(error(), '');
        await act(async () => ui.submit().click());
        assert.equal(ui.uploads.length, 1);
        assert.deepEqual(ui.uploads[0].body.getAll('files').map(file => file.name), ['valid-small.txt']);
      } finally { await ui.cleanup(); }
    });
  }

  test(`${method}: mixed empty and oversized errors persist until both invalid files are removed`, async () => {
    const ui = await mountUpload();
    const oversized = boundaryFiles.get(53_477_376);
    try {
      await ui.select(method, [new window.File([], 'empty.txt'), oversized, new window.File(['valid'], 'valid.txt')]);
      const error = () => ui.host.querySelector('[role="alert"]')?.textContent || '';
      assert.match(error(), /[Tt]ệp rỗng/);
      assert.ok(error().includes(oversized.name));
      assert.equal(ui.submit().disabled, true);
      await ui.remove('empty.txt');
      assert.doesNotMatch(error(), /[Tt]ệp rỗng/);
      assert.equal(ui.submit().disabled, true);
      await ui.remove(oversized.name);
      assert.equal(error(), '');
      assert.equal(ui.submit().disabled, false);
      assert.equal(ui.uploads.length, 0);
    } finally { await ui.cleanup(); }
  });
}
