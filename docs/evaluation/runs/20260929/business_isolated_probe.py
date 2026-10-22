"""Business state/permission probes using only in-memory objects and mocks."""
import asyncio
import json
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.api import workspaces
from app.api_compat import approvals, knowledge
from app.api_compat.documents import _check_doc_access, _can_modify_doc
from app.core.permissions import can_read_all_knowledge
from app.models.document import DocumentStatus

results = []


def record(name, expected, actual):
    results.append({"probe": name, "pass": expected == actual, "expected": expected, "actual": actual})


def err_code(fn, *args):
    try:
        fn(*args)
        return 200
    except HTTPException as exc:
        return exc.status_code


def user(role, uid=1, dept=1):
    return NS(id=uid, role=role, department_id=dept)


def db_with(obj):
    return NS(execute=AsyncMock(return_value=NS(scalar_one_or_none=lambda: obj)), commit=AsyncMock())


async def call(fn, obj, actor, **kwargs):
    db = db_with(obj)
    try:
        await fn(obj.id, db=db, current_user=actor, **kwargs)
        return {"http": 200, "approval_status": obj.approval_status,
                "status": getattr(obj.status, "value", obj.status), "commits": db.commit.await_count,
                "note": getattr(obj, "approval_note", None)}
    except HTTPException as exc:
        return {"http": exc.status_code, "approval_status": obj.approval_status,
                "commits": db.commit.await_count}


