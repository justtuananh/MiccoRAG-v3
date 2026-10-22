"""B06 diagnosis: persistence and owner detail already carry the rejection reason."""
from sqlalchemy import select

from app.api_compat import approvals
from app.models import Document
from app.models.audit_event import AuditEvent
from test_fix_crossstack import scoped_api, bearer  # noqa: F401


async def test_rejection_reason_survives_reload_and_keeps_detail_permissions(scoped_api):
    client, db, _ = scoped_api
    client._transport.app.include_router(approvals.router)
    doc = await db.get(Document, 104)
    doc.approval_status = 'pending'
    await db.commit()
    reason = 'Thiếu căn cứ.\nBổ sung ngày hiệu lực.'
    response = await client.post('/api/approvals/documents/104/reject',
                                 json={'note': f'  {reason}  '}, headers=bearer(4))
    assert response.status_code == 200, response.text
    db.expire_all()  # Force subsequent auth and detail reads to reload database state.
    for _ in range(2):
        response = await client.get('/api/documents/104', headers=bearer(5))
        assert response.status_code == 200, response.text
        assert response.json()['approval_status'] == 'rejected'
        assert response.json()['approval_note'] == reason
    audit = (await db.execute(select(AuditEvent).where(
        AuditEvent.object_id == 104, AuditEvent.action == 'reject'
    ))).scalar_one()
    assert audit.reason == reason
    for uid in [4, 6, 7]:
        response = await client.get('/api/documents/104', headers=bearer(uid))
        assert response.status_code == 403, response.text
        assert reason not in response.text
    assert (await client.get('/api/documents/104')).status_code == 401
