> **Đợt khắc phục 22/10/2026 — chỉ desktop:** Theo yêu cầu mới, B01/B02 mobile được loại khỏi đợt sửa này. Sol sửa mã, Luna kiểm tra độc lập bằng MCP Playwright. Xử lý lần lượt B03 → B11, chỉ chuyển lỗi sau khi kiểm tra đạt. B03 (lọc phòng ban) đã sửa và Luna kiểm tra PASS trên web thật. B04 (tệp rỗng) đã sửa và PASS public; B05 (tệp quá lớn) đã sửa và PASS public; B06 (lý do từ chối) đã sửa và PASS public; B07 (nhãn tri thức) đã sửa và PASS public; B08 (nút Google) đang xử lý. Số liệu NO-GO bên dưới là kết quả trước sửa. Nhật ký sửa: [qa-fixes-20261022](qa-fixes-20261022/README.md).

<!-- DESKTOP_FIXES_START -->

# Nhật ký khắc phục desktop 22/10/2026

Các ca bên dưới giữ nguyên bằng chứng trước/sau. B01/B02 mobile bỏ qua theo yêu cầu. Trạng thái hiện tại:

# Khắc phục và kiểm tra lại desktop — 22/10/2026

Đích: https://chatbot.coremind.io.vn. Sol sửa, Luna kiểm tra bằng MCP Playwright, parent triển khai có rollback. Không sửa mobile theo yêu cầu. Kết quả cũ giữ trong [hồ sơ chung](NGHIEM_THU_UI.md).

| Lỗi | Nội dung | Trạng thái |
|---|---|---|
| B01/B02 | Đăng nhập và footer mobile | Bỏ qua theo yêu cầu |
| B03 | Lọc phòng ban tài liệu | PASS live — [Sol](qa-fixes-20261022/B03-sol.md), [Luna](qa-fixes-20261022/B03-luna.md) |
| B04 | Tệp rỗng | PASS public — [Sol](qa-fixes-20261022/B04-sol.md), [Luna](qa-fixes-20261022/B04-luna.md) |
| B05 | Tệp vượt 50 MB | PASS public — [Sol](qa-fixes-20261022/B05-sol.md), [Luna](qa-fixes-20261022/B05-luna.md) |
| B06 | Lý do từ chối tài liệu | PASS public — [Sol](qa-fixes-20261022/B06-sol.md), [Luna](qa-fixes-20261022/B06-luna.md) |
| B07 | Nhãn xử lý tri thức | PASS public — [Sol](qa-fixes-20261022/B07-sol.md), [Luna](qa-fixes-20261022/B07-luna.md) |
| B08 | Nút Google không phản hồi | Đã triển khai phản hồi chưa hỗ trợ; chờ Luna xác minh |
| B09 | Quên mật khẩu không có trợ giúp | Chờ |
| B10 | URL lạ hiển thị trắng | Chờ |
| B11 | Lỗi tải tri thức hiển thị thành dữ liệu rỗng | Chờ |

Mỗi lỗi lưu bước tái hiện, expected, kết quả trước/sau, bản mã, bằng chứng và hồi quy trong Bxx-sol.md và Bxx-luna.md. Không ghi thông tin xác thực.

Các log RED/GREEN/unit/harness B04–B07 đã được giữ trong `harness/reports/fixes-20261022/`, không chỉ ở thư mục tạm. Mỗi PASS public có hash bundle và ảnh chụp trong báo cáo Luna tương ứng.



---


## Hồ sơ B03-luna

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



---


## Hồ sơ B03-sol

# B03 — Documents department filter (Sol implementation)

Ngày: 2026-10-22, ICT. Phạm vi: desktop `https://chatbot.coremind.io.vn`, chỉ B03.
Trạng thái: **candidate đã qua local regression/harness; chờ parent rollout và Luna MCP Playwright PASS**.
Không commit/reset/deploy/restart, không spawn agent, không sửa B01/B02 hoặc B04–B11.

## Baseline và root cause

Đã đọc `AGENTS.md`, `docs/qa-acceptance-20261022/sol-audit.md`, `luna-documents.md`,
và bằng chứng ROOT-DOC-DEPARTMENT trong `root-rechecks.md`.
Baseline acceptance: ordinary user phòng Kỹ thuật (dept3), DOC51
`QA-20261022-DOCS-acceptance.txt`; chọn Ban Giám đốc (dept6), request
`GET /api/documents?department_id=6` trả 200 nhưng vẫn có DOC51.
Đây là sai bộ lọc; bằng chứng ban đầu không chứng minh lộ dữ liệu ngoài quyền.

Frontend `micco-frontend/src/pages/Documents.jsx` đã đưa `selectedDeptId` vào query
`department_id`, fetch lại khi đổi chip và dùng sequence guard để loại response cũ.
Không cần đổi frontend cho root cause này.

Trong `app/api_compat/documents.py::list_documents`, query visibility/RBAC được áp dụng
cho ordinary user, nhưng điều kiện phòng ban được chọn lại bị chặn bởi
`can_read_all_knowledge(current_user)`. Vì vậy ordinary/manager bỏ qua query parameter.
Admin/directors đã được lọc theo phòng ban nên kiểm tra riêng Admin không bắt được lỗi.

Sửa thành thêm `Document.department_id == department_id` vào cùng query khi parameter
khác None, cho mọi role. Đây là phép AND với scope hiện có; giữ nguyên visibility,
uploader, approval, deleted/trash ownership và hậu kiểm `can_read_document`/workspace.
Chọn phòng khác không cấp thêm quyền đọc, cũng không ép department của user thành
department đang chọn. Public ở phòng khác vẫn xuất hiện nếu user vốn được đọc.

## Exact files changed bởi lượt B03

1. `micco-backend/backend/app/api_compat/documents.py`, quanh dòng 128–131:

   ```diff
   -    # Filter by selected department (admin only)
   -    if department_id is not None and can_read_all_knowledge(current_user):
   +    # Intersect the selected department with access scope for every role.
   +    if department_id is not None:
            stmt = stmt.where(Document.department_id == department_id)
   ```

2. `micco-backend/backend/tests/unit/test_document_department_filter.py` (mới):
   23 ca bằng HTTP route thật, JWT auth thật và SQLite async in-memory; không mock SQL,
   không gọi provider, không ghi dữ liệu production. Expected ID sets được đặt độc lập.
   Bao phủ ordinary/manager/Admin/directors, user không phòng ban, dept3/dept6/nonexistent/All,
   cross-department public/internal/private, public child trong private workspace của người khác,
   own/other pending, rejected và giao với trash ownership.
3. `docs/qa-fixes-20261022/B03-sol.md` (file này).

Các log verification nằm trong `harness/reports/` (gitignored); không sửa harness.
Các edits dirty có sẵn trong source đều giữ nguyên.

## Đối chiếu actual live baseline parent cung cấp

Baseline file:
`/tmp/micco-desktop-fixes-baseline/live-backend-app/api_compat/documents.py`.
Snapshot source trước B03: `/tmp/B03-documents-before.py`.

- Trước B03, source chỉ khác live ở **4 dòng trống chứa whitespace**, dòng source
  777/786/810/846 trong version upload. Không có khác biệt logic. Đã giữ nguyên chúng.
- Candidate so với live: một thay đổi logic điều kiện B03 ở trên, cộng 4 whitespace có sẵn.
- Đã so AST: live == pre-B03; candidate == live với đúng điều kiện B03 đã thay.
- Không sửa/copy `app/api/rag.py`; parent đã chỉ ra file đó có pending diff với live.
- `git diff --check` theo HEAD báo 4 whitespace có sẵn nói trên; diff B03 so với snapshot
  trước sửa không thêm whitespace lỗi. Không làm sạch chúng vì workspace dùng chung.

## Tests và kết quả

Venv thiếu `aiosqlite` dù `backend/requirements-dev.txt` đã có `aiosqlite==0.22.1`.
Đã cài đúng version vào `/tmp/B03-test-deps` bằng `pip --target`, không sửa venv,
requirements hay image. Các lệnh dưới dùng dependency tạm đó; nếu thư mục tạm không còn,
cần chuẩn bị lại dev dependency trước khi chạy. JWT key chỉ là fixture local không deploy.

Từ `micco-backend/backend/`:

```bash
PYTHONPATH=/tmp/B03-test-deps:. ../venv/bin/python -m pytest \
  tests/unit/test_document_department_filter.py -q --tb=short
```

**RED trước fix: 9 failed / 14 passed.** Các failure đúng lỗi filter bị bỏ qua, gồm
ordinary dept6 nhận thêm Tech DOC51/own pending/personal và trash dept6 nhận cả dept3.
Lần chạy đầu trước khi chuẩn bị dependency bị setup error thiếu aiosqlite; không tính
lần đó là RED chứng minh bug.

```bash
PYTHONPATH=/tmp/B03-test-deps:. ../venv/bin/python -m pytest \
  tests/unit/test_document_department_filter.py \
  tests/unit/test_fix_crossstack.py \
  tests/unit/test_director_knowledge_access.py \
  tests/unit/test_api_security_regressions.py -q --tb=short
```

**GREEN: 163 passed**, gồm đủ 23 ca B03. Có 3501 warning deprecation `datetime.utcnow()`
từ code hiện hữu; không sửa trong B03.

Từ repo root:

```bash
PYTHONPATH=/tmp/B03-test-deps:/home/micco/MiccoRAG-v3/micco-backend/backend \
RUN_INTEGRATION=0 RUN_RAG=0 RUN_EVAL=0 RUN_BENCH=0 RUN_E2E=0 \
bash harness/run.sh be --json --md
```

**303 passed; harness be: 1 PASS / 0 FAIL / 2 WARN, exit 0.**
WARN: chưa cài ruff và pytest-cov, nên lint/coverage chưa được chứng nhận.
Integration/RAG/eval/browser chưa chạy trong lượt implementation này.

Artifacts:

- `harness/reports/qa-fixes-20261022-b03/red.log`
- `harness/reports/qa-fixes-20261022-b03/focused.log`
- `harness/reports/qa-fixes-20261022-b03/harness.log`
- `harness/reports/20261022-104146.json`
- `harness/reports/20261022-104146.md`

## Candidate behavior và checklist Luna desktop

1. Ordinary dept3, All: DOC51 vẫn xuất hiện nếu fixture còn active/approved như baseline.
2. Tìm chính xác tên DOC51, chọn Ban Giám đốc (dept6), đợi request hoàn tất:
   200 với kết quả không chứa DOC51; UI hiện empty nếu không có match được quyền đọc.
3. Chọn Kỹ thuật (dept3): DOC51 trở lại; đổi về All giữ đúng scope cũ. Reload và thử
   table/grid, giữ search/type/category nếu đang chọn. Ghi request, selected chip và UI.
4. Dept6 có public doc được phép đọc: doc đó được phép hiện; internal/private của
   dept6 hoặc public child trong workspace không có quyền không được hiện với ordinary dept3.
5. Manager và Admin/directors: filter vẫn chọn đúng department, giữ scope/approval cũ.

Không cần fixture/auth production cho local tests. Luna cần ordinary dept3 session và
DOC51 còn tồn tại; nếu fixture đã dọn, parent cấp fixture tương đương qua kênh riêng.
Muốn chứng minh positive cross-dept public trên UI cần fixture public được quyền và
fixture restricted để đối chiếu; local regression đã bao phủ cả hai. Không xuất tokens.

## Handoff triển khai tối thiểu — parent thực hiện

Live backend do parent xác nhận: container `miccorag-production-backend-1`, image
`miccorag-backend:20261021-chatfix`. Compose hiện tại đặt app ở `/app/backend/app`,
source không được bind mount vào container nên sửa checkout chưa áp dụng cho live.

Parent tạo candidate image **FROM đúng actual live image ID/digest**, chỉ COPY:

```dockerfile
# FROM <actual live backend image ID/digest parent đã xác minh>
COPY micco-backend/backend/app/api_compat/documents.py /app/backend/app/api_compat/documents.py
```

Giữ metadata/ownership theo image live. File COPY có đúng một thay đổi logic B03 cùng
4 whitespace baseline đã nêu; không COPY toàn `app/`, không rebuild từ toàn dirty checkout,
không đưa `api/rag.py` pending vào image. Không cần DB migration, frontend build hay
thay env/auth cho B03. Parent giữ quyền chọn tag, rollout backend, readiness/health
verification và rollback về actual live baseline nếu cần.

Sau rollout, Luna dùng MCP Playwright trên desktop đích để xác nhận checklist trên.
**Sol dừng tại B03, không bắt đầu B04 hay issue khác trước parent xác nhận Luna PASS
và giao việc tiếp. Local PASS chưa phải production acceptance PASS.**



---


## Hồ sơ B04-luna

# B04 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn` public live baseline; desktop 1366×768, 100% zoom.  
Runner: isolated MCP Playwright tab. Auth initialized with private bootstrap `qaToken` for QA32 (UI header `QA2`). No app source, deployment, or business records changed.

## Status

**PASS — B04 public desktop postfix verified against `index-BtbYHPBg.js`.**

The pre-fix public baseline reproduced acceptance of a zero-byte TXT. On the live postfix bundle, picker, drop, and mixed selection all reject the empty file with a filename-specific alert and disabled Upload. Removing the empty file restores valid TXT eligibility. Upload was never clicked and no record was created.

## Baseline observations (approx. 13:45 ICT)

- Fixture: `.playwright-mcp/QA-20261022-DOCS-empty.txt` (0 B) and `.playwright-mcp/QA-20261022-DOCS-acceptance.txt` (186 B synthetic TXT).
- Picker: selecting the 0 B file showed `0 B • TXT`. With effective date `2026-10-22`, Upload was enabled and no alert was present. **B04 FAIL reproduced.**
- Drag-drop: dropping the same 0 B file onto the upload drop zone also showed `0 B • TXT`; with the valid date, Upload was enabled. **B04 FAIL reproduced through drop mode.**
- Mixed selection through picker: the zero-byte file and valid 186 B TXT appeared together. Because the zero-byte file had first been dropped, the picker appended its selection and the UI showed two empty-file entries plus the valid TXT. There was no validation alert and Upload remained enabled. The test did not submit.
- Removal recovery: removing both zero-byte entries left the valid TXT visible as `186 B • TXT`, retained the valid date, and kept Upload enabled. The valid synthetic file therefore remains selectable/eligible without uploading it.
- No upload request was issued. The Upload control was not activated; observed document requests in the session were GETs only. The modal was canceled through its Hủy button.
- Console error query: zero console errors. Page-error listener captured no errors during form interactions.

## Evidence

- `harness/reports/fixes-20261022/B04-baseline-picker-empty-valid-date.png` — empty file via picker, valid date, Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-drop-empty-valid-date.png` — empty file via drop, valid date, Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-picker-mixed.png` — empty and valid TXT files selected together; Upload enabled.
- `harness/reports/fixes-20261022/B04-baseline-picker-valid-after-empty-removal.png` — empty entries removed; valid TXT remains eligible.

## Live postfix observations (2026-10-22, approx. 13:41 ICT)

- Fresh public navigation with a cache-busting query loaded `index-BtbYHPBg.js` in the isolated MCP Playwright desktop tab. QA32 authenticated through the private bootstrap; viewport was 1366×768.
- Picker: selected the 0 B fixture and set effective date `2026-10-22`. The dialog displayed: `Tệp rỗng (0 B): QA-20261022-DOCS-empty.txt. Hãy xóa tệp rỗng và chọn tệp có nội dung trước khi tải lên.` Upload was disabled. The filename was named in the alert and the footer remained visible within the viewport.
- Drop: dropped the same 0 B fixture. It produced the filename-specific empty-file alert and disabled Upload.
- Mixed picker state: selected the 0 B fixture together with the 186 B valid TXT. The alert continued to identify the empty fixture and Upload remained disabled; both files stayed visible. Footer was visible at y=671 in the 768 px viewport.
- Recovery: removing the empty fixture cleared the alert; the valid TXT remained selected, effective date stayed `2026-10-22`, and Upload became enabled. Removing and reselecting `QA-20261022-DOCS-acceptance.txt` again left it eligible with no alert and the date retained.
- Upload was never activated. The request list showed only GET document-list requests; no empty-file or other upload request was issued. The modal was canceled after checks. Console query returned 0 errors; no page errors were captured.
- No business records were changed. No additional bug IDs were tested.

## Postfix evidence

- `harness/reports/fixes-20261022/B04-postfix-picker-empty-rejected.png` — picker rejection, filename alert, disabled Upload.
- `harness/reports/fixes-20261022/B04-postfix-drop-empty-rejected.png` — drop rejection.
- `harness/reports/fixes-20261022/B04-postfix-mixed-blocked.png` — valid + empty selected, error remains and Upload disabled.
- `harness/reports/fixes-20261022/B04-postfix-valid-after-empty-removed.png` — valid TXT remains eligible after removing the empty file.
- `harness/reports/fixes-20261022/B04-postfix-valid-reselected-eligible.png` — valid TXT removal/reselection recovery.



---


## Hồ sơ B04-sol

# B04 — client validation tệp 0 B

2026-10-22 ICT. **READY; code frozen**, chờ parent rollout và Luna live PASS.
Parent xác nhận candidate build `index-BtbYHPBg.js` và đang rollout image B04.
Không sửa B05/maxsize hay issue khác; không deploy/restart/commit/spawn agent.

## Baseline và root cause

Audit B04: picker chọn TXT 0 B, điền ngày hợp lệ thì Upload vẫn bật, không thông báo lỗi.
Parent báo Luna cũng đã tái hiện picker/drop/mixed trên baseline, không gửi upload.
Local regression render page thật tái hiện **4 FAIL trước sửa**: Upload có
`disabled=false` khi kỳ vọng phải chặn, ở cả picker/drop, single/mixed.

`stageFiles()` dùng chung cho picker và drop chỉ lọc extension. Trước sửa,
`handleUpload` và nút Upload chỉ kiểm tra số tệp/ngày/trạng thái uploading,
không xét tệp rỗng. Baseline parent `/tmp/micco-desktop-fixes-baseline/Documents.jsx`
khớp hoàn toàn snapshot trước B04 `/tmp/B04-Documents-before.jsx`.

## Exact files changed

- `micco-frontend/src/pages/Documents.jsx`: tính lỗi từ toàn bộ staged files có
  `size === 0`; thông báo tên tệp và hướng xử lý, `role="alert"`; khóa Upload và thêm
  guard vào handler; thêm accessible label cho nút xóa từng tệp.
- `micco-frontend/tests/document-empty-upload.test.mjs` (mới): 4 regression tests.
- `docs/qa-fixes-20261022/B04-sol.md` (file này).

Không thay dependencies, harness, backend hoặc các edits có sẵn. Không thêm size limit.

## Candidate behavior

- Tệp 0 B vẫn nằm trong danh sách để người dùng thấy/xóa đúng tệp. Lỗi hiện ngay
  cho cả picker và drag/drop; toàn bộ lần upload bị chặn khi còn bất kỳ tệp 0 B.
- Mixed valid+empty giữ cả hai trong danh sách, không âm thầm gửi riêng tệp valid.
  Thêm valid khác không xóa lỗi của tệp rỗng đang có.
- Xóa tệp rỗng cuối cùng tự hết lỗi. Các tệp valid còn lại upload được nếu ngày hợp lệ.
  Nếu không còn tệp, Upload vẫn khóa; chọn lại tệp có nội dung, kể cả cùng tên, sẽ phục hồi.
- B04 chỉ xác định 0 B bằng File.size, không đọc nội dung và không mở rộng sang
  tệp chỉ chứa whitespace hay validation >50 MB của B05.

## Verification đã hoàn tất — không chạy lại sau freeze

Node `/home/micco/node22/bin/node`: v22.23.2, npm 10.9.8.

Từ `micco-frontend/`, với `PATH=/home/micco/node22/bin:$PATH`:

```bash
node --test tests/document-empty-upload.test.mjs
npm run test:unit
```

Focused: **4 FAIL trước fix → 4 PASS sau fix**. Toàn bộ unit: **13 PASS / 0 FAIL**.
Tests dùng JSDOM + React thật, Vite SSR transform JSX ở middleware mode không mở
listening server. AuthContext/network là fixture; không auth production hay ghi DB.
Kiểm tra real picker/drop handlers, button state, error, không request khi invalid,
recovery sau remove/reselect và FormData chỉ chứa các tệp valid sau recovery.
Request valid được fixture trả 400 chủ động trước persistence; không upload dữ liệu thật.

Từ repo root:

```bash
PATH=/home/micco/node22/bin:$PATH RUN_E2E=0 bash harness/run.sh fe --json --md
```

**2 PASS / 0 FAIL / 1 WARN, exit 0**: eslint sạch và Vite build thành công.
WARN duy nhất: bỏ qua repo E2E; Luna sở hữu MCP Playwright acceptance.
Diff B04 không thêm whitespace lỗi.

Artifacts (gitignored): `harness/reports/qa-fixes-20261022-b04/`
gồm `red.log`, `focused.log`, `unit.log`, `harness.log`.
Harness reports: `harness/reports/20261022-134800.json` và `.md`.

## Parent/Luna handoff

Candidate Vite có sẵn `http://127.0.0.1:15175`, proxy backend 8001; không restart.
Parent sở hữu build/image rollout frontend từ candidate đã kiểm tra; B04 không cần
backend rollout, migration hoặc auth/env changes. Code đã freeze theo yêu cầu parent.

Luna desktop target `https://chatbot.coremind.io.vn`: kiểm tra picker và drop với
TXT 0 B, mixed valid+empty và ngày hợp lệ; lỗi chỉ rõ tệp, Upload disabled, không POST.
Thử thêm valid khi empty còn tồn tại, xóa empty để valid còn lại phục hồi, rồi
xóa/reselect cùng tên với nội dung hợp lệ. Không cần submit lên production để chứng minh
client validation/recovery. Ghi asset/version đang live và console errors.

Chưa tuyên bố B04 production PASS. **Dừng B04, chờ parent xác nhận Luna PASS và
giao việc tiếp trước khi làm B05.**



---


## Hồ sơ B05-luna

# B05 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`, desktop 1366×768.  
Runner: isolated MCP Playwright; QA32 authenticated through private bootstrap. Public postfix bundle verified as `index-D_MP0DTz.js` (`miccorag-frontend:20261022-desktop-b05`).

## Result

**PASS — client-side oversize validation and boundary behavior verified.** No upload was submitted, no business records changed, and no later bug IDs were tested.

## Steps and observations

1. Before rollout, on public `index-BtbYHPBg.js`, selected and dropped a local 51 MiB TXT with effective date `2026-10-22`. Both paths showed `51.0 MB • TXT`, no validation alert, and enabled Upload. This reproduced the B05 red baseline. Upload was not clicked.
2. After the parent confirmed the public B05 rollout, opened a fresh cache-busted session and verified the loaded asset `index-D_MP0DTz.js` and QA32 header (`QA2`). Picker selection of `QA-FIX-20261022-B05-51MiB.txt` (53,477,376 bytes) displayed a filename-specific alert stating the 50 MiB (52,428,800 byte) limit; Upload was disabled.
3. Dropped the same 51 MiB file through the upload drop zone. The same limit and filename alert appeared, and Upload stayed disabled.
4. Selected the valid 186 B TXT together with the 51 MiB fixture. The oversize alert remained and Upload was disabled. Removing the oversize file cleared the alert, kept the valid file and date selected, and re-enabled Upload.
5. Selected an exact 50 MiB TXT (52,428,800 bytes): no alert and Upload enabled. Selected a 50 MiB + 1 byte TXT (52,428,801 bytes): filename and byte limit appeared in the alert and Upload was disabled.
6. Quick B04 regression: the 0 B TXT still produced the empty-file filename alert and disabled Upload.

