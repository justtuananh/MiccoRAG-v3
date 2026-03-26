# RAG Pipeline Rules

## Chunking Strategy
- Default: RecursiveCharacterTextSplitter, chunk_size=512, overlap=50
- PDF: Ưu tiên giữ nguyên paragraph
- Code files: chunk theo function/class boundary

## Embedding
- Production: OpenAI text-embedding-3-small (1536 dims) → lưu vào pgvector
- Local dev: ChromaDB với same embedding model
- KHÔNG mix embedding models trong cùng một collection

## Retrieval
- Top-K mặc định: 5
- Reranking: CrossEncoder nếu có, skip nếu latency > 500ms
- Hybrid search: vector similarity + BM25 keyword (pgvector + pg_trgm)

## Context Assembly
```python
# Template chuẩn cho RAG context
SYSTEM_PROMPT = """You are a helpful assistant. Answer based ONLY on the provided context.
If the answer is not in the context, say "Tôi không tìm thấy thông tin này trong tài liệu."

Context:
{context}
"""
```

## Document Processing Pipeline
1. Upload → validate (PDF/DOCX/TXT only, max 50MB)
2. Extract text (PyMuPDF cho PDF, python-docx cho Word)
3. Clean text (remove headers/footers, normalize whitespace)
4. Chunk → embed → store
5. Return document_id để track
