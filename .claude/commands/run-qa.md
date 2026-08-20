---
description: Chạy QA tests và đảm bảo chất lượng đạt 95%
---

## QA Testing Workflow

### Quy trình test nhiều lần đạt 95% quality:

#### Lần 1: Initial Test
```bash
# Backend tests
cd /home/kms/micco-backend/backend && pytest tests/ -v --tb=short

# Frontend tests
cd /home/kms/micco/micco-frontend && npm run test
```

#### Lần 2: Integration Test
```bash
# Backend integration
cd /home/kms/micco-backend/backend && pytest tests/integration/ -v

# Check API endpoints
curl -s http://localhost:8000/api/v1/health
```

#### Lần 3: RAG Pipeline Test
```bash
# Full RAG pipeline
cd /home/kms/micco-backend/backend && pytest tests/integration/test_rag_pipeline.py -v
```

#### Lần N: Fix & Retest
- Nếu có failures → analyze và fix
- Retest cho đến khi đạt 95% pass rate

### Quality Criteria
```
✅ PASS = Test pass rate ≥ 95%
❌ FAIL = Test pass rate < 95%
```

### Report Format
```markdown
## QA Report - Iteration [N]

### Results
- Total: XX
- Passed: XX (XX%)
- Failed: XX

### Failed Tests
1. test_xxx - [reason] → Fixed by [agent]

### Status
[ ] Continue iteration
[x] Quality gate PASSED
```

## Quick Commands

### Single command - Run all tests
```bash
cd /home/kms/micco && \
  echo "=== BACKEND TESTS ===" && \
  cd backend && pytest tests/ -v --tb=line && \
  echo "=== FRONTEND TESTS ===" && \
  cd ../micco-frontend && npm run test
```

### With coverage
```bash
cd /home/kms/micco/backend && pytest tests/ --cov=app --cov-report=term-missing
```
