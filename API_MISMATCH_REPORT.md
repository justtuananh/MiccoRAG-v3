# Frontend-Backend API Mismatch Report
**Date:** 2026-04-03
**Scope:** miccoRAG-v3 frontend (`micco-frontend/src/`) vs. micco-backend (`micco-backend/backend/app/`)

---

## Summary
**Total mismatches found: 6**
- 🔴 **Critical:** 2
- 🟠 **High:** 1
- 🟡 **Medium:** 3

---

## 🔴 Critical Mismatches

### Mismatch 1: Expert — `avg_relevance` returned but `relevance_score` expected
- **Frontend:** `micco-frontend/src/pages/Expert.jsx:90` — `expert.relevance_score ?? 0`
- **Backend:** `micco-backend/backend/app/schemas/rag.py:300` — field is `avg_relevance: float`
- **Description:** The `ExpertRecommendation` Pydantic schema defines the field as `avg_relevance`, but the frontend's `ExpertCard` component reads `expert.relevance_score`. This means every expert card shows `0%` for relevance score.
- **Impact:** Expert recommendation cards always display 0% relevance. The relevance bar will always be empty (0%), misleading users.
- **Fix:** In `Expert.jsx:90`, change `expert.relevance_score ?? 0` to `expert.avg_relevance ?? 0`.

---

### Mismatch 2: ChatAssistant SSE — `enable_thinking` not sent by frontend
- **Frontend:** `micco-frontend/src/utils/api.js:264` — `streamChat()` sends `{ message, document_ids, mode, stream: true }`
- **Backend:** `micco-backend/backend/app/schemas/rag.py:176` — `ChatRequest` has `enable_thinking: bool = False`
- **Description:** The `streamChat()` function never sends `enable_thinking`. It only sends `message`, `document_ids`, `mode`, and `stream`. The backend requires `enable_thinking` (defaults to `False`), so thinking will always be off unless the frontend explicitly sets it. Additionally, `stream: true` is sent but is not defined in `ChatRequest` at all (harmless extra field, but indicates the frontend is not fully aligned).
- **Impact:** The "Thinking process" feature is silently disabled in the streaming chat UI because the frontend never passes `enable_thinking: true`. Users cannot see the LLM's reasoning process even if the backend supports it.
- **Fix:** Add `enable_thinking: options.enableThinking || false` to the `streamChat()` body, and pass it from `ChatAssistant.jsx` when calling `streamChat()`.

---

## 🟠 High Mismatches

### Mismatch 3: Non-streaming chat — `history` field not sent by frontend
- **Frontend:** `micco-frontend/src/utils/api.js:274-279` — `ragChatApi.chat()` sends `{ message, document_ids, mode }` (no `history`)
- **Backend:** `micco-backend/backend/app/schemas/rag.py:173` — `ChatRequest.history: list[ChatMessageSchema] = []` (no default, required field)
- **Description:** In Pydantic v2, `history: list[ChatMessageSchema] = []` means `history` is a **required** field (no `Field(default=...)` wrapper). If `history` is not in the JSON body, Pydantic will NOT apply the `= []` default at serialization time — the field will be missing. The non-streaming `POST /api/v1/rag/chat/{workspace_id}` endpoint (rag.py:930) validates the request body against `ChatRequest`, so a missing `history` field could cause a 422 validation error.
- **Impact:** The non-streaming fallback path in `ChatAssistant.jsx:760` (`ragChatApi.chat()`) would fail with HTTP 422. Currently this is a rarely-used fallback, but if the SSE stream fails and falls back to non-streaming, it will error out.
- **Fix:** Either (a) add `Field(default=[])` to `ChatRequest.history` in `schemas/rag.py`, or (b) always send `history: []` from the frontend `ragChatApi.chat()` call.

---

## 🟡 Medium Mismatches

### Mismatch 4: `suggested_questions` — backend returns array; frontend has incorrect fallback guard
- **Frontend:** `micco-frontend/src/pages/ChatAssistant.jsx:606-608`
  ```js
  if (Array.isArray(data) && data.length > 0) {
      setSuggestedQuestions(data); // data = plain string[] — ✅ correct
  }
  // Second branch: if (!Array.isArray(data)) checks data.workspaces — unused
  ```
