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
