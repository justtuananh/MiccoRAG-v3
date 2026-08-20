# RAG Pipeline Rules

MiccoRAG-v3 — Vietnamese RAG chatbot + document Q&A. This file describes the real
retrieval pipeline. Ground every change here in the actual stack, not older docs.

## Chunking Strategy
- Default: RecursiveCharacterTextSplitter, chunk_size=512, overlap=50
- PDF: Ưu tiên giữ nguyên paragraph
- Code files: chunk theo function/class boundary
- KHÔNG mix embedding models trong cùng một collection (re-embed on model change)

## Embedding
- Model: **gemini-embedding-001 (3072-dim)** — same model dev + prod.
- Called via the LLM provider factory `get_llm_provider()`; never call the embedding
  API directly.
- One embedding model per ChromaDB collection — switching dims requires a re-index.

## Vector Store
- **ChromaDB** in both dev and prod (NOT pgvector / FAISS / Qdrant).
- Container `nexusrag-chromadb`, host port **:8003**.
- PostgreSQL (`nexusrag-postgres`, host **:15435** → 5432, db `nexusrag`) holds
  relational data only (workspaces, documents, users) — NOT vectors.

## Retrieval
- Endpoint: `POST /api/v1/rag/query/{workspace_id}` → retrieval payload
  `{total_chunks, chunks, context, citations}` (this returns retrieved context, NOT a
  generated answer).
- Search modes: **hybrid** (default), `vector_only`, `naive`, `local`, `global`.
  - hybrid = vector similarity + keyword/graph signals.
  - local / global operate over the **NexusRAG** knowledge graph.
- Reranker: **Cohere rerank-multilingual-v3.0** (multilingual, tuned for Vietnamese).
- Knowledge graph: **NexusRAG** — powers `local`/`global` modes and graph-aware
  citations.

## Answer / Chat
- Endpoint: `POST /api/v1/rag/chat/{workspace_id}` → generated answer.
  Streaming variant: `POST /api/v1/rag/chat/{workspace_id}/stream`.
- Generation LLM: **Gemini (gemini-2.5-flash)** primary, Ollama alternative — always
  through `get_llm_provider()`.
- Suggested questions: `GET /api/v1/workspaces/{id}/suggested-questions`.

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
4. Chunk → embed (gemini-embedding-001) → store in ChromaDB
5. Return document_id để track

## Measuring Retrieval Quality
- Use the eval harness: `harness/eval/` (golden set `harness/eval/golden.jsonl` +
  `grade.py`). Run with `RUN_EVAL=1 bash harness/run.sh eval` (calls Gemini — paid).
- Metrics: `retrieval_hit_rate`, `keyword_hit_rate`, `citation_rate`, `pass@1`.
- Latency per search mode (hybrid/vector_only/naive): `RUN_BENCH=1 bash harness/run.sh bench`.
- Change chunking / embedding / reranker settings only alongside an eval run so you can
  compare before/after.