- **Backend:** `micco-backend/backend/app/api/workspaces.py:215` — returns `list[str]` directly (no wrapper)
- **Description:** The first branch (`Array.isArray`) handles the actual backend response correctly. However, the second guard `if (!Array.isArray(data) && data.workspaces)` references `data.workspaces` which never exists on the backend response (it's a plain `string[]`). The logic works by luck — if the response IS an array, the second branch is never entered. Not a bug, but fragile.
- **Impact:** Low — works correctly now. If the backend ever wraps the response in an object, the second branch would activate with wrong data.
- **Fix:** Remove the dead `data.workspaces` branch, or document that the endpoint returns a plain array.

---

### Mismatch 5: ChatAssistant mode selector — `graph_only` is not a valid backend mode
- **Frontend:** `micco-frontend/src/pages/ChatAssistant.jsx:931`
  ```jsx
  <option value="graph_only">Graph only</option>
  ```
- **Backend:** `micco-backend/backend/app/schemas/rag.py:14-16` — `mode` enum: `"hybrid" | "vector_only" | "naive" | "local" | "global"`
- **Description:** The chat UI's mode dropdown includes a "Graph only" option (`graph_only`), but the backend's `RAGQueryRequest` and `ChatRequest` schemas do not accept `graph_only`. Any call with `mode: "graph_only"` will either be ignored (backend falls back to `hybrid`) or cause unexpected behavior.
- **Impact:** The "Graph only" dropdown option silently does nothing — the backend ignores it and uses the workspace's default `hybrid` mode. Users selecting "Graph only" believe they are searching only the knowledge graph, but actually get hybrid search.
- **Fix:** Either (a) remove the `graph_only` option from the dropdown, or (b) implement `graph_only` mode in the backend RAG service.

---

### Mismatch 6: SSE stream — `stream: true` sent but not defined in backend schema
- **Frontend:** `micco-frontend/src/utils/api.js:264` — `streamChat()` body includes `stream: true`
- **Backend:** `micco-backend/backend/app/schemas/rag.py:170-177` — `ChatRequest` schema has no `stream` field
- **Description:** The frontend always sends `stream: true` in the chat streaming request body. The backend `ChatRequest` Pydantic schema has no such field. Since Pydantic v2 ignores extra fields by default, this does not cause an error — but it means the frontend is sending data the backend never reads.
- **Impact:** Harmless — no runtime error, but indicates incomplete integration. The `stream` flag was likely intended to distinguish streaming from non-streaming requests but is unused.
- **Fix:** Remove `stream: true` from the `streamChat()` body, or document that the streaming vs. non-streaming distinction is made by the endpoint path (`/stream` suffix), not the request body.

---

## ✅ Verified Matching Endpoints

The following frontend API calls correctly match their backend routes:

| Frontend Call | Backend Route | Notes |
|---|---|---|
| `ragFetch('/api/auth/login')` | `POST /api/auth/login` | ✅ |
| `ragFetch('/api/auth/register')` | `POST /api/auth/register` | ✅ |
| `ragFetch('/api/auth/me')` | `GET /api/auth/me` | ✅ |
| `ragFetch('/api/auth/departments')` | `GET /api/auth/departments` | ✅ |
| `authFetch('/api/admin/stats')` | `GET /api/admin/stats` | ✅ |
| `authFetch('/api/admin/users')` | `GET /api/admin/users` | ✅ |
| `authFetch('/api/admin/chat-logs')` | `GET /api/admin/chat-logs` | ✅ |
| `authFetch('/api/admin/departments')` | `GET /api/admin/departments` | ✅ |
| `authFetch('/api/approvals/count')` | `GET /api/approvals/count` | ✅ |
| `authFetch('/api/approvals/pending')` | `GET /api/approvals/pending` | ✅ |
| `authFetch('/api/approvals/documents/{id}/approve')` | `POST /api/approvals/documents/{id}/approve` | ✅ |
| `authFetch('/api/approvals/documents/{id}/reject')` | `POST /api/approvals/documents/{id}/reject` | ✅ |
| `approvalsApi.getDocumentStatus(id)` | `GET /api/approvals/documents/{id}/status` | ✅ |
| `documentsApi.list()` | `GET /api/documents` | ✅ |
| `documentsApi.get(id)` | `GET /api/documents/{id}` | ✅ |
| `documentsApi.upload()` | `POST /api/documents/upload` (multipart) | ✅ |
| `documentsApi.delete(id)` | `DELETE /api/documents/{id}` | ✅ |
| `documentsApi.listVersions(id)` | `GET /api/documents/{id}/versions` | ✅ |
| `documentsApi.uploadVersion()` | `POST /api/documents/{id}/versions` (multipart) | ✅ |
| `authFetch('/api/documents/processing-status')` | `GET /api/documents/processing-status` | ✅ |
| `authFetch('/api/knowledge')` | `GET /api/knowledge` | ✅ |
| `authFetch('/api/knowledge', POST)` | `POST /api/knowledge` | ✅ |
| `authFetch('/api/knowledge/{id}')` | `GET /api/knowledge/{id}` | ✅ |
| `authFetch('/api/knowledge/{id}', PUT)` | `PUT /api/knowledge/{id}` | ✅ |
| `authFetch('/api/knowledge/{id}', DELETE)` | `DELETE /api/knowledge/{id}` | ✅ |
| `authFetch('/api/chat/send')` | `POST /api/chat/send` | ✅ |
| `authFetch('/api/chat/history')` | `GET /api/chat/history` | ✅ |
| `ragChatApi.clearAllHistory()` | `DELETE /api/chat/all-history` | ✅ |
| `ragChatApi.getMyWorkspaceId()` | `GET /api/chat/my-workspace-id` | ✅ |
| `authFetch('/api/dashboard/stats')` | `GET /api/dashboard/stats` | ✅ |
| `authFetch('/api/dashboard/uploads-over-time')` | `GET /api/dashboard/uploads-over-time` | ✅ |
| `authFetch('/api/dashboard/document-status')` | `GET /api/dashboard/document-status` | ✅ |
| `authFetch('/api/dashboard/workspace-stats')` | `GET /api/dashboard/workspace-stats` | ✅ |
| `authFetch('/api/dashboard/recent-documents')` | `GET /api/dashboard/recent-documents` | ✅ |
| `workspacesApi.list()` | `GET /api/v1/workspaces` | ✅ |
| `workspacesApi.summary()` | `GET /api/v1/workspaces/summary` | ✅ |
| `workspacesApi.create()` | `POST /api/v1/workspaces` | ✅ |
| `workspacesApi.update()` | `PUT /api/v1/workspaces/{id}` | ✅ |
| `workspacesApi.delete()` | `DELETE /api/v1/workspaces/{id}` | ✅ |
| `workspacesApi.getSuggestedQuestions(id)` | `GET /api/v1/workspaces/{id}/suggested-questions` | ✅ (response is plain array) |
| `ragDocumentsApi.list(wsId)` | `GET /api/v1/documents/workspace/{wsId}` | ✅ |
| `ragDocumentsApi.get(docId)` | `GET /api/v1/documents/{docId}` | ✅ |
| `ragDocumentsApi.upload()` | `POST /api/v1/documents/upload/{wsId}` (multipart) | ✅ |
| `ragDocumentsApi.delete(docId)` | `DELETE /api/v1/documents/{docId}` | ✅ |
| `ragDocumentsApi.markdown(docId)` | `GET /api/v1/documents/{docId}/markdown` (returns `PlainTextResponse`) | ✅ |
| `ragDocumentsApi.update()` | `PUT /api/v1/documents/{docId}` | ✅ |
| `ragProcessApi.process(docId)` | `POST /api/v1/rag/process/{docId}` | ✅ |
| `ragProcessApi.processBatch(ids)` | `POST /api/v1/rag/process-batch` | ✅ |
| `ragProcessApi.stats(wsId)` | `GET /api/v1/rag/stats/{wsId}` | ✅ |
| `ragQueryApi.query(wsId, q, k)` | `POST /api/v1/rag/query/{wsId}` | ✅ |
| `ragChatApi.streamChat(wsId, msg, opts)` | `POST /api/v1/rag/chat/{wsId}/stream` | ✅ (SSE) |
| `ragChatApi.chat(wsId, msg, opts)` | `POST /api/v1/rag/chat/{wsId}` | ✅ (non-stream) |
| `ragChatApi.history(wsId)` | `GET /api/v1/rag/chat/{wsId}/history` | ✅ |
| `ragChatApi.clearHistory(wsId)` | `DELETE /api/v1/rag/chat/{wsId}/history` | ✅ |
| `ragGraphApi.getGraph(wsId)` | `GET /api/v1/rag/graph/{wsId}` | ✅ |
| `expert/recommend/{wsId}` (direct fetch) | `GET /api/v1/expert/recommend/{workspace_id}` | ✅ |

---

## Additional Issues

### Frontend uses direct Cloudflare URL, not Vite proxy
- **File:** `micco-frontend/.env`
  ```
  VITE_API_BASE_URL=https://night-polo-home-thermal.trycloudflare.com
  VITE_RAGV2_BASE_URL=https://night-polo-home-thermal.trycloudflare.com
  ```
- **Details:** Both base URLs point directly to the Cloudflare production backend. The Vite proxy configuration (`vite.config.js:14-18`) proxies `/api` → Cloudflare, but since the frontend resolves base URLs at runtime using `import.meta.env`, the proxy is bypassed. Requests go directly to Cloudflare.
- **Impact:** Works in production. In local dev, if the Cloudflare tunnel is down, the frontend will fail to reach the backend. The Vite proxy configuration is effectively unused.
- **Note:** This is an architectural observation, not a mismatch.

### Unused backend endpoints (frontend never calls them)
The following backend endpoints are registered but have no frontend consumer:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/rag/entities/{workspace_id}` | KG entity listing |
| `GET /api/v1/rag/relationships/{workspace_id}` | KG relationship listing |
| `GET /api/v1/rag/analytics/{workspace_id}` | Workspace analytics |
| `POST /api/v1/rag/reindex/{document_id}` | Reindex single document |
| `POST /api/v1/rag/reindex-workspace/{workspace_id}` | Reindex entire workspace |
| `GET /api/v1/rag/chunks/{document_id}` | Get document chunks |
| `POST /api/v1/rag/chat/{workspace_id}/rate` | Rate source citation |
| `GET /api/v1/rag/capabilities` | LLM capabilities check |
| `POST /api/v1/rag/debug-chat/{workspace_id}` | Debug chat endpoint |
| `GET /api/v1/config/status` | Backend config status |
| `GET /api/v1/documents/{docId}/images` | Document extracted images |
| `POST /api/approvals/knowledge/{id}/approve` | Approve knowledge entry |
| `POST /api/approvals/knowledge/{id}/reject` | Reject knowledge entry |
| `GET /api/approvals/documents/{id}/preview` | Preview doc during approval |

### Admin — communities/build endpoint
- **Frontend:** `micco-frontend/src/pages/Admin.jsx:166` — `authFetch('/api/admin/communities/build', {method:'POST'})`
- **Backend:** Not found in `api_compat/admin.py` or any other router
- **Impact:** Clicking the "Build Communities" button in Admin would send a request to an endpoint that does not exist → HTTP 404. If this feature is expected to work, the backend endpoint is missing.
- **Severity:** Medium (feature incomplete, not a runtime mismatch)

---

## Response Schema Notes (working correctly but worth documenting)

### Chat history response wrapping
- **Backend:** `GET /api/v1/rag/chat/{wsId}/history` returns `ChatHistoryResponse(workspace_id, messages, total)`
- **Frontend:** Accesses `data.messages` — works because `data` is the parsed JSON `{"workspace_id": N, "messages": [...], "total": N}`
- ✅ Correct

### Non-streaming chat response
- **Backend:** `POST /api/v1/rag/chat/{wsId}` returns `ChatResponse(answer, sources, related_entities, kg_summary, image_refs, thinking)`
- **Frontend:** `data.answer || data.content || data.message || JSON.stringify(data)` fallback chain
- ✅ Correct — primary field `answer` matches

### SSE complete event
- **Backend:** SSE `complete` event sends `{"answer": ..., "sources": [...], "image_refs": [...], "thinking": ..., "related_entities": [...]}`
- **Frontend:** `d.answer`, `d.sources`, `d.related_entities`, `d.thinking` from `chunk.data || chunk`
- ✅ Correct

### Suggested questions
- **Backend:** `GET /api/v1/workspaces/{id}/suggested-questions` returns `list[str]` directly (no wrapper)
- **Frontend:** `Array.isArray(data) && data.length > 0` — works for plain array
- ✅ Correct (see Mismatch 4 for fragility note)

### Document view — uses legacy API (not v2)
- `DocumentView.jsx` uses `documentsApi.get(id)` → `GET /api/documents/{id}` (legacy compat router)
- This correctly returns `owner`, `department` fields (mapped by `map_rag_doc_to_legacy_with_dept`)
- ✅ Not a mismatch — the page correctly uses the legacy API for its needs

---

*Report generated by systematic cross-reference of all backend routes (19 files) and all frontend API calls and page components (13 files).*
