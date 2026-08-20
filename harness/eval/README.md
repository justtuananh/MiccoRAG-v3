# Eval harness — RAG quality (MiccoRAG-v3)

Chấm chất lượng pipeline RAG trên một bộ **golden Q/A** grounded từ nội dung thật.

## Chạy
```bash
# Trên VPS (gọi Gemini — tốn phí):
RUN_EVAL=1 bash harness/run.sh eval
# hoặc trực tiếp:
RUN_EVAL=1 bash harness/eval.sh
# Chấm cả câu trả lời (gọi thêm /rag/chat):
RUN_EVAL=1 EVAL_ANSWER=1 bash harness/eval.sh
```

## Chỉ số
- **retrieval_hit_rate** — % câu hỏi truy xuất được chunk (`total_chunks > 0`).
- **keyword_hit_rate** — trung bình tỉ lệ `expected_keywords` xuất hiện trong `context`.
- **citation_rate** — % câu có `citations` khác rỗng.
- **answer_ok_rate** — (khi `EVAL_ANSWER=1`) câu trả lời không rỗng + chứa keyword.
- **pass@1** — `retrieval_ok AND keyword_ok AND (answer_ok nếu bật)`. Ngưỡng: `EVAL_MIN_PASS` (mặc định 0.6).

## Mở rộng golden set
Sửa `golden.jsonl` — mỗi dòng 1 JSON:
```json
{"id": "ws1-abc", "workspace_id": 1, "question": "…?", "expected_keywords": ["rag","fine"], "top_k": 5}
```
- `expected_keywords` rỗng `[]` → chỉ chấm theo retrieval (không xét keyword).
- Lấy câu hỏi grounded nhanh: `GET /api/v1/workspaces/{id}/suggested-questions`.
- Dòng bắt đầu bằng `#` bị bỏ qua (ghi chú).

## Biến môi trường
`HARNESS_BASE_URL` (mặc định tự dò 8001), `EVAL_GOLDEN`, `EVAL_ANSWER`, `EVAL_MIN_PASS`, `EVAL_JSON`.
Report JSON ghi vào `harness/reports/eval-<ts>.json`.
