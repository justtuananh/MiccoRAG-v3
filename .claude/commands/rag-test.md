---
description: Test toàn bộ RAG pipeline từ đầu đến cuối
---

Chạy end-to-end test cho RAG pipeline:
1. Upload file test (dùng fixture tests/fixtures/sample.pdf)
2. Verify chunking ra đúng số chunks
3. Verify embedding được store vào vector DB
4. Chạy query "tóm tắt nội dung tài liệu" và verify trả về context
5. Verify response có sources
6. Report kết quả và bất kỳ lỗi nào

Chạy lệnh: pytest tests/integration/test_rag_pipeline.py -v
