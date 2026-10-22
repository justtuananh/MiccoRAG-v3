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
