"""Conservative duplicate detection on extracted document text, scoped to one KB."""
from __future__ import annotations

import hashlib
import re
import unicodedata

from sqlalchemy import select, text

from app.models.document import Document, DocumentStatus


class ExactTextDuplicate(ValueError):
    """The extracted text is already claimed by another document in this KB."""

    def __init__(self):
        super().__init__('Nội dung văn bản đã tồn tại trong kho tri thức')


def canonical_text(raw: str) -> str:
    """Discard layout whitespace/Markdown decoration, retaining factual symbols.

    Punctuation, comparison operators, decimal/date separators, digits, and
    negation words are deliberately preserved. A formatting-only match can be
    missed; a changed business fact must never be declared an exact match.
    """
    value = unicodedata.normalize('NFC', raw or '')
    value = re.sub(r'(?m)^\s{0,3}#{1,6}\s+', '', value)
    # Paired emphasis only: keep literal 2**3 and identifiers such as A__B.
    value = re.sub(r'(?<!\w)\*\*(?=\w)([^*\n]+?)(?<=\w)\*\*(?!\w)', r'\1', value)
    value = re.sub(r'(?<!\w)__(?=\w)([^_\n]+?)(?<=\w)__(?!\w)', r'\1', value)
    return ' '.join(value.split())


def text_fingerprint(raw: str) -> str | None:
    normalized = canonical_text(raw)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest() if normalized else None


def _shingles(value: str, width: int = 5) -> set[tuple[str, ...]]:
    if len(value) > 200_000:
        return set()  # Approximate warnings are optional; exact hashing is full-text.
    tokens = value.split()
    if len(tokens) > 20_000:
        return set()
    if len(tokens) < width:
        return set()
    return {tuple(tokens[i:i + width]) for i in range(len(tokens) - width + 1)}


def similarity(left: str, right: str) -> float:
    a, b = _shingles(canonical_text(left)), _shingles(canonical_text(right))
    return len(a & b) / len(a | b) if a and b else 0.0


def verified_text_only(document: Document) -> bool:
    """Only block on exact text when neither side has unverified media.

    Historical PDF/DOCX rows with no parser marker have unknown image state.
    An extracted scan or chart can share OCR words while its visual facts differ.
    """
    if re.search(r'!\[[^]]*\]\([^)]*\)', document.markdown_content or ''):
        return False
    return (document.image_count or 0) == 0 and (
        document.file_type in {'txt', 'md'} or bool(document.parser_version))


async def claim_extracted_text(db, document: Document, extracted_text: str) -> None:
    """Claim a KB-local fingerprint before indexing; exact duplicates fail closed.

    PostgreSQL serializes the same KB+fingerprint until our commit. Legacy rows
    with stored markdown but no fingerprint are compared lazily, without a bulk
    data rewrite. The approximate check is advisory and capped at 40 rows.
    """
    digest = text_fingerprint(extracted_text)
    if digest is None:
        raise ValueError('Không trích xuất được nội dung văn bản')

    if db.get_bind().dialect.name == 'postgresql':
        lock = int.from_bytes(hashlib.sha256(
            f'text:{document.workspace_id}:{digest}'.encode()).digest()[:8],
            'big', signed=True)
        await db.execute(text('SELECT pg_advisory_xact_lock(:lock)'), {'lock': lock})

    scope = (Document.workspace_id == document.workspace_id,
             Document.id != document.id, Document.deleted_at.is_(None),
             Document.status != DocumentStatus.FAILED)
    exact_matches = list((await db.execute(select(Document).where(
        *scope, Document.text_fingerprint == digest).order_by(Document.id)
    )).scalars().all())
    # Historical records have no fingerprint; their stored extracted text is
    # the only safe basis for a comparison. Do not infer from filenames.
    legacy = (await db.execute(select(Document).where(
        *scope, Document.text_fingerprint.is_(None),
        Document.markdown_content.is_not(None)).order_by(Document.id)
    )).scalars().all()
    exact_matches.extend(other for other in legacy
                         if text_fingerprint(other.markdown_content) == digest)

    document.text_fingerprint = digest
    exact = next((other for other in exact_matches
                  if verified_text_only(document) and verified_text_only(other)), None)
    if exact is not None:
        document.duplicate_of_document_id = exact.id
        document.near_duplicate_document_id = None
        document.duplicate_similarity = 1.0
        document.status = DocumentStatus.FAILED
        document.error_message = str(ExactTextDuplicate())
        await db.commit()  # Release the advisory lock only after the claim is visible.
        raise ExactTextDuplicate()

    document.duplicate_of_document_id = None
    document.near_duplicate_document_id = None
    document.duplicate_similarity = None
    if exact_matches:
        # Text matches, but images/charts or historical media state are not
        # proven equivalent. Warn; do not claim whole-file identity.
        document.near_duplicate_document_id = exact_matches[0].id
        document.duplicate_similarity = 1.0
        await db.commit()
        return
    nearby = (await db.execute(select(Document).where(
        *scope, Document.markdown_content.is_not(None)
    ).order_by(Document.id.desc()).limit(40))).scalars().all()
    best_id, best_score = None, 0.0
    for other in nearby:
        score = similarity(extracted_text, other.markdown_content)
        if score > best_score:
            best_id, best_score = other.id, score
    if best_id is not None and best_score >= 0.80:
        document.near_duplicate_document_id = best_id
        document.duplicate_similarity = round(best_score, 3)
    await db.commit()  # Claim before any image, vector, or KG side effect.
