# frontend-agent — moved to a proper subagent

> This role is now a first-class, auto-routed Claude Code subagent: **`.claude/agents/frontend.md`**.
> When a frontend task comes up in MiccoRAG-v3 (React 19 + Vite plain JSX pages/components, chat UI +
> SSE, Tailwind, routing, api.js wiring), the `frontend` subagent is selected automatically — it edits
> the code and verifies via the harness (`harness/run.sh fe`, `RUN_E2E=1` for Playwright e2e).
>
> Kept only as a pointer (referenced by legacy `.claude/settings.json`). Edit `.claude/agents/frontend.md`.