async def main():
    director = user("Giám đốc", 10, 3)
    deputy = user("Phó giám đốc", 11, 3)
    staff = user("Nhân viên", 12, 1)
    head_a = user("Trưởng phòng", 13, 1)
    head_b = user("Trưởng phòng", 14, 2)
    admin = user("Admin", 15, None)
    private_b = NS(visibility="private", owner_id=99, department_id=None)
    dept_b = NS(visibility="department", owner_id=None, department_id=2)
    for actor in (director, deputy):
        record(f"{actor.role}: private KB read", True, workspaces._can_access_workspace(actor, private_b))
        record(f"{actor.role}: private KB modify", False, workspaces._can_modify_workspace(actor, private_b))
        record(f"{actor.role}: private KB delete", False, workspaces._can_delete_workspace(actor, private_b))
        record(f"{actor.role}: department B KB read", True, workspaces._can_access_workspace(actor, dept_b))
        doc = NS(visibility="private", uploader_id=99, department_id=None)
        record(f"{actor.role}: private doc read", 200, err_code(_check_doc_access, actor, doc))
        record(f"{actor.role}: private doc modify", 403, err_code(_can_modify_doc, actor, doc))
        for visibility, kb in [("private", NS(id=201, visibility="private", owner_id=99, department_id=None)),
                               ("department", NS(id=202, visibility="department", owner_id=None, department_id=2)),
                               ("public", NS(id=203, visibility="public", owner_id=None, department_id=None))]:
            update_db = db_with(kb)
            try:
                await workspaces.update_workspace(kb.id, NS(name="tamper"), update_db, actor)
                update_code = 200
            except HTTPException as exc:
                update_code = exc.status_code
            record(f"{actor.role}: PUT other {visibility} KB", (403, 0), (update_code, update_db.commit.await_count))
            delete_db = db_with(kb)
            try:
                await workspaces.delete_workspace(kb.id, delete_db, actor)
                delete_code = 204
            except HTTPException as exc:
                delete_code = exc.status_code
            record(f"{actor.role}: DELETE other {visibility} KB", (403, 0), (delete_code, delete_db.commit.await_count))
    record("staff A: private KB B read", False, workspaces._can_access_workspace(staff, private_b))
    record("staff A: department KB B read", False, workspaces._can_access_workspace(staff, dept_b))
    record("head A: department KB B modify", False, workspaces._can_modify_workspace(head_a, dept_b))
    record("admin: department KB B modify", True, workspaces._can_modify_workspace(admin, dept_b))
    for vis, expected in [("private", "approved"), ("public", "pending_dept"), ("department", "pending_dept")]:
        record(f"staff knowledge {vis} initial", expected, knowledge._initial_approval_status(staff.role, vis))
    record("head public knowledge initial", "pending_org", knowledge._initial_approval_status(head_a.role, "public"))
    record("director public knowledge initial", "approved", knowledge._initial_approval_status(director.role, "public"))

    # Branches stop at the first approval stage, so no indexing/file/DB connection.
    for actor, expected_http, expected_status in [
        (head_a, 200, "pending_org"), (head_b, 403, "pending"),
        (director, 403, "pending"), (staff, 403, "pending")]:
        doc = NS(id=501, approval_status="pending", visibility="public", department_id=1,
                 status=DocumentStatus.PENDING)
        actual = await call(approvals.approve_document, doc, actor, background_tasks=NS(add_task=lambda *a: None))
        record(f"public doc dept approve by {actor.role}/dept{actor.department_id}",
               {"http": expected_http, "approval_status": expected_status},
               {k: actual[k] for k in ("http", "approval_status")})
    for actor, expected_http, expected_status in [
        (head_a, 200, "pending_org"), (head_b, 403, "pending_dept"),
        (director, 403, "pending_dept"), (staff, 403, "pending_dept")]:
        entry = NS(id=601, approval_status="pending_dept", visibility="public", department_id=1,
                   status="Pending")
        actual = await call(approvals.approve_knowledge, entry, actor, background_tasks=NS(add_task=lambda *a: None))
        record(f"public knowledge dept approve by {actor.role}/dept{actor.department_id}",
               {"http": expected_http, "approval_status": expected_status},
               {k: actual[k] for k in ("http", "approval_status")})

    for state in ("approved", "rejected"):
        doc = NS(id=502, approval_status=state, visibility="public", department_id=1,
                 status=DocumentStatus.PENDING)
        actual = await call(approvals.approve_document, doc, head_a, background_tasks=NS(add_task=lambda *a: None))
        record(f"document repeat approve {state}", {"http": 400, "approval_status": state, "commits": 0}, actual)
        doc2 = NS(id=504, approval_status=state, visibility="public", department_id=1,
                  status=DocumentStatus.PENDING)
        actual2 = await call(approvals.reject_document, doc2, head_a, note="reason")
        record(f"document repeat reject {state}", {"http": 400, "approval_status": state, "commits": 0}, actual2)
        entry2 = NS(id=604, approval_status=state, visibility="public", department_id=1,
                    status="Pending")
        actual3 = await call(approvals.approve_knowledge, entry2, head_a, background_tasks=NS(add_task=lambda *a: None))
        record(f"knowledge repeat approve {state}", {"http": 400, "approval_status": state, "commits": 0}, actual3)
        entry3 = NS(id=605, approval_status=state, visibility="public", department_id=1,
                    status="Pending")
        actual4 = await call(approvals.reject_knowledge, entry3, head_a, note="reason")
        record(f"knowledge repeat reject {state}", {"http": 400, "approval_status": state, "commits": 0}, actual4)

    for kind, approve_fn, reject_fn, state in [
        ("document", approvals.approve_document, approvals.reject_document, "pending_org"),
        ("knowledge", approvals.approve_knowledge, approvals.reject_knowledge, "pending_org")]:
        for fn, action in [(approve_fn, "approve"), (reject_fn, "reject")]:
            obj = NS(id=606, approval_status=state, visibility="internal", department_id=1,
                     status="Pending")
            extra = {"background_tasks": NS(add_task=lambda *a: None)} if action == "approve" else {"note": "reason"}
            actual = await call(fn, obj, director, **extra)
            record(f"{kind} non-public pending_org {action}",
                   {"http": 400, "approval_status": state, "commits": 0}, actual)

    for kind, approve_fn, reject_fn, state in [
        ("document", approvals.approve_document, approvals.reject_document, "pending"),
        ("knowledge", approvals.approve_knowledge, approvals.reject_knowledge, "pending_dept")]:
        for fn, action in [(approve_fn, "approve"), (reject_fn, "reject")]:
            obj = NS(id=607, approval_status=state, visibility="public", department_id=2,
                     status="Pending")
            extra = {"background_tasks": NS(add_task=lambda *a: None)} if action == "approve" else {"note": "reason"}
            actual = await call(fn, obj, head_a, **extra)
            record(f"head A: other dept {kind} {action}",
                   {"http": 403, "approval_status": state, "commits": 0}, actual)

    for kind, approve_fn, reject_fn in [
        ("document", approvals.approve_document, approvals.reject_document),
        ("knowledge", approvals.approve_knowledge, approvals.reject_knowledge)]:
        for actor, state, denied_stage in [(head_a, "pending_org", "org"),
                                            (director, "pending" if kind == "document" else "pending_dept", "dept")]:
            for fn, action in [(approve_fn, "approve"), (reject_fn, "reject")]:
                obj = NS(id=608, approval_status=state, visibility="public", department_id=1,
                         status="Pending")
                extra = {"background_tasks": NS(add_task=lambda *a: None)} if action == "approve" else {"note": "reason"}
                actual = await call(fn, obj, actor, **extra)
                record(f"{actor.role}: {kind} {denied_stage} {action}",
                       {"http": 403, "approval_status": state, "commits": 0}, actual)

    entry = NS(id=602, approval_status="pending_dept", visibility="public", department_id=1,
               status="Pending", approval_note=None)
    actual = await call(approvals.reject_knowledge, entry, head_a, note="  ")
    record("knowledge reject blank note", {"http": 400, "approval_status": "pending_dept", "commits": 0}, actual)

    doc = NS(id=503, approval_status="pending", visibility="internal", department_id=1,
             status=DocumentStatus.PENDING, approval_note=None)
    actual = await call(approvals.reject_document, doc, head_a, note=None)
    record("document reject blank note observed", {"http": 200, "approval_status": "rejected", "status": "rejected", "commits": 1, "note": None}, actual)

    # Read-only detail endpoint for an item outside the department approval queue.
    foreign_doc = NS(id=701, approval_status="pending", visibility="internal", department_id=2,
                     status=DocumentStatus.PENDING, chunk_count=0, error_message=None, updated_at=None)
    foreign_db = db_with(foreign_doc)
    try:
        payload = await approvals.get_document_status(foreign_doc.id, foreign_db, head_a)
        code = 200
    except HTTPException as exc:
        payload = None
        code = exc.status_code
    record("head A: status of pending doc B (observed)",
           {"http": 200, "document_id": 701},
           {"http": code, "document_id": payload.get("id") if isinstance(payload, dict) else None})

    print(json.dumps({"environment": "in-memory objects; production code functions; no DB/file/index writes",
                      "passed": sum(v["pass"] for v in results), "total": len(results), "results": results}, ensure_ascii=False))


asyncio.run(main())
