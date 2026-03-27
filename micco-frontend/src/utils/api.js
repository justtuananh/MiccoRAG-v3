/**
 * api.js — Centralized API service layer
 *
 * micco-server  → auth, dashboard, knowledge, admin, approvals
 * MiccoRAG-v2   → documents (workspaces), chatbot (RAG)
 */

const RAG_V2_BASE = import.meta.env.VITE_RAGV2_BASE_URL || 'http://localhost:8000';

// ─── MiccoRAG-v2 base fetch (no auth token needed) ──────────────────────────

export async function ragFetch(path, options = {}) {
  const url = `${RAG_V2_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  return res;
}

// ─── Workspaces (MiccoRAG-v2) ───────────────────────────────────────────────

export const workspacesApi = {
  /** GET /api/v1/workspaces */
  list: () => ragFetch('/api/v1/workspaces'),

  /** GET /api/v1/workspaces/summary */
  summary: () => ragFetch('/api/v1/workspaces/summary'),

  /** POST /api/v1/workspaces */
  create: (body) =>
    ragFetch('/api/v1/workspaces', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** PUT /api/v1/workspaces/{id} */
  update: (id, body) =>
    ragFetch(`/api/v1/workspaces/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  /** DELETE /api/v1/workspaces/{id} */
  delete: (id) =>
    ragFetch(`/api/v1/workspaces/${id}`, { method: 'DELETE' }),
};

// ─── Documents (MiccoRAG-v2) ────────────────────────────────────────────────

export const ragDocumentsApi = {
  /** GET /api/v1/documents/workspace/{workspaceId} */
  list: (workspaceId) =>
    ragFetch(`/api/v1/documents/workspace/${workspaceId}`),

  /** GET /api/v1/documents/{docId} */
  get: (docId) => ragFetch(`/api/v1/documents/${docId}`),

  /** POST /api/v1/documents/upload/{workspaceId}  (multipart) */
  upload: (workspaceId, file) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${RAG_V2_BASE}/api/v1/documents/upload/${workspaceId}`, {
      method: 'POST',
      body: form,
    });
  },

  /** DELETE /api/v1/documents/{docId} */
  delete: (docId) =>
    ragFetch(`/api/v1/documents/${docId}`, { method: 'DELETE' }),

  /** GET /api/v1/documents/{docId}/markdown */
  markdown: (docId) =>
    ragFetch(`/api/v1/documents/${docId}/markdown`),

  /** PUT /api/v1/documents/{docId} */
  update: (docId, body) =>
    ragFetch(`/api/v1/documents/${docId}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  /** GET /api/v1/documents/{docId}/download */
  downloadUrl: (docId) => `${RAG_V2_BASE}/api/v1/documents/${docId}/download`,
};

// ─── RAG Processing (MiccoRAG-v2) ───────────────────────────────────────────

export const ragProcessApi = {
  /** POST /api/v1/rag/process/{docId} */
  process: (docId) =>
    ragFetch(`/api/v1/rag/process/${docId}`, { method: 'POST' }),

  /** POST /api/v1/rag/process-batch  body: { document_ids: [...] } */
  processBatch: (documentIds) =>
    ragFetch('/api/v1/rag/process-batch', {
      method: 'POST',
      body: JSON.stringify({ document_ids: documentIds }),
    }),

  /** GET /api/v1/rag/stats/{workspaceId} */
  stats: (workspaceId) =>
    ragFetch(`/api/v1/rag/stats/${workspaceId}`),
};

// ─── RAG Query (MiccoRAG-v2) ────────────────────────────────────────────────

export const ragQueryApi = {
  /** POST /api/v1/rag/query/{workspaceId} */
  query: (workspaceId, question, topK = 5) =>
    ragFetch(`/api/v1/rag/query/${workspaceId}`, {
      method: 'POST',
      body: JSON.stringify({ question, top_k: topK }),
    }),
};

// ─── Chat (MiccoRAG-v2) ─────────────────────────────────────────────────────

export const ragChatApi = {
  /**
   * POST /api/v1/rag/chat/{workspaceId}/stream — SSE streaming
   * Returns a ReadableStream. Caller should read with EventSource or fetch reader.
   */
  streamChat: async (workspaceId, message, options = {}) => {
    const url = `${RAG_V2_BASE}/api/v1/rag/chat/${workspaceId}/stream`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        document_ids: options.documentIds || [],
        mode: options.mode || 'hybrid',
        stream: true,
      }),
    });
    return res; // caller handles res.body ReadableStream
  },

  /** POST /api/v1/rag/chat/{workspaceId} — non-streaming */
  chat: (workspaceId, message, options = {}) =>
    ragFetch(`/api/v1/rag/chat/${workspaceId}`, {
      method: 'POST',
      body: JSON.stringify({
        message,
        document_ids: options.documentIds || [],
        mode: options.mode || 'hybrid',
      }),
    }),

  /** GET /api/v1/rag/chat/{workspaceId}/history */
  history: (workspaceId) =>
    ragFetch(`/api/v1/rag/chat/${workspaceId}/history`),

  /** DELETE /api/v1/rag/chat/{workspaceId}/history */
  clearHistory: (workspaceId) =>
    ragFetch(`/api/v1/rag/chat/${workspaceId}/history`, { method: 'DELETE' }),
};

// ─── Helper: parse SSE stream ────────────────────────────────────────────────
/**
 * Reads a streaming fetch response (SSE/NDJSON) and calls onChunk for each
 * SSE data event. Calls onDone when the stream closes.
 *
 * Each SSE line: "data: {...json...}\n\n"
 */
export async function readSSEStream(response, { onChunk, onDone, onError }) {
  if (!response.ok) {
    const text = await response.text();
    onError?.(new Error(`HTTP ${response.status}: ${text}`));
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // SSE messages are separated by double newlines
      const messages = buffer.split('\n\n');
      buffer = messages.pop(); // keep incomplete last chunk

      for (const message of messages) {
        if (!message.trim()) continue;

        let eventType = null;
        let dataStr = null;

        for (const line of message.split('\n')) {
          const trimmed = line.trim();
          if (trimmed.startsWith('event:')) {
            eventType = trimmed.slice(6).trim();
          } else if (trimmed.startsWith('data:')) {
            dataStr = trimmed.slice(5).trim();
          }
          // ignore ':' comment lines (heartbeat)
        }

        if (!dataStr) continue;
        if (dataStr === '[DONE]') {
          onDone?.();
          return;
        }

        try {
          const parsed = JSON.parse(dataStr);
          // Merge SSE event type into chunk so handlers can use chunk.event
          const chunk = eventType ? { event: eventType, ...parsed } : parsed;
          onChunk?.(chunk);
        } catch {
          onChunk?.({ raw: dataStr });
        }
      }
    }
    onDone?.();
  } catch (err) {
    onError?.(err);
  }
}

// ─── Knowledge Graph (MiccoRAG-v2) ──────────────────────────────────────────
export const ragGraphApi = {
  /** GET /api/v1/rag/graph/{workspaceId} */
  getGraph: (workspaceId) =>
    ragFetch(`/api/v1/rag/graph/${workspaceId}`),
};
