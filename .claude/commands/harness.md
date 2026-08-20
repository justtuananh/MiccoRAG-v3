---
description: Run the MiccoRAG-v3 harness on the KMS VPS and summarize results.
---

# /harness [component]

Runs the MiccoRAG-v3 test/verify harness over SSH and summarizes the output
(each component prints `TỔNG: N PASS / M FAIL / K WARN`, exit 0 when no FAIL).

Default (no arg) = `all` (free preset: `smoke be fe test deploy`).

## Free components / presets

`<arg>` ∈ `{smoke, be, fe, qa, test, deploy, all}`:

```
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh <arg>'
```

- `smoke` — infra/health checks
- `be` — backend: ruff + pytest unit + coverage
- `fe` — frontend: eslint + vite build
- `test` — all pytest suites (backend + legacy micco-server)
- `deploy` — read-only deploy-verify (containers, migrations, nginx routing; surfaces the `:8089` nginx drift as WARN)
- `qa` — quality gate: `smoke + be + fe + test` → GO / NO-GO
- `all` — free preset (default)

## Paid components (cost Gemini API calls — opt in)

```
ssh KMS 'RUN_EVAL=1  bash /home/kms/MiccoRAG-v3/harness/run.sh eval'
ssh KMS 'RUN_BENCH=1 bash /home/kms/MiccoRAG-v3/harness/run.sh bench'
```

- `eval` — RAG quality on the golden set (retrieval/keyword/citation rates, pass@1)
- `bench` — latency per search mode (hybrid / vector_only / naive); slow

## Artifacts

Append `--json` and/or `--md` to write `harness/reports/<ts>.{json,md}` (gitignored):

```
ssh KMS 'bash /home/kms/MiccoRAG-v3/harness/run.sh all --json --md'
```

## Safety

- **Shared VPS** — the harness only inspects `nexusrag-*` / `micco-*` containers and never
  restarts or removes anything. Do not touch other projects on the box.
- `eval` and `bench` call **Gemini** and cost money — run them only when explicitly asked.

After running, report the per-component `TỔNG` line, overall PASS/FAIL/WARN, and any
FAIL or notable WARN (e.g. the `:8089` nginx drift).