All states used valid effective date `2026-10-22`. The modal was canceled after checks. Network inspection showed only GET requests; no upload POST was issued. Console error query returned zero errors, and page-error capture was empty.

## Evidence

- Red baseline: `harness/reports/fixes-20261022/B05-baseline-picker-51MiB.png`, `B05-baseline-drop-51MiB.png`.
- Postfix: `B05-postfix-picker-51MiB-rejected.png`, `B05-postfix-drop-51MiB-rejected.png`, `B05-postfix-mixed-oversize-blocked.png`, `B05-postfix-valid-after-oversize-removed.png`, `B05-postfix-exact-50MiB-eligible.png`, `B05-postfix-50MiB-plus1-rejected.png`, `B05-postfix-B04-empty-regression.png` (all under `harness/reports/fixes-20261022/`).

The three local B05 large fixtures were deleted after testing; the existing small QA fixtures were left untouched.



---


## Hồ sơ B05-sol

# B05 — giới hạn upload phía client

2026-10-22 ICT. **READY, code final; chờ Luna public PASS.**

Root cause: picker/drop dùng chung staging nhưng không kiểm tra File.size; submit
và disabled guard chỉ chặn tệp 0 B/ngày thiếu. Backend compat thực tế dùng
`MAX_FILE_SIZE = 50 * 1024 * 1024` và từ chối khi `len(content) > MAX_FILE_SIZE`:
ngưỡng hợp lệ tối đa **52.428.800 byte = 50 MiB mỗi tệp**, inclusive.

Files thay đổi:

- `micco-frontend/src/pages/Documents.jsx`: thêm đúng ngưỡng backend, copy MiB/số byte;
  lỗi chứa tên và kích thước thực từng tệp quá lớn; kết hợp lỗi 0 B hiện hữu;
  khóa Upload và guard handler khi còn tệp invalid.
- `micco-frontend/tests/document-empty-upload.test.mjs`: thêm 8 behavioral tests,
  giữ nguyên 4 test B04.
- Report này. Snapshot trước sửa: `/tmp/B05-Documents-before.jsx` và
  `/tmp/B05-tests-before.mjs`; các edits cũ được giữ nguyên.

Candidate giữ tệp invalid trong danh sách; mixed không gửi riêng valid.
Thêm valid không xóa lỗi. Xóa oversized cuối cùng phục hồi nếu còn valid và ngày
đúng; nếu còn empty thì vẫn chặn. Tổng nhiều tệp vượt 50 MiB vẫn được chọn khi
mỗi tệp hợp lệ; không áp sai giới hạn cho cả batch.

Verification Node22: RED **8 FAIL / 4 PASS**; GREEN focused **12 PASS**;
unit **21 PASS**; fe harness **2 PASS / 0 FAIL / 1 WARN**, eslint/build đạt.
WARN là bỏ qua E2E dành cho Luna. Tests render page/handlers thật, File có size thật
ở đúng ngưỡng, +1 byte và 51 MiB; network fixture không ghi dữ liệu thật.
Không submit oversized lên production; không đổi backend, deploy hay restart.

Luna desktop: picker/drop exact-limit enabled; +1 byte/51 MiB single/mixed disabled,
lỗi tên/kích thước/max rõ; remove/reselect recovery và 0 B vẫn bị chặn. Parent sở hữu
rollout public static và container. Không làm issue tiếp theo trước parent đóng B05.

```bash
# micco-frontend/
export PATH=/home/micco/node22/bin:$PATH
node --test tests/document-empty-upload.test.mjs
npm run test:unit
# repo root
RUN_E2E=0 bash harness/run.sh fe --json --md
```

Logs: `harness/reports/qa-fixes-20261022-b05/{red,focused,unit,harness}.log`.
Harness: `harness/reports/20261022-135851.{json,md}`.



---


## Hồ sơ B06-luna

# B06 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`, desktop 1366×768.  
Runner: isolated MCP Playwright contexts. QA32 owner and manager16 (TĐA, Kỹ thuật) sessions were initialized from the private bootstrap; credentials were not printed or stored.

## Fixture and red baseline

**Fixture ready for Sol:** document ID `DOC-0078` (UI route `/documents/78`), filename `QA-FIX-20261022-B06-rejection.txt`. Created exactly once through the QA32 upload UI as a 133 B synthetic TXT with `Nội bộ`, department Kỹ thuật, effective 2026-10-22 through 2026-10-29. Content explicitly marks it QA-only and references B06-20261022. No preexisting or trashed document was opened for mutation.

Manager16/TĐA opened the approvals UI, previewed this only pending document, then rejected it with the specified reason: `QA B06: Thiếu nội dung hướng dẫn cần bổ sung.` The UI returned success from the UI-triggered rejection action for document 78; the manager queue then showed no items awaiting approval. No approval action was clicked.

After reloading the owner detail, the status displayed `Từ chối`, but the specified reason was not visible in the detail or activity text. This reproduces B06’s red baseline. The synthetic fixture remains active and rejected for postfix verification; do not clean it up until parent approval.

## Evidence

- `harness/reports/fixes-20261022/B06-owner-upload-ready.png` — file, dates, and Internal visibility prepared before the single UI upload.
- `harness/reports/fixes-20261022/B06-manager-pending-preview.png` — manager queue with the QA fixture pending review.
- `harness/reports/fixes-20261022/B06-manager-rejection-reason-ready.png` — requested reason entered in the manager rejection flow before submission.
- `harness/reports/fixes-20261022/B06-manager-rejected-queue.png` — manager queue after rejection; no pending documents.
- `harness/reports/fixes-20261022/B06-owner-rejected-after-reload-baseline.png` — owner reload shows `Từ chối`, without the rejection reason.

## Postfix status

**PASS — verified after parent-confirmed public rollout.** A new owner context loaded the public bundle `index-Cezh4tO7.js` and opened `/documents/78`. After the first reload, owner detail displayed the exact reason `QA B06: Thiếu nội dung hướng dẫn cần bổ sung.`; after a second reload, the same reason remained visible exactly once. Status remained `Từ chối`. The activity log said `Hệ thống đã từ chối tài liệu này`; no pending-approval activity was present.

For the normal-document guard, the owner opened existing approved document `DOC-0020` (`Quy trình an toàn trong sản xuất vật liệu nổ công nghiệp.pdf`) read-only. It showed `Đã phê duyệt`, had no `Lý do từ chối` panel, and did not contain the synthetic B06 reason. The test run captured zero page errors and zero console errors across owner reloads and the read-only normal-document navigation. No approval or additional upload was performed.

Postfix screenshot evidence: `harness/reports/fixes-20261022/B06-owner-rejected-after-reload-postfix.png` and `B06-owner-normal-approved-no-reason.png`. The manager16 review/reject screenshots and owner red-baseline screenshot above preserve the setup and before/after state. DOC-0078 remains active and rejected; cleanup is pending parent approval and was not attempted.



---


## Hồ sơ B06-sol

# B06 — owner thấy lý do từ chối

2026-10-22 ICT. **READY, frontend-only; chờ Luna public PASS.**

Baseline audit/Luna: DOC54 rejected nhưng owner detail/reload không thấy reason;
DOC54 hiện trong trash. Parent/Luna sở hữu fixture mới DOC78; Sol không mutation
production, không dùng hay cleanup các DOC55–77.

Root cause: reject đã persist `approval_note` và audit reason. Compat detail serializer
đã trả note sau kiểm tra quyền. `DocumentView` không render note; activity còn coi
mọi trạng thái chưa approved là pending. SQL test xác nhận persistence/API đúng,
không cần sửa backend hay copy `api/rag.py` pending.

Files thay đổi:

- `micco-frontend/src/pages/DocumentView.jsx`: section “Lý do từ chối” chỉ cho rejected,
  giữ newline/wrap, render text an toàn; fallback rõ cho legacy thiếu note.
  Activity hiển thị rejected, không dùng ngày upload làm thời điểm từ chối.
- `micco-frontend/tests/document-rejection-reason.test.mjs` (mới): owner/reload,
  missing/empty note, non-rejected, HTML/long text và denied detail.
- `micco-backend/backend/tests/unit/test_document_rejection_reason.py` (mới): reject,
  expire/reload SQL, owner detail/note/audit, 403/401 ngoài quyền.
- Report này. Giữ nguyên edits có sẵn; snapshot `/tmp/B06-DocumentView-before.jsx`.

Checks: frontend RED **5 FAIL / 3 PASS**, GREEN **8 PASS**; toàn unit **29 PASS**.
Backend characterization **1 PASS**, 28 deprecation warnings hiện hữu.
Node22 frontend harness **2 PASS / 0 FAIL / 1 WARN**: eslint/build đạt, E2E dành cho Luna.
Không thay backend source, không deploy/restart/spawn agent; không làm B07.

```bash
# micco-frontend/, Node22
export PATH=/home/micco/node22/bin:$PATH
node --test tests/document-rejection-reason.test.mjs
npm run test:unit
# repo root
RUN_E2E=0 bash harness/run.sh fe --json --md
# micco-backend/backend/ (aiosqlite dev dependency ở /tmp như B03)
PYTHONPATH=/tmp/B03-test-deps:. ../venv/bin/python -m pytest \
  tests/unit/test_document_rejection_reason.py -q --tb=short
```

Logs: `harness/reports/qa-fixes-20261022-b06/{red,focused,backend,unit,harness}.log`;
harness `20261022-140543.{json,md}`.

Parent rollout frontend public static + container. Luna dùng fixture do mình tạo:
owner detail/reload phải thấy đúng reason, activity rejected; approved/pending bình thường,
không cấp thêm quyền đọc cho user khác. Sol chờ parent đóng B06 trước issue tiếp theo.



---


## Hồ sơ B07-luna

# B07 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: public desktop app, 1366×768.  
Runner: isolated MCP Playwright contexts. QA32 owner and manager16 (TĐA, Kỹ thuật) sessions were initialized from the private bootstrap; credentials were not printed or stored.

## Fixture and red baseline

Created exactly one authorized synthetic knowledge item through the QA32 UI:

- Title: `QA-FIX-20261022-B07-knowledge`
- Knowledge ID: **5**
- Visibility: `Nội bộ`; owner is QA Acceptance 20261022 in Kỹ thuật
- Effective dates: 2026-10-22 through 2026-10-29
- Content: `Kiểm thử QA B07. Mã tham chiếu B07-20261022. Không phải nội dung nghiệp vụ.`

The ordinary UI submitted it for approval. The UI-generated POST response was HTTP 201 with `id=5`, `approval_status=pending_dept`, `status=Pending`, and `ingest_status=pending`. The initial owner card showed `Chờ duyệt cấp phòng` and `Chờ xử lý`.

Manager16/TĐA switched to the Tri thức approval tab, previewed this only pending knowledge item, confirmed the same dates, and approved it. The UI-generated approval response was HTTP 200 with `message=Đã phê duyệt tri thức` and `id=5`. No other item was approved. The approval response did not include a generated document ID; the UI-generated knowledge list response also had no `document_id` or `source_document_id`, so no generated document ID is known.

After owner reload, the card still displayed `Chờ xử lý`. In the response generated by that UI reload, the matching row had `approval_status=approved`, `status=Active`, and `ingest_status=indexed`. This reproduces B07 without treating the approval as failed: approval and ingestion are complete in the UI data while the card label is stale. No RAG question or existing-knowledge edit was performed.

## Evidence

- `harness/reports/fixes-20261022/B07-owner-submit-ready.png` — authorized metadata/content before submission.
- `B07-owner-submitted-pending.png` — owner card after ordinary submission.
- `B07-manager-knowledge-pending.png`, `B07-manager-approval-confirm.png`, `B07-manager-approval-done.png` — manager preview queue, date confirmation, and completed approval.
- `B07-owner-approved-reloaded-baseline.png` — red baseline card still says `Chờ xử lý` after reload.

## Postfix status

**PASS — public B07 bundle verified.** A cache-busted owner reload loaded `index-D8tIQKNf.js`. In grid view, the single card for knowledge ID 5 displayed `Hoạt động`, `Nội bộ`, and `Đã đồng bộ`. Switching to list view preserved the same correct labels and a single matching title; switching back to grid preserved them again. The card no longer says `Chờ xử lý`.

For approval and ingest distinction, the UI-generated knowledge list response for ID 5 still reported `approval_status=approved`, `status=Active`, and `ingest_status=indexed`; this confirms the status text reflects indexing separately from approval and active state. The matching card title count was 1 in both grid and list views. In a fresh manager16 UI context, the Tri thức approval queue was empty and showed `Không có tri thức chờ phê duyệt`.

No JavaScript page errors or console errors were captured during the owner reload, grid/list switches, or manager queue check. No document was uploaded, no existing knowledge was edited, and no RAG question was asked. The parent’s supplemental database correlation identifies generated document `DOC-0079` (`QA-FIX-20261022-B07-knowledge.md`, workspace 8); the UI-generated knowledge responses themselves exposed knowledge ID 5 and status fields, but no document ID. Knowledge ID 5 and DOC-0079 remain active for the later RAG regression; no cleanup was attempted.

Postfix evidence: `harness/reports/fixes-20261022/B07-owner-grid-postfix.png`, `B07-owner-list-postfix.png`, and `B07-manager-queue-empty-postfix.png`. The red baseline remains at `B07-owner-approved-reloaded-baseline.png` for comparison with its stale `Chờ xử lý` label.



---


## Hồ sơ B07-sol

# B07 — knowledge card ingestion status

2026-10-22 ICT. **READY, frontend-only; chờ Luna public PASS.**

Baseline FINAL `luna-knowledge.md`: entry3 sau manager approval có
`approval_status=approved`, `ingest_status=indexed`, `status=Active`, nhưng card sau
reload vẫn “Chờ xử lý”. Entry cũ đã trashed; Luna sở hữu fixture mới. Sol không
mutation dữ liệu production.

Root cause: `nexus_rag_service.py` ghi ingestion hoàn tất là `indexed`;
`api_compat/knowledge.py::_to_response` serialize đúng nguyên giá trị.
`KnowledgeCard` chỉ map `completed`, nên `indexed` rơi vào fallback pending.
Không phải approval chưa thành công hay backend chưa persist.

Files thay đổi:

- `micco-frontend/src/components/knowledge/KnowledgeCard.jsx`: thêm đúng một dòng
  `indexed` → icon xanh và “Đã đồng bộ”, tương thích alias `completed` hiện hữu.
- `micco-frontend/tests/knowledge-ingest-status.test.mjs` (mới): 10 matrix cases
  render card thật và một ca fresh page loads + grid/list bằng API fixture.
- Report này. Giữ nguyên edits cũ; snapshot `/tmp/B07-KnowledgeCard-before.jsx`.

Approval và ingestion vẫn độc lập: approved không tự thành completed; pending,
processing, failed và pending approval giữ nhãn tương ứng. Unknown/null không hiện
“Đã đồng bộ”. Không sửa status filter, polling, permission, backend hay B08/B11.

Verification: RED **2 FAIL / 9 PASS**, GREEN focused **11 PASS**; toàn unit **40 PASS**.
Node22 fe harness **2 PASS / 0 FAIL / 1 WARN**, eslint/build đạt, WARN bỏ qua E2E
dành cho Luna. Source Knowledge page/backend serializer không đổi.

```bash
# micco-frontend/
export PATH=/home/micco/node22/bin:$PATH
node --test tests/knowledge-ingest-status.test.mjs
npm run test:unit
# repo root
RUN_E2E=0 bash harness/run.sh fe --json --md
```

Logs: `harness/reports/qa-fixes-20261022-b07/{red,focused,unit,harness}.log`;
harness `20261022-141154.{json,md}`.

Parent rollout frontend public static + container; không cần backend image.
Luna kiểm tra fixture own sau manager approval/indexing: reload card ở grid/list
phải “Đã đồng bộ” đúng khi API indexed; pending/failed không được giả completed.
Chưa tuyên bố production PASS; chờ parent đóng B07 trước B08.



---


## Hồ sơ B08-luna

# B08 — Luna desktop QA

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: public login page, desktop 1366×768.  
Runner: isolated MCP Playwright guest context; no auth token or credentials entered.

## Red baseline

Public asset at baseline: `index-D8tIQKNf.js`. Before clicking **Đăng nhập với Google**, the guest page was at `/login?qa-fix=B08-red...`, showed the login/register controls and email/password fields, and had no `docvault_token`. After one normal UI click, URL and visible text were unchanged. No auth-related request, popup, external redirect, token, or cookie change was observed. The Google domain and likely app Google-auth endpoints were guarded by route interception in the test context; no interception fired. Page and console error captures were empty.

This reproduces the dead-control baseline. The empty guest form remains usable; no credential was entered and no authentication was attempted. No email or message was sent.

Evidence: `harness/reports/fixes-20261022/B08-baseline-login-before.png` and `B08-baseline-login-after-google.png`.

## Postfix status

Waiting for parent-confirmed public B08 rollout. In a fresh guest context, verify both Google controls (login and registration) provide clear feedback or a safe OAuth handoff without completing external login. Check keyboard Enter with empty form fields, confirm email/password and registration fields remain usable, and verify Google clicks do not create an app auth request, token, or session. Do not navigate to Google or enter real credentials. Do not test B09 or other cases.



---


## Hồ sơ B08-sol

# B08 — Google login feedback

2026-10-22 ICT. **READY, frontend-only; chờ Luna public PASS.**

Đã kiểm tra backend đang dùng: compat auth chỉ có departments/register/login/me/avatar;
không tìm thấy OAuth Google route, callback, config hay OAuth library. Các Google
imports hiện tại là Gemini. Route frontend `/login` dùng `AuthPage`, không dùng
legacy `Login.jsx`. Nút Google trong SignInForm chưa có handler nên không phản hồi.

Theo tiêu chí audit, candidate báo rõ:
“Đăng nhập bằng Google chưa được cấu hình. Vui lòng sử dụng email và mật khẩu để đăng nhập.”
Thông báo `role="status"`, ID riêng bằng `useId`, button liên kết `aria-describedby`.
Giữ native `type="button"`, focus được, không submit form, không gọi auth/network hay
điều hướng. Email/password đã nhập được giữ nguyên; login lỗi và retry thành công
tiếp tục hoạt động. Không tạo OAuth integration, yêu cầu credentials hay gửi thông tin
ra ngoài. B09 chưa sửa.

Files thay đổi:

- `micco-frontend/src/pages/AuthPage.jsx`: state/feedback riêng cho Google sign-in.
- `micco-frontend/tests/auth-google-unavailable.test.mjs` (mới): render AuthPage thật,
  activation/status, focus/association/repeated activation, no fake authentication,
  giữ inputs và normal login failure/success recovery.
- Report này. Snapshot trước sửa `/tmp/B08-AuthPage-before.jsx`; giữ nguyên edits cũ.

Verification: RED **2 FAIL / 1 PASS**, GREEN focused **3 PASS**; unit **43 PASS**.
Node22 fe harness **2 PASS / 0 FAIL / 1 WARN**, eslint/build đạt. WARN là bỏ qua E2E.
JSDOM kiểm tra native focus/click; Enter/Space thật dành cho Luna, không tuyên bố
đã kiểm browser keyboard. Không deploy/restart/spawn agent.

```bash
# micco-frontend/
export PATH=/home/micco/node22/bin:$PATH
node --test tests/auth-google-unavailable.test.mjs
npm run test:unit
# repo root
RUN_E2E=0 bash harness/run.sh fe --json --md
```

Logs: `harness/reports/qa-fixes-20261022-b08/{red,focused,unit,harness}.log`;
harness `20261022-141956.{json,md}`.

Parent rollout frontend static + container. Luna desktop: click và Tab/Enter/Space
Google, đọc status, không redirect/fake success; normal email/password vẫn dùng được.
Sol chờ parent đóng B08 trước B09.


<!-- DESKTOP_FIXES_END -->


---
# Hồ sơ kiểm tra trước sửa (lưu đối chiếu)


# Kịch bản nghiệm thu giao diện miccoRAG

- Địa chỉ duy nhất: https://chatbot.coremind.io.vn
- Lượt kiểm tra: 22/10/2026, múi giờ Asia/Ho_Chi_Minh.
- Kết luận cuối: **NO-GO**. 11 issue đã xác nhận: **2 S1 + 9 S2**. Ma trận 35 tiêu chí: **6 PASS / 9 FAIL / 19 PARTIAL / 1 NOT_RUN**. Không có thay đổi mã hoặc triển khai sửa lỗi trong đợt này.
- Công cụ thực hiện: MCP Playwright; Luna kiểm thử, Sol đặt tiêu chí và kiểm tra bằng chứng.
- Tài khoản: nhân viên QA riêng, quản lý cùng phòng ban và admin. Không ghi mật khẩu, JWT hoặc cookie vào tài liệu.

## Cách chạy lại

1. Chuẩn bị tài khoản nhân viên thử riêng, quản lý cùng phòng ban, tài khoản khác phòng ban và admin. Không dùng quyền admin thay cho kiểm thử nhân viên.
2. Mở https://chatbot.coremind.io.vn bằng phiên trình duyệt sạch. Đăng nhập bằng giao diện cho ca kiểm tra đăng nhập; phiên khởi tạo bằng token chỉ chứng minh khôi phục phiên/quyền, không chứng minh đăng nhập mật khẩu.
3. Chạy các ca bên dưới theo thứ tự. Ghi thời điểm, vai trò, trình duyệt, kích thước và mức thu phóng. Mỗi ca phải có kết quả thực tế và bằng chứng.
4. Dùng dữ liệu tổng hợp có tiền tố `QA-<ngày>-<nhóm>-`; lưu ID và dọn đúng dữ liệu do ca kiểm tra tạo. Không duyệt, sửa hoặc xóa hồ sơ nghiệp vụ sẵn có.
5. Thử giao diện máy tính và điện thoại; phân biệt thu nhỏ kích thước cửa sổ, mô phỏng thiết bị có cảm ứng, phóng to trang và điện thoại thật.
6. Sau ca đăng xuất, thử Back và tải lại trang bảo vệ. Sau ca ghi dữ liệu, tải lại trang để xác nhận dữ liệu đã lưu.
7. Nếu một ca lỗi, ghi bước tái hiện và ảnh trước khi chuyển tiếp; sửa lỗi phải được kiểm thử lại trên bản đang phục vụ ở URL trên.

## Quy ước kết quả

| Trạng thái | Ý nghĩa |
|---|---|
| PASS | Đã thao tác giao diện, quan sát đủ kết quả mong đợi và có bằng chứng. |
| FAIL | Có sai lệch tái hiện được giữa kỳ vọng và hành vi thực tế. |
| BLOCKED | Có phụ thuộc hoặc môi trường khiến không thể hoàn tất ca. |
| NOT_RUN | Chưa thực hiện; không được tính PASS. |
| N/A | Không thuộc phạm vi sản phẩm đã thống nhất; phải ghi lý do. |

Một trang tải được không đồng nghĩa mọi chức năng của trang đã đạt. Không dùng số ca PASS để che ca quan trọng chưa chạy. Không kết luận không còn lỗi chỉ từ một lượt kiểm thử.

