"""Audit and rebuild one KB's LightRAG files without touching its source directory.

Example (from backend directory with its environment loaded):
  PYTHONPATH=. python harness/ops/rebuild_kg_offline.py --kb-id 35 \
    --source-root /staging/backend/data/lightrag \
    --backup-root /staging/repair-backups \
    --output-root /staging/repair-output-35 --execute --require-graph

The output is a separate BASE_DIR tree, never installed automatically. A service
restart and manual, backed-up swap are required before using it for any KB.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sys
import uuid
from datetime import date
from pathlib import Path


def fingerprint_tree(folder: Path) -> dict[str, str]:
    """Hash all regular files; reject symlinks and unusual entries."""
    result = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise ValueError('Unsafe source entry')
        if path.is_file():
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def source_ids(raw: str) -> list[str]:
    return [part.strip() for part in (raw or '').replace('<SEP>', ',').split(',') if part.strip()]


def validate_rebuild(kb_dir: Path, allowed: set[int], require_graph: bool) -> dict:
    import networkx as nx

    def read(name):
        path = kb_dir / name
        return json.loads(path.read_text()) if path.exists() else {}

    full = read('kv_store_full_docs.json')
    chunks = read('kv_store_text_chunks.json')
    statuses = read('kv_store_doc_status.json')
    allowed_text = {str(item) for item in allowed}
    if set(full) != allowed_text or set(statuses) != allowed_text:
        raise ValueError('Rebuilt full-doc/status IDs differ from DB allowlist')
    if not chunks or any(str(row.get('full_doc_id')) not in allowed_text for row in chunks.values()):
        raise ValueError('Rebuilt chunks are empty or contain a foreign document')
    graph_file = kb_dir / 'graph_chunk_entity_relation.graphml'
    if not graph_file.exists():
        raise ValueError('Rebuilt graph file missing')
    graph = nx.read_graphml(graph_file)
    if require_graph and (not graph.nodes or not graph.edges):
        raise ValueError('Rebuilt graph is empty')
    refs = []
    for _, attrs in graph.nodes(data=True):
        refs.extend(source_ids(attrs.get('source_id', '')))
    for _, _, attrs in graph.edges(data=True):
        refs.extend(source_ids(attrs.get('source_id', '')))
    if graph.nodes and (not refs or not set(refs) <= set(chunks)):
        raise ValueError('Rebuilt graph has missing or foreign chunk provenance')
    return {'document_ids': sorted(allowed), 'full_docs': len(full),
            'chunks': len(chunks), 'nodes': len(graph.nodes), 'edges': len(graph.edges),
            'graph_source_ids_valid': True}


async def run(args) -> dict:
    # Import after the caller has supplied the isolated backend environment.
    from sqlalchemy import text
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.services.knowledge_graph_service import KnowledgeGraphService

    source_root = args.source_root.resolve()
    source = source_root / f'kb_{args.kb_id}'
    backup_root = args.backup_root.resolve()
    output = args.output_root.resolve()
    if not source.is_dir() or source.is_symlink():
        raise ValueError('Source KB directory missing or unsafe')
    if args.kb_id < 1:
        raise ValueError('Invalid KB ID')
    if (output == source or output.is_relative_to(source_root) or
            source.is_relative_to(output) or backup_root == source_root or
            backup_root.is_relative_to(source_root)):
        raise ValueError('Backup/output must be outside the source tree')
    if output.exists() and not args.verify_only:
        raise FileExistsError('Output already exists; no overwrite')
    async with AsyncSessionLocal() as db:
        rows = await db.execute(text("""
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name IN ('documents', 'knowledge_bases')
        """))
        columns = {}
        for table, column in rows:
            columns.setdefault(table, set()).add(column)
        required = {'id', 'workspace_id', 'status', 'approval_status', 'markdown_content'}
        if not required <= columns.get('documents', set()) or 'id' not in columns.get('knowledge_bases', set()):
            raise ValueError('Source database is missing required document/KB columns')
        kb_deleted = 'deleted_at' if 'deleted_at' in columns['knowledge_bases'] else 'NULL AS deleted_at'
        kb = (await db.execute(text(f'SELECT id, {kb_deleted} FROM knowledge_bases WHERE id=:id'),
                               {'id': args.kb_id})).mappings().first()
        if kb is None or kb['deleted_at'] is not None:
            raise ValueError('KB missing or deleted')
        optional = [
            name if name in columns['documents'] else f'NULL AS {name}'
            for name in ('deleted_at', 'effective_from', 'effective_until')
        ]
        query = ("SELECT id, markdown_content, " + ', '.join(optional) +
                 " FROM documents WHERE workspace_id=:id "
                 "AND lower(status::text)='indexed' AND approval_status='approved'")
        docs = list((await db.execute(text(query), {'id': args.kb_id})).mappings().all())
    today = date.today()
    allowed = {
        doc['id'] for doc in docs
        if doc['deleted_at'] is None
        and (doc['effective_from'] is None and args.include_undated or
             doc['effective_from'] is not None and doc['effective_from'] <= today)
        and (doc['effective_until'] is None or doc['effective_until'] >= today)
    }
    if not allowed and docs:
        raise ValueError('KB has approved indexed documents but none are eligible; refusing to clear graph')
    if not allowed and args.require_graph:
        raise ValueError('Cannot require non-empty graph for verified-empty KB')
    full_path = source / 'kv_store_full_docs.json'
    full_docs = json.loads(full_path.read_text()) if full_path.exists() else {}
    if not isinstance(full_docs, dict):
        raise ValueError('Invalid source full-doc storage')
    payloads = {}
    fallback_ids = []
    undated_ids = []
    for doc in docs:
        did = doc['id']
        if did not in allowed:
            continue
        if doc['effective_from'] is None:
            undated_ids.append(did)
        markdown = doc['markdown_content']
        if not markdown or not markdown.strip():
            raise ValueError(f'No verified DB markdown for allowed document {did}')
        content = full_docs.get(str(did), {}).get('content')
        if not isinstance(content, str) or content != markdown:
            if not args.allow_db_fallback:
                raise ValueError(f'Missing or mismatched persisted content for allowed document {did}')
            fallback_ids.append(did)
        # Rebuild only from the database row owned by this KB. Old graph facts,
        # including mixed entity descriptions, are never copied into output.
        payloads[did] = markdown
    before_hashes = fingerprint_tree(source)
    markdown_hashes = {
        str(did): hashlib.sha256(payloads[did].encode('utf-8')).hexdigest()
        for did in sorted(payloads)
    }
    report = {'kb_id': args.kb_id, 'source_document_ids': sorted(allowed),
              'db_markdown_fallback_ids': sorted(fallback_ids),
              'undated_document_ids': sorted(undated_ids),
              'serving_eligible': not undated_ids,
              'verified_empty': not bool(allowed),
              'source_markdown_sha256': markdown_hashes,
              'source_files_sha256': before_hashes,
              'source_file_count': len(before_hashes), 'execute': args.execute,
              'source_unchanged': True}
    if args.verify_only:
        manifest_path = output / 'repair-manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for key in ('kb_id', 'source_document_ids', 'source_markdown_sha256',
                    'source_files_sha256', 'verified_empty'):
            if manifest.get(key) != report[key]:
                raise ValueError(f'Rebuild manifest stale or mismatched: {key}')
        rebuilt = output / 'data/lightrag' / f'kb_{args.kb_id}'
        if fingerprint_tree(rebuilt) != manifest['rebuilt_files_sha256']:
            raise ValueError('Rebuilt files changed after preparation')
        return {'kb_id': args.kb_id, 'verified': True,
                'source_document_ids': sorted(allowed),
                'serving_eligible': not undated_ids}
    if not args.execute:
        return report

    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / f'kb_{args.kb_id}_{uuid.uuid4().hex[:12]}'
    shutil.copytree(source, backup, symlinks=False)
    if fingerprint_tree(source) != before_hashes or fingerprint_tree(backup) != before_hashes:
        raise RuntimeError('Source changed during snapshot or backup hash mismatch')
    temporary = output.parent / f'.{output.name}.building-{uuid.uuid4().hex[:12]}'
    temporary.mkdir(parents=True)
    original_base = settings.BASE_DIR
    try:
        settings.BASE_DIR = temporary
        rebuilt = temporary / 'data/lightrag' / f'kb_{args.kb_id}'
        if payloads:
            kg = KnowledgeGraphService(args.kb_id)
            try:
                for did in sorted(payloads):
                    await kg.ingest(payloads[did], did)
            finally:
                await kg.cleanup()
            stats = validate_rebuild(rebuilt, allowed, args.require_graph)
        else:
            rebuilt.mkdir(parents=True)
            stats = {'document_ids': [], 'full_docs': 0, 'chunks': 0,
                     'nodes': 0, 'edges': 0, 'graph_source_ids_valid': True}
        if fingerprint_tree(source) != before_hashes:
            raise RuntimeError('Source changed while rebuilding; do not install output')
        report.update({'backup': str(backup), 'output': str(output),
                       'backup_hash_verified': True, 'rebuilt': stats,
                       'rebuilt_files_sha256': fingerprint_tree(rebuilt)})
        (temporary / 'repair-manifest.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        )
        os.replace(temporary, output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    finally:
        settings.BASE_DIR = original_base
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kb-id', type=int, required=True)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--backup-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Build separate output; never swaps source')
    parser.add_argument('--verify-only', action='store_true',
                        help='Recheck source DB markdown, old KG and prepared copy hashes; no writes')
    parser.add_argument('--require-graph', action='store_true')
    parser.add_argument('--allow-db-fallback', action='store_true',
                        help='Use same-KB DB markdown when polluted KG lacks an allowed document')
    parser.add_argument('--include-undated', action='store_true',
                        help='Build an OFFLINE copy from approved undated DB markdown; output cannot serve until source-owned dates are verified')
    parser.add_argument('--runtime-env', type=Path, help='Private JSON env file for isolated staging')
    args = parser.parse_args()
    try:
        if args.runtime_env:
            os.environ.update(json.loads(args.runtime_env.read_text()))
        print(json.dumps(asyncio.run(run(args)), ensure_ascii=False, indent=2))
    except Exception as error:
        print(f'Offline rebuild failed: {type(error).__name__}: {error}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
