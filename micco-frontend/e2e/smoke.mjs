// e2e/smoke.mjs — Playwright smoke e2e cho MiccoRAG-v3 frontend.
// Boot SPA React trong trình duyệt thật (dùng gói `playwright` đã cài + chromium cache sẵn).
// Chạy:  npm run test:e2e         (mặc định http://127.0.0.1:5174)
//        E2E_BASE_URL=http://127.0.0.1:8888 npm run test:e2e   (qua nginx gateway)
// Cần: Vite dev (:5174) hoặc nginx gateway (:8888) đang chạy.
import { chromium } from 'playwright';

const BASE = (process.env.E2E_BASE_URL || 'http://127.0.0.1:5174').replace(/\/$/, '');
let failures = 0;
const check = (cond, msg) => {
  console.log(`  ${cond ? '✅ PASS' : '❌ FAIL'}: ${msg}`);
  if (!cond) failures++;
};

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(String(e)));

  const resp = await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  check(resp && resp.status() < 400, `GET ${BASE} -> ${resp ? resp.status() : 'no response'}`);

  const title = await page.title();
  check(typeof title === 'string' && title.length >= 0, `document.title = "${title}"`);

  await page.waitForSelector('#root', { timeout: 15000 });
  // Chờ React mount (root có con)
  await page
    .waitForFunction(() => {
      const r = document.querySelector('#root');
      return r && r.children.length > 0;
    }, { timeout: 20000 })
    .catch(() => {});
  const mounted = await page.evaluate(() => {
    const r = document.querySelector('#root');
    return !!r && r.children.length > 0;
  });
  check(mounted, 'React da mount vao #root (SPA render)');

  check(
    pageErrors.length === 0,
    `khong co pageerror (${pageErrors.length})` + (pageErrors[0] ? `: ${pageErrors[0].slice(0, 120)}` : ''),
  );
} finally {
  await browser.close();
}

console.log(failures === 0 ? '\nE2E: PASS' : `\nE2E: FAIL (${failures})`);
process.exit(failures === 0 ? 0 : 1);
