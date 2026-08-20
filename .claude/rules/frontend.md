# Frontend Rules (React + Vite)

## Stack
- React 19 + Vite 7
- Plain JavaScript JSX (`.jsx`) — NOT TypeScript, NOT Next.js
- Tailwind CSS 3 for styling
- react-router-dom v7 for routing
- State = React Context + hooks (no TanStack Query, no Redux)
- Tiptap for the rich-text editor
- Recharts for charts/metrics
- lucide-react for icons
- Package manager: npm (not pnpm on this box)
- Vite dev server on :5174

## Chat UI
- Streaming: consume `POST /api/v1/rag/chat/{workspace_id}/stream` via `fetch` + `ReadableStream` (or EventSource).
- Non-streaming generated answer: `POST /api/v1/rag/chat/{workspace_id}`.
- Retrieval-only (no answer): `POST /api/v1/rag/query/{workspace_id}` returns `{total_chunks, chunks, context, citations}`.
- Message format: `{ role: "user" | "assistant", content: string, citations?: Citation[] }`.
- Always render a loading state (skeleton/spinner) while fetching.
- Suggested questions: `GET /api/v1/workspaces/{id}/suggested-questions`.

## API Calls
- Call the FastAPI backend under `/api/v1` (routers: workspaces, documents, rag, config, expert) through the gateway — there are no Next.js route handlers.
- Dev auth bypass: send header `Authorization: Bearer dev-skip` for read/smoke flows.
- Wrap routes with an error boundary; surface failures via toast notifications.
- Never hardcode provider calls in the client — the backend selects the LLM via its provider factory.

## UX States (required on every data view)
- **Loading**: skeleton or spinner, never a blank screen.
- **Empty**: explicit empty-state message + call-to-action (e.g. "No documents yet — upload one").
- **Error**: inline error + retry affordance; toast for transient failures.
- Keep layouts responsive (mobile → desktop) with Tailwind breakpoints.

## File Upload
- Drag & drop with react-dropzone.
- Accept only: PDF, DOCX, TXT.
- Show a progress bar during upload.
- Client-side max 50MB validation before sending.
