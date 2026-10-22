"""Extracted-text duplicate rules on real ORM rows, without provider calls."""
from datetime import datetime

import pytest

from app.models import Document
from app.models.document import DocumentStatus
from app.services.document_lifecycle import set_family_deleted
from app.services.text_duplicate import (
    ExactTextDuplicate, canonical_text, claim_extracted_text,
    similarity, text_fingerprint,
)
from test_fix_crossstack import scoped_api


def candidate(doc_id, workspace_id, filename, byte_hash):
    return Document(id=doc_id, workspace_id=workspace_id, filename=filename,
                    original_filename=filename, file_type=filename.rsplit('.', 1)[-1],
                    file_size=100, uploader_id=5, status=DocumentStatus.PARSING,
                    approval_status='approved', content_hash=byte_hash)


def test_canonicalization_keeps_business_facts_distinct():
    text = '  # Quy tắc\n\n**Không** chi quá 12.5% trước 01/09/2026. '
    assert canonical_text(text) == 'Quy tắc Không chi quá 12.5% trước 01/09/2026.'
    assert text_fingerprint(text) == text_fingerprint('Quy tắc Không chi quá 12.5% trước 01/09/2026.')
    for changed in ('Quy tắc Không chi quá 125% trước 01/09/2026.',
                    'Quy tắc chi quá 12.5% trước 01/09/2026.',
                    'Quy tắc Không chi quá 12.5% trước 02/09/2026.',
                    'Quy tắc Không chi ít hơn 12.5% trước 01/09/2026.',
                    'Pressure limit 2 MPa.', 'Pressure limit 2 mPa.',
                    '2**3', '23', 'A__B', 'AB'):
        assert text_fingerprint(text) != text_fingerprint(changed)
    assert text_fingerprint('Pressure limit 2 MPa.') != text_fingerprint('Pressure limit 2 mPa.')
    assert text_fingerprint('2**3') != text_fingerprint('23')
    assert text_fingerprint('A__B') != text_fingerprint('AB')


async def test_pdf_docx_different_bytes_same_extracted_text_is_exact(scoped_api):
    _, db, _ = scoped_api
    original = await db.get(Document, 100)
    original.filename = original.original_filename = 'policy.pdf'
    original.file_type = 'pdf'
    original.content_hash = 'a' * 64
    original.markdown_content = '# Quy tắc\n**Không** chi quá 12.5%.'
    original.parser_version = 'docling'
    incoming = candidate(210, 10, 'policy.docx', 'b' * 64)
    incoming.parser_version = 'docling'
    db.add(incoming)
    await db.commit()

    with pytest.raises(ExactTextDuplicate):
        await claim_extracted_text(db, incoming, 'Quy tắc Không chi quá 12.5%.')
    assert incoming.status == DocumentStatus.FAILED
    assert incoming.duplicate_of_document_id == original.id
    assert incoming.content_hash != original.content_hash
    assert str(original.id) not in incoming.error_message


async def test_ocr_text_is_compared_but_changed_numbers_and_negation_are_not_exact(scoped_api):
    _, db, _ = scoped_api
    text = 'OCR result: must not pay 1000 VND after 02/10/2026.'
    first = candidate(211, 10, 'scan.pdf', 'c' * 64)
    first.markdown_content = text
    db.add(first)
    await db.commit()
    await claim_extracted_text(db, first, text)

    for doc_id, changed in ((212, text.replace('1000', '1001')),
                            (213, text.replace('must not', 'must'))):
        item = candidate(doc_id, 10, f'scan-{doc_id}.pdf', str(doc_id) * 32)
        item.markdown_content = changed
        db.add(item)
        await db.commit()
        await claim_extracted_text(db, item, changed)
        assert item.duplicate_of_document_id is None
        assert item.status != DocumentStatus.FAILED
        assert item.text_fingerprint != first.text_fingerprint


async def test_duplicate_scope_is_only_same_kb_and_near_match_is_advisory(scoped_api):
    _, db, _ = scoped_api
    words = [f'condition{i}' for i in range(60)]
    text = ' '.join(words)
    source = candidate(214, 10, 'source.pdf', 'e' * 64)
    source.markdown_content = text
    db.add(source)
    await db.commit()
    await claim_extracted_text(db, source, text)

    other_kb = candidate(215, 11, 'foreign.docx', 'f' * 64)
    other_kb.markdown_content = text
    db.add(other_kb)
    await db.commit()
    await claim_extracted_text(db, other_kb, text)
    assert other_kb.duplicate_of_document_id is None

    changed = text.replace('condition30', 'conditionNEW')
    near = candidate(216, 10, 'near.docx', 'g' * 64)
    near.markdown_content = changed
    db.add(near)
    await db.commit()
    await claim_extracted_text(db, near, changed)
    assert similarity(text, changed) >= 0.80
    assert near.near_duplicate_document_id == source.id
    assert near.duplicate_similarity >= 0.80
    assert near.duplicate_of_document_id is None
    assert near.status != DocumentStatus.FAILED


async def test_same_ocr_words_with_unverified_images_is_advisory(scoped_api):
    _, db, _ = scoped_api
    text = 'OCR chart: authorized ceiling 1200 VND, effective 01/09/2026.'
    original = candidate(218, 10, 'scanned-a.pdf', 'j' * 64)
    original.parser_version = 'docling'
    original.image_count = 1
    original.markdown_content = text
    db.add(original)
    await db.commit()
    await claim_extracted_text(db, original, text)

    alternate = candidate(219, 10, 'scanned-b.pdf', 'k' * 64)
    alternate.parser_version = 'docling'
    alternate.image_count = 1
    alternate.markdown_content = text
    db.add(alternate)
    await db.commit()
    await claim_extracted_text(db, alternate, text)
    assert alternate.duplicate_of_document_id is None
    assert alternate.near_duplicate_document_id == original.id
    assert alternate.duplicate_similarity == 1.0
    assert alternate.status != DocumentStatus.FAILED


async def test_restore_rejects_same_extracted_text_with_different_bytes(scoped_api):
    _, db, _ = scoped_api
    old = await db.get(Document, 100)
    old.content_hash = 'h' * 64
    old.markdown_content = 'Do not approve after 31/12/2026.'
    old.parser_version = 'docling'
    await set_family_deleted(db, old)
    await db.commit()
    replacement = candidate(217, 10, 'replacement.docx', 'i' * 64)
    replacement.markdown_content = '**Do not approve** after 31/12/2026.'
    replacement.parser_version = 'docling'
    db.add(replacement)
    await db.commit()

    with pytest.raises(ValueError, match='Duplicate content on restore'):
        await set_family_deleted(db, old, restore=True)
    assert old.deleted_at is not None
