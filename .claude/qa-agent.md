# qa-agent — moved to a proper subagent

> This role is now a first-class, auto-routed Claude Code subagent: **`.claude/agents/qa.md`**.
> When a QA/"ready to merge?"/end-to-end verification task comes up, the `qa` subagent is selected
> automatically — it runs the quality gate (`harness/run.sh qa` → GO/NO-GO) and delegates fixes to the
> backend/frontend/test subagents.
>
> Kept only as a pointer (referenced by legacy `.claude/settings.json`). Edit `.claude/agents/qa.md`.
