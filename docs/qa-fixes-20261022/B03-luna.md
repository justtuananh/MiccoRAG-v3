# B03 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`  
Scope: B03 department filter only; desktop 1366×768, 100% zoom, no mobile.  
Runner: isolated MCP Playwright context/tab. No app source, deployment, or records changed.

## Status

**B03 PASS after postfix retest.** The pre-fix baseline reproduced the defect; the live candidate now filters ordinary and admin lists correctly, reset restores the original results, and no page or console errors were captured.

The public `/login` page loaded at 1366×768. Login and registration panels rendered in the accessibility snapshot; the captured console error query returned zero errors. Screenshot: `harness/reports/fixes-20261022/B03-public-login-desktop.png`.

Attempted the explicitly provided private bootstrap using `page.request.get('http://127.0.0.1:18997/bootstrap').json()` from the MCP Playwright runner, twice. Both attempts failed before receiving a response with `ECONNREFUSED 127.0.0.1:18997`. No values were printed or stored. Consequently no authenticated baseline was possible in this run. Need parent to make bootstrap reachable from the runner or provide a working private setup path. User specified QA32 remains inactive and all QA docs47–54 are trashed; none were touched.

## Prior observed behavior (audit evidence; not a new baseline run)

`docs/qa-acceptance-20261022/sol-audit.md` SOL-03 and `luna-documents.md` D01-DEPT report the same B03: ordinary QA user, desktop 1366×768, exact search for active DOC-0051 (Kỹ thuật), select Ban Giám đốc; selected filter chip updates and UI GET with `department_id=6` returns 200, but DOC-0051 (186 B) remains visible. Reset to All worked. Audit explicitly found no evidence of a permissions leak; this establishes a filtering defect, not cross-department disclosure.

## Retest procedure when auth and candidate are ready

Use only UI navigation/actions in the isolated desktop tab. Bootstrap is permitted only for session initialization. Do not call business APIs as a substitute for UI. Use existing active documents read-only; do not create fixtures, restore trashed QA docs, or alter approval, ownership, department, or document state.

1. Set viewport to 1366×768 and confirm the page remains desktop (no mobile emulation). Record candidate/live build identity if visible or supplied by parent.
2. Initialize an ordinary QA session (user id 6, Kỹ thuật) through the private bootstrap into the app's documented `docvault_token` localStorage key without logging token material. Navigate through the app to Documents.
3. Identify an existing active, readable Kỹ thuật document using the list UI. Prefer DOC-0051 only if it remains active and visible. Record its displayed ID/name and department; avoid opening unrelated records.
4. Search its exact filename. Wait for the list UI/network activity to settle. Capture the visible selected department control and rows for All, Kỹ thuật, and Ban Giám đốc. Under each selection, verify every visible result's department against the selected department; Ban Giám đốc must not retain the Kỹ thuật row. Also check an existing Ban Giám đốc item only if one is already visible to the ordinary user; do not use unrelated data as a fixture.
5. Reset department to All. Verify the selected control visibly resets and the result set returns to the unfiltered result set (same exact search, same query). Clear the search and verify normal all-department listing returns, if that is how the UI exposes reset. Wait on the observable list state/request completion, not a fixed delay.
6. Check ordinary user's permissions remain unchanged: the department filter must only narrow already-authorized rows, and must not reveal a document or metadata that is absent from the ordinary user's unfiltered list. Do not test by opening a guessed URL or by querying APIs. Compare the UI row set before and after filter operations; filtering must not broaden access.
7. Capture a final screenshot after reset and inspect console errors generated during the run. Compare against the initial console baseline (zero console errors on public login). Record any new JS errors with message and action stage. A successful HTTP response alone is not a pass.
8. Repeat the same read-only filter/reset behavior under the adminToken (id 5) in its own isolated context/session if available, as a separate diagnostic baseline. Admin coverage does not replace ordinary-user permission verification. Never record token values.