## Chuẩn bị bộ kiểm thử nhiều agent

- MCP Playwright cần `--isolated` cho mỗi tiến trình; nếu dùng hồ sơ mặc định đồng thời có thể gặp `Browser is already in use`. Đây là lỗi bộ kiểm thử, không phải lỗi ứng dụng.
- Mỗi agent sử dụng browser context/page riêng và tên đánh dấu riêng, không điều hướng hoặc đóng tab của agent khác.
- Thu thập snapshot, ảnh, lỗi console và trạng thái request khi cần; không xuất header xác thực hoặc nội dung chứa bí mật.
- Đợt này có hai lượt đầu bị khóa hồ sơ; phải chạy lại trước khi tính kết quả.

## Mẫu ghi từng ca

| ID | Vai trò / thiết bị | Điều kiện | Bước thực hiện | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bằng chứng / lỗi / dọn dữ liệu |
|---|---|---|---|---|---|---|---|
| Ví dụ | Nhân viên / điện thoại | Đã đăng nhập | 1. Mở Tài liệu. 2. Chọn tệp QA. 3. Nhập ngày hiệu lực. | Nút tải lên hiển thị và được bật. | Điền sau khi kiểm tra. | NOT_RUN | Điền đường dẫn ảnh và ID dữ liệu. |


## Bản triển khai đã kiểm tra

- Frontend asset quan sát trên public URL: `/assets/index-BMztbSwt.js`.
- Image frontend: `miccorag-frontend:20260930-e16c7ae`; backend: `miccorag-backend:20261021-chatfix`.
- Browser: Chromium/HeadlessChrome155; có mô phỏng cảm ứng/isMobile và nhiều viewport. Chưa có bằng chứng từ Safari/iPhone/Android thật.
- Bốn nhóm Luna: auth/navigation/mobile; documents/approval/status; chat/expert/graph; knowledge/workspace. Model `gpt-6-luna`, reasoning medium. Sol đặt 35 tiêu chí và audit bằng chứng bằng `gpt-6.1-sol`, reasoning medium.
- Hai lượt đầu auth/docs bị khóa profile MCP trước khi truy cập trang; đã chạy lại với `--isolated`. Không tính các lượt bị chặn đó là PASS ứng dụng.
- Tài khoản QA đã được tạo bằng Admin UI; đăng nhập mật khẩu thật được nhóm auth và parent xác minh. Phiên manager/admin được khởi tạo ngắn hạn từ userDB chỉ dùng cho các ca có quyền tương ứng.
- Đã thử cùng một fixture: upload DOC51 → manager duyệt → indexed, 1 chunk → câu hỏi mã tham chiếu → câu trả lời đúng → citation mở đúng nguồn. File QA được giữ trong lúc Sol kiểm tra và đã được chuyển vào thùng rác sau khi audit hoàn tất.
- Không có thay đổi mã ứng dụng hoặc triển khai trong lượt kiểm thử này. Lỗi đã phát hiện chưa được coi là đã sửa.

## Kết luận kiểm tra chéo quan trọng

- Thông báo đăng nhập sai **có hiển thị** ngoài thẻ form; FAIL AUTH-03 ban đầu của Luna đã bị parent bác bỏ bằng UI thật.
- Sắp xếp tài liệu **có hoạt động**: parent kiểm tra18 tên qua 4 trang Admin, thứ tự theo tên đúng và nút chuyển đổi thay đổi thứ tự. FAIL Sort của Luna trên bộ dữ liệu 2 tên có cùng thứ tự là chưa đủ cơ sở.
- Phiên bản V2 còn chờ duyệt trong khi V1 hiện tại là hành vi có chủ đích; cập nhật tri thức qua PUT có thể tạo phiên bản kế tiếp, không tự kết luận tạo trùng.
- Lỗi mobile login 100% bị lớp trang trí che và hộp thoại workspace 360×640 có footer ngoài màn hình đã được parent tái hiện độc lập.
- Tệp 0 B/>50 MB mới kiểm tra điều khiển và xác thực khi chọn file; không suy ra backend chấp nhận tệp không hợp lệ từ việc nút được bật. Không gửi tệp 51 MB lên production.
- Các phép thử 503 là mô phỏng lỗi riêng trong browser QA, không phải bằng chứng server production tự phát 503.


## Dữ liệu mẫu và tham số cho lần chạy sau

1. Đặt D là ngày chạy thực tế, E là D + 7 ngày. Dùng D/E thay cho ngày cố định trong các kết quả lịch sử bên dưới. Không tái sử dụng ngày hết hiệu lực đã qua rồi kết luận upload/RAG lỗi.
2. Tạo tài khoản QA mới hoặc kích hoạt lại tài khoản QA qua admin và đặt mật khẩu riêng bằng kênh phù hợp. Không có mật khẩu/token trong file này; mật khẩu DB chỉ là hash.
3. Chuẩn bị file UTF-8 `QA-<ngày>-DOCS-acceptance.txt` với nội dung sau; thay mã tham chiếu theo ngày nếu cần rồi dùng đúng mã đó làm expected của câu hỏi chat.

```text
Tài liệu kiểm thử tổng hợp QA-20261022-DOCS.
Nội dung chỉ dùng để kiểm thử giao diện và quy trình phê duyệt.
Mã tham chiếu: DOCS-ACCEPTANCE-20261022-01.
```

4. Câu hỏi kiểm tra: “Theo tài liệu <tên tệp vừa tải>, mã tham chiếu là gì?” Expected: đúng mã tham chiếu trong tệp, citation mở chính tài liệu vừa được duyệt/indexed. Ghi ID thật; không mặc định DOC51 tồn tại ở lần sau.
5. Tệp phiên bản2: đổi một dòng và thêm mã `VERSION-2`, giữ liên kết qua luồng Phiên bản mới. Candidate chờ duyệt chưa được tính là phiên bản đang dùng.
6. Tệp âm tính: TXT rỗng0B; CSV nhỏ không hỗ trợ; TXT51MB chỉ chọn để kiểm tra validation phía trình duyệt, không upload file lớn thật lên production. Tên dài và hai TXT nhỏ để kiểm tra danh sách tệp/mobile.
7. Tạo tri thức và workspace riêng với tiền tố QA theo ngày; ghi rõ personal/private so với Nội bộ/phòng ban. Dùng người duyệt cùng phòng ban cho fixture cần duyệt. Không duyệt hồ sơ thật của người khác.
8. Khi kết thúc: xóa lịch sử chat QA, chuyển các fixture QA vào thùng rác và vô hiệu hóa tài khoản QA nếu không còn sử dụng; không xóa nhật ký audit. Ghi rõ dữ liệu còn lưu theo chính sách30ngày.


## Audit cập nhật cuối — ưu tiên hơn kết quả cũ

### Sol — phụ lục DELTA cuối, 22/10/2026

**NO-GO giữ nguyên. 35 ca chuẩn: 6 PASS / 9 FAIL / 19 PARTIAL / 1 NOT_RUN (A07); tổng 35.** Có **11 issue được chấp nhận: 2 S1 + 9 S2**, chưa có bằng chứng sửa lỗi. B01 overlay mobile 390×844 ở 100% và B02 footer workspace 360×640 vẫn chặn luồng. Không quan sát S0 trong phạm vi đã chạy; không bảo đảm không còn lỗi.

Phạm vi: đọc lại `luna-chat.md` bản cập nhật, đối chiếu `criteria.md`, `sol-audit.md` và xem trực tiếp ba ảnh mới bên dưới. Chỉ ghi phụ lục này; giữ nguyên nội dung và timestamp audit gốc. Không chạy lại sáu kiểm tra độc lập, không hỏi LLM, không thao tác UI/API hoặc sửa nguồn/deploy.

#### Ma trận 35 ca — chỉ các dòng thay đổi

Các dòng khác kế thừa audit gốc; biến thể PASS không tự nâng cả ID chuẩn thành PASS.

| ID | Trước → sau | Bằng chứng bổ sung được chấp nhận | Phần chưa đủ |
|---|---|---|---|
| C04 | PARTIAL → PARTIAL | C04a–c đã có reload, Hủy/xóa và cách ly user. C04d báo cáo đăng nhập bằng form trong context không inject token, gửi câu QA51, đổi KB Kỹ thuật → Default Workspace → KB Kỹ thuật, logout rồi login lại; lịch sử còn. | Chưa thử đổi nhanh khi request cũ đang chạy, race/ghi đè lịch sử. Ảnh tĩnh không chứng minh toàn chuỗi chuyển trạng thái. |
| C05 | NOT_RUN → PARTIAL | Ordinary không thấy mode/system prompt; Admin có Hybrid/Vector only/Graph only, chọn Vector rồi trả Hybrid, không gửi câu hỏi. Abort request chat trong browser làm hiện lỗi, gợi ý thử lại và dừng loading; báo cáo ghi composer dùng được. | Chưa so đầu ra retrieval giữa mode; chưa bấm retry và xác nhận hoàn tất. Abort trước backend chưa kiểm chứng ngắt giữa stream đang trả dữ liệu. Chưa chứng minh loại trừ tài liệu pending/khác workspace. |

#### Đối chiếu artifact mới

Tất cả ảnh ở `harness/reports/acceptance-20261022/`.

- Đã xem [luna-c04-workspace-a-return.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-a-return.png>) và [luna-c04-login-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login-history.png>): đều thấy QA2, KB Kỹ thuật, câu QA51, đáp án đúng mã và citation `[p8sc]`. Hai ảnh có cùng nội dung byte; tự chúng không phân biệt thời điểm trước/sau login. Chấp nhận chuỗi thao tác theo báo cáo Luna, không coi ảnh là bằng chứng độc lập đầy đủ.
- Đã xem [luna-c05-aborted-stream.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-aborted-stream.png>): thấy `Failed to fetch` và “Đưa câu hỏi vào ô nhập để thử lại”, không có đáp án hoàn tất giả. Ảnh không tự chứng minh composer có thể gửi thành công; phần này dựa trên quan sát worker và chưa có retry hoàn tất.
- Artifact bổ trợ được báo cáo: [luna-c04-login.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login.png>), [luna-c04-seed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-seed.png>), [luna-c04-workspace-b.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-b.png>), [luna-c04-logout.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-logout.png>), [luna-c05-admin-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-admin-mode.png>), [luna-c04-c05-cleanup.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-c05-cleanup.png>). Chưa xem trực tiếp các ảnh này trong lượt DELTA.

#### Điều kiện còn lại

Tổng chat trả phí được worker báo là **7**; thông điệp fault injection bị abort trước mạng/backend, không phải một truy vấn LLM hay outage production. Worker báo đã xóa riêng chat QA, reload xác nhận và đóng context; phụ lục không xác minh cleanup fixture/account do parent phụ trách.

Trước GO vẫn cần sửa/retest hai S1, hoàn tất các khoảng trống C04/C05 trên và D08/D09/D10/K05 cùng các PARTIAL khác hoặc ngoại lệ được người nghiệm thu chấp nhận. A07 vẫn NOT_RUN. Không thêm issue cho Expert no-match; giữ các kết luận bác bỏ login-error/sort và đánh giá version pending của audit gốc. Parent cập nhật một tài liệu dùng lại `docs/NGHIEM_THU_UI.md` theo DELTA này, không thay timestamp audit cũ.



## Audit đầy đủ 35 ID — đọc cùng phụ lục cập nhật

### Sol — audit độc lập cuối, 22/10/2026

**Kết luận: NO-GO cho nghiệm thu đầy đủ ngày 23/10.** Có 2 lỗi S1 chặn thao tác cảm ứng ở viewport đã kiểm tra; đồng thời còn thiếu bằng chứng trên history, stream lỗi, chia sẻ/quyền tải trực tiếp và vòng đời phiên bản. Không phát hiện S0 trong phạm vi thực thi; điều này không chứng nhận toàn bộ hệ thống không có lỗi hoặc không có lỗ hổng.

**35 ca chuẩn: 6 PASS / 9 FAIL / 18 PARTIAL / 2 NOT_RUN.** Đây là số ID chuẩn duy nhất, không cộng các dòng biến thể của Luna/parent. FAIL nghĩa là có ít nhất một biến thể sai; PARTIAL nghĩa là đã chạy một phần nhưng chưa đủ toàn bộ tiêu chí. Một lỗi có thể ảnh hưởng nhiều ID, không nhân thành nhiều bug. Có **11 issue được chấp nhận: 2 S1 + 9 S2**; Google và quên mật khẩu là issue bổ sung của UI hiện hữu, không thêm ID vào mẫu số 35. Không có ngoại lệ S2 nào được người nghiệm thu phê chuẩn trong hồ sơ này.

Đích: https://chatbot.coremind.io.vn. Audit kết thúc khoảng 10:20 ICT. Asset trực tiếp được Sol thấy: `/assets/index-BMztbSwt.js`; image parent ghi nhận: frontend `miccorag-frontend:20260930-e16c7ae`, backend `miccorag-backend:20261021-chatfix`. Các kết quả chỉ áp dụng bản này. Đã đọc lại báo cáo knowledge bản FINAL lúc 10:17; nguồn gồm criteria, bốn báo cáo Luna, root-rechecks và common file `docs/NGHIEM_THU_UI.md`.

#### Phương pháp và kiểm tra độc lập

MCP Playwright `browser_run_code_unsafe`, context/page riêng, marker `qa-sol-audit`; không điều hướng/click/đóng default page. Bootstrap chỉ khởi tạo phiên ordinary; không xuất hay lưu thông tin xác thực. Không tạo/sửa/xóa dữ liệu, không hỏi LLM, không sửa nguồn/deploy/commit. Chỉ file audit này được ghi. Context riêng đã đóng và route fault injection đã tháo.

| Kiểm tra | Role / device | Thao tác và bằng chứng UI trực tiếp | Kết quả |
|---|---|---|---|
| SOL-01 | Khách, 390×844, isMobile/touch, DPR2, zoom100% | Mở `/login`; click Đăng nhập timeout 2.5s. Nút x40/y446/w310/h48; elementFromPoint ở giữa là DIV vòng tròn của overlay z20, không thuộc nút; visualViewport.scale=1. Không cần gửi credentials để chứng minh interception. | Xác nhận B01. |
| SOL-02 | Ordinary, cùng context, 360×640 | Workspace → Tạo mới; Hủy ở y658.5..704.5 trước/sau scrollIntoView; không có vùng cuộn trong dialog; click timeout vì ngoài viewport. Escape đóng được. | Xác nhận B02. |
| SOL-03 | Ordinary, 1366×768 | Documents → tìm đúng DOC51 → Ban Giám đốc; đợi UI GET có department_id=6 hoàn tất200. Snapshot vẫn có đúng dòng QA 186B sau request. | Xác nhận B03; không phải rò dữ liệu. |
| SOL-04 | Ordinary, desktop | Chỉ chặn GET `/api/knowledge` trong page riêng, trả503 tổng hợp; UI ghi0 bài/“Chưa có tri thức nào”, không error/retry; tháo chặn sau quan sát. | Xác nhận B11 nhánh lỗi mô phỏng; không phải outage tự phát. |
| SOL-05 | Ordinary, desktop | Mở `/qa-sol-audit-unknown-20261022`, đợi networkidle; body text và ariaSnapshot đều rỗng. | Xác nhận B10. Parent cũng đã tái hiện với khách. |
| SOL-06 | Ordinary, desktop | Mở `/documents/51`: UI hiện DOC-0051, đúng filename,186B,Kỹ thuật,Nội bộ,ngày22–29/10,“Đã phê duyệt”, hoạt động upload/approve. | Xác nhận metadata/approval đúng ID; không tải file. Snapshot ban đầu có “TXT — không thể xem trực tiếp”; chưa đợi riêng nội dung preview nên không kết luận bug preview mới. |

Một lần thử giữ biến global giữa tool calls không tồn tại; đã tìm lại đúng page riêng rồi chạy tiếp. Đây là hạn chế tooling, không phải lỗi sản phẩm và không được tính thêm ca. Tổng cộng sáu recheck nghiệp vụ, không mở rộng sang toàn bộ route.

Sol đã dùng view_image xem: root-mobile-login-overlay, root-workspace-mobile-360, root-auth-invalid-visible, DOCS-empty-validation, DOCS-oversize-validation, DOCS-reject-owner-reloaded, luna-chat-doc51-citation-open, ordinary-approved-after-manager, DOCS-detail-pending, DOCS-manager-approved, DOCS-replacement-indexed, luna-auth-login-success, root-logout-mobile, workspace-in-chat-selector, knowledge-edited, root-knowledge-simulated-503. Tất cả nằm dưới `harness/reports/acceptance-20261022/`.

**Chất lượng artifact:** [DOCS-manager-approved.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-manager-approved.png>) trắng, không tự chứng minh approval. Thay bằng tường thuật UI, replacement-indexed, approval-pending và SOL-06, không ghép ảnh detail DOC47 thành detail DOC51. [workspace-in-chat-selector.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-chat-selector.png>) đang hiển thị KB Kỹ thuật và hội thoại DOC51, chưa chứng minh riêng workspace QA private đã được chọn; K05 giữ PARTIAL. Download DOC47/V1/V2 có so byte theo báo cáo, nhưng Sol không tải lại. Quan sát metadata request phát sinh từ UI được dùng hỗ trợ chẩn đoán, không thay thao tác UI bằng gọi API.

#### Ma trận đủ 35 ID

Quy ước: desktop các worker chủ yếu1366×768, không tự chứng nhận1440×900. Phiên ordinary=QA dùng một lần; manager cùng phòng; other=QA khác phòng; Admin/manager thường khởi tạo token. Auth thành công bằng mật khẩu có bằng chứng riêng. Mọi PARTIAL bên dưới là thiếu bằng chứng, không tự xem là product failure.

| ID | Kết quả | Role / device / biến thể đã đối chiếu; phần còn thiếu | Nguồn |
|---|---|---|---|
| A01 | PASS | Khách desktop: root/protected vềlogin, landing/register/form validation tải được. Không chứng nhận đăng ký hợp lệ end-to-end. | ROOT-PUBLIC-REGISTER, Luna auth |
| A02 | FAIL | Ordinary desktop: mật khẩu đúng/sai/rỗng, show/hide và reload có bằng chứng; sai có thông báo. Mobile390 touch100% bị B01. Malformed login email/double-submit chưa đủ. | AUTH01/02, ROOT-AUTH-ERROR/PASSWORD, SOL01 |
| A03 | PARTIAL | Ordinary: logout hai tab, Back/Reload vềlogin đạt. Chưa đủ Forward, mở login khi còn phiên, token-expiry/401 recovery và Safari BFCache. | ROOT-LOGOUT/SESSION-RELOAD |
| A04 | PARTIAL | Ordinary: bốn route thật `/admin`,`/departments`,`/graph-knowledge`,`/approvals` vềdashboard. Admin admin/approvals/graph có thao tác; chưa đủ artifact route `/departments` riêng và toàn bộ menu đối chiếu. Không chứng nhận API RBAC. | ROOT-ROLES, admin/graph/docs reports |
| A05 | PARTIAL | Ordinary desktop/mobile: menu và dashboard tabs dùng được. Chưa đối chiếu toàn bộ metric, recent-document link, Back/deep-link ở mọi menu. | ROOT-DASHBOARD-TABS/MOBILE-NAV |
| A06 | PARTIAL | Admin desktop: QA search/empty/export CSV, audit mask/pagination, department search đạt. Role filter/user pagination, audit detail và departments route riêng chưa đủ. | ROOT-ADMIN-USERS/AUDIT/DEPT |
| A07 | NOT_RUN | Admin CRUD user/department + edit/reload/delete-cancel chưa được nghiệm thu thành ca. Việc parent tạo user để chuẩn bị không đủ validation/evidence vòng đời. Không chạy mutation ở audit. | Common file preparation; không có ca đầy đủ |
| A08 | PARTIAL | Ordinary desktop: profile đúng, sửa nháp/Escape/mở lại không lưu; theme reload đạt. X/save/avatar và đối chiếu theme toàn trang chưa đủ. | ROOT-PROFILE-CANCEL/THEME |
| D01 | FAIL | Ordinary desktop list/grid/search/type/status/reset đạt; department B03 sai. Admin18 tài liệu/4trang sort/pagination đạt; ordinary nhiều trang chưa có dataset. List-error branch chưa chạy. | DOCS D01, ROOT-DOC-SORT-PAGES, SOL03 |
| D02 | PASS | Ordinary desktop: TXT hợp lệ + ngày + Nội bộ tạo một tài liệu, pending rõ và reload metadata; replacement DOC51 liên kết qua duyệt/indexed/chat. | DOCS D02, SOL06 |
| D03 | FAIL | Ordinary desktop: CSV/thiếu ngày/ngày đảo bị chặn; 0B và51MiB không có client validation, Upload bật (B04/B05). Không submit hai tệp đó; backend acceptance chưa biết. | DOCS D03, ảnh empty/oversize |
| D04 | PARTIAL | Ordinary desktop DOC47: upload trùng có cảnh báo, Hủy không tạo bản thứ hai. Chưa double-click/retry và duplicate-check với nội dung ngoài quyền. | DOCS D04/observations |
| D05 | FAIL | Ordinary→manager desktop DOC51 preview/approve/reload đạt; DOC54 reject bắt buộc lý do nhưng owner reload không thấy lý do (B06). Preapproval RAG exclusion/pending_org chưa đủ. | DOCS D05, reject-owner image, SOL06 |
| D06 | PARTIAL | DOC51 approved + completed186B/1chunk, reload và chọn Completed lại đạt; không suy reset tab là reset job. Failed-job/reason và mọi biến thể status chưa đủ. | DOCS D06, replacement-indexed |
| D07 | PARTIAL | DOC47 TXT preview/metadata có ảnh; PDF20 native viewer1/1 zoom đạt. Không chuyển bằng chứng TXT47 thành TXT51; bảng/ảnh/định dạng còn lại và TXT51 preview hoàn tất chưa chứng nhận. | DOCS D07, ROOT-PDF-VIEWER, SOL06 |
| D08 | PARTIAL | Owner DOC47 current/V1/V2 tải và byte-match; other list/detail bị chặn. Share/copy-link sang context không quyền và download replacement DOC51 chưa chạy. | DOCS D08, download artifacts |
| D09 | PARTIAL | Owner desktop upload candidate V2/ghi chú/history và tải V1/V2 đã làm. V1 current khi V2 pending không phải bug; approve→indexed→effective→V2 current, metadata cancel chưa đủ. | DOCS counts/observations/version artifacts |
| D10 | PARTIAL | Owner DOC47 delete-cancel/delete/restore/delete, other list/direct-detail đạt; trash đã làm rõ là soft-delete. Other direct download/preview/version và deleted-document RAG exclusion chưa chạy. | DOCS D10/observations |
| C01 | PASS | Ordinary KB Kỹ thuật/DOC51: blank disabled, gợi ý điền composer, gửi đúng reference, analyzing→final6.1/6.8s. | Luna chat C01, answer/memory images |
| C02 | PASS | Ordinary desktop: citation[yr76] mở đúng filename và reference DOC51 hỗ trợ câu trả lời. | Citation-open image đã xem |
| C03 | PASS | Ordinary desktop: follow-up nhớ mã, câu hỏi ngày không có trong nguồn được abstain; clipboard đối chiếu đúng. Chỉ chứng nhận các câu đã hỏi. | Luna chat C03a/b/c |
| C04 | PARTIAL | Reload/history/cancel-clear và user khác không thấy QA messages đạt. Workspace A→B→A, đổi nhanh/race và logout/login persistence chưa chạy. | Luna chat C04a–d |
| C05 | NOT_RUN | Không có picker thấy được; chưa so ordinary/Admin, abort stream/error/retry, pending/cross-workspace exclusion. Không có bằng chứng để coi picker vắng mặt là N/A cho cả ca. | Luna chat C05 |
| C06 | PARTIAL | Ordinary desktop: search/cards, document link tới list có QA-owned docs. Ask-link timeout chưa có destination; không đủ chứng minh user_id filter thật. Nonsense search có kết quả chưa đủ oracle để FAIL ranking. | Luna Expert C06 |
| C07 | PARTIAL | Admin desktop: workspace data/empty/return, hover/focus/zoom/fit đạt. Pan/legend filter chưa chạy; degree0 là nghi vấn, chưa thành bug. Ordinary route denial có ROOT-ROLES. | Luna graph C07, ROOT-GRAPH-SWITCH |
| K01 | FAIL | Ordinary desktop: inline content/search/category/status/layout và other-user isolation có kiểm tra; 503 mô phỏng thành empty giả (B11). | Luna knowledge K01/K04c, SOL04 |
| K02 | PASS | Ordinary desktop: required fields/create/edit/reload/delete-cancel có UI; edit tạo successor version, không tự kết luận duplicate. HTML/script fixture không được cấp/chạy; không chứng nhận XSS hoặc loại bỏ stale versions trong retrieval. | Luna knowledge FINAL K02, edit images |
| K03 | FAIL | Ordinary→manager: internal submit/preview/approve/reload đạt, nhưng indexed vẫn ghi Chờ xử lý (B07). Preapproval RAG exclusion và đầy đủ restore retrieval chưa chứng nhận. | FINAL K03, ordinary-approved image |
| K04 | FAIL | Ordinary desktop private CRUD/filter/scope-lock/reload; public/dept403 đúng và không tạo record; other/Admin visibility đã quan sát. 390footer đạt;360footer bị B02. | FINAL K04, ROOT-MOBILE-WORKSPACE, SOL02 |
| K05 | PARTIAL | Workspace delete/cancel/restore + selector inspections có tường thuật. Một screenshot selected-workspace không khớp fixture; Documents không có workspace picker. Chưa đủ cross-page ID và quyền sau restore; không suy UI label thành ID đúng. | FINAL K05, selector artifacts |
| U01 | FAIL | Mobile390 menu/composer/upload100% có bằng chứng, workspace390footer đạt; mobilelogin B01 và workspace360 B02 không đạt. Desktop1440×900 riêng, toàn modal/mobile flow chưa đủ. | ROOT-MOBILE-NAV, Luna mobile, SOL01/02 |
| U02 | PARTIAL | Touch100% upload footer thấy được; parent CDP scale2 ghi visual195×422/footer744..784. Chưa chứng minh không thể pan/cuộn tới footer hoặc đủ metrics/reset cùng trạng thái; không chấp nhận FAIL toàn mobile/pinch từ ảnh đơn. | ROOT prior zoom; admin-upload/mobile-zoom-200 |
| U03 | PARTIAL | Enter login, profile một bướcTab/Escape, modal Hủy có bằng chứng; full Tab/ShiftTab/Space/focus-return/trap cho menu/upload/profile chưa chạy đủ. | ROOT-PROFILE-CANCEL/MOBILE-ENTER |
| U04 | PARTIAL | Modal knowledge360 cuộn được; mobile composer hiện. Chưa real keyboard, desktop browser zoom200%, Safari/iOS/Android thật. Đây là giới hạn môi trường, không product fail. | Knowledge mobile, chat mobile |
| U05 | FAIL | B10 unknown URL trắng, B11 knowledge simulated503 empty giả; workspace simulated503/error/retry đạt. Missing document ID, browser offline toàn bộ và console toàn route chưa đủ. | ROOT-UNKNOWN/KNOW-ERROR/WS-ERROR, SOL04/05 |

