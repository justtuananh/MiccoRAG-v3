"""LightRAG must isolate shared process state without relocating existing files."""
from pathlib import Path

from app.core.config import settings
from app.services import knowledge_graph_service as module


async def test_per_kb_namespace_preserves_legacy_disk_path(monkeypatch, tmp_path):
    import lightrag
    from lightrag.kg import shared_storage

    root = tmp_path / 'data' / 'lightrag'
    for wid in (7, 8):
        directory = root / f'kb_{wid}'
        directory.mkdir(parents=True)
        (directory / 'kv_store_text_chunks.json').write_text(f'{{"fixture": "kb_{wid}"}}')
    monkeypatch.setattr(settings, 'BASE_DIR', tmp_path)
    monkeypatch.setattr(module, 'get_embedding_provider',
                        lambda: type('Embed', (), {'get_dimension': lambda self: 3072})())

    created = []
    class FakeLightRAG:
        def __init__(self, **kwargs):
            created.append(kwargs)

        async def initialize_storages(self):
            pass

    initialized = []
    async def init_status(*, workspace):
        initialized.append(workspace)

    monkeypatch.setattr(lightrag, 'LightRAG', FakeLightRAG)
    monkeypatch.setattr(shared_storage, 'initialize_pipeline_status', init_status)
    first = module.KnowledgeGraphService(7)
    second = module.KnowledgeGraphService(8)
    await first._get_rag()
    await second._get_rag()

    assert [item['workspace'] for item in created] == ['kb_7', 'kb_8']
    assert [Path(item['working_dir']) for item in created] == [root, root]
    assert initialized == ['kb_7', 'kb_8']
    assert (root / 'kb_7' / 'kv_store_text_chunks.json').read_text() == '{"fixture": "kb_7"}'
    assert (root / 'kb_8' / 'kv_store_text_chunks.json').read_text() == '{"fixture": "kb_8"}'
    assert (root / 'kb_7' / '.embedding_dim').read_text() == '3072'
    assert (root / 'kb_8' / '.embedding_dim').read_text() == '3072'
