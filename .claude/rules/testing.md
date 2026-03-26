# Testing Rules

## Test Structure
```
tests/
├── unit/
│   ├── test_rag_chunking.py
│   ├── test_llm_provider.py
│   └── test_document_parser.py
├── integration/
│   ├── test_api_chat.py
│   └── test_api_upload.py
└── conftest.py
```

## Fixtures bắt buộc (conftest.py)
- `mock_openai_client` — mock OpenAI để test không tốn tiền
- `mock_gemini_client` — mock Gemini
- `test_db` — PostgreSQL test database (dùng pytest-asyncio)
- `sample_pdf` — PDF test fixture
- `authenticated_client` — FastAPI TestClient với JWT token

## Rules
- Mock mọi external API calls (OpenAI, Gemini) trong unit tests
- Integration test dùng test database riêng (TEST_DATABASE_URL)
- Mỗi test phải cleanup data sau khi chạy
- Tên test: test_{function_name}_{scenario}_{expected_result}
  Ví dụ: test_retrieve_chunks_empty_query_returns_empty_list
