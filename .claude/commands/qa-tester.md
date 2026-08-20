---
description: QA Testing skill - chạy harness gates và đảm bảo chất lượng trước khi bàn giao
---

## QA Tester Skill

Chạy the unified harness và đảm bảo chất lượng đạt mục tiêu trước khi bàn giao.
Everything runs through the repo-root `harness/` (never ad-hoc `pytest`/`npm` in random dirs).

### Workflow
```
1. Run the QA gate  (smoke + be + fe + test → GO/NO-GO)
2. Run full pytest suites
3. Run frontend e2e (opt-in, Playwright)
4. Analyze failures from the harness report
5. Report → Fix → Re-test
6. Loop đến khi gate = GO
```

### Commands

Run from the VPS (`ssh KMS`), repo root `/home/kms/MiccoRAG-v3`.

#### QA gate (primary — GO/NO-GO)
```bash
bash harness/run.sh qa            # = smoke + be + fe + test, prints GO / NO-GO
```

#### Backend tests (ruff if present + pytest unit + coverage)
```bash
bash harness/run.sh be
```

#### All pytest suites (backend + micco-server legacy)
```bash
bash harness/run.sh test          # micco-server legacy WARN-skips if langgraph missing
```

#### Frontend checks (eslint + vite build; e2e opt-in)
```bash
bash harness/run.sh fe            # lint + build only (no unit-test runner exists)
RUN_E2E=1 bash harness/run.sh fe  # + Playwright e2e
```

#### RAG quality (opt-in, calls Gemini — paid)
```bash
RUN_EVAL=1 bash harness/run.sh eval   # golden set: retrieval/keyword/citation, pass@1
```

Each component prints `TỔNG: N PASS / M FAIL / K WARN` and exits 0 when there are no FAIL.
Add `--json` / `--md` to also write a report to `harness/reports/<ts>.{json,md}`.

### Quality Criteria
| Metric | Target |
|--------|--------|
| QA gate | GO (no FAIL in smoke/be/fe/test) |
| Test Pass Rate | ≥ 95% |
| Coverage | not gated yet — coverage tooling not installed |
| Critical Bugs | 0 |

> Note: frontend has **no unit-test runner** — only eslint + `vite build` + optional Playwright e2e.
> Backend coverage is emitted best-effort by `be`; a hard coverage threshold isn't wired up yet.

### Report Template
```markdown
## QA Report

### Summary
- Gate: GO / NO-GO
- Backend tests: XX/XX passed (XX%)
- Frontend: lint ✅ / build ✅ / e2e ✅
- Status: ✅ PASS / ❌ FAIL

### Failures
| Component | Test | Error | Fix |
|-----------|------|-------|-----|
| ... | ... | ... | ... |

### Next Steps
...
```
