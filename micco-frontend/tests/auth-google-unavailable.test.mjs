import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { createServer } from 'vite';

const dom = new JSDOM('<!doctype html><html><body></body></html>', { url: 'http://b08.fixture/login' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const { default: React, act } = await import('react');
const { createRoot } = await import('react-dom/client');
const { MemoryRouter, Routes, Route } = await import('react-router-dom');
const vite = await createServer({ configFile: false, server: { middlewareMode: true }, esbuild: { jsx: 'automatic' } });
const { default: AuthPage } = await vite.ssrLoadModule('/src/pages/AuthPage.jsx');
const { AuthContext } = await vite.ssrLoadModule('/src/context/authContextCore.js');
const { ThemeContext } = await vite.ssrLoadModule('/src/context/themeContextCore.js');
const oldFetch = globalThis.fetch;
after(async () => { globalThis.fetch = oldFetch; await vite.close(); dom.window.close(); });

async function mountAuth() {
  const host = document.createElement('div');
  document.body.append(host);
  const logins = [], registrations = [], requests = [];
  let success = false;
  globalThis.fetch = async (url, options = {}) => {
    requests.push(url);
    assert.equal(url, '/api/auth/departments');
    assert.equal(options.method || 'GET', 'GET');
    return new Response('[]');
  };
  const root = createRoot(host);
  await act(async () => root.render(React.createElement(MemoryRouter, { initialEntries: ['/login'] },
    React.createElement(AuthContext.Provider, { value: {
      login: async (...args) => { logins.push(args); return { success }; },
      register: async (...args) => { registrations.push(args); return { success: false }; },
    } }, React.createElement(ThemeContext.Provider, { value: { isDark: false, toggleTheme() {} } },
      React.createElement(Routes, null,
        React.createElement(Route, { path: '/login', element: React.createElement(AuthPage) }),
        React.createElement(Route, { path: '/dashboard', element: React.createElement('p', null, 'Signed in fixture') })))))));
  // AuthPage also mounts a CSS-hidden compact form; select the desktop sign-in form.
  const form = host.querySelector('form');
  const google = [...form.querySelectorAll('button')].find(button => button.textContent.includes('Đăng nhập với Google'));
  const fill = async (placeholder, value) => act(async () => {
    const input = form.querySelector(`input[placeholder="${placeholder}"]`);
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(input, value);
    input.dispatchEvent(new window.Event('input', { bubbles: true }));
  });
  const submit = async () => act(async () => form.dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true })));
  return { host, form, google, logins, registrations, requests, fill, submit,
    succeed: () => { success = true; },
    cleanup: async () => { await act(async () => root.unmount()); host.remove(); } };
}

test('Google activation reports unavailable without authenticating, redirecting or losing form values', async () => {
  const ui = await mountAuth();
  try {
    await ui.fill('Địa chỉ Email', 'b08@fixture.test');
    await ui.fill('Mật khẩu', 'fixture-password');
    assert.equal(ui.form.querySelector('[role="status"], [role="alert"]'), null);
    await act(async () => ui.google.click());
    const status = ui.form.querySelector('[role="status"], [role="alert"]');
    assert.ok(status, 'Google button must give accessible feedback');
    assert.match(status.textContent, /Google chưa được cấu hình/);
    assert.match(status.textContent, /email và mật khẩu/);
    assert.equal(ui.form.querySelector('input[type="email"]').value, 'b08@fixture.test');
    assert.equal(ui.form.querySelector('input[type="password"]').value, 'fixture-password');
    assert.equal(ui.logins.length, 0);
    assert.equal(ui.registrations.length, 0);
    assert.ok(ui.host.contains(ui.form), 'still on login page');
    assert.ok(ui.requests.every(url => url === '/api/auth/departments'));
  } finally { await ui.cleanup(); }
});

test('Google remains a focusable native button with associated status on repeated activation', async () => {
  const ui = await mountAuth();
  try {
    assert.equal(ui.google.type, 'button');
    assert.equal(ui.google.disabled, false);
    assert.equal(ui.google.tabIndex, 0);
    ui.google.focus();
    assert.equal(document.activeElement, ui.google);
    await act(async () => { ui.google.click(); ui.google.click(); });
    assert.equal(ui.form.querySelectorAll('[role="status"], [role="alert"]').length, 1);
    const status = document.getElementById(ui.google.getAttribute('aria-describedby'));
    assert.ok(status, 'native keyboard activation target describes its feedback');
    assert.match(status.textContent, /Google chưa được cấu hình/);
    assert.equal(document.activeElement, ui.google);
    assert.equal(ui.logins.length, 0);
  } finally { await ui.cleanup(); }
});

test('email/password failure and successful retry still work after Google feedback', async () => {
  const ui = await mountAuth();
  try {
    await act(async () => ui.google.click());
    await ui.fill('Địa chỉ Email', 'b08@fixture.test');
    await ui.fill('Mật khẩu', 'fixture-password');
    await ui.submit();
    assert.match(ui.host.textContent, /Đăng nhập thất bại/);
    assert.deepEqual(ui.logins, [['b08@fixture.test', 'fixture-password']]);
    assert.equal(ui.form.querySelector('button[type="submit"]').disabled, false);
    ui.succeed();
    await ui.submit();
    assert.match(ui.host.textContent, /Signed in fixture/);
    assert.equal(ui.logins.length, 2);
    assert.equal(ui.registrations.length, 0);
  } finally { await ui.cleanup(); }
});
