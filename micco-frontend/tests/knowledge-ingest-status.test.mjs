import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://b07.fixture/knowledge' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { default: React, act } = await import('react');
const { createRoot } = await import('react-dom/client');
const { renderToStaticMarkup } = await import('react-dom/server');
const { MemoryRouter } = await import('react-router-dom');
const vite = await createServer({ configFile: false, server: { middlewareMode: true }, esbuild: { jsx: 'automatic' } });
const { default: KnowledgeCard } = await vite.ssrLoadModule('/src/components/knowledge/KnowledgeCard.jsx');
const { default: Knowledge } = await vite.ssrLoadModule('/src/pages/Knowledge.jsx');
const { AuthContext } = await vite.ssrLoadModule('/src/context/authContextCore.js');
after(async () => { await vite.close(); dom.window.close(); });

function entry(approval, ingest) {
  return {
    id: 1, title: 'B07 synthetic knowledge', owner: 'Owner', department: 'Kỹ thuật',
    content_text: 'Synthetic content', content_html: '<p>Synthetic content</p>',
    visibility: 'internal', status: approval === 'approved' ? 'Active' : 'Pending',
    approval_status: approval, ingest_status: ingest, category: 'Chung', tags: [],
  };
}

for (const [approval, ingest, label, approvalLabel] of [
  ['approved', 'indexed', 'Đã đồng bộ', null],
  ['approved', 'completed', 'Đã đồng bộ', null],
  ['approved', 'processing', 'Đang xử lý', null],
  ['approved', 'pending', 'Chờ xử lý', null],
  ['approved', 'failed', 'Lỗi', null],
  ['pending_dept', 'pending', 'Chờ xử lý', 'Chờ duyệt cấp phòng'],
  ['pending_org', 'pending', 'Chờ xử lý', 'Chờ duyệt cấp tổ chức'],
  ['rejected', 'pending', 'Chờ xử lý', 'Từ chối'],
  ['approved', null, 'Chờ xử lý', null],
  ['approved', 'unknown', 'Chờ xử lý', null],
]) {
  test(`${approval}/${ingest}: ingestion reflects its own status independently of approval`, () => {
    const host = document.createElement('div');
    host.innerHTML = renderToStaticMarkup(React.createElement(KnowledgeCard, { entry: entry(approval, ingest) }));
    const status = host.querySelector(`div[title="${label}"]`);
    assert.ok(status, `expected ingestion label ${label}`);
    assert.equal(status.textContent, label);
    if (label !== 'Đã đồng bộ') assert.doesNotMatch(host.textContent, /Đã đồng bộ/);
    if (approvalLabel) assert.ok(host.textContent.includes(approvalLabel));
  });
}

test('fresh page loads reflect pending, approved-processing and indexed API state in grid and list', async () => {
  for (const [approval, ingest, label] of [
    ['pending_dept', 'pending', 'Chờ xử lý'],
    ['approved', 'processing', 'Đang xử lý'],
    ['approved', 'indexed', 'Đã đồng bộ'],
  ]) {
    const host = document.createElement('div');
    document.body.append(host);
    const root = createRoot(host);
    const authFetch = async (url, options = {}) => {
      assert.equal(url, '/api/knowledge');
      assert.equal(options.method || 'GET', 'GET');
      return new Response(JSON.stringify({ items: [entry(approval, ingest)] }));
    };
    try {
      await act(async () => root.render(React.createElement(MemoryRouter, null,
        React.createElement(AuthContext.Provider, { value: { authFetch } }, React.createElement(Knowledge)))));
      assert.match(host.textContent, /B07 synthetic knowledge/);
      assert.equal(host.querySelector(`div[title="${label}"]`)?.textContent, label);
      const listIcon = host.querySelector('svg.lucide-list');
      assert.ok(listIcon, 'list layout toggle');
      await act(async () => listIcon.closest('button').click());
      assert.equal(host.querySelector(`div[title="${label}"]`)?.textContent, label);
      if (ingest === 'indexed') assert.doesNotMatch(host.textContent, /Chờ xử lý|Chờ duyệt cấp phòng/);
      else assert.doesNotMatch(host.textContent, /Đã đồng bộ/);
    } finally {
      await act(async () => root.unmount());
      host.remove();
    }
  }
});
