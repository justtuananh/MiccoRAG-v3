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
