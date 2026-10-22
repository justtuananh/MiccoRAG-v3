"""Read-only live RBAC probe. Execute on VPS backend through SSH stdin."""
import asyncio
import json
from datetime import timedelta

import httpx
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document


async def main():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User).order_by(User.id))).scalars().all()
        kbs = (await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.id))).scalars().all()
        docs = (await db.execute(select(Document).order_by(Document.id))).scalars().all()
    by_role = {}
    for user in users:
        by_role.setdefault(user.role, user)
    summary = {"environment": "live 127.0.0.1:8001; DB read-only", "fixtures": {
        "roles": {role: sum(u.role == role for u in users) for role in by_role},
        "kb_visibility_counts": {v: sum(k.visibility == v for k in kbs) for v in set(k.visibility for k in kbs)},
        "doc_visibility_counts": {v: sum(d.visibility == v for d in docs) for v in set(d.visibility for d in docs)},
    }, "probes": []}
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=20) as client:
        for role in ["Admin", "Giám đốc", "Phó giám đốc", "Trưởng phòng", "Nhân viên"]:
            user = by_role.get(role)
            if not user:
                continue
            token = create_access_token({"sub": str(user.id)}, expires_delta=timedelta(minutes=2))
            headers = {"Authorization": "Bearer " + token}
            item = {"role": role, "department_id": user.department_id}
            for path, key in [
                ("/api/v1/workspaces", "workspaces"),
                ("/api/v1/workspaces/summary", "summary"),
                ("/api/documents", "documents"),
                ("/api/knowledge", "knowledge"),
                ("/api/approvals/count", "approvals_count"),
                ("/api/approvals/pending", "approvals_pending"),
            ]:
                try:
                    resp = await client.get(path, headers=headers)
                    payload = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else None
                    data = {"status": resp.status_code}
                    if key in ("workspaces", "summary") and isinstance(payload, list):
                        data["ids"] = [v.get("id") for v in payload]
                    elif key == "documents":
                        if isinstance(payload, dict):
                            data["shape"] = list(payload.keys())
                            for name in ("items", "documents"):
                                if isinstance(payload.get(name), list):
                                    data["ids"] = [v.get("id") for v in payload[name]]
                        elif isinstance(payload, list):
                            data["ids"] = [v.get("id") for v in payload]
                    elif key == "knowledge" and isinstance(payload, dict):
                        data["ids"] = [v.get("id") for v in payload.get("items", [])]
                        data["total"] = payload.get("total")
                    elif key == "approvals_count" and isinstance(payload, dict):
                        data["count"] = payload.get("count")
                    elif key == "approvals_pending" and isinstance(payload, dict):
                        data["document_count"] = len(payload.get("documents", []))
                        data["knowledge_count"] = len(payload.get("knowledge", []))
                    item[key] = data
                except Exception as exc:
                    item[key] = {"error_type": type(exc).__name__}
            detail = []
            for kb in kbs:
                try:
                    resp = await client.get(f"/api/v1/workspaces/{kb.id}", headers=headers)
                    detail.append({"id": kb.id, "visibility": kb.visibility,
                                   "owner_id": kb.owner_id, "department_id": kb.department_id,
                                   "status": resp.status_code})
                except Exception as exc:
                    detail.append({"id": kb.id, "error_type": type(exc).__name__})
            item["workspace_details"] = detail
            summary["probes"].append(item)
    print(json.dumps(summary, ensure_ascii=False))


asyncio.run(main())
