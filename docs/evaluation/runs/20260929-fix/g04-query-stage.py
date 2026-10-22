"""Read-only staged retrieval diagnostic for the original G04 question."""
import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

os.environ.update(json.load(open("/tmp/micco-fix-20260929/runtime-env.json")))
sys.path.insert(0, "/tmp/micco-fix-20260929/micco-backend/backend")

import httpx
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.user import User

QUESTION = (
    "Theo quy trình mua sắm vật tư được chọn, gói đúng 500 triệu đồng có "
    "phải đấu thầu không, ai phê duyệt và thời gian xử lý tối đa bao nhiêu "
    "ngày làm việc?"
)


async def main():
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.role == "Giám đốc"))).scalars().first()
        if user is None:
            raise RuntimeError("No director in cloned DB")
        token = create_access_token({"sub": str(user.id)}, timedelta(minutes=5))
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "http://127.0.0.1:18001/api/v1/rag/query/9",
            headers={"Authorization": f"Bearer {token}"},
            json={"question": QUESTION, "document_ids": [22], "top_k": 8, "mode": "hybrid"},
        )
    obj = response.json()
    result = {
        "status": response.status_code,
        "question": QUESTION,
        "chunk_ids": [chunk.get("chunk_id") for chunk in obj.get("chunks", [])],
        "chunk_document_ids": [chunk.get("citation", {}).get("document_id") if chunk.get("citation") else chunk.get("metadata", {}).get("document_id") for chunk in obj.get("chunks", [])],
        "chunk_source_labels": [chunk.get("metadata", {}).get("source") for chunk in obj.get("chunks", [])],
        "canonical_source_label": "Quy trình mua sắm vật tư an toàn.docx" in obj.get("context", ""),
        "context_has_table_row": "20 ngày làm việc" in obj.get("context", "") and "Giám đốc" in obj.get("context", ""),
        "context": obj.get("context", ""),
        "citations": obj.get("citations", []),
        "error": obj.get("detail") if response.status_code != 200 else None,
    }
    out = Path("/tmp/micco-fix-20260929/g04-query-stage.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({key: result[key] for key in ("status", "chunk_ids", "chunk_document_ids", "context_has_table_row")}, ensure_ascii=False))


asyncio.run(main())
