"""Duplicate matches never grant access to another uploader's pending content."""
from datetime import datetime
from app.models import Document
from test_fix_crossstack import scoped_api,bearer


async def test_duplicate_check_links_only_readable_same_workspace_target(scoped_api):
    client,db,_=scoped_api
    upload=await db.get(Document,100)
    original=await db.get(Document,104)
    original.uploader_id=6
    original.original_filename='PENDING_HIDDEN_NAME.txt'
    upload.text_fingerprint='f'*64
    upload.duplicate_of_document_id=104
    await db.commit()
    response=await client.get('/api/documents/100/duplicate-check',headers=bearer(5))
    assert response.status_code==200
    assert response.json()['checked'] and response.json()['match_type']=='exact'
    assert response.json()['match'] is None and 'PENDING_HIDDEN_NAME' not in response.text
    admin=await client.get('/api/documents/100/duplicate-check',headers=bearer(1))
    assert admin.json()['match']=={'id':104,'name':'PENDING_HIDDEN_NAME.txt'}
    original.deleted_at=datetime.utcnow();await db.commit()
    assert (await client.get('/api/documents/100/duplicate-check',headers=bearer(1))).json()['match'] is None


async def test_duplicate_endpoint_preserves_private_document_boundary(scoped_api):
    client,db,_=scoped_api
    original=await db.get(Document,102)
    original.text_fingerprint='a'*64
    original.near_duplicate_document_id=100
    original.duplicate_similarity=.97
    await db.commit()
    assert (await client.get('/api/documents/102/duplicate-check')).status_code==401
    assert (await client.get('/api/documents/102/duplicate-check',headers=bearer(6))).status_code==403
    # Even a malformed stored cross-KB link cannot disclose another workspace.
    own=await client.get('/api/documents/102/duplicate-check',headers=bearer(5))
    assert own.status_code==200 and own.json()['match_type']=='similar'
    assert own.json()['match'] is None
