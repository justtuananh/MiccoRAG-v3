---
description: Phát triển backend code trong micco-backend
---

## Backend Development Workflow

### Working Directory
```
/home/kms/MiccoRAG-v3/micco-backend/backend
```

### Development Steps

1. **Understand Requirements**
   - Đọc yêu cầu từ user
   - Check existing code structure
   - Identify files cần modify

2. **TDD Workflow (BẮT BUỘC)**
   ```
   1. Viết FAILING test trước
   2. Chạy test → confirm fail
   3. Implement minimum code để pass
   4. Chạy lại → GREEN
   5. Refactor nếu cần
   ```

3. **Code Standards**
   - Mọi async function phải có type hints
   - Mọi endpoint phải có docstring
   - Follow `/api/v1/` convention
   - Pydantic v2 syntax

4. **File Structure**
   ```
   backend/
   ├── app/
   │   ├── api/           # Routers
   │   ├── core/          # Config, security
   │   ├── models/        # DB models
   │   ├── schemas/       # Pydantic schemas
   │   └── services/      # Business logic
   └── tests/
       ├── unit/
       └── integration/
   ```

### Common Tasks

#### Add new API endpoint
```python
# 1. Add schema in app/schemas/
class NewFeatureRequest(BaseModel):
    field: str

# 2. Add router in app/api/
@router.post("/new-feature")
async def create_new_feature(request: NewFeatureRequest):
    """Create new feature."""
    ...

# 3. Add to router.py
router.include_router(new_feature_router, prefix="/new-feature")

# 4. Write test
def test_create_new_feature():
    ...
```

#### Add new service
```python
# app/services/new_service.py
from typing import Optional

async def process_something(data: str) -> Optional[str]:
    """Process something."""
    ...
```

### Commands
```bash
# Run server
cd /home/kms/MiccoRAG-v3/micco-backend/backend && uvicorn app.main:app --reload

# Run tests
cd /home/kms/MiccoRAG-v3/micco-backend/backend && pytest tests/ -x --tb=short

# With coverage
cd /home/kms/MiccoRAG-v3/micco-backend/backend && pytest --cov=app --cov-report=html
```

### Testing
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Specific test
pytest tests/unit/test_xxx.py::test_yyy -v
```

### Checklist trước khi complete task
- [ ] Code follows conventions
- [ ] Type hints on all functions
- [ ] Docstrings on all endpoints
- [ ] Unit tests written (TDD)
- [ ] Integration tests pass
- [ ] No hardcoded secrets
- [ ] Error handling in place
