# LLM Integration Rules

## Provider Architecture
Luôn dùng abstract LLMProvider interface — KHÔNG call OpenAI/Gemini trực tiếp trong business logic.

```python
# ĐÚNG — qua provider abstraction
from app.services.llm import get_llm_provider
llm = get_llm_provider()  # trả về OpenAI hoặc Gemini tùy env

# SAI — gọi trực tiếp
from openai import AsyncOpenAI
client = AsyncOpenAI()
```

## Streaming
- Mọi chat endpoint PHẢI support streaming (Server-Sent Events)
- Dùng `async for chunk in response:` pattern
- Frontend nhận stream qua EventSource

## Token Tracking
Mọi LLM call phải log:
```python
logger.info("LLM call", extra={
    "provider": provider_name,
    "model": model_name,
    "prompt_tokens": usage.prompt_tokens,
    "completion_tokens": usage.completion_tokens,
    "latency_ms": elapsed_ms
})
```

## Error Handling
- OpenAI rate limit → retry với exponential backoff (tenacity)
- OpenAI error → fallback sang Gemini nếu LLM_FALLBACK=true
- Luôn return structured error: {"error": "...", "code": "...", "retry_after": ...}