## Acceptance criteria

- Selecting a department narrows the UI result rows to that department; the selected department is reflected consistently in the control and the result set.
- Reset to All clears the selection and restores exactly the unfiltered results for the same search; clearing search returns the normal list.
- For ordinary user id 6, neither selecting nor resetting reveals documents outside the user's existing authorized result set. No direct URL or API permission bypass is attempted.
- No new JavaScript console errors occur during filter, result update, or reset.
- Capture evidence for initial list, each relevant selected filter, reset result, viewport, role, and candidate build. Do not report PASS until each criterion has evidence.

## Evidence inventory

- `harness/reports/fixes-20261022/B03-public-login-desktop.png` — public login at target, viewport 1366×768, before authentication.
- Existing references (not generated by this run): `harness/reports/acceptance-20261022/DOCS-dept-filter-mismatch.png`, `harness/reports/acceptance-20261022/DOCS-ui-observations.md`, and `harness/reports/acceptance-20261022/root-department-filter-mismatch.png` as referenced in the audit. They document the prior mismatch only; they are not evidence of a candidate retest.

## Run log

| Stage | Result |
|---|---|
| Public site navigation | PASS — redirected to `/login`; title `TKV - Nền tảng tri thức` |
| Desktop viewport | PASS — 1366×768 |
| Login page rendering | PASS — login and registration controls present in accessibility snapshot |
| Console errors at public login | PASS — zero errors returned |
| Private bootstrap (initial attempt) | BLOCKED — two requests returned `ECONNREFUSED`; later follow-up succeeded with HTTP 200 (see authenticated baseline below) |
| Ordinary/admin B03 baseline | CAPTURED — B03 FAIL reproduced in authenticated live baseline below |
| Candidate B03 retest | PASS — live backend `miccorag-backend:20261022-desktop-b03`, ready 10:44:28; frontend unchanged |


## Authenticated live baseline follow-up (2026-10-22, approx. 10:43 ICT)

MCP Playwright bootstrap subsequently returned HTTP 200. The ordinary session (token for user id 6, Kỹ thuật) and admin session (id 5) were initialized in the same isolated desktop runner tab without printing credential material. Viewport remained 1366×768. No writes, uploads, restores, or business-record changes were made.

| UI step | Observed result | Finding |
|---|---|---|
| Admin → Documents → All | 17 total; 5 rows on page 1 | Admin list available for comparison. |
| Admin → Ban Giám đốc | 6 total; UI request completed 200 | Filter responds and narrows admin dataset. |
| Admin → Kỹ thuật | 1 total; UI request completed 200 | One existing Tech row identified; row text matched the ordinary user's sole unfiltered row. |
| Ordinary id 6 → Documents → All | 1 total | Sole row matches the admin Kỹ thuật-filtered row. `B03-ordinary-all-baseline.png`. |
| Ordinary id 6 → Ban Giám đốc | UI-generated department-filter request completed 200; selected chip active; same one row remained, byte-for-byte equal rendered row text to All | **B03 reproduced:** a Kỹ thuật row remains under Ban Giám đốc. No evidence of an access expansion: the row was already in the ordinary unfiltered UI result set. `B03-ordinary-bgd-filter-stale-row.png`. |
| Ordinary id 6 → Kỹ thuật | UI-generated request completed 200; 1 row remained | Consistent with the admin Tech result. |
| Reset to All | All is visibly selected and the list returned to one row in the rendered snapshot | Baseline reset appears to work for this one-row dataset; it cannot prove restoration over a larger ordinary dataset. |

QA-FIXTURE-DOC-0051 / `QA-20261022-DOCS-acceptance.txt` was searched by exact filename through the UI and was not found in active documents. Per instruction, no trashed QA docs were restored and QA32 was not used. No synthetic fixture was created.

At the time this baseline section was first written, the post-action console check was pending. The postfix run below subsequently checked page and console errors across the full B03 retest and found none; it used a fresh isolated MCP Playwright tab after the runner context had restarted.

