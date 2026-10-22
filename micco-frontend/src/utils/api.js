/**
 * api.js — Centralized API service layer
 *
 * micco-server  → auth, dashboard, knowledge, admin, approvals, documents (v1)
 * MiccoRAG-v2   → documents (workspaces), chatbot (RAG), rag processing
 */

const RAG_V2_BASE = import.meta.env?.VITE_RAGV2_BASE_URL || '';
const LEGACY_BASE = ''; // proxied through Vite

// ─── AUTH-11: centralized 401 (session-expired) signal ─────────────────────
/**
 * ragFetch/ragFetchV2 are plain module functions (not hooks), so they can't
 * call useAuth().logout() directly. Instead they broadcast this event on a
 * 401, and AuthContext listens for it and calls logout() — so an expired/
 * revoked token logs the user out and ProtectedRoute redirects to /login,
 * instead of pages silently rendering an empty list (see R5-2).
 */
function notifyUnauthorized(res, requestToken) {
  if (res && res.status === 401 && localStorage.getItem('docvault_token') === requestToken) {
    window.dispatchEvent(new Event('auth:unauthorized'));
  }
  return res;
}

// ─── Auth-aware fetch (for micco-server API) ───────────────────────────────
/**
 * Fetch helper that prepends Vite proxy base and injects Bearer token.
 * Used for all /api/* calls (micco-server endpoints).
 */
