# LLM Integration Rules

## Provider Architecture
Luôn dùng abstract LLMProvider interface — KHÔNG call Gemini/Ollama trực tiếp trong business logic.
Primary provider là **Google Gemini (`gemini-2.5-flash`)**, alternative là **Ollama**; chọn qua env,
truy cập DUY NHẤT qua factory `get_llm_provider()`.

```python
# ĐÚNG — qua provider abstraction
from app.services.llm import get_llm_provider
llm = get_llm_provider()  # trả về Gemini (primary) hoặc Ollama (alternative) tùy env

# SAI — gọi provider trực tiếp
import google.generativeai as genai
model = genai.GenerativeModel("gemini-2.5-flash")  # bypass factory → cấm
```

## Streaming
- Mọi chat endpoint PHẢI support streaming (Server-Sent Events / SSE)
- Streaming chat endpoint: `POST /api/v1/rag/chat/{workspace_id}/stream`
- Dùng `async for chunk in response:` pattern
- Frontend nhận stream qua EventSource

## Token Tracking
Mọi LLM call phải log:
```python
logger.info("LLM call", extra={
    "provider": provider_name,   # gemini | ollama
    "model": model_name,         # vd gemini-2.5-flash
    "prompt_tokens": usage.prompt_tokens,
    "completion_tokens": usage.completion_tokens,
    "latency_ms": elapsed_ms
})
```

## Reranking (KHÔNG phải LLM provider)
- Rerank kết quả retrieval dùng **Cohere `rerank-multilingual-v3.0`** — tách biệt khỏi `get_llm_provider()`,
  không route qua LLM factory. Đây là bước riêng trong pipeline RAG, không phải generation.

## Error Handling
- Gemini rate limit → retry với exponential backoff (tenacity)
- Gemini error → fallback sang Ollama nếu `LLM_FALLBACK=true`
- Luôn return structured error: {"error": "...", "code": "...", "retry_after": ...}
