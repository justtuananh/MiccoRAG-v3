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