export function ragFetch(path, options = {}) {
  const token = localStorage.getItem('docvault_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const url = path.startsWith('http') ? path : `${LEGACY_BASE}${path}`;
  return fetch(url, { ...options, headers }).then(res => notifyUnauthorized(res, token));
}

// ─── MiccoRAG-v2 base fetch ────────────────────────────────────────────────

// ragFetchV2: used by workspacesApi, ragDocumentsApi, ragProcessApi, ragChatApi
async function ragFetchV2(path, options = {}) {
  const url = `${RAG_V2_BASE}${path}`;
  const token = localStorage.getItem('docvault_token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { ...options, headers });
  return notifyUnauthorized(res, token);
}

// ─── Workspaces (MiccoRAG-v2) ───────────────────────────────────────────────

export const workspacesApi = {
  /** GET /api/v1/workspaces */
  list: () => ragFetchV2('/api/v1/workspaces'),

  /** GET /api/v1/workspaces/summary */
  summary: () => ragFetchV2('/api/v1/workspaces/summary'),

  /** POST /api/v1/workspaces */
  create: (body) =>
    ragFetchV2('/api/v1/workspaces', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  /** PUT /api/v1/workspaces/{id} */
  update: (id, body) =>
    ragFetchV2(`/api/v1/workspaces/${id}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  /** DELETE /api/v1/workspaces/{id} */
  delete: (id) =>
    ragFetchV2(`/api/v1/workspaces/${id}`, { method: 'DELETE' }),

  /** GET /api/v1/workspaces/{id}/suggested-questions */
  getSuggestedQuestions: (id) =>
    ragFetchV2(`/api/v1/workspaces/${id}/suggested-questions`),
};


// ─── Documents (micco-server compatibility API) ────────────────────────────
/**
 * Uses /api/documents/* endpoints (no workspace prefix).
 * These are the "legacy" document routes backed by the same database
 * as auth/admin/knowledge, scoped by department.
 */

export const documentsApi = {
  duplicateCheck: (id) => ragFetch(`/api/documents/${id}/duplicate-check`),
  /** GET /api/documents */
  list: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.search) qs.set('search', params.search);
    if (params.type) qs.set('type', params.type);
    if (params.category) qs.set('category', params.category);
    if (params.department_id) qs.set('department_id', params.department_id);
    const query = qs.toString();
    return ragFetch(`/api/documents${query ? '?' + query : ''}`);
  },

  /** GET /api/documents/{id} */
  get: (docId) => ragFetch(`/api/documents/${docId}`),

  /** POST /api/documents/upload (multipart) */
  upload: (files, options = {}) => {
    const form = new FormData();
    files.forEach(file => form.append('files', file));
    if (options.visibility) form.append('visibility', options.visibility);
    if (options.department_id) form.append('department_id', options.department_id);
    if (options.tags) form.append('tags', options.tags);
    if (options.category) form.append('category', options.category);
    if (options.effective_from) form.append('effective_from', options.effective_from);
    if (options.effective_until) form.append('effective_until', options.effective_until);
    const token = localStorage.getItem('docvault_token');
    return fetch(`/api/documents/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
  },

  /** DELETE /api/documents/{id} */
  delete: (docId) => ragFetch(`/api/documents/${docId}`, { method: 'DELETE' }),

  /** GET /api/documents/{id}/download */
  downloadUrl: (docId) => `/api/documents/${docId}/download`,

  /** GET /api/documents/{id}/thumbnail */
  thumbnailUrl: (docId) => `/api/documents/${docId}/thumbnail`,

  /** GET /api/documents/{id}/versions */
  listVersions: (docId) => ragFetch(`/api/documents/${docId}/versions`),

  /** POST /api/documents/{id}/versions (multipart) */
  uploadVersion: (docId, file, changeNote, effectiveFrom, effectiveUntil) => {
    const form = new FormData();
    form.append('file', file);
    if (changeNote) form.append('change_note', changeNote);
    if (effectiveFrom) form.append('effective_from', effectiveFrom);
    if (effectiveUntil) form.append('effective_until', effectiveUntil);
    const token = localStorage.getItem('docvault_token');
    return fetch(`/api/documents/${docId}/versions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
  },

  /** GET /api/documents/{id}/versions/{versionId}/download */
  downloadVersionUrl: (docId, versionId) => `/api/documents/${docId}/versions/${versionId}/download`,
};


// ─── Documents (MiccoRAG-v2) ────────────────────────────────────────────────

export const ragDocumentsApi = {
  /** GET /api/v1/documents/workspace/{workspaceId} */
  list: (workspaceId) =>
    ragFetchV2(`/api/v1/documents/workspace/${workspaceId}`),

  /** GET /api/v1/documents/{docId} */
  get: (docId) => ragFetchV2(`/api/v1/documents/${docId}`),

  /** POST /api/v1/documents/upload/{workspaceId}  (multipart) */
  upload: (workspaceId, file, options = {}) => {
    const form = new FormData();
    form.append('file', file);
    if (options.visibility) form.append('visibility', options.visibility);
    if (options.department_id) form.append('department_id', options.department_id);
    if (options.effective_from) form.append('effective_from', options.effective_from);
    if (options.effective_until) form.append('effective_until', options.effective_until);
    
    const token = localStorage.getItem('docvault_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(`${RAG_V2_BASE}/api/v1/documents/upload/${workspaceId}`, {
      method: 'POST',
      headers,
      body: form,
    });
  },

  /** DELETE /api/v1/documents/{docId} */
  delete: (docId) =>
    ragFetchV2(`/api/v1/documents/${docId}`, { method: 'DELETE' }),

  /** GET /api/v1/documents/{docId}/markdown */
  markdown: (docId) =>
    ragFetchV2(`/api/v1/documents/${docId}/markdown`),

  /** PUT /api/v1/documents/{docId} */
  update: (docId, body) =>
    ragFetchV2(`/api/v1/documents/${docId}`, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  /** GET /api/v1/documents/{docId}/download */
  downloadUrl: (docId) => `${RAG_V2_BASE}/api/v1/documents/${docId}/download`,

  /** Image bytes require the same bearer auth and document permission as the source. */
  imageFile: (docId, imageId) =>
    ragFetchV2(`/api/v1/documents/${encodeURIComponent(docId)}/images/${encodeURIComponent(imageId)}/file`),
};

// ─── RAG Processing (MiccoRAG-v2) ───────────────────────────────────────────

export const ragProcessApi = {
  /** POST /api/v1/rag/process/{docId} */
  process: (docId) =>
    ragFetchV2(`/api/v1/rag/process/${docId}`, { method: 'POST' }),

  /** POST /api/v1/rag/process-batch  body: { document_ids: [...] } */
  processBatch: (documentIds) =>
    ragFetchV2('/api/v1/rag/process-batch', {
      method: 'POST',
      body: JSON.stringify({ document_ids: documentIds }),
    }),

  /** GET /api/v1/rag/stats/{workspaceId} */
  stats: (workspaceId) =>
    ragFetchV2(`/api/v1/rag/stats/${workspaceId}`),
};

// ─── Approvals (micco-server parity) ──────────────────────────────────────
export const approvalsApi = {
  /** GET /api/approvals/count */
  count: () => ragFetch('/api/approvals/count'),

  /** GET /api/approvals/pending */
  pending: () => ragFetch('/api/approvals/pending'),

  /** POST /api/approvals/documents/{id}/approve */
  approveDocument: (id) => ragFetch(`/api/approvals/documents/${id}/approve`, { method: 'POST' }),

  /** POST /api/approvals/documents/{id}/reject */
  rejectDocument: (id, note) => ragFetch(`/api/approvals/documents/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ note })
  }),

  /** GET /api/approvals/documents/{id}/status — poll processing state after approve */
  getDocumentStatus: (id) => ragFetch(`/api/approvals/documents/${id}/status`),
};

// ─── RAG Query (MiccoRAG-v2) ────────────────────────────────────────────────

export const ragQueryApi = {
  /** POST /api/v1/rag/query/{workspaceId} */
  query: (workspaceId, question, topK = 5) =>
    ragFetchV2(`/api/v1/rag/query/${workspaceId}`, {
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
    const token = localStorage.getItem('docvault_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(url, {
      method: 'POST',
      headers,
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
    ragFetchV2(`/api/v1/rag/chat/${workspaceId}`, {
      method: 'POST',
      body: JSON.stringify({
        message,
        document_ids: options.documentIds || [],
        mode: options.mode || 'hybrid',
      }),
    }),

  /** GET /api/v1/rag/chat/{workspaceId}/history */
  history: (workspaceId) =>
    ragFetchV2(`/api/v1/rag/chat/${workspaceId}/history`),

  /** DELETE /api/v1/rag/chat/{workspaceId}/history */
  clearHistory: (workspaceId) =>
    ragFetchV2(`/api/v1/rag/chat/${workspaceId}/history`, { method: 'DELETE' }),

  /** DELETE /api/chat/all-history — clears all chat history for every personal workspace of the current user */
  clearAllHistory: () =>
    ragFetch('/api/chat/all-history', { method: 'DELETE' }),

  /** GET /api/chat/my-workspace-id — returns { workspace_id } of the current user's personal workspace */
  getMyWorkspaceId: () =>
    ragFetch('/api/chat/my-workspace-id'),
};

// ─── Helper: parse SSE stream ────────────────────────────────────────────────
/**
 * Reads a streaming fetch response (SSE/NDJSON) and calls onChunk for each
 * SSE data event. Only an explicit complete event or [DONE] confirms success.
 *
 * Each SSE line: "data: {...json...}\n\n"
 */
export async function readSSEStream(response, { onChunk, onDone, onError }) {
  if (!response.ok) {
    const text = await response.text();
    onError?.(new Error(`HTTP ${response.status}: ${text}`));
    return;
  }
  if (!response.body) {
    onError?.(new Error('Luồng phản hồi không có dữ liệu.'));
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finished = false;

  const processMessage = (message) => {
    if (!message.trim() || finished) return;
    let eventType = null;
    const dataLines = [];
    for (const line of message.split('\n')) {
      if (line.startsWith('event:')) eventType = line.slice(6).trim();
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
    }
    const dataStr = dataLines.join('\n');
    if (!dataStr) return;
    if (dataStr === '[DONE]') {
      finished = true;
      onDone?.();
      return;
    }
    let parsed;
    try {
      parsed = JSON.parse(dataStr);
    } catch {
      onChunk?.({ raw: dataStr });
      return;
    }
    const chunk = eventType ? { ...parsed, event: eventType } : parsed;
    const type = chunk.event || chunk.type;
    if (type === 'error') {
      finished = true;
      onError?.(new Error(chunk.message || chunk.data?.message || 'Luồng trả lời bị lỗi.'));
      return;
    }
    onChunk?.(chunk);
    if (type === 'complete') {
      finished = true;
      onDone?.();
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n?/g, '\n');

      // SSE messages are separated by double newlines
      const messages = buffer.split('\n\n');
      buffer = messages.pop(); // keep incomplete last chunk

      for (const message of messages) processMessage(message);
      if (finished) return;
    }
    buffer += decoder.decode().replace(/\r\n?/g, '\n');
    if (buffer.trim()) processMessage(buffer);
    if (!finished) onError?.(new Error('Luồng trả lời kết thúc trước khi có xác nhận hoàn tất.'));
  } catch (err) {
    if (!finished) onError?.(err);
  } finally {
    reader.releaseLock();
  }
}

// ─── Knowledge Graph (MiccoRAG-v2) ──────────────────────────────────────────
export const ragGraphApi = {
  /** GET /api/v1/rag/graph/{workspaceId} */
  getGraph: (workspaceId) =>
    ragFetchV2(`/api/v1/rag/graph/${workspaceId}`),
};