#### Issue được chấp nhận và cách tái hiện

Đường dẫn ảnh dưới đây đều tương đối với `harness/reports/acceptance-20261022/`. Owner là nhóm đề xuất xử lý, chưa phải cam kết đã nhận việc. Tất cả còn OPEN; deadline đề xuất: trước quyết định nghiệm thu23/10. S2 chỉ được miễn khi người có quyền ghi nhận rõ owner/hạn, không tự chuyển thành PASS.

| Bug | Mức / owner | Bước → actual / expected; phạm vi | Artifact |
|---|---|---|---|
| B01 | S1 / frontend-auth | Mobile390×844 touch100% → login → chạm giữa Đăng nhập: overlay chặn pointer. Expected form nhận touch. Enter là workaround nhưng layout che cả form, không đạt login thông thường trên mobile. | root-mobile-login-overlay.png; SOL01 |
| B02 | S1 / frontend-workspace | Mobile360×640 touch100% → Workspace/Tạo mới → cuộn tới footer: Hủy/Tạo mới vẫn ngoài viewport, không vùng cuộn. Expected tiếp cận save/cancel. Escape chỉ hủy, không hoàn tất create; đổi sang thiết bị/viewport khác không hoàn thành luồng ở360. Nâng từ S2 worker vì chặn CRUD được phép. | root-workspace-mobile-360.png; SOL02 |
| B03 | S2 / backend+frontend-documents | Tìm DOC51 Kỹ thuật → chọn Ban Giám đốc → chờ200: vẫn có DOC51. Expected department filter đúng. Không có leak ngoài quyền đã chứng minh. | root-department-filter-mismatch.png; SOL03 |
| B04 | S2 / frontend-upload | Chọn TXT0B + ngày hợp lệ: không error, Upload bật. Expected validation trước submit. Chỉ kết luận client gap. | DOCS-empty-validation.png |
| B05 | S2 / frontend-upload | Chọn51MiB dù copy tối đa50MB + ngày hợp lệ: không error, Upload bật. Expected chặn rõ. Không submit; không tuyên bố server chấp nhận hoặc xử lý file lớn. | DOCS-oversize-validation.png |
| B06 | S2 / frontend+backend-documents | Manager reject DOC54 kèm lý do → owner detail/reload: chỉ Từ chối, không lý do/activity reason. Expected owner biết cách sửa. | DOCS-reject-reason-ready.png; DOCS-reject-owner-reloaded.png |
| B07 | S2 / frontend-knowledge | Duyệt knowledgeQA ID3 → owner reload: card Hoạt động nhưng Chờ xử lý; UI-triggered list diagnosis đã indexed/approved. Expected processing label đồng nhất. Không gọi approval thất bại. | ordinary-approved-after-manager.png; FINAL knowledge report |
| B08 | S2 / frontend-auth | Desktop login → Google: không destination/dialog/feedback. Expected OAuth hoặc trạng thái chưa hỗ trợ rõ. Visible control nằm trong phạm vi UI; provider end-to-end chưa xác minh. | root-auth-placeholder-actions.png; ROOT-GOOGLE |
| B09 | S2 / frontend-auth | Login → Quên mật khẩu: chỉ thêm#; expected recovery/help có ích. | root-auth-placeholder-actions.png; ROOT-FORGOT |
| B10 | S2 / frontend-routing | URL không tồn tại → body trắng, không đường quay lại; expected404 hoặc fallback rõ. | root-unknown-route.png; SOL05 |
| B11 | S2 / frontend-knowledge | Fault injection GET knowledge503 trong contextQA → UI0 bài/Chưa có tri thức nào. Expected lỗi tải/retry, không empty giả. Chỉ bug xử lý lỗi mô phỏng. | root-knowledge-simulated-503.png; SOL04 |

#### Kết luận bị bác bỏ hoặc chưa đủ chứng cứ

- AUTH-03 “không báo sai mật khẩu”: bác bỏ. [root-auth-invalid-visible.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-auth-invalid-visible.png>) cho thấy Đăng nhập thất bại ngoài form; locator worker quá hẹp.
- D01-SORT “sort không hoạt động”: bác bỏ. Dataset hai dòng có thể trùng newest/name order; parent18 dòng/4trang đổi sort và localeCompare('vi') đạt. Không cộng FAIL đó.
- `/admin/users` và `/knowledge-graph` trắng không chứng minh vượt/chặn quyền route thật. Dùng `/admin` và `/graph-knowledge`; URL lạ trắng thuộc B10 riêng.
- V2 pending trong khi V1 current không phải bug được chứng minh. Giữ D09 PARTIAL đến khi UI xác nhận activation; không lấy code comments thay bằng chứng.
- Knowledge edit có successor/supersedes: không gắn duplicate FAIL. Việc nhiều sibling version active/listed còn cần product xác nhận và kiểm tra retrieval; chưa hứa không có stale-source issue.
- Expert nonsense trả66/60%: chưa có policy/oracle cho no-match/fallback; chỉ quan sát chất lượng, không FAIL ranking. Ask-link và owner filter vẫn cần chạy.
- Graph degree0 dù có edges, nguồn rộng trong câu abstain trước handoff: chưa đủ chứng minh sai ngữ nghĩa; không tính bug.
- Trash DOC47/candidate: bản follow-up giải thích trống ngay sau restore, sau delete có restore actions. Không còn chứng cứ permanent delete. Giữ các thiếu sót D10 khác.
- Profile-lock trước retry là BLOCKED-TOOL đã vượt qua, không product fail. Harness20P/0F/5W chỉ smoke/deploy, không cộng vào35 ca UI.

#### Phần phải chạy lại, blocker và dữ liệu tồn dư

**Không còn blocker MCP hoặc thiếu mật khẩu chung cho lượt này.** C05 và A07 là NOT_RUN; không được đổi tên thành lỗi công cụ. Ordinary multipage thiếu dataset (Admin đã kiểm tra riêng). Real mobile keyboard/Safari/Android chưa có môi trường; HTML/script fixture chưa có trong phạm vi. Không thực hiện API-only security audit.

Trước GO cần tối thiểu: sửa và retest B01/B02 ở100% đúng360/390 touch; hoàn tất C04 workspaceA→B→A/rapid-switch/logout-login và C05 abort/error/retry; D08 share/copy/direct unauthorized file/version; D09 approved-version activation; D10 direct unauthorized preview/download/version và deleted-source exclusion; K05 đúng fixture/ID và quyền sau restore; bổ sung evidence các PARTIAL khác hoặc xin ngoại lệ rõ ràng cho biến thể phụ. Kiểm tra preapproval exclusion bằng fixture phù hợp và giữ giới hạn LLM; không hỏi vô hạn để tìm câu trả lời đẹp.

Dữ liệu theo báo cáo cuối, **Sol không dọn hay thay đổi**:

- DOC51 đang active/approved/indexed,186B,KB Kỹ thuật, reference `DOCS-ACCEPTANCE-20261022-01`; Sol06 thấy đúng ID/approval. Parent quyết định cleanup sau khi kết thúc review.
- DOC47 và candidate version trong trash30ngày; DOC54 rejected trong trash. Candidate ID chưa được báo cáo rõ: parent cần bổ sung trước cleanup, không đoán ID và không purge hàng loạt.
- Knowledge IDs1/2/3/4 và `QA-20261022-WS-Luna-Private` soft-deleted trong trash; public/dept permission fixtures nhận403 nên không được tạo. Generated knowledge docs được worker báo đã không còn trong exact search; chưa chứng nhận purge vector.
- Disposable QA user cùng quyền/department được chuẩn bị cho lượt này còn tồn tại; manager/Admin/other-user sessions chỉ dùng theo cấp. Parent cần chốt user nào là tài khoản tạo mới để disable/delete đúng người. Không coi các user sẵn có là dữ liệu QA để xóa.
- Chat worker báo đã xóa riêng lịch sử QA tạo trong lượt và reload xác nhận; không xóa history tài khoản khác. Local downloads/TXT/sparse51MiB và ảnh/log còn trong artifacts; chúng không phải document51MiB trên production.

#### Handoff cho common file lần chạy sau

Parent đưa phần kết luận/ma trận này vào **một common file** `docs/NGHIEM_THU_UI.md`, đánh dấu rõ các dòng worker bị supersede thay vì để FAIL cũ đứng ngang kết luận cuối. Sol chỉ sở hữu file audit này, không sửa common file.

Các bước cần thêm để common file tự chạy lại được: sổ fixture theo ID/owner/workspace/scope/current-version và lịch cleanup; endpoint bootstrap là tạm thời không phải prerequisite dùng lại ngày mai, lấy credentials qua kênh riêng; chọn đúng visible form/toàn-body error; ghi viewport/touch/DPR/zoom và thử pointer thật không force-click; dataset sort có hai thứ tự khác nhau và đọc đủ các trang; chờ đúng request/UI state thay fixed delay; download đối chiếu bytes; capture terminal screenshot không trắng; chụp selected QA workspace cùng tên/ID; nhãn rõ fault injection; U02 đủ visualViewport metrics và pan/scroll/reset; U03 full focus loop; U04 real keyboard/desktopzoom200%; ghi retry tối đa/timeouts/giới hạn LLM và trạng thái dữ liệu trước cleanup. Parent cần giữ một artifact index với tên file thực tế, vai trò, timestamp và linked canonicalID.

**NO-GO gồm cả lỗi đã xác nhận và thiếu bằng chứng luồng chính.** Ngay cả khi hạ hai mobile issue thành S2 theo ngoại lệ được chủ nghiệm thu chấp nhận, hồ sơ hiện tại vẫn chưa đủ GO vì các kiểm tra history/stream/version/access còn thiếu. Không có thay đổi nguồn hoặc triển khai nào được audit này tuyên bố đã sửa lỗi.



## Dữ liệu QA và trạng thái sau cleanup

### Dọn dữ liệu sau kiểm tra

Parent thực hiện sau khi cả kiểm thử chức năng và Sol audit hoàn tất, ngày22/10/2026. Đây là bước dọn dữ liệu, không thay đổi kết luận các ca đã kiểm tra.

- Qua UI nhân viên, chuyển đúng `DOC-0051 / QA-20261022-DOCS-acceptance.txt` vào thùng rác và kiểm tra nó xuất hiện trong thùng rác. Không xóa tài liệu nghiệp vụ.
- Qua UI nhân viên, xóa workspace tự sinh `personal-32`, ID17, chỉ thuộc tài khoản QA32 và đã có0tài liệu đang hoạt động. Workspace thử ID18 đã ở thùng rác từ lượt Luna. Không xóa workspace phòng ban hoặc Default Workspace.
- Qua UI Admin, tìm đúng `qa.acceptance.20261022@micco.local`, mở Vô hiệu hóa, kiểm tra modal ghi đúng tênQA, xác nhận và reload. Dòng tài khoản chuyển **Không hoạt động**. UserID32 được giữ cho nhật ký, không xóa user có sẵn.
- Đối chiếu DB chỉ đọc sau thao tácUI:0tài liệuQA hoạt động,0tri thứcQA hoạt động,0workspace thuộcQA hoạt động. Tài liệu47,48,49,50,51,52,53,54 ở thùng rác;48/50/52/53 là tài liệu được tạo từ tri thứcQA. Tri thức1/2/3/4 và workspace17/18 đã soft-delete. Giữ dữ liệu theo chính sách thùng rác30ngày; không purge hàng loạt hoặc xóa audit log.
- Luna đã xóa lịch sử chatQA tạo trong đợt và xác nhận bằng reload; không xóa chat của người dùng thật. Tổng7câu hỏi UI gửi tớiLLM; ca abort được chặn trongbrowser trướcbackend.
- Các context của các nhómchat/knowledge và Sol được đóng; parent dọn cáccontext riêng và phiênadmin thử còn lại. Phiênbootstrap ngắn hạn không phải tài khoản/mật khẩu để dùng lại ngày mai.
- Serverbootstrap localhost và cácfile chứa phiên/mật khẩu tạm được dừng/xóa ở cuối lượt; cấu hìnhMCP tạm `--isolated` được hoàn nguyên. Lần chạy song song sau vẫn phải chuẩn bị profile tách biệt theo phần hướng dẫn.
- Ảnh/log, CSV chỉ có một dòngQA và fixtureTXT nhỏ được giữ làm bằng chứng. Tệp51MB local được xóa sau kiểm tra; không từng được upload lênproduction.

Bằng chứngUI: [root-cleanup-doc51-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-cleanup-doc51-trash.png>), [root-cleanup-qa-user-disabled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-cleanup-qa-user-disabled.png>). Sổ fixture trên đây bổ sung ID cụ thể cho phần tồn dư trong audit gốc; DOC51 **không còn active** sau cleanup. Muốn chạy lại phải tạo/restore fixture và kích hoạt/reset tài khoảnQA theo quy trìnhadmin phù hợp.



## Tiêu chí và các bước chuẩn để chạy lại

### Checklist nghiệm thu miccoRAG — 22/10/2026

Đích: https://chatbot.coremind.io.vn — phục vụ nghiệm thu ngày 23/10/2026. Đây là **tiêu chí**, chưa có ca nào được xác nhận PASS. Một checklist chung cho bốn nhóm Luna; Sol duyệt bằng chứng và quyết định cuối cùng. Mã local có thể khác bản production: ghi nhận khác biệt, không suy ra hành vi live từ mã.

#### Quy tắc thực hiện và ghi kết quả

- Thực hiện qua MCP Playwright như người dùng: mở trang, bấm, nhập, chọn tệp, theo dõi kết quả. Đọc mã/API hỗ trợ chẩn đoán không thay thế thao tác UI. Không sửa code, deploy hoặc thay cấu hình server trong lượt nghiệm thu.
- Mỗi nhóm dùng phiên/browser context riêng và tài khoản QA được parent cấp; không giành shared profile. Lỗi khóa profile là `BLOCKED-TOOL`, không phải lỗi ứng dụng. Parent đã báo cấu hình MCP `--isolated`; mỗi nhóm phải xác nhận công cụ thực sự chạy trước khi kiểm thử. Không sửa cấu hình để tự giải quyết ngoài phạm vi.
- Parent đã tạo tài khoản thường QA dùng một lần qua Admin UI. Dùng tài khoản đó để kiểm tra quyền thường; phiên Admin không thay thế kiểm thử quyền thường. Không ghi mật khẩu, token, hash, dữ liệu nhạy cảm vào báo cáo/ảnh.
- Pha lập tiêu chí chỉ đọc mã, không thay đổi production. Ở pha thực thi, chỉ CRUD trong tài khoản/workspace/tệp QA mà parent cho phép, tiền tố `QA-20261022-<nhóm>-<tên>`. Không sửa/xóa/duyệt dữ liệu nghiệp vụ sẵn có. Thiếu quyền hoặc fixture thì BLOCKED; không tự mở rộng phạm vi. Chat có thể lưu lịch sử/tốn LLM: dùng workspace QA, tối đa 3 câu hỏi cho mỗi kịch bản RAG, không lặp vô hạn.
- Trạng thái từng ca: `NOT-RUN`, `PASS`, `FAIL`, `BLOCKED-TOOL`, `BLOCKED-DATA`, `BLOCKED-AUTH`, `N/A`. Chỉ PASS khi đủ bước và bằng chứng. Ca mới chạy một phần giữ BLOCKED và ghi phần đã kiểm tra. N/A cần Sol chấp nhận lý do; tính năng đang có nút nhưng hỏng không phải N/A.
- Mức độ khi sai: `S0` rò dữ liệu/vượt quyền/mất dữ liệu; `S1` chặn luồng chính đăng nhập, upload, duyệt, đọc tài liệu, RAG hoặc CRUD được phép; `S2` lỗi có cách đi vòng hữu dụng, thiếu khả năng tiếp cận; `S3` thẩm mỹ. Có thể nâng mức theo tác động thực tế, ghi lý do.
- Mỗi ca ghi: ID + biến thể, người chạy, thời gian/múi giờ, URL, vai trò (nguồn phiên: mật khẩu hay cấp sẵn), viewport/isMobile/zoom, fixture ID, bước thực tế, expected, actual, trạng thái, severity nếu lỗi, đường dẫn bằng chứng, blocker/cleanup. Không dùng câu chung “mọi chức năng tốt”.
- Bằng chứng tối thiểu: snapshot hoặc ảnh cho điểm kết thúc; lỗi có ảnh, bước tái hiện, lỗi console/network liên quan (đã che bí mật), HTTP status khi có. Ca thay đổi dữ liệu cần trước/sau và tải lại xác nhận. Download cần tên tệp, kích thước, mở đọc/đối chiếu nội dung. RAG cần câu hỏi, câu trả lời và đoạn nguồn đối chiếu. Không cần lưu toàn bộ nội dung tài liệu thật.
- Mỗi bước tải trang/dữ liệu chờ tối đa 30 giây, chat tối đa 120 giây, xử lý tệp nhỏ tối đa 5 phút; ghi thời gian thực tế. Quá giới hạn ghi timeout và trạng thái còn lại; không tuyên bố thất bại xử lý vĩnh viễn nếu job vẫn đang chạy. Retry một lần nếu cần và giữ cả bằng chứng lần đầu.
- Các nhóm lưu báo cáo riêng dưới thư mục này, cùng tham chiếu ID dưới đây; không sửa tiêu chí hoặc báo cáo của nhóm khác. Không chia sẻ tài khoản giữa nhóm khi đang đăng xuất/đổi phiên. Bàn giao fixture phụ thuộc bằng ID và trạng thái rõ ràng.

#### Ma trận bao phủ từ route thực tế

Nguồn đã đọc: `micco-frontend/src/App.jsx`, `layouts/DashboardLayout.jsx`, `utils/roles.js`, `utils/api.js`, `context/AuthContext.jsx`, các page bên dưới; backend `core/permissions.py`, `models/document.py`. API dùng cả `/api/*` và `/api/v1/*` trong cùng backend; không giả định hai backend riêng. Route không có menu vẫn phải thử trực tiếp.

| Nhóm Luna | Route / phạm vi | Vai trò bắt buộc | Ca sở hữu |
|---|---|---|---|
| A — auth/mobile/admin | `/`, `/landing`, `/login`, `/register`, `/dashboard`, `/admin`, `/departments`; điều hướng, hồ sơ, mobile/keyboard | Khách + thường QA + Admin | A01–A08, U01–U05 |
| B — docs/approval/status | `/documents`, `/documents/:id`, `/approvals`, `/processing-status` | Thường QA + người duyệt được cấp | D01–D10 |
| C — chat/expert/graph | `/chat`, `/expert`, `/graph-knowledge` | Thường QA + Admin cho graph | C01–C07 |
| D — knowledge/workspace | `/knowledge`, `/workspaces` | Thường QA + Admin khi cần quyền | K01–K05 |

Quyền route trong mã: các route nghiệp vụ cần đăng nhập; `/approvals` cho Admin/Trưởng phòng/Giám đốc/Phó giám đốc; `/admin`, `/departments`, `/graph-knowledge` chỉ Admin. Người thường mở trực tiếp route đặc quyền phải bị chặn/chuyển dashboard và không nhận dữ liệu đặc quyền. Các phép đọc cụ thể vẫn phụ thuộc chủ sở hữu/phòng ban/phạm vi; “public” nội bộ không đồng nghĩa công khai cho khách Internet. A kiểm tra chặn route; nhóm tính năng kiểm tra phạm vi dữ liệu.

