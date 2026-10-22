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
