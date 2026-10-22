"""Re-run knowledge-graph ingest for documents whose KG pass failed.

Re-building the graph does not touch the vector index or the original file, so
the document stays searchable throughout. Use it for documents that were
indexed while KG extraction was failing (e.g. LLM timeouts).

Usage (inside the backend container, from /app/backend)::

    python scripts/kg_reingest.py 26 39 41 16
    python scripts/kg_reingest.py --all-failed
    python scripts/kg_reingest.py --all-failed --dry-run

Exit code is non-zero when at least one document still fails.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.document import Document, DocumentStatus  # noqa: E402
from app.models.knowledge_base import KnowledgeBase  # noqa: E402
from app.services.knowledge_graph_service import KnowledgeGraphService  # noqa: E402


async def _collect_targets(session, ids: list[int], all_failed: bool) -> list[int]:
    if not all_failed:
        return ids
    rows = await session.execute(
        select(Document.id)
        .where(
            Document.status == DocumentStatus.INDEXED,
            Document.deleted_at.is_(None),
            (Document.kg_status.is_(None)) | (Document.kg_status != "processed"),
        )
        .order_by(Document.id)
    )
    return list(rows.scalars().all())


def _entity_types(value) -> list[str] | None:
    if isinstance(value, list):
        return value
    return None


async def run(ids: list[int], all_failed: bool, dry_run: bool) -> int:
    failures = 0
    services: dict[int, KnowledgeGraphService] = {}

    async with AsyncSessionLocal() as session:
        targets = await _collect_targets(session, ids, all_failed)
        if not targets:
            print("Không có tài liệu nào cần chạy lại KG.")
            return 0
        print(f"Sẽ xử lý {len(targets)} tài liệu: {targets}")

        try:
            for document_id in targets:
                doc = (
                    await session.execute(select(Document).where(Document.id == document_id))
                ).scalar_one_or_none()
                if doc is None:
                    print(f"[{document_id}] bỏ qua — không tồn tại")
                    continue
                if doc.deleted_at is not None:
                    print(f"[{document_id}] bỏ qua — đã bị xoá")
                    continue
                if not (doc.markdown_content or "").strip():
                    print(f"[{document_id}] bỏ qua — không có markdown_content")
                    continue

                kb = (
                    await session.execute(
                        select(KnowledgeBase).where(KnowledgeBase.id == doc.workspace_id)
                    )
                ).scalar_one_or_none()

                if dry_run:
                    print(
                        f"[{document_id}] (dry-run) kb={doc.workspace_id} "
                        f"kg_status={doc.kg_status!r} chars={len(doc.markdown_content)}"
                    )
                    continue

                kg = services.get(doc.workspace_id)
                if kg is None:
                    kg = KnowledgeGraphService(
                        workspace_id=doc.workspace_id,
                        kg_language=getattr(kb, "kg_language", None),
                        kg_entity_types=_entity_types(getattr(kb, "kg_entity_types", None)),
                    )
                    services[doc.workspace_id] = kg

                print(f"[{document_id}] đang ingest vào KG (kb={doc.workspace_id}) ...", flush=True)
                try:
                    outcome = await kg.ingest(doc.markdown_content, document_id=document_id)
                    doc.kg_status = outcome
                    doc.kg_error = (
                        None
                        if outcome == "processed"
                        else "KG capacity limit reached; document indexed without graph data"
                    )
                    print(f"[{document_id}] {outcome}", flush=True)
                except Exception as exc:  # noqa: BLE001 — report and continue with next doc
                    failures += 1
                    doc.kg_status = "failed"
                    doc.kg_error = str(exc)[:500]
                    print(f"[{document_id}] FAILED: {exc}", flush=True)
                await session.commit()
        finally:
            for kg in services.values():
                await kg.cleanup()

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="*", type=int, help="Document IDs")
    parser.add_argument("--all-failed", action="store_true", help="All INDEXED docs without processed KG")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would run")
    args = parser.parse_args()

    if not args.documents and not args.all_failed:
        parser.error("provide document IDs or --all-failed")

    return asyncio.run(run(args.documents, args.all_failed, args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