#### A — Auth, dashboard, quản trị (mỗi ca bắt đầu NOT-RUN)

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| A01 | Context sạch mở `/`, `/login`, `/register`, `/landing`; mở `/documents` và một route Admin khi chưa đăng nhập. | Root tới login; landing và form hiển thị; route bảo vệ về login, không ló dữ liệu. Chuyển login/register hoạt động. | S1; lộ dữ liệu S0 |
| A02 | Đăng nhập bằng mật khẩu QA hợp lệ qua form; thử mật khẩu sai một lần, trường rỗng/email sai; reload sau đăng nhập. | Sai có thông báo, không cấp phiên; đúng tới dashboard, tên/vai trò đúng và giữ phiên sau reload; không gửi trùng khi bấm liên tiếp. | S1 |
| A03 | Với phiên đã đăng nhập mở login; logout; Back/Forward/reload vào dashboard và route Admin; nếu có hai tab cùng tài khoản, kiểm tra tab còn lại. | Login chuyển dashboard khi còn phiên; logout chặn đọc dữ liệu ở mọi tab/back cache. Hết hạn/401 phải về login, không hiện danh sách rỗng giả thành công. Mô phỏng hết hạn chỉ trong context QA, ghi rõ mô phỏng. | S0 nếu lộ; khác S1 |
| A04 | Người thường mở trực tiếp `/admin`, `/departments`, `/graph-knowledge`, `/approvals`; đối chiếu menu. Admin mở các route được cấp. | Người thường không có dữ liệu/nút đặc quyền; Admin truy cập đúng. Không coi ẩn menu là đủ bằng chứng phân quyền. | S0 |
| A05 | Dashboard: đọc thống kê, đổi từng tab, mở tài liệu gần đây; đi toàn bộ menu, Back và reload deep link. | Không trang trắng/404 bất ngờ; tab/menu active đúng, số liệu hợp lý và theo quyền; link mở đúng tài liệu. Liệt kê route chỉ truy cập được bằng URL. | S1 nếu chặn luồng; khác S2 |
| A06 | Admin: mở danh sách user, tìm QA, lọc vai trò/phân trang; mở log và chi tiết; mở tab phòng ban và `/departments`. | Bộ lọc/đếm/trang nhất quán, không crash; chi tiết log đọc được. Không đọc sâu dữ liệu cá nhân ngoài nhu cầu QA. | S2; lộ quyền S0 |
| A07 | Trong phạm vi được phép: tạo/sửa user hoặc phòng ban QA, xác nhận reload; mở modal xóa rồi Hủy. Nếu parent đã tạo user, vẫn ghi riêng bước tự thực thi. | Validation rõ, dữ liệu lưu đúng, Hủy không xóa; không tự nâng quyền tài khoản thường. Thao tác chưa được phép là BLOCKED-DATA. | S1 |
| A08 | Mở menu tài khoản/hồ sơ, kiểm tra tên/phòng ban; đóng bằng X/Escape; đổi dark/light và reload. Chỉ lưu thay đổi hồ sơ QA khi được phép, không đổi mật khẩu chung. | Modal hoạt động, dữ liệu đúng, theme đọc được và duy trì theo thiết kế; không thay dữ liệu khi chỉ đóng. | S2 |

**Cổng bằng chứng đăng nhập:** token Admin được parent cấp/mint từ user DB chỉ chứng minh luồng phiên đã đăng nhập; không PASS A02. Mật khẩu DB là hash, không thể coi đó là mật khẩu thật hoặc thử đăng nhập bằng hash. Nếu chưa có mật khẩu dùng được, A02 là `BLOCKED-AUTH`; ghi rõ tài khoản thường QA có/không đăng nhập qua form. Không được suy ra “login tốt” từ `/auth/me` thành công. Register có thể kiểm tra form/validation không submit; tạo tài khoản mới chỉ khi parent cho phép, nếu chưa thử submit phải ghi thiếu bao phủ.

#### B — Tài liệu, duyệt, tiến trình

Fixture: tệp TXT/PDF nhỏ chứa câu duy nhất dễ đối chiếu; ngày hiệu lực hợp lệ; ghi workspace/phạm vi/chủ sở hữu. Mã upload chính quảng bá PDF/TXT/DOCX/PPTX/MD, tối đa 50MB; form phiên bản còn nhận XLSX. Kiểm tra đúng lời hứa UI live, không tự coi XLSX được hỗ trợ mọi luồng.

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| D01 | Mở danh sách, chuyển bảng/thẻ; tìm một tên tồn tại rồi chuỗi không tồn tại; lọc loại/trạng thái/phòng ban và xóa bộ lọc. | Kết quả khớp, giữ đúng quyền, empty state rõ; lỗi tải không bị trình bày thành không có tài liệu. | S1; phụ S2 |
| D02 | Mở upload, chọn tệp nhỏ hợp lệ; điền phạm vi/phòng ban/ngày hiệu lực theo form, submit một lần; reload danh sách. | Footer/nút gửi tiếp cận được; một tài liệu được tạo, tên/metadata đúng, có tiến độ hoặc trạng thái chờ duyệt rõ; không báo indexed khi chỉ upload xong. | S1 |
| D03 | Chọn loại không hỗ trợ, tệp rỗng, ngày hết trước ngày hiệu lực; kiểm tra thiếu trường; thử tệp quá giới hạn chỉ nếu fixture/quyền cho phép. | Validation rõ, không toast thành công giả, có thể sửa và gửi lại. Không gửi tệp lớn thật chỉ để tạo tải production. Từng biến thể thiếu fixture ghi BLOCKED-DATA. | S2; chặn tệp hợp lệ S1 |
| D04 | Upload lại cùng fixture QA một lần; quan sát cảnh báo trùng/panel kiểm tra trùng nếu có; Hủy thao tác không cần thiết. | Không tạo âm thầm nhiều bản do double-click/retry; cảnh báo/biện pháp xử lý phù hợp; không lộ tên/nội dung tệp ngoài quyền qua duplicate check. | S1; rò dữ liệu S0 |
| D05 | Với tài liệu thường QA: kiểm tra trước duyệt; người duyệt mở preview, duyệt fixture phù hợp; fixture thứ hai từ chối với lý do. | Chưa duyệt không tham gia RAG; đúng người có quyền duyệt, trạng thái/lý do/badge cập nhật sau reload. Nếu có `pending_org`, không coi duyệt cấp phòng là hoàn tất duyệt tổ chức; không tự duyệt dữ liệu thật. | S1; vượt quyền S0 |
| D06 | Theo dõi cùng ID trên documents/status/approvals, refresh, đổi tab all/active/completed/failed theo UI. | Phân biệt pending/parsing/processing/indexing/indexed/failed và approval; thành công cuối cần indexed + approved, không bắt buộc nhìn thấy mọi bước thoáng qua. Lỗi có lý do; refresh không reset tiến trình. Job quá thời gian ghi timeout, không restart hệ thống. | S1 |
| D07 | Mở detail fixture, đọc preview/markdown/PDF theo loại; kiểm tra tiêu đề/metadata/version; quay lại list. | Đúng tài liệu, ký tự Việt/bảng/ảnh fixture đọc được, loading/error có lối thoát; không spinner vô hạn. | S1 |
| D08 | Tải file hiện tại và phiên bản QA sẵn có, mở bản tải; sao chép link/chia sẻ và mở trong context không quyền. | File đúng tên/nội dung/phiên bản; link không cấp quyền ngoài chính sách, không chỉ tải HTML lỗi. | S1; rò dữ liệu S0 |
| D09 | Nếu được phép, upload phiên bản mới fixture với ghi chú/ngày; reload lịch sử, tải cả hai phiên bản; mở sửa metadata rồi Hủy. | Lịch sử/phiên bản hiện tại đúng, file cũ còn đúng, version mới tuân thủ duyệt/phạm vi; Hủy không lưu. | S1 |
| D10 | Với hai user/phòng ban QA hoặc fixture riêng: người không quyền thử detail/download/preview/version; mở xóa rồi Hủy. Xóa/khôi phục chỉ fixture QA được phép. | Không lộ dữ liệu qua URL trực tiếp; Hủy giữ nguyên; xóa/khôi phục nhất quán và tài liệu bị xóa không được RAG dùng. Thiếu user đối chiếu là BLOCKED-AUTH. | S0; luồng QA lỗi S1 |

#### C — Chat/RAG, chuyên gia, graph

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| C01 | Mở chat, chọn workspace QA, gửi câu hỏi có đáp án trong D06 đã indexed+approved; quan sát streaming đến kết thúc. | Đúng workspace, không gửi rỗng/trùng, nội dung Việt rõ, trạng thái gửi kết thúc; trả lời phù hợp fixture. Chưa có fixture đạt điều kiện là BLOCKED-DATA, không PASS bằng lời chào. | S1 |
| C02 | Bấm citation trong câu trả lời, mở nguồn/đoạn trích, đối chiếu câu khẳng định và tài liệu gốc. | Citation trỏ đúng tài liệu truy cập được và hỗ trợ nội dung; không bịa nguồn, không lộ tài liệu ngoài quyền. | S1; lộ dữ liệu S0 |
| C03 | Hỏi tiếp “quy định đó áp dụng khi nào?” theo fixture; hỏi một thông tin không có trong nguồn. | Giữ đúng ngữ cảnh; thiếu căn cứ nói rõ giới hạn, không tự khẳng định dữ kiện trái nguồn. Đánh giá theo ý nghĩa, không so khớp nguyên văn câu trả lời. | S1 |
| C04 | Reload, đổi workspace A→B→A; logout/login lại cùng user và thử user QA khác nếu được cấp; mở modal xóa lịch sử rồi Hủy. | Lịch sử đúng user/workspace, không ghi đè bởi request cũ khi đổi nhanh; reload và logout không âm thầm xóa lịch sử; Hủy không mất dữ liệu. Không xóa lịch sử chung. | S0 nếu lộ; khác S1 |
| C05 | Kiểm tra chọn tài liệu/mode nếu UI có; thường so với Admin; thử lỗi mạng/stream ngắt chỉ bằng chặn request trong context QA rồi khôi phục. | Phạm vi/mode theo quyền; không dùng tài liệu chưa duyệt/khác workspace. Stream lỗi có thông báo, không đánh dấu hoàn tất giả và có thể gửi lại. Mô phỏng phải gắn nhãn, không tính là lỗi live tự phát. | S1; lộ dữ liệu S0 |
| C06 | Expert: chọn workspace, tìm chủ đề fixture, mở thẻ/kết quả, bấm đi tới chat/tài liệu. | Kết quả có cơ sở theo dữ liệu được phép; link/context đúng; nếu link có `user_id`, danh sách tài liệu thực sự phải lọc tương ứng. Không có kết quả hiển thị rõ; thiếu fixture chuyên gia không chứng minh ranking PASS. | S2; chặn chính S1 |
| C07 | Admin mở graph, chọn workspace có dữ liệu, tương tác node/pan/zoom/filter nếu có; đổi workspace rỗng rồi quay lại. | Đồ thị/detail khớp workspace, không dữ liệu cũ sót, empty/error rõ, UI vẫn dùng được; người thường bị chặn theo A04. Không chạy build graph production. | S2; rò dữ liệu S0 |

#### D — Tri thức và workspace

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| K01 | Knowledge: tìm mục có thật/không có; mở chi tiết; kiểm tra lọc/phạm vi theo UI. | Nội dung và kết quả khớp, không lộ draft/khác phòng ban ngoài quyền, empty/error phân biệt. | S1; lộ dữ liệu S0 |
| K02 | Tạo tri thức QA (tiêu đề/nội dung/phạm vi hợp lệ), thử trường bắt buộc trước; sửa fixture và reload; mở xóa rồi Hủy. | Validation rõ, chỉ một mục được lưu, cập nhật tồn tại sau reload; Hủy không xóa. Nội dung chỉ đọc không chạy HTML/script khi có fixture an toàn được phép. | S1; thực thi mã S0 |
| K03 | Người thường gửi tri thức QA qua luồng duyệt nếu UI hỗ trợ; bàn giao ID cho B kiểm tra tab knowledge/preview/duyệt; sau đó kiểm tra lại. Xóa/restore chỉ fixture được phép. | Phân biệt trạng thái duyệt và ingest; chưa duyệt chưa thành nguồn RAG; preview/render đúng, duyệt và trash không làm mất dữ liệu ngoài fixture. Thiếu lượt duyệt là BLOCKED, không PASS lifecycle. | S1; vượt quyền S0 |
| K04 | Workspace: list/search/lọc phạm vi, mở create; tạo workspace QA, reload, sửa tên/mô tả; kiểm tra loại/phạm vi khi sửa. | Chỉ thấy workspace được phép, create/update tồn tại; mã hiện tại khóa đổi phạm vi workspace đã tạo, UI live cần rõ ràng và nhất quán. Không đổi scope dữ liệu thật. | S1; vượt quyền S0 |
| K05 | Vào workspace QA từ chat/docs/expert nếu có; so user khác; mở delete rồi Hủy; nếu được phép xóa/restore workspace QA và reload. | Các trang thống nhất tên/ID/quyền, Hủy giữ nguyên; xóa có xác nhận và không xóa tài liệu/workspace khác; restore không mở rộng quyền. | S1; mất/lộ dữ liệu S0 |

#### U — Thiết bị, bàn phím, modal, lỗi (A sở hữu; nhóm khác bổ sung bằng chứng)

| ID | Bước cụ thể | Kết quả mong đợi | Mức độ nếu sai |
|---|---|---|---|
| U01 | Desktop 1440×900, mobile 390×844 `isMobile:true` ở zoom 100%; mở menu, documents/upload, chat composer, knowledge/workspace modal. | Nội dung/nút chính không bị che/cắt; mobile menu mở/đóng và chọn route được; cuộn tới mọi điều khiển, không phải thu nhỏ để thao tác. | S1 nếu không hoàn thành; khác S2 |
| U02 | Cùng context mobile mở upload 100%, chụp footer; pinch/page scale 200%, ghi `visualViewport` và vị trí footer, thử pan/cuộn tới footer, reset 100%. | Tách hai biến thể. Known case: **100% footer upload thấy được; isMobile=true pinch200% làm visualViewport còn khoảng một nửa và footer nằm ngoài vùng nhìn thấy**. Chỉ kết luận lỗi ở tổ hợp tái hiện; ngoài vùng nhìn ban đầu chưa đủ chứng minh không tiếp cận được. Ghi có/không pan/cuộn tới được, mức ảnh hưởng. Không gọi “toàn bộ mobile hỏng”. | S2 mặc định; S1 nếu chặn hoàn tất không có cách đi vòng |
| U03 | Dùng Tab/Shift+Tab/Enter/Space/Escape qua login, menu, upload, modal hồ sơ/xác nhận; đóng modal và kiểm tra focus. | Focus thấy rõ, thứ tự hợp lý, thao tác chính được bằng bàn phím; modal giữ focus bên trong, Escape theo trạng thái an toàn, đóng trả focus; không submit/xóa khi Hủy. | S2; thao tác mất dữ liệu S0 |
| U04 | Mobile focus input để bật bàn phím nếu môi trường hỗ trợ; thử cuộn modal dài; desktop browser zoom 200% riêng. | Input/footer/composer còn tiếp cận được; không nhầm desktop zoom với pinch mobile. Giả lập không có bàn phím thật phải ghi giới hạn, không PASS phần chưa thử. | S2; chặn chính S1 |
| U05 | Trong context QA mô phỏng offline hoặc abort một request danh sách rồi retry; mở ID không tồn tại và URL lạ; quan sát console trên route chính. | Có thông báo phù hợp và đường quay lại/retry, không thành công giả/empty giả, không lộ stack/secrets; điều hướng khác vẫn dùng được. URL lạ trắng là lỗi trải nghiệm, nâng mức nếu làm mắc kẹt. | S2; chặn chính S1 |

U02 cần ghi: viewport cấu hình, `isMobile`, DPR, `innerWidth/innerHeight`, `visualViewport.width/height/scale/offsetTop/offsetLeft`, `getBoundingClientRect()` footer, screenshot 100% và 200%; đối chiếu cùng trạng thái modal. Không báo PASS pinch chỉ vì đổi viewport nhỏ hoặc desktop zoom. Nếu MCP không hỗ trợ pinch, phần đó BLOCKED-TOOL và giữ known case như thông tin cần xác minh, không tự chứng nhận đã sửa.

#### Sol audit và điều kiện GO / NO-GO

1. Parent thu đủ bốn báo cáo và artifact rồi giao **một lượt Sol review mới**. Các lượt khóa shared profile ban đầu được ghi BLOCKED-TOOL; lượt thay thế phải có bằng chứng thực thi mới, không chuyển kết quả cũ thành PASS theo suy đoán.
2. Sol đối chiếu từng ID/biến thể với checklist; lập bảng PASS/FAIL/BLOCKED/NOT-RUN/N/A theo nhóm, vai trò, desktop/mobile. Không lấy tổng PASS của harness/local test làm bằng chứng nghiệm thu production UI. Ghi build/version production nếu biết và mọi giới hạn chưa đối chiếu được.
3. Audit 100% S0/S1 và blocker; xem artifact của A02/A03/A04, D02/D05/D06/D08/D10, C01/C02/C04, K02/K04/K05, U01/U02. Kiểm tra ID fixture liên kết qua upload→duyệt→indexed→RAG, không ghép bằng chứng từ tài liệu khác. Mỗi nhóm phải có ít nhất một bằng chứng thao tác UI thực tế; báo cáo toàn mô tả mã/API chưa đủ.
4. Bằng chứng thiếu/mâu thuẫn: trả về BLOCKED/chưa xác minh, chỉ định bước chạy lại có giới hạn. Mỗi lỗi có severity, tác động, cách tái hiện, artifact, owner; trùng lỗi gộp issue nhưng giữ các test ID. Không giảm severity chỉ vì là lỗi đã biết.
5. **GO** khi tất cả ca áp dụng đã có bằng chứng đủ, không còn S0/S1, không còn BLOCKED/NOT-RUN trên luồng chính: login mật khẩu và session, quyền thường, upload→duyệt→indexed→xem/tải→RAG/citation/history, CRUD knowledge/workspace, mobile 100%. Ca S2/S3 hoặc phần phụ ngoài luồng chính còn thiếu phải được người có quyền nghiệm thu chấp nhận ngoại lệ rõ ràng, ghi owner/hạn xử lý; Sol không tự coi là PASS.
6. **NO-GO** nếu có S0/S1 chưa xử lý, hoặc thiếu bằng chứng/khả năng chạy luồng chính kể trên. Phân biệt “NO-GO vì lỗi đã xác nhận” với “NO-GO vì chưa đủ bằng chứng”; không diễn giải BLOCKED do mật khẩu/công cụ thành lỗi sản phẩm. Chỉ có token mint và thiếu A02 thì chưa đủ ký GO đầy đủ.
7. Nếu U02 chỉ lỗi pinch200% trong khi U01 100% đạt, ghi ngoại lệ đúng phạm vi và khả năng đi vòng; không NO-GO toàn mobile theo suy luận. Nếu xác nhận nút gửi không thể tiếp cận và chặn tác vụ thì áp quy tắc S1. Không hứa GO trước khi có dữ liệu thực thi.

Mẫu dòng kết quả để tái sử dụng: `ID | biến thể/role/device | status | actual | severity | evidence | blocker/cleanup`. Báo cáo cuối ghi rõ số ca chưa chạy và giới hạn, không chỉ tỷ lệ PASS.



## Báo cáo thao tác nhóm Auth / navigation / mobile — nguyên văn

### Authentication and navigation acceptance — Luna

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: https://chatbot.coremind.io.vn  
Role: disposable ordinary QA account (Kỹ thuật), authenticated through UI unless stated  
Viewports: desktop 1366×768; one separate isMobile emulation attempt at 390×844  
Method: MCP Playwright only. Auth setup used private bootstrap locally; credentials and tokens are omitted.

#### Summary

5 PASS, 1 FAIL, 7 NOT_RUN, 0 BLOCKED. This is a limited partial pass, not full authentication/navigation acceptance. No business data was changed. No cleanup needed.

| ID | Preconditions / role / viewport | Numbered human steps | Expected | Actual | Status | Evidence | Bug / cleanup |
|---|---|---|---|---|---|---|---|
| AUTH-01 | Fresh browser context, 1366×768, unauthenticated | 1. Open /login. 2. Enter disposable QA account email/password in first login form. 3. Click exact “Đăng nhập”. | Successful login routes to dashboard and shows authenticated user. | Routed to /dashboard; dashboard metrics and account label “QA2” rendered. | PASS | [luna-auth-login-success.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login-success.png) | None |
| AUTH-02 | Fresh context, unauthenticated, 1366×768 | 1. Open /login. 2. Submit login form empty. | Required fields prevent submission and indicate missing input. | Email input retained native required validity; browser validation message “Please fill out this field.” appeared. | PASS | [luna-auth-login.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login.png) | No data created. |
| AUTH-03 | Fresh context, unauthenticated, 1366×768 | 1. Open /login. 2. Enter QA email and incorrect password. 3. Submit. | Clear human-readable invalid-credentials feedback; remain unauthenticated. | Login API returned 401 and the page stayed at /login, but the login form displayed no visible error text after the response. | FAIL | [luna-auth-invalid.png](/home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-invalid.png) | **Major usability defect:** no visible explanation after rejected credentials. Repro steps above. No data created. |
| NAV-01 | Authenticated ordinary role, desktop 1366×768 | 1. Login via UI. 2. Click account avatar/name. | Account menu exposes profile and logout actions. | Menu rendered identity, department, “Thông tin cá nhân”, and “Đăng xuất”. | PASS | luna-auth-dashboard.png *(artifact thiếu; không dùng làm bằng chứng độc lập, xem kiểm tra chéo parent)* | None |
| AUTH-04 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /admin/users. | Ordinary role is denied or redirected with meaningful state. | URL remained /admin/users while body was empty at the observation point; insufficient evidence to distinguish denial, delayed render, or broken route. | NOT_RUN | No screenshot | Needs rerun after route/role behavior clarified. |
| AUTH-05 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /departments. | Ordinary role cannot access departments administration. | Redirected to /dashboard. | PASS | Dashboard screenshot above | No mutation. |
| AUTH-06 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /approvals. | Ordinary role cannot access approvals administration. | Redirected to /dashboard. | PASS | Dashboard screenshot above | No mutation. |
| AUTH-07 | Authenticated ordinary role, desktop 1366×768 | 1. Login. 2. Navigate directly to /knowledge-graph. | Unauthorized route denied or redirected. | URL stayed /knowledge-graph with empty body at observation time; inconclusive. | NOT_RUN | No screenshot | Needs route confirmation and rerun. |
| AUTH-08 | Fresh unauthenticated context, 1366×768 | 1. On /login, press password “HIỆN”. 2. Inspect input type. 3. Press “ẨN”. | Password changes between text and password. | Locator became stale after rerender and the evidence capture failed; no PASS claim. | NOT_RUN | None | Rerun needed with stable selector. |
| AUTH-09 | Authenticated ordinary role | 1. Login. 2. Select logout. 3. Use browser Back and refresh. | Session cleared and protected page remains inaccessible. | Not completed; no reliable evidence of logout/back/session semantics. | NOT_RUN | None | No cleanup required. |
| NAV-02 | Authenticated ordinary role, keyboard | 1. Tab through dashboard controls. 2. Open account menu. 3. Press Escape and inspect focus. | Keyboard focus is visible; Escape closes overlays and restores focus. | Not run. | NOT_RUN | None | — |
| NAV-03 | Authenticated ordinary role; 360×640, 390×844, 844×390 and 390×844 isMobile emulation | 1. Login. 2. Open nav drawer/account menu. 3. inspect horizontal overflow and tap targets at each viewport. | Navigation is usable without clipping/overflow. | Attempted mobile login, but first login form was not visible under isMobile emulation; stopped without interacting with shared tabs. | NOT_RUN | None | Mobile layout remains unassessed. |
| AUTH-10 | Unauthenticated, register form | 1. Submit register form empty. 2. Try malformed email/mismatched confirmation. | Safe validation; no account created without valid inputs. | Not run. | NOT_RUN | None | No account created. |

