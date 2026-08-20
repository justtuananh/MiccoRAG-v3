---
description: Phối hợp 2 agent backend và frontend để hoàn thành task
---

## Quy trình phối hợp Agent

Khi user giao task yêu cầu cả backend và frontend:

### Bước 1: Analyze Task
- Đọc yêu cầu chi tiết từ user
- Xác định scope: backend-only, frontend-only, hoặc full-stack
- Nếu full-stack → tiến hành bước 2

### Bước 2: Lên kế hoạch
Tạo task list:
```
Task: [Mô tả]
├── Backend Tasks:
│   ├── [ ] Task 1
│   └── [ ] Task 2
├── Frontend Tasks:
│   ├── [ ] Task 1
│   └── [ ] Task 2
└── Integration:
    └── [ ] Test kết nối
```

### Bước 3: Backend Implementation
1. Spawn backend-dev agent:
   ```
   - Implement backend API endpoints
   - Write/update unit tests
   - Update schemas
   ```
2. Backend dev hoàn thành → notify frontend

### Bước 4: Frontend Implementation
1. Spawn frontend-dev agent:
   ```
   - Implement UI components
   - Integrate API calls
   - Update state management
   ```
2. Frontend dev hoàn thành → notify QA

### Bước 5: QA Testing
1. Spawn qa-tester agent
2. Run full test suite
3. Nếu fail → feedback cho agent liên quan
4. Lặp lại đến khi đạt 95%

### Bước 6: Final Report
Tạo báo cáo hoàn thành:
```markdown
# Task Completion Report

## Status: ✅ COMPLETE / ❌ INCOMPLETE

## Backend Changes
- Files modified: ...
- Tests: ...

## Frontend Changes
- Components modified: ...
- Tests: ...

## Quality
- Test Pass Rate: XX%
- Coverage: XX%
- Critical Bugs: 0

## Notes
...
```

## Commands để spawn agents

### Backend Agent
```bash
# Sử dụng Agent tool với backend-dev
Task: [mô tả]
Working dir: /home/kms/micco-backend/backend
```

### Frontend Agent
```bash
# Sử dụng Agent tool với frontend-dev
Task: [mô tả]
Working dir: /home/kms/micco/micco-frontend
```

## Coordination Notes
- Backend và Frontend phải agree về API contract trước khi implement
- Dùng shared schema file để đảm bảo consistency
- Nếu có conflict → discuss và resolve trước khi code
