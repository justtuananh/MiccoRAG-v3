"""An upload retry is tied to actor, endpoint, exact payload and current access."""
import hashlib,json
from sqlalchemy import select,text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.models.upload_receipt import UploadReceipt
from app.models import Document,KnowledgeBase
from app.core.permissions import can_read_document


def payload_hash(payload):
    return hashlib.sha256(json.dumps(jsonable_encoder(payload),sort_keys=True,ensure_ascii=False).encode()).hexdigest()


async def replay_upload(db,user,route,key,payload):
    if not isinstance(key,str):return None
    if not key.strip():raise HTTPException(status_code=400,detail='Khóa gửi lại không được rỗng')
    if db.get_bind().dialect.name=='postgresql':
        lock=int.from_bytes(hashlib.sha256(f'{user.id}:{route}:{key}'.encode()).digest()[:8],'big',signed=True)
        await db.execute(text('SELECT pg_advisory_xact_lock(:lock)'),{'lock':lock})
    receipt=(await db.execute(select(UploadReceipt).where(UploadReceipt.actor_id==user.id,UploadReceipt.route==route,UploadReceipt.request_key==key))).scalar_one_or_none()
    if receipt is None:return None
    if receipt.payload_hash!=payload_hash(payload):
        raise HTTPException(status_code=409,detail='Khóa gửi lại đã được dùng cho nội dung khác')
    rows=receipt.response if isinstance(receipt.response,list) else [receipt.response]
    for row in rows:
        doc=await db.get(Document,row['id'])
        kb=await db.get(KnowledgeBase,doc.workspace_id) if doc else None
        if doc is None or kb is None or not can_read_document(user,doc,kb,allow_owner_pending=True):
            raise HTTPException(status_code=403,detail='Tài liệu của yêu cầu trước không còn khả dụng')
    return receipt.response


def record_upload(db,user,route,key,payload,response):
    if isinstance(key,str):
        db.add(UploadReceipt(actor_id=user.id,route=route,request_key=key,payload_hash=payload_hash(payload),response=jsonable_encoder(response)))


async def lock_upload_hashes(db,workspace_id,hashes):
    if not hasattr(db,'get_bind') or db.get_bind().dialect.name!='postgresql':return
    for digest in sorted(set(hashes)):
        lock=int.from_bytes(hashlib.sha256(f'upload:{workspace_id}:{digest}'.encode()).digest()[:8],'big',signed=True)
        await db.execute(text('SELECT pg_advisory_xact_lock(:lock)'),{'lock':lock})

async def require_filename_choice(db, workspace_id, filenames, choice):
    """A different payload with an existing filename needs an explicit new-document choice."""
    if choice not in {None, 'new_document'}:
        raise HTTPException(status_code=400, detail='Lựa chọn trùng tên không hợp lệ')
    names=[str(name or '').strip().casefold() for name in filenames]
    await lock_upload_hashes(db,workspace_id,['filename:'+name for name in names])
    existing=set(str(name).strip().casefold() for name in (await db.execute(select(Document.original_filename).where(
        Document.workspace_id==workspace_id,Document.deleted_at.is_(None),
    ))).scalars().all())
    if choice!='new_document' and (existing.intersection(names) or len(set(names))!=len(names)):
        raise HTTPException(status_code=409,detail='Tên tệp đã tồn tại. Chọn tạo tài liệu riêng hoặc mở tài liệu hiện có để thêm phiên bản mới.')