#### Notes

- /login presents login and registration forms in the same page; additional email/password inputs belong to the registration form and hidden auxiliary UI. Selectors must scope to the first login form.
- The disposable account and its existing QA-owned records were left intact because other acceptance work may use that account.
- Browser setup succeeded with the isolated MCP server. No shared default page was navigated, clicked, resized, or closed.




## Báo cáo thao tác nhóm Documents / approval — nguyên văn

### Production acceptance — documents (Luna)

Date: 2026-10-22 (Asia/Ho_Chi_Minh)  
Target: `https://chatbot.coremind.io.vn`  
Viewport: desktop 1366×768, zoom 100%, `isMobile=false`  
UI access: MCP Playwright only, dedicated contexts. Bootstrap tokens were used only to initialize the ordinary QA, manager, and other-department sessions; none are recorded here.

#### First-run note

The first runner initialization hit the shared-browser profile lock before any navigation (`Browser is already in use … use --isolated`). Parent enabled an isolated new MCP process; the retry succeeded. No production data was changed during the blocked attempt. Evidence from this successful run supersedes the initial blocker for cases actually completed below.

#### Fixture and handoff

The current Chat handoff fixture is **DOC-0051**, [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>), 186 B, visibility `Nội bộ`, department/workspace `Kỹ thuật` / `KB Kỹ thuật`. The owner session shows `Đã phê duyệt`; the same name appears in `/processing-status` → `Hoàn tất` with `TXT · 186 B` and `Hoàn tất · 1 chunks`. It is intentionally left active for Chat Luna C01/C02; parent coordinates final cleanup.

Synthetic content contains reference `DOCS-ACCEPTANCE-20261022-01`. Suggested Chat question: **“Theo tài liệu QA-20261022-DOCS-acceptance.txt, mã tham chiếu là gì?”** Expected answer is that synthetic reference. No RAG question was sent in this documents pass.

Earlier fixture DOC-0047 went through upload, manager approval, indexing, detail and downloads, then the test workflow deleted and restored it through the UI. A later list-menu delete moved DOC-0047 and its version-test candidate out of active rows; direct UI navigation to `/documents/47` redirected to `/documents`. A subsequent trash-panel check confirmed DOC-0047 and the candidate are retained in the 30-day trash with `Khôi phục` actions. The earlier “Thùng rác trống” observation was immediately after restoring DOC-0047, before that later delete. DOC-0051 was created as a replacement and remains active. Do not delete it before Chat tests.

#### Cases

| ID | Role / precondition | Human UI steps | Expected | Actual | Status | Evidence | Severity / cleanup |
|---|---|---|---|---|---|---|---|
| ENV-01 | MCP isolated context; ordinary disposable QA; desktop | 1. Bootstrap ordinary token into dedicated browser context. 2. Open `/dashboard`. | Production dashboard opens as ordinary QA. | Isolated runner succeeded; dashboard showed QA2 and loaded overview. Initial pre-isolation attempt had profile-lock error before navigation. | PASS (retry) | [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>); first blocked attempt recorded above | No app issue; no cleanup. |
| D01-LIST | Ordinary QA; documents list | 1. Open Documents. 2. Switch table → grid → table. 3. Search exact QA filename, then a nonexistent QA string, then clear. 4. Select TXT and Indexed filters, then reset type/status to All. | Layouts render; exact/empty searches differ; file type and status filters narrow; controls can be reset. | Table and grid rendered. Exact search returned QA file; nonexistent query showed “Không tìm thấy tài liệu”. TXT filter returned 1 document; All returned 2; Indexed returned 2; both filters reset to All. | PASS | [DOCS-replacement-list-filtered.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-list-filtered.png>); [DOCS-replacement-indexed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-indexed.png>); [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>) | No issue on exercised search/type/status variants. |
| D01-DEPT | Ordinary QA; DOC-0051 belongs to Kỹ thuật | 1. Search exact QA filename. 2. Select Kỹ thuật, then Ban Giám đốc. 3. Observe selected chip and row. 4. Reset to All. | Selected department filters rows to that department. | Both department clicks visibly made the selected chip active, but the Kỹ thuật QA row remained while Ban Giám đốc was selected. Reset to All succeeded. Reproduced with exact-name search and saved screenshot. | FAIL — S2 | [DOCS-dept-filter-mismatch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-dept-filter-mismatch.png>) | No data changed. Filter control gives incorrect results; workaround is search/status/type filtering. |
| D01-PAGE | Ordinary QA; current list had one page | 1. Observe pagination controls after All filters. 2. Inspect previous/next. | Multi-page navigation works when more than one page exists. | Only one page was available; previous and next were disabled. No multi-page fixture created. | NOT-RUN (data unavailable) | [DOCS-replacement-list-filtered.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-list-filtered.png>) | No conclusion about multi-page behavior. |
| D01-SORT | Ordinary QA; two visible documents | 1. Record row order. 2. Click Sắp xếp twice, waiting after each click. 3. Observe popup/state/order. | Sort action changes or exposes an order choice with visible feedback. | Both clicks left the same row order, opened no menu, and exposed no pressed/active state. With two rows dated 22/10 and 13/09, a sort toggle should have changed the order at least once. | FAIL — S2 | Sanitized result in [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>) | No data changed. |
| D02 | Ordinary QA; no matching filename initially | 1. Open Upload. 2. Choose synthetic TXT, inspect required date with blank selection. 3. Enter 2026-10-22 to 2026-10-29, select Internal, submit once. 4. Reload and open detail. | Required metadata blocks empty submission; valid file creates one record with metadata and clear pending/processing state. | Blank required date left upload disabled. Valid submit created one [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>); UI said upload succeeded and waiting approval; detail preserved dates, visibility, owner, size, and ID. Replacement is DOC-0051. | PASS | [DOCS-detail-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-pending.png>); [DOCS-replacement-list-filtered.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-list-filtered.png>); [DOCS-replacement-indexed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-indexed.png>) | DOC-0047 was superseded; DOC-0051 intentionally left active for Chat. |
| D03-VALIDATION | Ordinary QA; safe synthetic fixtures | 1. Select unsupported CSV and observe error. 2. Leave required date empty. 3. Enter expiration before effective date, observe validity, correct it. | Unsupported file and invalid/missing dates are rejected and can be corrected. | Unsupported CSV showed format error and Upload disabled. Blank required date disabled Upload. Expiration input had `min=2026-10-22`; 2026-10-21 was invalid (`Value must be 10/22/2026 or later.`); corrected date allowed the valid TXT upload. | PASS | [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>); `.playwright-mcp/QA-20261022-DOCS-unsupported.csv` | None. |
| D03-EMPTY | Ordinary QA; 0 B local TXT; no submit | 1. Select `QA-20261022-DOCS-empty.txt`. 2. Set effective date to 2026-10-22. 3. Observe form validation and stop before submit. | Empty file is rejected with clear validation. | UI accepted the 0 B selection, displayed `0 B • TXT`, showed no error, and enabled Upload once the required date was set. Per instruction, request was not submitted. | FAIL — S2 | [DOCS-empty-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-empty-validation.png>) | No record created; local fixture only. |
| D03-LIMIT | Ordinary QA; 51 MiB sparse local TXT; no submit | 1. Select `QA-20261022-DOCS-51mb.txt`. 2. Set effective date to 2026-10-22. 3. Observe limit validation and stop before submit. | UI advertises maximum 50 MB and rejects larger files before submission. | UI displayed `51.0 MB • TXT` despite “Tối đa 50MB”; no validation error appeared and Upload was enabled. Per instruction, request was not submitted. | FAIL — S2 | [DOCS-oversize-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-oversize-validation.png>) | No request/record created; sparse local fixture only. |
| D04 | Ordinary QA; DOC-0047 existed at time of duplicate test | 1. Select same basename [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>) with short synthetic content. 2. Enter valid dates and submit once. | Duplicate is surfaced; no silent second document is created. | UI displayed “Tên tệp đã tồn tại. Chọn tạo tài liệu riêng hoặc mở tài liệu hiện có để thêm phiên bản mới.” Original remained one row. Modal was canceled; no duplicate record created. | PASS | [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>); [DOCS-detail-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-pending.png>) | No duplicate cleanup needed. |
| D05-APPROVE | Ordinary QA; department manager TĐA | 1. Manager opens Approvals and previews only QA fixture. 2. Approve and confirm dates. 3. Reload owner detail. | Authorized reviewer previews correct file; approval state is reflected. | DOC-0051 was previewed and approved after date confirmation; owner detail changed to `Đã phê duyệt`; processing later completed. | PASS | [DOCS-approval-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-approval-pending.png>); [DOCS-manager-approved.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-manager-approved.png>); [DOCS-replacement-approval-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-approval-pending.png>); [DOCS-replacement-indexed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-indexed.png>) | DOC-0051 remains approved for Chat. |
| D05-REJECT | Ordinary QA fixture DOC-0054; manager TĐA | 1. Manager opens pending item. 2. Choose Reject, enter required reason, submit. 3. Owner opens detail and reloads. | Reject requires a reason; owner sees rejected badge and reason after reload. | Manager reason field was required and accepted the QA reason; queue cleared. Owner detail after reload showed status `Từ chối`, but neither that reason nor a rejection event/reason appeared in detail/activity. | FAIL — S2 (reason not surfaced to owner) | [DOCS-reject-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-pending.png>); [DOCS-reject-reason-ready.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-reason-ready.png>); [DOCS-reject-owner-reloaded.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-owner-reloaded.png>) | DOC-0054 (ID `DOC-0054`) was soft-deleted by its owner through detail UI after verification; UI trash contains this QA record with a restore action. It was not purged. DOC-0051 was untouched. |
| D06 | Ordinary QA; manager review complete | 1. Open processing status. 2. Select Completed. 3. Match filename, size, workspace, chunk count. 4. Reload and reselect Completed. | Same document can be traced; approved and indexed are distinct; final state reports completion and refresh does not lose job state. | Completed tab displayed the matching QA filename, `Kỹ thuật`, `TXT · 186 B`, and `Hoàn tất · 1 chunks`; detail separately showed `Đã phê duyệt`. Reload reset the selected tab to in-progress (empty list) while the Completed counter stayed 1; reselecting Completed showed the record. | PASS | [DOCS-replacement-indexed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-indexed.png>) | DOC-0051 active for Chat; no restart/API checks used. |
| D07 | Ordinary QA; TXT detail | 1. Open fixture from list. 2. Read preview and metadata. 3. Return through Documents breadcrumb. | Correct record opens; Vietnamese content and metadata display without stuck loading. | TXT preview rendered all synthetic Vietnamese lines and reference. Dates, owner, workspace, visibility, approval state, version history, and ID displayed. | PASS (TXT variant) | [DOCS-detail-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-pending.png>); [DOCS-detail-v2.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-v2.png>) | PDF/other-format rendering not tested; only TXT fixture was in scope. |
| D08 | Ordinary QA; DOC-0047 versions and other-department account | 1. Download current file via detail button. 2. Download V2 and V1 via version history. 3. Compare downloaded bytes to local synthetic fixtures. 4. In other-department context, list docs and open observed direct detail URL. | Downloads match requested version; unauthorized context cannot read document via list or URL. | DOC-0047 current file (186 B), V2 (191 B), and V1 (186 B) downloaded through UI; each exactly matched its synthetic source. Other-department UI list omitted QA file and direct `/documents/47` redirected to its own list. Share/copy-link behavior and replacement DOC-0051 download were not run. | BLOCKED (partial) | Download artifacts [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>), `version1-…(V 1.0).txt`, `version2-…(V 2.0).txt`; byte equality checked locally; no other-user screenshot retained because it included unrelated document names. | No leak observed for DOC-0047; DOC-0051 remains active for Chat. |
| D10 | Ordinary QA, other-department read-only QA; owned DOC-0047 | 1. Open detail delete confirmation. 2. Cancel and verify detail remains. 3. Confirm delete. 4. Restore via trash. 5. Delete again via list menu. 6. Verify other-department list and direct URL access. | Cancel preserves data; restore returns only owned fixture; unauthorized user cannot read it through direct URL; delete retains item in trash. | Cancel kept detail; detail delete moved it to trash; restore returned it to active list. Later list-menu delete removed it and the version-test candidate from active rows. Trash panel subsequently showed both QA records with `Khôi phục`; direct URL redirected and other-department list omitted DOC-0047. This is consistent with soft delete; no permanent-delete issue confirmed. | PASS (delete/cancel/restore/access) | [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>); [DOCS-detail-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-pending.png>); trash state recorded as sanitized UI observation (no screenshot retained due unrelated QA names in list) | DOC-0047 and version-test candidate remain in 30-day trash. DOC-0051 is active and must remain until Chat tests finish. |
| D-MOBILE | Ordinary QA; viewport only changed in own context | 1. At 390×844 and 360×640 open Upload. 2. Select two small QA TXT fixtures, including a long filename. 3. Set required date. 4. Check footer position/visibility and cancel; do not submit. | Upload footer remains reachable by normal screen/modal scroll and multiple filenames remain usable. | At both viewports, two files loaded; Upload button remained within viewport (390×844: top 744, bottom 784; 360×640: top 550, bottom 590). Footer was visible without page scroll; dialog was canceled each time. | PASS (viewport-only responsive check) | [DOCS-mobile-upload-390x844.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-mobile-upload-390x844.png>); [DOCS-mobile-upload-360x640.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-mobile-upload-360x640.png>) | No upload submitted. This does not test `isMobile:true`, keyboard, pinch zoom, or U02. |

#### Counts and limits

`PASS`: 11 (ENV-01 retry, D01-LIST, D02, D03-VALIDATION, D04, D05-APPROVE, D06, D07 TXT variant, D09 pending-version semantics, D10, D-MOBILE).  
`FAIL`: 5 (D01-DEPT, D01-SORT, D03-EMPTY, D03-LIMIT, D05-REJECT reason visibility), all classified S2.  
`BLOCKED`: 1 (D08 share/copy-link and DOC-0051 download variants).  
`NOT-RUN`: 2 (D01-PAGE multi-page data unavailable; D09 candidate approval→indexed→current activation). No multi-page dataset was created.

No blanket document acceptance is claimed. The confirmed issues are ineffective department and sort controls, enabled submission controls for empty and >50 MB files, and no owner-visible rejection reason/history after reload. Remaining variants include multi-page traversal, share/copy-link, DOC-0051 download, and approved-version activation. DOC-0051 remains active and untouched for Chat tests. DOC-0054 alone was soft-deleted after the rejection test; no other trash entries were changed in this follow-up. No app source, deployment, containers, or existing business records were modified.



## Báo cáo thao tác nhóm Chat / expert / graph — nguyên văn

### Luna report — C: chat/RAG, Expert, graph

Date: 2026-10-22, ICT (observed UI timestamps approx. 09:51–10:22). Target: `https://chatbot.coremind.io.vn`. Evidence is under `harness/reports/acceptance-20261022/`.

#### Run context

- Chat/Expert/mobile: desktop or mobile-emulated Playwright context using the parent-provided ordinary QA account (`QA2`), token injected only to establish the session. No password login was attempted here.
- Graph: separate Playwright context with parent-provided Admin session. Isolation check: separate context with the supplied other-department read-only account.
- Desktop viewport 1366×768. Mobile composer check: viewport 390×844, `isMobile:true`, `hasTouch:true`, DPR 2. No app code, config, production records, users, or documents were changed.
- Paid chat/RAG questions: seven total (two exploratory before the replacement-fixture handoff, four earlier questions against the handed-off fixture, and one additional QA51 history-seed question for this follow-up); no further questions were sent. Any pre-handoff responses are excluded from C01/C02 fixture evidence. The C05 fault-injection message was intercepted and aborted in the browser before reaching the app/backend, so it was not a paid request.
- QA fixture handoff: `DOC-0051`, [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>), 186 B, Nội bộ, KB Kỹ thuật, approved, processing Hoàn tất / 1 chunk. QA reference: `DOCS-ACCEPTANCE-20261022-01`. No fixture cleanup performed; parent owns it.

#### Results

| ID / variant | Role / device | Status | Actual and evidence | Cleanup / notes |
|---|---|---|---|---|
| C01 — workspace, blank input, fixture question, stream | QA2 / desktop | PASS | Opened Chat and confirmed the active workspace was `KB Kỹ thuật` (the fixture workspace); the selector exposed the available workspaces. Blank composer kept Send disabled. Suggested-question chips populated the composer and required a separate Send action. Sent the handed-off fixture question: “Theo tài liệu QA-20261022-DOCS-acceptance.txt, mã tham chiếu là gì?” Final answer was `Mã tham chiếu là DOCS-ACCEPTANCE-20261022-01.` in 6.1 s. A same-fixture follow-up showed the visible analyzing state at 0.5 s and completed in 6.8 s. See [luna-chat-doc51-answer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-answer.png>), [luna-chat-memory-loading.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-loading.png>), [luna-chat-memory-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-final.png>). | QA2 history cleared and verified empty after reload. |
| C02 — citation to original fixture | QA2 / desktop | PASS | Clicked citation `[yr76]` in the answer. In-app preview opened [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>); its text contained the same reference supporting the answer. Filename, reference, and preview-close control were visible. See [luna-chat-doc51-citation-open.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-citation-open.png>). | No document edits. |
| C03a — follow-up memory | QA2 / desktop | PASS | Asked “Vừa rồi tài liệu nêu mã tham chiếu nào?” The answer retained the exact reference from the prior turn. See [luna-chat-memory-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-final.png>). | History cleared after checks. |
| C03b — unsupported fact | QA2 / desktop | PASS | In the same conversation, asked “Tài liệu nêu ngày nào quy định này bắt đầu áp dụng?” The assistant said the permitted source lacked enough information. See [luna-chat-insufficient-info.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-insufficient-info.png>). | This is a refusal/grounding check, not a relevance defect. |
| C03c — copy answer | QA2 / desktop | PASS | Granted clipboard permissions to this test context, clicked the visible Copy button, and read clipboard via `navigator.clipboard.readText()`. Clipboard matched the displayed follow-up answer and citation marker. See [luna-chat-copy.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-copy.png>). | Clipboard permission was context-local. |
| C04a — reload persistence | QA2 / desktop | PASS | The two-turn handed-off-fixture conversation remained visible after reloading `/chat`. See [luna-chat-doc51-history-reload.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-history-reload.png>). | Then cleared own QA2 chat. |
| C04b — clear confirmation/cancel | QA2 / desktop | PASS | Opened “Xóa lịch sử?”, clicked “Không”; both turns remained. Reopened confirmation, clicked “Có”, reloaded, and saw the initial chat view with no prior turns. See [luna-chat-clear-cancel.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-clear-cancel.png>), [luna-chat-cleanup-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-cleanup-final.png>). | Only QA2 history created in this run was cleared. |
| C04c — user history isolation | Other-department read-only user / desktop | PASS | While QA2 had its own messages, initialized a separate supplied other-user session. Its Chat opened to its own `KB Nhân sự` initial view; neither QA2 question nor citation markers appeared. See [luna-chat-other-user-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-other-user-history.png>). | No messages sent as the other user. |
| C04d — workspace A→B→A and logout/login persistence | QA2 / desktop, fresh no-token-injection context | PASS | After UI login, sent the one authorized QA51 reference question (answer matched). Switched `KB Kỹ thuật` → `Default Workspace` (0 docs) → `KB Kỹ thuật`; the original question, answer, and citation remained on return. Used the account menu to log out; UI returned to Login. Re-entered the parent-provided credentials through the login form in the same context, reopened Chat, and verified the same QA51 history remained. Evidence: [luna-c04-seed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-seed.png>), [luna-c04-workspace-b.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-b.png>), [luna-c04-workspace-a-return.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-a-return.png>), [luna-c04-logout.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-logout.png>), [luna-c04-login-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login-history.png>). | No static token init script was used. The QA51 history was cleared after the C05 check. |
| C05a — mode visibility/selection by role | QA2 and Admin / desktop | PASS | Ordinary Chat showed no mode combobox or system-prompt control. Admin Chat showed Hybrid / Vector only / Graph only and the system-prompt button. Selected Vector only, verified the value, then restored Hybrid; no query was sent. No document picker was visible. Evidence: [luna-c05-admin-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-admin-mode.png>); ordinary initial Chat snapshot is represented in [luna-chat-cleanup-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-cleanup-final.png>). | UI control visibility/selection only; no retrieval comparison across modes. |
| C05b — simulated stream abort and retry state | QA2 / desktop, fault injection | PASS | Before sending the second message, installed a page-local abort route for `/api/v1/rag/chat/**` plus an API fallback. UI POST path `/api/v1/rag/chat/8/stream` was intercepted and aborted before network delivery. In 1.2 s the UI displayed `Failed to fetch` and “Đưa câu hỏi vào ô nhập để thử lại”; loading stopped and the composer was enabled. Screenshot: [luna-c05-aborted-stream.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-aborted-stream.png>). | Fault injection only; not a production outage. The failed message was not sent to the model. No retry was clicked. |
| C06a — Expert relevant query/cards | QA2 / desktop | PASS | Selected `KB Kỹ thuật`; searched “quy trình phê duyệt tài liệu”. UI returned two ranked cards (QA Acceptance 20261022 and Admin Hệ Thống) with relevance scores and “Hỏi về tài liệu” / “Xem tài liệu” buttons. See [luna-expert-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-search.png>). | Rank quality is limited to this observed query. |
| C06b — Expert document link | QA2 / desktop | PASS | Clicked “Xem tài liệu” on the QA contact card. UI opened the Documents list; the QA-owned entries included the handed-off [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>). See [luna-expert-card-detail.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-card-detail.png>). The list displayed five QA-owned documents, consistent with the card’s QA owner. | No document opened for editing. |
| C06c — no-match search / empty state | QA2 / desktop | FAIL — S2 | Searched `QA-20261022 no-match xylophone 918273` in KB Kỹ thuật. UI still returned two contacts at 66% and 60%, rather than a clear empty/no-match result. Screenshot: [luna-expert-empty-results.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-empty-results.png>). This is evidence of weak no-match handling for this deliberately unrelated query; it does not establish that the earlier broad RAG abstention was wrong. | Repro: Expert → KB Kỹ thuật → enter exact no-match string → Find contact. |
| C06d — Ask about result link | QA2 / desktop | NOT-RUN | A bounded click attempt timed out waiting for the old Expert result button after navigation/state changed; no reliable destination evidence was captured. | No claim about link target/context. |
| C07a — Admin graph workspace switch/data/empty/return | Admin / desktop | PASS | Graph opened in Admin context. KB Kỹ thuật showed graph data; switched to KB Kinh doanh and observed 43 entities / 37 links; switched to Default Workspace and saw an explicit no-graph-data message; returned to KB Kinh doanh and confirmed its data restored. Evidence: [luna-graph-admin.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-admin.png>), [luna-graph-business.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-business.png>), [luna-graph-empty.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-empty.png>). | No graph build or mutation. |
| C07b — node hover/focus and zoom/fit | Admin / desktop | PASS | Hovered a visible canvas node and saw a tooltip with its label/type; clicked the node and the graph focused/zoomed it. Clicked Zoom In and “Vừa toàn bộ màn hình” (fit). Evidence: [luna-graph-node-hover.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-hover.png>), [luna-graph-node-focus.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-focus.png>), [luna-graph-interactions.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-interactions.png>). | A sidebar detail pane was not observed; side panels showed graph counts and top entities. Pan and legend-filter interactions were not run. |
| Chat composer mobile viewport supplement | QA2 / 390×844 touch-emulated | PASS (composer visibility only) | Confirmed `innerWidth/Height=390×844`, DPR 2, touch and coarse pointer enabled. Composer rectangle was within viewport (`x=20,y=782,w=302,h=42,bottom=824`) and remained accessible in the initial view. Screenshot: [luna-chat-mobile-touch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-mobile-touch.png>). | Does not certify all of U01/U04; no real mobile keyboard was available and no pinch zoom was tested. |

