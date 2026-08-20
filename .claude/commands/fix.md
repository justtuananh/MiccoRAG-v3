# Fix Command — Fix + TDD Loop

> **Trigger**: Khi user yêu cầu sửa chức năng, fix bug, hoặc cải thiện feature.
>
> **Cách dùng**: `/fix <mô tả bug/feature cần sửa>`

## Workflow

### 1. Hiểu vấn đề (Root Cause)
- Đọc code liên quan, trace execution flow
- Xác định root cause — **KHÔNG fix nếu chưa hiểu root cause**
- Nếu là bug: chạy systematic-debugging skill trước

### 2. Sửa code
- Thực hiện edit/Write
- Hook sẽ tự động format code (ruff cho Python)

### 3. Test tự động (sau mỗi lần sửa)

Sau mỗi lần `Edit`/`Write` hoàn thành, **tự động chạy test**:

**Backend file changed** → pytest + coverage loop:
```bash
cd micco-backend/backend
pytest tests/ -v --tb=short --cov=app --cov-report=term
# Loop: nếu FAIL → fix lại → test lại
# Stop khi: all pass + coverage ≥ 95%
```

**Frontend file changed** → Playwright E2E loop:
```bash
# Kiểm tra frontend đang chạy ở port 5174
# Chạy playwright e2e test
cd .claude/skills/playwright-e2e
node run.js http://localhost:5174
# Loop: nếu FAIL → fix lại → test lại
# Stop khi: all pass
```

### 4. Coverage Gate
- **Backend**: ≥ 95% coverage mới stop loop
- **Frontend**: Tất cả E2E tests pass
- **Max loops**: 10 lần (sau đó báo user)

### 5. Verification
Sau khi stop, verify lại lần cuối:
```bash
pytest tests/ -v  # backend
node run.js http://localhost:5174  # frontend
```

### 6. Report kết quả
```
## Fix Report

| Item | Status |
|------|--------|
| Root Cause | ... |
| Fix Applied | ... |
| Tests | ✅ X passed |
| Coverage | X% |
| Loops | X |
```

## Notes
- Nếu backend + frontend cùng thay đổi → chạy cả hai
- Nếu dev server không chạy → tự khởi động
- Hook `ruff format` chạy tự động sau mỗi edit