### Follow-up evidence inventory

- `harness/reports/fixes-20261022/B03-ordinary-all-baseline.png` — ordinary id 6, All, one row.
- `harness/reports/fixes-20261022/B03-ordinary-bgd-filter-stale-row.png` — ordinary id 6, Ban Giám đốc selected, same row remains.


## Postfix live retest (2026-10-22, after 10:44:28 ICT)

Target: public `https://chatbot.coremind.io.vn`. Parent reported live backend image `miccorag-backend:20261022-desktop-b03`, health 200, and frontend unchanged (`index-BMztbSwt.js`). Fresh MCP Playwright isolated tab; viewport 1366×768. Bootstrap returned 200. Page-error and console-error listeners were attached before navigation; both result arrays were empty. All actions were normal UI clicks. Filter HTTP responses were awaited only to synchronize with UI changes; no business API was invoked directly. No records were written or modified.

| Role / UI action | Result | Verdict |
|---|---|---|
| Ordinary id 6: All | 1 active row; 1 total | Baseline result set captured. |
| Ordinary: Kỹ thuật | 1 row; identical rendered row set to All; request 200 | PASS — correct Tech row retained. |
| Ordinary: Ban Giám đốc | 0 rows; “Không tìm thấy tài liệu”; request 200 | PASS — pre-fix stale Tech row no longer appears. |
| Ordinary: reset All | 1 row; exact rendered row set restored to initial All; request 200 | PASS — reset works. |
| Admin id 5: All | 17 total; 5 on page 1 | Admin baseline. |
| Admin: Kỹ thuật | 1 total; row set exactly matches ordinary Kỹ thuật | PASS — role views agree for the existing Tech document. |
| Admin: Ban Giám đốc | 6 total; 5 on page 1; request 200 | PASS — nonempty department filter works. |
| Admin: reset All | 17 total; original first-page row set restored exactly; request 200 | PASS — reset works. |
| Ordinary permission subset | All has one Tech row; Tech filter retains only that same row; Board filter is empty; reset equals All | PASS — no row outside the ordinary unfiltered result set was revealed by these filter operations. |
| Page/console errors | `pageErrors=[]`, `consoleErrors=[]` for fresh navigation and the full B03 run | PASS — no new JavaScript or console errors observed. |

### Baseline versus candidate

- **Pre-fix (10:43):** ordinary All showed 1 row; Ban Giám đốc also showed the exact same row, which matched the admin Kỹ thuật result. B03 FAIL was reproduced.
- **Post-fix:** ordinary All=1, Kỹ thuật=1 (same row), Ban Giám đốc=0, reset=1 (exactly the All row). Admin All=17, Kỹ thuật=1, Ban Giám đốc=6, reset=17 with the original page-1 rows. B03 PASS.

### Dataset limit and evidence

Only one active document was visible in the ordinary user's unfiltered list, and it matched the admin Kỹ thuật result. This is sufficient to distinguish Kỹ thuật (one matching row) from Ban Giám đốc (zero rows) for this user's available data, but it does not exercise a multi-document ordinary result set. Admin's existing documents provided a nonempty Ban Giám đốc check. Exact-name search for DOC-0051 had already returned no active result; no trashed QA document was restored and QA32/qaToken was not used. No fixture was needed. No other bug IDs or future bug cases were tested.

Screenshots captured after the candidate became live:

- Ordinary: `harness/reports/fixes-20261022/B03-postfix-ordinary-all.png`, `B03-postfix-ordinary-tech.png`, `B03-postfix-ordinary-board.png`, `B03-postfix-ordinary-reset.png`.
- Admin: `harness/reports/fixes-20261022/B03-postfix-admin-all.png`, `B03-postfix-admin-tech.png`, `B03-postfix-admin-board.png`, `B03-postfix-admin-reset.png`.