#### Relevance observation kept separate from a defect

Before the replacement-fixture handoff, one broad question about what the test document included returned an explicit “not enough information” abstention plus four unrelated source citations from KB Kỹ thuật. The assistant did **not** answer with unsupported business facts. Because the question was broad and the handoff later established a replacement fixture, this is not counted as a C01/C02 failure or a confirmed relevance bug. The query/source behavior is visible in [luna-chat-answer1.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-answer1.png>) and [luna-chat-sources.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-sources.png>); the cited source opened an unrelated document in [luna-chat-source-open.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-source-open.png>). Sol can decide whether this exploratory observation merits a separate retrieval query after reviewing the exact source and replacement-fixture evidence.

On the Business graph, the rendered graph reported 37 links while the visible “Thực thể trọng tâm” degree badges read `0`; node hover/focus worked. This is recorded as an observation for Sol to inspect, not declared a defect from UI evidence alone.

#### Evidence files

All paths below are relative to `harness/reports/acceptance-20261022/`:

- Chat: [luna-chat-doc51-answer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-answer.png>), [luna-chat-doc51-citation-open.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-citation-open.png>), [luna-chat-memory-loading.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-loading.png>), [luna-chat-memory-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-final.png>), [luna-chat-insufficient-info.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-insufficient-info.png>), [luna-chat-copy.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-copy.png>), [luna-chat-doc51-history-reload.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-history-reload.png>), [luna-chat-clear-cancel.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-clear-cancel.png>), [luna-chat-cleanup-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-cleanup-final.png>), [luna-chat-other-user-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-other-user-history.png>), [luna-chat-mobile-touch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-mobile-touch.png>), [luna-c04-login.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login.png>), [luna-c04-seed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-seed.png>), [luna-c04-workspace-b.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-b.png>), [luna-c04-workspace-a-return.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-a-return.png>), [luna-c04-logout.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-logout.png>), [luna-c04-login-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login-history.png>), [luna-c05-aborted-stream.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-aborted-stream.png>), [luna-c04-c05-cleanup.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-c05-cleanup.png>).
- Expert: [luna-expert-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-search.png>), [luna-expert-card-detail.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-card-detail.png>), [luna-expert-empty-results.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-empty-results.png>).
- Graph: [luna-graph-admin.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-admin.png>), [luna-graph-business.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-business.png>), [luna-graph-empty.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-empty.png>), [luna-graph-node-hover.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-hover.png>), [luna-graph-node-focus.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-focus.png>), [luna-graph-interactions.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-interactions.png>). Admin mode selector: [luna-c05-admin-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-admin-mode.png>).

#### Residual coverage

- Not run: C05 comparison of retrieval outputs across Admin modes and any document picker (none was visible); C06 “Ask about documents” destination/context; graph pan and legend filters; real-device keyboard/pinch behavior.
- Fixture residual data: none created by this scope. Parent-provided `DOC-0051` remains for parent-owned cleanup.
- Scope cleanup complete: QA2 chat messages created during this run were cleared and verified absent after reload. No other account’s data was changed.



## Báo cáo thao tác nhóm Knowledge / workspace — nguyên văn

### D — Knowledge & workspace acceptance report (Luna)

**Status: FINAL** — assigned UI scope completed; production UI only. **Target:** `https://chatbot.coremind.io.vn`  
**Run:** 2026-10-22, 09:58–10:05 ICT (Asia/Ho_Chi_Minh). Production build/version not exposed.  
**Roles:** disposable ordinary QA user, Admin, manager, and other-department read-only QA user in separate dedicated Playwright contexts. No credentials/tokens recorded.  
**Viewports:** desktop 1366×768; mobile emulation `isMobile:true`, DPR 1 at 360×640 and 390×844.  
**Scope:** K01–K05 and responsive knowledge/workspace forms. No application code/config changes; no non-QA business records changed; no LLM requests. All test actions were through the UI. Request/response metadata was inspected only to diagnose UI-triggered edit, approval, and permission outcomes.

#### Findings

- **Knowledge edit/version behavior:** the tested action was the visible **Chỉnh sửa** button; its modal was titled “Chỉnh sửa tri thức” and prefilled with the existing title. **Cập nhật** emitted `PUT /api/knowledge/1` (HTTP 200), not a create-form request. The UI/API response created version ID 2 (`QA-20261022-KNOW-Luna-Draft-Edited`, `supersedes_entry_id=1`). A diagnostic repeat from ID 1 again used `PUT /api/knowledge/1`, created ID 4 (`QA-20261022-KNOW-Luna-Draft-ReproEdit`, `supersedes_entry_id=1`), and left original ID 1 visible. The two edits are sibling versions created via the edit route; this was not accidental use of create. The versions appeared as separate cards and survived reload. The acceptance case’s edit/save/reload passed. Whether listing multiple active sibling versions is intended version history or could expose stale content in retrieval was not established; no RAG query was run against these private entries.
- **Approval vs ingestion state:** internal ID 3 initially showed `Chờ duyệt cấp phòng`; its diagnostic state was `approval_status=pending_dept`, `ingest_status=pending`. Manager preview and approval succeeded. Afterward a UI-triggered list response showed `approval_status=approved`, `ingest_status=indexed`, `status=Active`; ordinary user search and reload still found it. The card continued to display `Chờ xử lý` after indexing completed. This label is not the approval state; it is a stale/mismatched processing label (S2).
- **Workspace permissions:** ordinary user could choose department/public radios, but UI warned save might be denied. With parent authorization, a department fixture received `POST /api/v1/workspaces` HTTP 403 and “Chỉ Admin hoặc Trưởng phòng mới được tạo workspace phòng ban”; a public fixture received HTTP 403 and “Chỉ Admin mới được tạo workspace công khai”. Neither appeared in the list after submit.
- **Mobile workspace form:** at 360×640, create dialog footer remained at y=658.5–704.5; no descendant was scrollable, and `scrollIntoViewIfNeeded()` left it offscreen. Clicking **Hủy** timed out because it remained outside the viewport. Escape safely closed the unsaved form. At 390×844, footer bounds y=760.5–806.5 were in view. Knowledge form footer at 360×640 could be scrolled into view.
- **Cleanup:** all four own knowledge records (IDs 1–4) are in knowledge trash; deleting version ID 4 through the UI removed its version family (IDs 1/2/4). Approved ID 3 was separately deleted after verification. The own private workspace is in workspace trash. Trash UI offers restore for 30 days but no permanent-delete control. Knowledge-generated `.md` rows no longer appeared in Documents exact-title search after cleanup. The other test group’s [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>) was not changed.

#### Case results

| ID | variant / role / device | Status | Actual and evidence | Cleanup / notes |
|---|---|---|---|---|
| K01 | ordinary; desktop | PASS (inline card detail) | Initial list showed 0. An impossible search showed “Không tìm thấy tri thức phù hợp”; clearing reset it. QA content was fully readable in cards. Category `Chung`, status `Bản nháp`, and grid/list controls were exercised; the no-results state was distinct. There is no separate detail page/control surfaced; full content is inline. Evidence: [knowledge-create-modal.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-create-modal.png>), [knowledge-pending-filter.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-pending-filter.png>), [knowledge-list-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-list-mode.png>). | Used only own QA content. |
| K02 | ordinary; desktop | PASS — create/edit/reload/cancel; version-list intent needs product review | Blank form submit disabled; valid personal fixture ID 1 saved and survived reload. **Chỉnh sửa** opened a prefilled edit modal. `PUT /api/knowledge/1` returned ID 2; repro through the same edit flow returned ID 4, both `supersedes_entry_id=1`. Original and edited versions remained separate cards after reload. Delete-confirm **Hủy** preserved the item. Evidence: [knowledge-create-filled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-create-filled.png>), [knowledge-created.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-created.png>), [knowledge-edit-before.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-edit-before.png>), [knowledge-edited.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-edited.png>), [edit-original-before-repro.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/edit-original-before-repro.png>), [edit-original-after-repro.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/edit-original-after-repro.png>), [knowledge-delete-cancel-dialog.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-delete-cancel-dialog.png>). | IDs 1, 2, 4 soft-deleted; all are in own trash. No retrieval query to assess superseded-version impact. |
| K03a | ordinary submit → manager preview/approve → ordinary reload; desktop | PASS — approval lifecycle | Ordinary internal fixture ID 3 showed `Chờ duyệt cấp phòng` and appeared in manager Approvals → `Tri thức 1`. Manager preview showed the synthetic content. Date confirm was effective `2026-10-22`, no expiration; manager approved only this QA item. Manager queue then showed no pending knowledge. Ordinary search and reload retained the approved item. Evidence: [knowledge-internal-submitted.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-internal-submitted.png>), [manager-knowledge-approvals.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-knowledge-approvals.png>), [manager-knowledge-preview.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-knowledge-preview.png>), [manager-approval-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-approval-confirm.png>), [manager-approval-done.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-approval-done.png>), [ordinary-approved-after-manager.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/ordinary-approved-after-manager.png>). | ID 3 soft-deleted after verification; in own trash. |
| K03b | ordinary after manager approval; desktop | FAIL — S2 status display | Ordinary card continued to say `Chờ xử lý` after UI-triggered state showed `approved`, `indexed`, and `Active`. Do not confuse this label with approval state. Evidence: [ordinary-approved-after-manager.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/ordinary-approved-after-manager.png>). | No data left active. |
| K04a | ordinary private CRUD; desktop | PASS | Created `QA-20261022-WS-Luna-Private`, description, `Local Search`; list/search/reload retained it. Edited description and mode to `Naive (BM25)`; reload retained both. Private filter included it and department filter excluded it. Cancel-delete left it present. Existing-workspace edit disabled scope radios and stated scope cannot change. Evidence: [workspace-created.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-created.png>), [workspace-delete-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-delete-confirm.png>), [workspace-restored.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-restored.png>). | Deleted/restored/deleted; private workspace in own trash. |
| K04b | ordinary department/public negative tests; desktop | PASS — denied | Department fixture `QA-20261022-WS-Luna-DeptPermission`: UI submit got 403 and role-specific toast. Public fixture `QA-20261022-WS-Luna-PublicPermission`: UI submit got 403 and Admin-only toast. Exact searches found no created rows. Evidence: [workspace-department-permission-before-submit.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-department-permission-before-submit.png>), [workspace-department-permission-result.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-department-permission-result.png>), [workspace-public-permission-before-submit.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-public-permission-before-submit.png>), [workspace-public-permission-result.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-public-permission-result.png>). | No unexpected records to clean. |
| K04c | ordinary / other-department / Admin visibility; desktop | PASS for observed scope | While private workspace was active, other-department user exact searches returned no QA private workspace or QA knowledge; Admin could see QA items. Admin inspection was read-only except the explicitly authorized manager approval of ID 3. Evidence: [other-user-knowledge-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/other-user-knowledge-search.png>), [admin-knowledge-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/admin-knowledge-search.png>). | No other user’s records changed. |
| K04d | ordinary; 390×844 mobile | PASS | Workspace create footer bounds y=760.5–806.5 within viewport. Evidence: [mobile390-workspace-footer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile390-workspace-footer.png>). | Form canceled. |
| K04e | ordinary; 360×640 mobile | FAIL — S2 | Workspace modal bounds 0–640; footer stayed y=658.5–704.5, with no scrollable descendant. Normal scroll-into-view did not move it; **Hủy** click timed out as offscreen; Escape safely closed unsaved form. Knowledge submit footer moved from y=747 to y=543 on scroll. Evidence: [mobile360-workspace-form.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-workspace-form.png>), [mobile360-workspace-department-choice.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-workspace-department-choice.png>), [mobile360-knowledge-footer-scrolled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-knowledge-footer-scrolled.png>). | No data created in this mobile attempt. |
| K05 | ordinary; desktop; no LLM | PASS for supported selectors | Restored QA workspace appeared in Chat and Expert selectors. Selecting it changed Chat heading/composer and Expert label. Both showed 0 docs; no query sent. Documents page exposed department filters but no workspace selector. Evidence: [chat-workspace-menu.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/chat-workspace-menu.png>), [workspace-in-chat-selector.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-chat-selector.png>), [expert-workspace-menu.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/expert-workspace-menu.png>), [workspace-in-expert.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-expert.png>), [workspace-in-documents.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-documents.png>). | Workspace returned to trash after selector checks. |

#### Additional verification

- Workspace create with blank name disabled **Tạo mới**; valid private name enabled it. Knowledge required title/date/content before **Đề xuất phê duyệt** enabled.
- Admin saw QA records read-only; manager approved only ID 3 using the UI and confirmed its effective date.
- Exact search in Documents for `QA-20261022-KNOW-Luna` returned no items after knowledge cleanup. No document row outside our prefix was modified.
- Final `/knowledge` and `/workspaces` route interval had no console/page errors or HTTP responses ≥400 after listeners were attached ([final-workspaces-cleaned.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/final-workspaces-cleaned.png>)); this does not cover all prior interaction time.

#### Evidence

Screenshots are in `harness/reports/acceptance-20261022/`. The knowledge IDs above were read from responses to UI-triggered requests for diagnosis; no direct API call created, edited, approved, or deleted a record.

**Final cleanup state:** knowledge IDs 1, 2, 3, and 4 are soft-deleted in the QA knowledge trash; `QA-20261022-WS-Luna-Private` is soft-deleted in workspace trash. Department/public negative-test workspaces were denied (403) and were never created. No LLM requests were made. No application code was changed.



## Kiểm tra chéo và các kết quả ghi đè của parent

### Kiểm tra chéo của parent bằng MCP Playwright

Đích https://chatbot.coremind.io.vn, ngày 22/10/2026. Tất cả kết quả dưới đây là thao tác UI live, không suy ra từ mã. Context riêng, tài khoản nhân viên QA; không thay mật khẩu hoặc dữ liệu nghiệp vụ.

#### Kết quả

| ID | Điều kiện và các bước chạy lại | Mong đợi | Quan sát thực tế | Kết quả | Bằng chứng |
|---|---|---|---|---|---|
| ROOT-AUTH-ERROR | Context sạch 1366×768. 1. Mở login. 2. Điền email QA và mật khẩu sai. 3. Bấm Đăng nhập. 4. Đợi phản hồi và tìm thông báo trên toàn trang, không chỉ trong form. | Lỗi rõ ràng, không cấp phiên. | API 401; thông báo **Đăng nhập thất bại** hiển thị ở phía trên, ngoài thẻ form. Báo lỗi AUTH-03 của Luna là false positive do phạm vi locator. | PASS; bác bỏ FAIL ban đầu | [root-auth-invalid-visible.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-auth-invalid-visible.png>) |
| ROOT-AUTH-PASSWORD | Tại login desktop. 1. Nhập mật khẩu thử. 2. Bấm HIỆN. 3. Bấm ẨN. | Đổi kiểu input mà không mất giá trị. | type đổi `password → text → password`. | PASS | Kết quả MCP Playwright trong lịch sử thread; không lưu mật khẩu. |
| ROOT-MOBILE-LOGIN | Context `isMobile:true, hasTouch:true, DPR:3`, 390×844, zoom100%. 1. Mở login. 2. Điền tài khoản QA ở `form:visible`. 3. Chạm/bấm nút Đăng nhập bằng thao tác thông thường. | Nút nhận được chạm; đăng nhập thành công. | Click timeout vì lớp trang trí của overlay desktop chặn pointer. Nút ở x40,y446,w310,h48; elementFromPoint tại giữa nút là vòng tròn trang trí. `visualViewport.scale=1`. Overlay desktop có z20 nhưng không ẩn ở mobile, form mobile z10. **S1: luồng đăng nhập mobile bị che**, dù có thể đi vòng bằng phím Enter. Không phải lỗi pinch zoom. | FAIL | [root-mobile-login-overlay.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-mobile-login-overlay.png>) |
| ROOT-MOBILE-ENTER | Tiếp ca trên. 1. Đặt focus ở mật khẩu. 2. Nhấn Enter. | Gửi form và xác thực đúng. | Tới dashboard, menu tài khoản hiển thị. Đây là cách đi vòng, không làm ROOT-MOBILE-LOGIN thành PASS. | PASS (workaround) | [root-mobile-dashboard.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-mobile-dashboard.png>) |
| ROOT-ROLES | Đã đăng nhập nhân viên. 1. Mở lần lượt `/admin`, `/departments`, `/graph-knowledge`, `/approvals`. 2. Đợi điều hướng hoàn tất. | Không truy cập UI đặc quyền; về dashboard. | Cả bốn route đều chuyển về `/dashboard`. Luna trước đó dùng sai `/admin/users` và `/knowledge-graph`; hai URL sai đó không phải phép thử quyền route thật. | PASS ở mức UI redirect; không chứng nhận toàn bộ API RBAC | MCP trả danh sách requested/actual bốn route trong lịch sử thread. |
| ROOT-MOBILE-NAV | Đã đăng nhập. Lặp ở360×640,390×844,844×390. 1. Mở menu. 2. Chạm Tài liệu. 3. Mở lại menu, về Tổng quan. | Link đi đúng trang, drawer đóng, không tràn ngang. | Ba kích thước đều tới documents/dashboard; drawer đóng; scrollWidth không vượt innerWidth. | PASS cho các thao tác đã nêu | [root-mobile-dashboard.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-mobile-dashboard.png>) và kết quả MCP từng viewport. |
| ROOT-SESSION-RELOAD | Sau đăng nhập mobile bằng Enter. 1. Reload dashboard. 2. Đợi menu tài khoản. | Phiên được giữ. | Dashboard và menu tài khoản vẫn có. | PASS | Cùng context ROOT-MOBILE-NAV. |
| ROOT-LOGOUT | Cùng context mở thêm tab documents. 1. Ở tab đầu mở menu→Đăng xuất. 2. Quan sát hai tab. 3. Back rồi Reload tab đầu. | Xóa phiên; hai tab và back/reload không lộ trang bảo vệ. | Hai tab đều `/login`; token localStorage không còn; không có menu tài khoản; Back/Reload vẫn login. | PASS cho Chrome/Chromium session đã thử; không chứng nhận BFCache Safari thật | [root-logout-mobile.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-logout-mobile.png>) |
| ROOT-GRAPH-SWITCH | Admin desktop1366×768. 1. Mở graph. 2. Đợi KB Kỹ thuật tải thật. 3. Chọn KB Kinh doanh. 4. Đợi request hoàn tất. | Tên workspace và dữ liệu thay đổi đồng bộ. | Kỹ thuật28thực thể/18liên kết; Kinh doanh43/37. Không tính lượt snapshot trước khi fetch xong là empty bug. | PASS riêng chuyển workspace/hiển thị số liệu; node/pan/zoom do nhóm C kiểm tra | [root-graph-business.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-graph-business.png>) |
| ROOT-GOOGLE | Login desktop, chưa đăng nhập. 1. Bấm Đăng nhập với Google. 2. Quan sát điều hướng và UI. | Mở luồng OAuth hoặc nói rõ chưa hỗ trợ. | URL giữ nguyên, không có dialog hoặc trạng thái mới; mã hiện tại cũng không gắn handler cho nút. Chưa có xác nhận OAuth thuộc phạm vi nghiệm thu. | FAIL S2 đối với điều khiển đang hiển thị; Sol cần quyết định phạm vi | [root-auth-placeholder-actions.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-auth-placeholder-actions.png>) |
| ROOT-FORGOT | Login desktop. 1. Bấm Quên mật khẩu?. | Có luồng phục hồi/hướng dẫn hoặc thông báo rõ. | Chỉ chuyển `/login` thành `/login#`, không có luồng phục hồi. | FAIL S2 đối với link đang hiển thị | Cùng ảnh placeholder. |
| ROOT-UNKNOWN | Context sạch. 1. Mở `/qa-nonexistent-20261022`. 2. Đợi network idle. | Trang404/điều hướng rõ và đường quay lại. | Nội dung body rỗng, không có link quay về. | FAIL S2 | [root-unknown-route.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-unknown-route.png>) |
| ROOT-KNOW-ERROR | Nhân viênQA. 1. Trong context Playwright chặn duy nhất GET `/api/knowledge`, trả503 tổng hợp. 2. Mở trang Tri thức và đợi hoàn tất. 3. Bỏ chặn. | Báo lỗi tải và cho phép thử lại; không giả không có dữ liệu. | Hiển thị0bài và “Chưa có tri thức nào”, không có thông báo lỗi/retry. Đây là **fault injection trong browser**, không khẳng định backend production tự phát503. | FAIL S2 cho nhánh xử lý lỗi | [root-knowledge-simulated-503.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-knowledge-simulated-503.png>) |
| ROOT-WS-ERROR | Cùng kiểu fault injection nhưng GET `/api/v1/workspaces`. 1. Mở Workspaces. 2. Quan sát lỗi. 3. Bỏ chặn. 4. Bấm Thử lại. | Báo lỗi rõ và khôi phục khi server có lại. | Báo “Không thể tải danh sách workspace. Vui lòng thử lại.”; retry trả200 và lỗi được xóa. | PASS cho lỗi503/retry mô phỏng | [root-workspaces-simulated-503.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspaces-simulated-503.png>) |
| ROOT-ADMIN-USERS | Admin1366×768. 1. Tìm chính xác emailQA. 2. Đợi bảng còn một dòng. 3. Bấm Xuất. 4. Đọc CSV tải xuống. 5. Tìm chuỗi không tồn tại. | Tìm/lọc/xuất đúng tập kết quả và có empty state. | Bảng một dòngQA, tải `users.csv` thành công; CSV gồm header4cột và duy nhất một dòngQA. Tìm không có hiện “Không tìm thấy người dùng”. | PASS cho các biến thể đã thử | [root-admin-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-search.png>); [root-admin-users-export.csv](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-users-export.csv>) |
| ROOT-ADMIN-AUDIT | Admin. 1. Mở Lịch sử hệ thống. 2. Quan sát nội dung hội thoại trước khi nhập lý do. 3. Bấm Tiếp rồi Trước. | Hội thoại được ẩn theo chính sách, phân trang đổi kết quả. | Các dòng hiển thị “[Nội dung hội thoại được ẩn]”; nút mở nội dung bị vô hiệu khi thiếu lý do. Bấm Tiếp đổi dòng đầu rồi về Trước. Không mở nội dung hội thoại thực. | PASS cho mask/phân trang; chưa thử mở nội dung sau lý do | Kết quả snapshot và so sánh dòng đầu trong MCP. |
| ROOT-ADMIN-DEPT | Admin. 1. Mở tab Phòng ban. 2. Đợi dữ liệu tải xong. 3. Tìm Kỹ thuật. | Danh sách lọc theo tên và số thành viên. | Còn thẻKỹ thuật, mô tả và3thành viên. Không sửa/xóa phòng ban. | PASS cho đọc/tìm; CRUD phòng ban chưa thử | Snapshot MCP. |
| ROOT-PROFILE-CANCEL | Nhân viên desktop. 1. Menu tài khoản→Thông tin cá nhân. 2. Gõ tên khác không lưu. 3. Tab trong modal. 4. Escape. 5. Mở lại. | Đóng bằng Escape, hủy không lưu; focus vẫn trong modal khi đang mở. | Modal đúng tên/phòng ban; một bướcTab giữ focus bên trong. Escape đóng; mở lại vẫn tênQA cũ. Không PUT hồ sơ. | PASS cho mở/hủy/Escape/Tab đơn; chưa chứng minh toàn bộ vòng focus trap hoặc lưu hồ sơ | [root-profile-cancel.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-profile-cancel.png>) |
| ROOT-THEME | Nhân viên desktop. 1. Toggle dark mode. 2. Reload. 3. Khôi phục sáng. | Theme đổi và giữ sau reload. | light→dark, reload vẫndark, cuối cùng khôi phụclight. | PASS cho trạng thái/persistence; chưa đo tương phản mọi trang | MCP trả initial/toggled/reloaded/restored. |
| ROOT-PUBLIC-REGISTER | Chưa đăng nhập, desktop. 1. Mở `/`. 2. Mở documents/admin. 3. Mở landing. 4. Mở register. 5. Nhập mật khẩu xác nhận khác. 6. Điền dữ liệu còn lại hợp lệ nhưng tên1ký tự, chấp nhận điều khoản và gửi. | Root/protected vềlogin, landing tải; sai xác nhận hoặc tên ngắn bị chặn. | Root/protected vềlogin; landing cóh1; mismatchhiện vàsubmitdisabled; tênngắnhiện “Tên phải có ít nhất2ký tự”. Không gửi yêu cầu đăng ký hợp lệ lênserver. | PASS cho các biến thể mô tả; đăng ký thật chưa thử | [root-register-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-register-validation.png>) |
| ROOT-MOBILE-WORKSPACE | Context riêng, nhân viên, `isMobile:true,hasTouch:true`, zoom100%. Lặp360×640 và390×844. 1. Mở Workspace. 2. Bấm Tạo mới. 3. Kiểm tra vị trí Hủy/Tạo mới và vùng cuộn. 4. Đóng bằng Escape. | Có thể tiếp cận các nút trên màn hình và cuộn nếu nội dung dài. | 360×640: cả hai nút ởy658.5..704.5, ngoài chiều cao640; không có phần tử con cuộn được. 390×844: nút ởy760.5..806.5, bên trong màn hình. Xác nhận độc lập kết quả của Luna; không tạo workspace trong phép thử này. | FAIL ở360×640; PASS riêng khả năng nhìn thấy footer390×844. Severity chốt bởi Sol. | [root-workspace-mobile-360.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspace-mobile-360.png>); [root-workspace-mobile-390.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspace-mobile-390.png>) |
| ROOT-DASHBOARD-TABS | Nhân viên desktop. 1. Mở Dashboard. 2. Chuyển Hoạt động. 3. Về Thống kê. | Hai tab chuyển được, thống kê được khôi phục. | Heading “Tổng quan · Của tôi”; tabHoạt động tải và tabThống kê hiện lại biểu đồWorkspace. Chưa đối chiếu tất cả metric với dữ liệu nguồn. | PASS cho điều khiển tab; A05 so khớp số liệu toàn bộ vẫn thiếu | [root-dashboard-statistics.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-dashboard-statistics.png>) |
| ROOT-PDF-VIEWER | Nhân viên có quyền đọc PDF có sẵn. 1. Ở danh sách mở menu cuối dòngPDF→Xem. 2. Đợi trangdetail và PDF viewer. 3. Kiểm tra số trang. 4. Bấm Zoomin rồiZoomout. | PDF được nạp trong viewer, điều khiển hoạt động. | `/documents/20` mở iframeblob có xác thực và viewerPDF củaChromium; toolbar cho trang1/1 và thay đổi mứczoom khi bấm. Không đọc/trích nội dung nghiệp vụ vào báo cáo. Không dùng `networkidle` làm điều kiện hoàn tất vì viewer có thể giữrequest. | PASS riêng nạpPDF/điều khiển; không chứng nhận chất lượng hiển thị toàn văn hoặc mọi định dạng | [root-pdf-page-number.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-pdf-page-number.png>); kết quảMCP |
| ROOT-DOC-DEPARTMENT | Nhân viênQA desktop. 1. Tìm đúng tênDOC51 thuộcKỹ thuật. 2. Chọn chipBanGiámđốc. 3. Đợi requestlọc kết thúc. | Không trả lại tài liệuKỹ thuật dưới bộ lọcBanGiámđốc. | RequestUI có `department_id=6`, trả200; chipđược chọn nhưng dòngQA51 vẫn xuất hiện. Xác nhận độc lập lỗiD01-DEPT củaLuna. Không phải quan sát lộ dữ liệu ngoài quyền: vẫn là tài liệu được quyền củaQA. | FAIL S2 | [root-department-filter-mismatch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-department-filter-mismatch.png>) |
| ROOT-DOC-SORT-PAGES | Admin desktop,18tài liệu/4trang. 1. Chuyển trang2 rồi về1. 2. Bấm Sắp xếp hai lần. 3. Bật thứ tựtheotên, đi đủ4trang, thu tên hiển thị và đối chiếu thứ tự. 4. Vềtrang1 và khôi phục mới nhất. | Phân trang thay nội dung; sort đổi thứ tự và danh sách tên theoabc. | Trang1/2 đều5dòng khác nhau; mỗi lầnbấmSort đổi thứtự. Thu đủ18tên qua4trang; thứtự hợp lệ theo `localeCompare('vi')` lẫn mặc định. **Bác bỏ FAIL D01-SORT củaLuna**: ởdatasetnhânviên chỉ2tên, newest vàname trùng thứtự nên agent không đủ dữ liệu để kết luận. | PASS choAdmin4trang vàsort; không tựsuy ra datasetnhânviênnhiềutrang đãtest | [root-admin-document-sort.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-document-sort.png>); kết quảMCP chứa số lượng/boolean, khôngxuất danh sách nghiệp vụ. |

