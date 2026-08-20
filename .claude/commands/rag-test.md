---
description: Test toàn bộ RAG pipeline từ đầu đến cuối
---

Chạy end-to-end test cho RAG pipeline:
1. Upload file test (dùng fixture trong `micco-backend/backend/tests/fixtures/`, ví dụ `sample.pdf`)
2. Verify chunking ra đúng số chunks
3. Verify embedding (**gemini-embedding-001**, 3072-dim) được store vào **ChromaDB** (container `nexusrag-chromadb`, host :8003) — KHÔNG phải pgvector/FAISS/Qdrant
4. Chạy retrieval `POST /api/v1/rag/query/{workspace_id}` với câu hỏi "tóm tắt nội dung tài liệu" và verify payload trả về `{total_chunks, chunks, context, citations}` (đây là retrieval, chưa sinh câu trả lời)
5. Verify có `citations`; nếu cần kiểm tra câu trả lời sinh bởi LLM (**Gemini** `gemini-2.5-flash`) thì gọi thêm `POST /api/v1/rag/chat/{workspace_id}` (streaming: `/rag/chat/{workspace_id}/stream`)
6. Report kết quả và bất kỳ lỗi nào

## Cách chạy

Integration test đã tồn tại tại `micco-backend/backend/tests/integration/test_rag_pipeline.py`.

- Qua harness (khuyến nghị — gọi Gemini nên cần opt-in):

  ```
  RUN_INTEGRATION=1 bash harness/run.sh be
  ```

- Hoặc chạy pytest trực tiếp:

  ```
  pytest micco-backend/backend/tests/integration/test_rag_pipeline.py -v
  ```

## Đánh giá chất lượng RAG (golden set)

Để đo retrieval/answer quality trên golden set (`harness/eval/golden.jsonl` + `grade.py`,
metrics: retrieval_hit_rate / keyword_hit_rate / citation_rate / pass@1):

```
RUN_EVAL=1 bash harness/run.sh eval
```
