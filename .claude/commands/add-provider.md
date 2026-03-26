---
description: Thêm LLM provider mới vào hệ thống
---

Để thêm LLM provider mới có tên $ARGUMENTS:
1. Tạo file backend/app/services/llm/providers/$ARGUMENTS.py
2. Implement LLMProvider abstract class
3. Thêm vào factory trong backend/app/services/llm/__init__.py
4. Thêm env var LLM_PROVIDER=$ARGUMENTS vào .env.example
5. Viết unit test trong tests/unit/test_llm_$ARGUMENTS.py
6. Update CLAUDE.md phần LLM Providers