#### Nền tảng bổ sung

`bash harness/run.sh smoke deploy --json --md` đã chạy trên host này: smoke13PASS/0FAIL/3WARN, deploy7PASS/0FAIL/2WARN; tổng20PASS/0FAIL/5WARN. Đây không phải bằng chứng thay cho chức năng UI. Log: [platform-check.log](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/platform-check.log>).

WARN: DuckDNS updater tùy chọn không triển khai (xuất hiện hai component); workspace không xác thực trả401 khi dev-skip tắt; chưa bật RAG query của smoke; chưa thấy alembic_version. Không suy từ WARN thành lỗi UI live.

#### Điện thoại và thu phóng đã xác minh ở lượt trước

MCP Playwright có mô phỏng `isMobile:true,hasTouch:true,DPR3`. Upload footer ở100% hiển thị trong390×844,360×640,375×500,844×390,390×320. Dùng CDP `Emulation.setPageScaleFactor=2`, layout vẫn390×844 nhưng visual viewport195×422, footer y744..784 nằm ngoài vùng nhìn. Kết quả này chứng minh điều kiện pinch200%, không chứng minh lỗi mọi điện thoại và không phải kiểm tra Safari/iOS thật. Ảnh: [mobile-zoom-200.png](</home/micco/MiccoRAG-v3/harness/reports/admin-upload-20261022/mobile-zoom-200.png>).

#### Giới hạn

- Đây là kiểm tra Chromium có mô phỏng mobile, chưa phải iPhone/Safari hoặc Android thật.
- Google login và quên mật khẩu mới kiểm tra thao tác khởi động; chưa có luồng OAuth/phục hồi hoạt động để xác minh end-to-end. Chưa xác nhận đăng ký thật, profile/avatar, offline toàn trình duyệt và ID tài liệu không tồn tại. Các mục này phải được Sol ghi riêng nếu chưa có nhóm khác bổ sung.
- Chưa sửa code hoặc triển khai. Lỗi mobile login vẫn tồn tại trên public URL ở thời điểm kiểm tra.



## Chỉ mục artifact thực tế

Thời gian dưới đây là mtime của file trên host, không tự thay thế thời điểm thao tác. Cột nhóm chỉ để tra cứu; xem testcase để xác định đúng vai trò/thiết bị. Ảnh trắng và ảnh trùng đã được Sol đánh dấu trong audit, không dùng làm bằng chứng độc lập.

| Artifact | Nhóm tiêu chí | Vai trò tham chiếu | Mtime ICT |
|---|---|---|---|
| [DOCS-approval-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-approval-pending.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:49:55 |
| [DOCS-dept-filter-mismatch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-dept-filter-mismatch.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:06:14 |
| [DOCS-detail-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-pending.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:49:32 |
| [DOCS-detail-v2.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-detail-v2.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:02 |
| [DOCS-empty-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-empty-validation.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:45 |
| [DOCS-manager-approved.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-manager-approved.png>) | D01–D10 | Manager | 2026-10-22 09:50:09 |
| [DOCS-manager-dashboard.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-manager-dashboard.png>) | D01–D10 | Manager | 2026-10-22 09:49:42 |
| [DOCS-mobile-upload-360x640.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-mobile-upload-360x640.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:47 |
| [DOCS-mobile-upload-390x844.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-mobile-upload-390x844.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:47 |
| [DOCS-oversize-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-oversize-validation.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:46 |
| [DOCS-reject-owner-reloaded.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-owner-reloaded.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:04:36 |
| [DOCS-reject-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-pending.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:04:22 |
| [DOCS-reject-reason-ready.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-reject-reason-ready.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:04:28 |
| [DOCS-replacement-approval-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-approval-pending.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:55 |
| [DOCS-replacement-indexed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-indexed.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:57 |
| [DOCS-replacement-list-filtered.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-replacement-list-filtered.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:45 |
| [DOCS-ui-observations.md](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-ui-observations.md>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:10:48 |
| [DOCS-version-ready.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/DOCS-version-ready.png>) | D01–D10 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:52 |
| [QA-20261022-DOCS-acceptance.txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/QA-20261022-DOCS-acceptance.txt>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:49:33 |
| [admin-knowledge-pending.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/admin-knowledge-pending.png>) | K01–K03 / U05 | Admin | 2026-10-22 09:58:29 |
| [admin-knowledge-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/admin-knowledge-search.png>) | K01–K03 / U05 | Admin | 2026-10-22 09:53:05 |
| [chat-workspace-menu.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/chat-workspace-menu.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:55 |
| [edit-original-after-repro.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/edit-original-after-repro.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 10:00:06 |
| [edit-original-before-repro.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/edit-original-before-repro.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 10:00:05 |
| [expert-workspace-menu.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/expert-workspace-menu.png>) | C06 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:56 |
| [final-workspaces-cleaned.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/final-workspaces-cleaned.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:58:08 |
| [knowledge-create-filled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-create-filled.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:45 |
| [knowledge-create-modal.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-create-modal.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:30 |
| [knowledge-created.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-created.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:47 |
| [knowledge-delete-cancel-dialog.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-delete-cancel-dialog.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:45 |
| [knowledge-delete-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-delete-confirm.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:45 |
| [knowledge-deleted-one.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-deleted-one.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:53 |
| [knowledge-edit-before.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-edit-before.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:56 |
| [knowledge-edited.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-edited.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:02 |
| [knowledge-final-cleanup-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-final-cleanup-trash.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:03:42 |
| [knowledge-final-trash-approval.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-final-trash-approval.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:58:36 |
| [knowledge-final-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-final-trash.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:23 |
| [knowledge-generated-documents.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-generated-documents.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:03:55 |
| [knowledge-internal-before-submit.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-internal-before-submit.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:58:22 |
| [knowledge-internal-submitted.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-internal-submitted.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:58:23 |
| [knowledge-list-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-list-mode.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:55:18 |
| [knowledge-original-restored.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-original-restored.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:51 |
| [knowledge-pending-filter-internal.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-pending-filter-internal.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:58:35 |
| [knowledge-pending-filter.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-pending-filter.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:31 |
| [knowledge-restored-for-diagnostic.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-restored-for-diagnostic.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:36 |
| [knowledge-restored.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-restored.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:55:04 |
| [knowledge-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/knowledge-trash.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:54 |
| [luna-auth-invalid.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-invalid.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:48:27 |
| [luna-auth-login-success.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login-success.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:48:12 |
| [luna-auth-login.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-auth-login.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:47:28 |
| [luna-c04-c05-cleanup.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-c05-cleanup.png>) | C01–C05 | Xem testcase | 2026-10-22 10:22:30 |
| [luna-c04-login-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login-history.png>) | C01–C05 | Xem testcase | 2026-10-22 10:21:05 |
| [luna-c04-login.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-login.png>) | C01–C05 | Xem testcase | 2026-10-22 10:19:20 |
| [luna-c04-logout.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-logout.png>) | C01–C05 | Xem testcase | 2026-10-22 10:20:57 |
| [luna-c04-seed.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-seed.png>) | C01–C05 | Xem testcase | 2026-10-22 10:20:34 |
| [luna-c04-workspace-a-return.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-a-return.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:20:37 |
| [luna-c04-workspace-b.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c04-workspace-b.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:20:35 |
| [luna-c05-aborted-stream.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-aborted-stream.png>) | C01–C05 | Xem testcase | 2026-10-22 10:21:24 |
| [luna-c05-admin-mode.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-c05-admin-mode.png>) | C01–C05 | Admin | 2026-10-22 10:22:01 |
| [luna-chat-answer1.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-answer1.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:25 |
| [luna-chat-cleanup-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-cleanup-final.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:08:02 |
| [luna-chat-clear-cancel.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-clear-cancel.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:58 |
| [luna-chat-clear-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-clear-confirm.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:38 |
| [luna-chat-copy.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-copy.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:05:11 |
| [luna-chat-doc51-answer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-answer.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:01:08 |
| [luna-chat-doc51-citation-open.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-citation-open.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:01:14 |
| [luna-chat-doc51-history-clean.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-history-clean.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:05:45 |
| [luna-chat-doc51-history-reload.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-doc51-history-reload.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:05:41 |
| [luna-chat-followup-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-followup-final.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:09 |
| [luna-chat-followup.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-followup.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:00 |
| [luna-chat-grounded-source.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-grounded-source.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:17 |
| [luna-chat-history-cleared.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-history-cleared.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:50 |
| [luna-chat-history-reload.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-history-reload.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:59:31 |
| [luna-chat-insufficient-info.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-insufficient-info.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:51 |
| [luna-chat-memory-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-final.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:05:01 |
| [luna-chat-memory-loading.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-memory-loading.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:04:55 |
| [luna-chat-mobile-touch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-mobile-touch.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:17 |
| [luna-chat-mobile.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-mobile.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:07:06 |
| [luna-chat-other-user-history.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-other-user-history.png>) | C01–C05 | User đối chiếu | 2026-10-22 10:05:29 |
| [luna-chat-source-open.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-source-open.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:45 |
| [luna-chat-sources.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-sources.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:34 |
| [luna-chat-workspace-menu.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-chat-workspace-menu.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:51:41 |
| [luna-expert-card-detail.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-card-detail.png>) | C06 | Xem testcase | 2026-10-22 10:01:50 |
| [luna-expert-empty-results.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-empty-results.png>) | C06 | Xem testcase | 2026-10-22 10:06:51 |
| [luna-expert-initial.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-initial.png>) | C06 | Xem testcase | 2026-10-22 10:00:08 |
| [luna-expert-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-search.png>) | C06 | Xem testcase | 2026-10-22 10:00:49 |
| [luna-expert-workspaces.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-expert-workspaces.png>) | C06 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:00:14 |
| [luna-graph-admin.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-admin.png>) | C07 | Admin | 2026-10-22 10:02:35 |
| [luna-graph-business.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-business.png>) | C07 | Xem testcase | 2026-10-22 10:02:58 |
| [luna-graph-empty.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-empty.png>) | C07 | Xem testcase | 2026-10-22 10:03:48 |
| [luna-graph-interactions.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-interactions.png>) | C07 | Xem testcase | 2026-10-22 10:03:13 |
| [luna-graph-node-focus.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-focus.png>) | C07 | Xem testcase | 2026-10-22 10:04:22 |
| [luna-graph-node-hover-click.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-hover-click.png>) | C07 | Xem testcase | 2026-10-22 10:04:03 |
| [luna-graph-node-hover.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-hover.png>) | C07 | Xem testcase | 2026-10-22 10:04:22 |
| [luna-graph-node-select.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-node-select.png>) | C07 | Xem testcase | 2026-10-22 10:03:35 |
| [luna-graph-workspaces.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/luna-graph-workspaces.png>) | C07 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:44 |
| [manager-approval-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-approval-confirm.png>) | Tra theo báo cáo | Manager | 2026-10-22 10:01:41 |
| [manager-approval-done.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-approval-done.png>) | Tra theo báo cáo | Manager | 2026-10-22 10:01:47 |
| [manager-approvals-initial.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-approvals-initial.png>) | Tra theo báo cáo | Manager | 2026-10-22 10:01:18 |
| [manager-knowledge-approvals.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-knowledge-approvals.png>) | K01–K03 / U05 | Manager | 2026-10-22 10:01:24 |
| [manager-knowledge-preview.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/manager-knowledge-preview.png>) | K01–K03 / U05 | Manager | 2026-10-22 10:01:29 |
| [mobile360-knowledge-footer-scrolled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-knowledge-footer-scrolled.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:10 |
| [mobile360-knowledge-form.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-knowledge-form.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:53:17 |
| [mobile360-workspace-department-choice.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-workspace-department-choice.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:28 |
| [mobile360-workspace-footer-scrolled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-workspace-footer-scrolled.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:56:16 |
| [mobile360-workspace-form.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile360-workspace-form.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:53:19 |
| [mobile390-knowledge-footer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile390-knowledge-footer.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:11 |
| [mobile390-workspace-footer.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/mobile390-workspace-footer.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:54:10 |
| [ordinary-approved-after-manager.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/ordinary-approved-after-manager.png>) | Tra theo báo cáo | Manager | 2026-10-22 10:01:54 |
| [other-user-knowledge-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/other-user-knowledge-search.png>) | K01–K03 / U05 | User đối chiếu | 2026-10-22 09:52:57 |
| [platform-check.log](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/platform-check.log>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:48:15 |
| [root-admin-document-sort.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-document-sort.png>) | Tra theo báo cáo | Admin | 2026-10-22 10:12:06 |
| [root-admin-search.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-search.png>) | Tra theo báo cáo | Admin | 2026-10-22 09:56:45 |
| [root-admin-users-export.csv](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-admin-users-export.csv>) | Tra theo báo cáo | Admin | 2026-10-22 09:56:45 |
| [root-auth-invalid-visible.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-auth-invalid-visible.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:51:20 |
| [root-auth-placeholder-actions.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-auth-placeholder-actions.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:55:02 |
| [root-cleanup-doc51-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-cleanup-doc51-trash.png>) | Cleanup | Xem testcase | 2026-10-22 10:24:47 |
| [root-cleanup-qa-user-disabled.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-cleanup-qa-user-disabled.png>) | Cleanup | Xem testcase | 2026-10-22 10:26:24 |
| [root-dashboard-statistics.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-dashboard-statistics.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 10:06:02 |
| [root-department-filter-mismatch.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-department-filter-mismatch.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 10:10:59 |
| [root-graph-business.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-graph-business.png>) | C07 | Xem testcase | 2026-10-22 09:49:50 |
| [root-knowledge-simulated-503.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-knowledge-simulated-503.png>) | K01–K03 / U05 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:55:27 |
| [root-logout-mobile.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-logout-mobile.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:53:36 |
| [root-mobile-dashboard.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-mobile-dashboard.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:53:19 |
| [root-mobile-login-overlay.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-mobile-login-overlay.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:52:49 |
| [root-pdf-page-number.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-pdf-page-number.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 10:10:15 |
| [root-profile-cancel.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-profile-cancel.png>) | A01–A08 / U01 | Xem testcase | 2026-10-22 09:57:41 |
| [root-register-validation.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-register-validation.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:59:19 |
| [root-unknown-route.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-unknown-route.png>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:55:03 |
| [root-workspace-mobile-360.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspace-mobile-360.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:03:50 |
| [root-workspace-mobile-390.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspace-mobile-390.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:03:50 |
| [root-workspaces-simulated-503.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/root-workspaces-simulated-503.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:55:27 |
| [version1-QA-20261022-DOCS-acceptance.txt (V 1.0).txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/version1-QA-20261022-DOCS-acceptance.txt (V 1.0).txt>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:52:10 |
| [version2-QA-20261022-DOCS-acceptance.txt (V 2.0).txt](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/version2-QA-20261022-DOCS-acceptance.txt (V 2.0).txt>) | Tra theo báo cáo | Xem testcase | 2026-10-22 09:52:10 |
| [workspace-create-modal.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-create-modal.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:11 |
| [workspace-created.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-created.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:17 |
| [workspace-delete-confirm-final.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-delete-confirm-final.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:38 |
| [workspace-delete-confirm.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-delete-confirm.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:45 |
| [workspace-department-permission-before-submit.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-department-permission-before-submit.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:16 |
| [workspace-department-permission-result.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-department-permission-result.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:17 |
| [workspace-final-cleanup-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-final-cleanup-trash.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:04:03 |
| [workspace-final-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-final-trash.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:45 |
| [workspace-in-chat-selector.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-chat-selector.png>) | C01–C05 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:40 |
| [workspace-in-documents.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-documents.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:41 |
| [workspace-in-expert.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-in-expert.png>) | C06 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:42 |
| [workspace-public-permission-before-submit.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-public-permission-before-submit.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:23 |
| [workspace-public-permission-result.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-public-permission-result.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 10:02:24 |
| [workspace-restored.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-restored.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:44 |
| [workspace-scope-radio-warning.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-scope-radio-warning.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:37 |
| [workspace-trash.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspace-trash.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:57:39 |
| [workspaces-list.png](</home/micco/MiccoRAG-v3/harness/reports/acceptance-20261022/workspaces-list.png>) | K04–K05 / U01 | Nhân viên / đối chiếu theo ca | 2026-10-22 09:52:05 |

Ghi chú kiểm tra file cuối: báo cáo Auth gốc dẫn `luna-auth-dashboard.png` nhưng file không tồn tại. Đã đánh dấu thiếu bằng chứng thay vì giữ liên kết hỏng; không tạo ảnh thay thế giả. Các kết quả kiểm tra chéo parent và kết luận Sol vẫn được giữ riêng.
