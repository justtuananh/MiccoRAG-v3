---
description: QA Testing skill - chạy tests và đảm bảo chất lượng 95%
---

## QA Tester Skill

Chạy tests và đảm bảo chất lượng đạt 95% trước khi bàn giao.

### Workflow
```
1. Run backend tests
2. Run frontend tests
3. Analyze failures
4. Report → Fix → Re-test
5. Loop đến khi 95% pass
```

### Commands

#### Backend Tests
```bash
cd /home/kms/micco/backend && pytest tests/ -v --tb=short
```

#### Frontend Tests
```bash
cd /home/kms/micco/micco-frontend && npm run test
```

#### Full QA Pipeline
```bash
# 1. Backend
cd /home/kms/micco/backend && pytest tests/ -v

# 2. Frontend
cd /home/kms/micco/micco-frontend && npm run test

# 3. RAG Pipeline
cd /home/kms/micco/backend && pytest tests/integration/test_rag_pipeline.py -v
```

### Quality Criteria
| Metric | Target |
|--------|--------|
| Test Pass Rate | ≥ 95% |
| Coverage | ≥ 80% |
| Critical Bugs | 0 |

### Report Template
```markdown
## QA Report

### Summary
- Tests: XX/XX passed (XX%)
- Coverage: XX%
- Status: ✅ PASS / ❌ FAIL

### Failures
| Test | Error | Fix |
|------|-------|-----|
| ... | ... | ... |

### Next Steps
...
```
