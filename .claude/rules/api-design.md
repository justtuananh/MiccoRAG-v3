# API Design Rules

## Endpoint Structure
- Base: /api/v1/
- Tất cả response wrap trong: {"data": ..., "meta": {...}}
- Error response: {"error": {"message": "...", "code": "...", "details": {}}}

## Versioning
- Luôn có /api/v1/ prefix
- Breaking changes → tạo /api/v2/, KHÔNG xóa v1 ngay

## Request/Response
```python
# Mọi endpoint phải có schema rõ ràng
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    stream: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: List[DocumentSource]
    usage: TokenUsage
```

## Auth
- JWT Bearer token cho mọi endpoint trừ /health và /docs
- Rate limiting: 60 req/min per user, 10 req/min cho /upload

## Async
- Mọi endpoint PHẢI là async def
- File upload xử lý via background task (BackgroundTasks)
