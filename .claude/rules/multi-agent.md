# Multi-Agent Collaboration Rules

## Overview
Hệ thống sử dụng 3 agents để phối hợp phát triển:
- **backend-dev**: Phát triển backend FastAPI
- **frontend-dev**: Phát triển frontend React
- **qa-tester**: Testing và quality assurance

## Workflow

### Task分配
```
User Task
    ↓
┌─────────────────────────────────────┐
│         Main Agent (This Claude)     │
│  1. Analyze task                    │
│  2. Determine: backend/FE/both      │
│  3. Coordinate agents               │
└─────────────────────────────────────┘
    ↓
┌──────────┐    ┌──────────┐
│ Backend  │    │ Frontend │
│   Dev    │    │   Dev    │
└──────────┘    └──────────┘
    ↓                ↓
┌─────────────────────────────────────┐
│           QA Tester                  │
│  Run tests → 95% pass               │
└─────────────────────────────────────┘
    ↓
 Final Report
```

## Coordination Protocol

### Backend-First Tasks
1. Backend dev implement API + tests
2. Frontend dev implement UI (sau khi API ready)
3. QA test cả hai

### Frontend-First Tasks
1. Frontend dev implement UI (mock data)
2. Backend dev implement API
3. QA test integration

### Full-Stack Tasks
1. Agree on API contract trước
2. Parallel development (nếu possible)
3. Integration testing
4. QA verification

## Agent Communication

### Via Task System
- Backend dev complete → create task for frontend
- Frontend dev complete → create task for QA
- QA find bugs → assign to relevant agent

### Via File System
- API schemas trong `backend/app/schemas/`
- Frontend types trong `micco-frontend/src/types/`
- Shared contracts đảm bảo consistency

## Quality Gates

### Before any agent completes
- [ ] Code follows conventions
- [ ] Type hints / TypeScript types
- [ ] Error handling
- [ ] Unit tests written

### Before QA sign-off
- [ ] Unit tests ≥ 95% pass
- [ ] Integration tests pass
- [ ] No critical bugs
- [ ] Coverage ≥ 80%

## Commands Reference
| Command | Description |
|---------|------------|
| `/coordinate-task` | Bắt đầu phối hợp agents |
| `/backend-dev` | Backend development guide |
| `/frontend-dev` | Frontend development guide |
| `/qa-tester` | QA testing guide |
| `/run-qa` | Run tests to 95% |

## Error Handling
- Agent fail → analyze error → assign fix → retry
- Max 3 retries per agent per task
- Escalate to user nếu không resolve được
