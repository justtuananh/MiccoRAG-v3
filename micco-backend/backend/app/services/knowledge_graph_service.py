"""
Knowledge Graph Service
========================

Per-workspace Knowledge Graph using LightRAG with configurable LLM + embeddings.
File-based storage (NetworkX graph + NanoVectorDB) — no extra Docker services.

Usage:
    kg = KnowledgeGraphService(workspace_id=1)
    await kg.ingest("markdown text from document...")
    result = await kg.query("What are the key themes?", mode="hybrid")
    await kg.cleanup()
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import resource
import shutil
import weakref
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings
from app.services.llm import get_embedding_provider, get_llm_provider
from app.services.llm.types import LLMMessage

logger = logging.getLogger(__name__)
_INGEST_LOCKS: weakref.WeakValueDictionary[int, asyncio.Lock] = weakref.WeakValueDictionary()
_ACTIVE_KB_NAMESPACES: set[int] = set()
_INIT_LOCK = asyncio.Lock()


class KGCapacityExceeded(RuntimeError):
    """The graph is unavailable because its configured capacity was reached."""


def _ingest_lock(workspace_id: int) -> asyncio.Lock:
    lock = _INGEST_LOCKS.get(workspace_id)
    if lock is None:
        lock = asyncio.Lock()
        _INGEST_LOCKS[workspace_id] = lock
    return lock


def _process_rss_bytes() -> int:
    """Current Linux resident set; high-water fallback if /proc is unavailable."""
    try:
        pages = int(Path('/proc/self/statm').read_text().split()[1])
        return pages * os.sysconf('SC_PAGE_SIZE')
    except (OSError, ValueError, IndexError):
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


# ---------------------------------------------------------------------------
# Provider-based adapters for LightRAG
# ---------------------------------------------------------------------------

async def _kg_llm_complete(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[list] = None,
    keyword_extraction: bool = False,
    **kwargs,
) -> str:
    """
    LightRAG-compatible LLM function using the configured provider.

    Notes:
    - Thinking is explicitly disabled: LightRAG expects strict delimiter-based
      output ("<|>"). Thinking adds overhead and can interfere with the format,
      causing the "Complete delimiter can not be found" warnings.
    - max_tokens is set to NEXUSRAG_KG_EXTRACT_MAX_TOKENS (default 16384) to prevent
      truncation mid-output. LightRAG's parser silently drops ALL entities/relations
      from a chunk if the response is cut off before the "<|COMPLETE|>" marker, so
      truncation here is a primary cause of an empty-looking knowledge graph even
      though the document was indexed successfully.
    """
    provider = get_llm_provider()

    messages: list[LLMMessage] = []

    if system_prompt:
        messages.append(LLMMessage(role="system", content=system_prompt))

    if history_messages:
        for msg in history_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append(LLMMessage(role=role, content=content))

    messages.append(LLMMessage(role="user", content=prompt))

    # think=False: KG extraction needs strict structured output, not chain-of-thought.
    max_tokens = settings.NEXUSRAG_KG_EXTRACT_MAX_TOKENS
    result = await provider.acomplete(
        messages, temperature=0.0, max_tokens=max_tokens, think=False,
    )
    # acomplete can return LLMResult if thinking=True elsewhere — extract text
    text = result.content if hasattr(result, "content") else (result or "")

    # Detect likely truncation: LightRAG expects the response to end with the
    # "<|COMPLETE|>" marker (or be empty when a chunk has no entities). A response
    # that has content but no completion marker almost certainly hit max_tokens and
    # will be silently discarded in full by LightRAG's parser — log it loudly so this
    # failure mode is visible instead of manifesting as "empty knowledge graph".
    if text and "<|COMPLETE|>" not in text:
        logger.warning(
            "KG extraction response missing '<|COMPLETE|>' marker "
            f"(len={len(text)} chars, max_tokens={max_tokens}) — likely truncated by "
            "the LLM output limit. LightRAG will discard this chunk's entities/"
            "relations entirely. Consider raising NEXUSRAG_KG_EXTRACT_MAX_TOKENS."
        )

    return text


async def _kg_embed(texts: list[str]) -> np.ndarray:
    """LightRAG-compatible embedding function using the configured provider."""
    provider = get_embedding_provider()
    return await provider.embed(texts)


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class KnowledgeGraphService:
    """
    Per-workspace Knowledge Graph service backed by LightRAG.

    Storage: file-based (NetworkX for graph, NanoVectorDB for vectors).
    Each knowledge base gets its own working directory.
    """

    def __init__(
        self,
        workspace_id: int,
        kg_language: str | None = None,
        kg_entity_types: list[str] | None = None,
    ):
        self.workspace_id = workspace_id
        self.working_dir = str(
            settings.BASE_DIR / "data" / "lightrag" / f"kb_{workspace_id}"
        )
        # Per-workspace overrides (fallback to global settings)
        self.kg_language = kg_language or settings.NEXUSRAG_KG_LANGUAGE
        self.kg_entity_types = kg_entity_types or settings.NEXUSRAG_KG_ENTITY_TYPES
        self._rag = None
        self._initialized = False
        self._chunk_to_doc_map: dict[str, str] | None = None

    async def _get_chunk_to_doc_map(self) -> dict[str, str]:
        """Load chunk-to-document mapping from LightRAG storage."""
        map_data = self._chunk_to_doc_map
        if map_data is not None:
            return map_data
        
        mapping: dict[str, str] = {}
        # Path to kv_store_text_chunks.json
        storage_path = Path(self.working_dir) / "kv_store_text_chunks.json"
        
        if storage_path.exists():
            try:
                import json
                with open(storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for chunk_id, chunk_info in data.items():
                        # In LightRAG, chunk_info usually has 'full_doc_id' 
                        # if ingested with ids parameter.
                        doc_id = chunk_info.get("full_doc_id")
                        if doc_id:
                            mapping[chunk_id] = str(doc_id)
            except Exception as e:
                logger.error(f"Failed to load chunk-to-doc mapping: {e}")
        
        self._chunk_to_doc_map = mapping
        return mapping

    @staticmethod
    def _source_allowed(source_id: str, allowed_ids: set[str], chunk_map: dict[str, str]) -> bool:
        """A merged KG fact is safe only when every source is known and readable."""
        sources = [part.strip() for part in (source_id or "").replace("<SEP>", ",").split(",") if part.strip()]
        if not sources:
            return False
        for source in sources:
            doc_id = chunk_map.get(source)
            if doc_id is None:
                alternate = source[6:] if source.startswith("chunk-") else f"chunk-{source}"
                doc_id = chunk_map.get(alternate)
            if doc_id not in allowed_ids:
                return False
        return True

    async def _get_rag(self):
        """Lazy-initialize LightRAG instance."""
        if self._rag is not None and self._initialized:
            return self._rag
        async with _INIT_LOCK:
            return await self._get_rag_locked()

    async def _get_rag_locked(self):
        if self._rag is not None and self._initialized:
            return self._rag
        # LightRAG retains process-global workspace data after finalize_storages;
        # there is no safe per-workspace eviction while another request may use it.
        # Bound how many different namespaces this worker may load. Restarting a
        # worker after a maintenance window releases the global cache.
        if (self.workspace_id not in _ACTIVE_KB_NAMESPACES and
                len(_ACTIVE_KB_NAMESPACES) >= settings.NEXUSRAG_KG_MAX_ACTIVE_KBS_PER_PROCESS):
            raise KGCapacityExceeded("KG active workspace limit reached in this process")
        if (self.workspace_id not in _ACTIVE_KB_NAMESPACES and
                _process_rss_bytes() + settings.NEXUSRAG_KG_INIT_RESERVE_BYTES >=
                settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES):
            raise KGCapacityExceeded("KG worker RSS limit reached before workspace load")

        from lightrag import LightRAG
        from lightrag.utils import wrap_embedding_func_with_attrs
        from lightrag.kg.shared_storage import initialize_pipeline_status

        os.makedirs(self.working_dir, exist_ok=True)

        # Dynamic embedding dimension from the configured provider
        emb_provider = get_embedding_provider()
        embedding_dim = emb_provider.get_dimension()

        # Detect dimension mismatch when switching providers
        dim_marker = Path(self.working_dir) / ".embedding_dim"
        if dim_marker.exists():
            prev_dim = int(dim_marker.read_text().strip())
            if prev_dim != embedding_dim:
                logger.warning(
                    f"Embedding dimension changed ({prev_dim} → {embedding_dim}) "
                    f"for workspace {self.workspace_id}. Clearing KG data for rebuild."
                )
                shutil.rmtree(self.working_dir)
                os.makedirs(self.working_dir, exist_ok=True)
        dim_marker.write_text(str(embedding_dim))

        @wrap_embedding_func_with_attrs(embedding_dim=embedding_dim, max_token_size=8192)
        async def embedding_func(texts: list[str]) -> np.ndarray:
            return await _kg_embed(texts)

        # LightRAG's in-process shared stores are keyed by workspace, not by
        # working_dir. Use its workspace namespace while keeping the existing
        # on-disk data/lightrag/kb_<id>/ paths unchanged.
        workspace_namespace = f"kb_{self.workspace_id}"
        self._rag = LightRAG(
            working_dir=str(Path(self.working_dir).parent),
            workspace=workspace_namespace,
            llm_model_func=_kg_llm_complete,
            embedding_func=embedding_func,
            chunk_token_size=settings.NEXUSRAG_KG_CHUNK_TOKEN_SIZE,
            enable_llm_cache=True,
            kv_storage="JsonKVStorage",
            vector_storage="NanoVectorDBStorage",
            graph_storage="NetworkXStorage",
            doc_status_storage="JsonDocStatusStorage",
            # --- Performance tuning ---
            # Disable gleaning (re-extraction retry): saves 1 extra LLM call per chunk.
            # Gleaning improves recall slightly but doubles processing time.
            entity_extract_max_gleaning=0,
            # Allow up to 4 concurrent LLM calls (entity extraction per chunk).
            # Gemini API allows high concurrency; adjust down if rate-limited.
            llm_model_max_async=4,
            # --- End performance tuning ---
            addon_params={
                "language": self.kg_language,
                "entity_types": self.kg_entity_types,
            },
        )

        await self._rag.initialize_storages()
        await initialize_pipeline_status(workspace=workspace_namespace)
        self._initialized = True
        _ACTIVE_KB_NAMESPACES.add(self.workspace_id)

        logger.info(
            f"LightRAG initialized for workspace {self.workspace_id} "
            f"(embedding_dim={embedding_dim})"
        )
        return self._rag

    def _disk_bytes(self) -> int:
        """Count this KB's persisted storage, including vector and cache files."""
        total = 0
        for path in Path(self.working_dir).rglob("*"):
            if path.is_symlink():
                raise ValueError("Unsafe symlink in KG storage")
            if path.is_file():
                total += path.stat().st_size
        return total

    async def ingest(self, markdown_content: str, document_id: int | None = None) -> None:
        """
        Ingest markdown content into the knowledge graph.
        LightRAG extracts entities and relationships automatically.
        """
        async with _ingest_lock(self.workspace_id):
            await self._ingest_locked(markdown_content, document_id)

    async def _ingest_locked(self, markdown_content: str, document_id: int | None) -> None:
        if not markdown_content.strip():
            logger.warning(f"Empty content for workspace {self.workspace_id}, skipping KG ingest")
            return
        if document_id is None:
            raise ValueError("KG capacity control requires a document ID")

        rag = await self._get_rag()
        # LightRAG's JSON full-doc file is durable after each completed ingest.
        # Fail closed if it cannot be read rather than bypassing the quota.
        full_docs_path = Path(self.working_dir) / "kv_store_full_docs.json"
        full_docs = json.loads(full_docs_path.read_text()) if full_docs_path.exists() else {}
        if not isinstance(full_docs, dict):
            raise ValueError("Invalid KG full-doc storage")
        # An already ingested document must not be deleted by a quota rollback.
        # LightRAG treats repeated IDs as duplicates, so there is no work to do.
        if await rag.full_docs.get_by_id(str(document_id)) is not None:
            logger.info("KG document %s already present in workspace %s", document_id, self.workspace_id)
            return
        doc_count = len(full_docs)
        node_count = len(await rag.chunk_entity_relation_graph.get_all_nodes())
        edge_count = len(await rag.chunk_entity_relation_graph.get_all_edges())
        disk_bytes = self._disk_bytes()
        rss_bytes = _process_rss_bytes()
        max_docs = settings.NEXUSRAG_KG_MAX_DOCUMENTS_PER_KB
        max_nodes = settings.NEXUSRAG_KG_MAX_NODES_PER_KB
        max_edges = settings.NEXUSRAG_KG_MAX_EDGES_PER_KB
        max_bytes = settings.NEXUSRAG_KG_MAX_DISK_BYTES_PER_KB
        if (doc_count >= max_docs or node_count >= max_nodes or
                edge_count >= max_edges or disk_bytes >= max_bytes or
                rss_bytes >= settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES):
            logger.warning(
                "KG capacity reached for workspace %s: docs=%s/%s nodes=%s/%s "
                "edges=%s/%s disk=%s/%s rss=%s/%s; skipping document %s",
                self.workspace_id, doc_count, max_docs, node_count, max_nodes,
                edge_count, max_edges, disk_bytes, max_bytes, rss_bytes,
                settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES, document_id,
            )
            return
        if (doc_count / max_docs >= settings.NEXUSRAG_KG_CAPACITY_WARN_RATIO or
                node_count / max_nodes >= settings.NEXUSRAG_KG_CAPACITY_WARN_RATIO or
                edge_count / max_edges >= settings.NEXUSRAG_KG_CAPACITY_WARN_RATIO or
                disk_bytes / max_bytes >= settings.NEXUSRAG_KG_CAPACITY_WARN_RATIO or
                rss_bytes / settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES >=
                settings.NEXUSRAG_KG_CAPACITY_WARN_RATIO):
            logger.warning(
                "KG capacity nearing limit for workspace %s: docs=%s/%s nodes=%s/%s "
                "edges=%s/%s disk=%s/%s rss=%s/%s",
                self.workspace_id, doc_count, max_docs, node_count, max_nodes,
                edge_count, max_edges, disk_bytes, max_bytes, rss_bytes,
                settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES,
            )

        try:
            await rag.ainsert(markdown_content, ids=[str(document_id)])
            self._chunk_to_doc_map = None
            after_nodes = len(await rag.chunk_entity_relation_graph.get_all_nodes())
            after_edges = len(await rag.chunk_entity_relation_graph.get_all_edges())
            after_bytes = self._disk_bytes()
            after_docs = json.loads(full_docs_path.read_text()) if full_docs_path.exists() else {}
            if not isinstance(after_docs, dict):
                raise ValueError("Invalid KG full-doc storage after ingestion")
            if (after_nodes > max_nodes or after_edges > max_edges or
                    after_bytes > max_bytes or len(after_docs) > max_docs or
                    _process_rss_bytes() > settings.NEXUSRAG_KG_MAX_PROCESS_RSS_BYTES):
                await rag.adelete_by_doc_id(str(document_id))
                self._chunk_to_doc_map = None
                raise RuntimeError(
                    f"KG capacity exceeded for workspace {self.workspace_id}; "
                    f"rolled back document {document_id}"
                )
            logger.info(
                f"KG ingested {len(markdown_content)} chars for doc {document_id} in workspace {self.workspace_id}"
            )

            # Check if entities were actually extracted
            try:
                if not after_nodes:
                    model = (
                        settings.OLLAMA_MODEL
                        if settings.LLM_PROVIDER.lower() == "ollama"
                        else settings.LLM_MODEL_FAST
                    )
                    logger.warning(
                        f"KG extraction produced 0 entities for workspace {self.workspace_id}. "
                        f"Model '{model}' may not support LightRAG's entity extraction format. "
                        f"Consider using a larger model (e.g. qwen3:14b, gemma3:12b) for KG."
                    )
            except Exception:
                pass

        except Exception as e:
            logger.error(f"KG ingest failed for workspace {self.workspace_id}: {e}")
            raise

    async def query(
        self,
        question: str,
        mode: str = "hybrid",
        top_k: int = 10,
        allowed_doc_ids: list[int] | None = None,
    ) -> str:
        """
        Query the knowledge graph.

        Args:
            question: Natural language question
            mode: Query mode — "naive", "local", "global", "hybrid"
            top_k: Number of results

        Returns:
            LightRAG response text with KG-augmented answer
        """
        if allowed_doc_ids is not None:
            # LightRAG's generated answer has no document provenance. A scoped
            # request can only use factual graph context that we can verify.
            return await self.get_relevant_context(question, allowed_doc_ids=allowed_doc_ids)

        from lightrag import QueryParam

        rag = await self._get_rag()

        try:
            result = await asyncio.wait_for(
                rag.aquery(
                    question,
                    param=QueryParam(mode=mode, top_k=top_k),
                ),
                timeout=settings.NEXUSRAG_KG_QUERY_TIMEOUT,
            )
            return result or ""
        except asyncio.TimeoutError:
            logger.warning(
                f"KG query timed out after {settings.NEXUSRAG_KG_QUERY_TIMEOUT}s "
                f"for workspace {self.workspace_id}"
            )
            return ""
        except Exception as e:
            logger.error(f"KG query failed for workspace {self.workspace_id}: {e}")
            return ""

    async def cleanup(self) -> None:
        """Finalize storages on shutdown."""
        if self._rag:
            try:
                await self._rag.finalize_storages()
                logger.info(f"KG storages finalized for workspace {self.workspace_id}")
            except Exception as e:
                logger.warning(f"KG cleanup failed for workspace {self.workspace_id}: {e}")
            self._rag = None
            self._initialized = False

    async def delete_document(self, document_id: int) -> None:
        """Delete a document's node and edge data from the Knowledge Graph."""
        rag = await self._get_rag()
        try:
            await rag.adelete_by_doc_id(str(document_id))
            self._chunk_to_doc_map = None
            logger.info(f"Deleted document {document_id} from Knowledge Graph")
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from KG: {e}")

    def delete_project_data(self) -> None:
        """Delete all KG data for this knowledge base."""
        path = Path(self.working_dir)
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Deleted KG data for workspace {self.workspace_id}")
        self._rag = None
        self._initialized = False

    # ------------------------------------------------------------------
    # Knowledge Graph exploration (Phase 9)
    # ------------------------------------------------------------------

    async def get_entities(
        self,
        search: str | None = None,
        entity_type: str | None = None,
        limit: int = 200,
        offset: int = 0,
        allowed_doc_ids: list[int] | None = None,
    ) -> list[dict]:
        """
        List all entities in the knowledge graph.
        
        If allowed_doc_ids is provided, filters entities belonging to those documents.
        """
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph

        try:
            all_nodes = await storage.get_all_nodes()
        except Exception as e:
            logger.error(f"Failed to get KG nodes for workspace {self.workspace_id}: {e}")
            return []

        # Build allowed IDs set for fast lookup
        allowed_ids_str = set(str(id) for id in allowed_doc_ids) if allowed_doc_ids is not None else None
        chunk_map = await self._get_chunk_to_doc_map() if allowed_ids_str is not None else None

        entities = []
        for node in all_nodes:
            node_id = node.get("id", "")
            etype = node.get("entity_type", "Unknown")
            desc = node.get("description", "")
            source_id = node.get("source_id", "") # e.g. "chunk-ID" or "chunk-ID1,chunk-ID2"
            
            # Filtering by allowed document IDs
            if allowed_ids_str is not None:
                if not self._source_allowed(source_id, allowed_ids_str, chunk_map):
                    continue

            # Existing filters
            if entity_type and etype.lower() != entity_type.lower():
                continue
            if search and search.lower() not in node_id.lower():
                continue

            # Get degree (number of relationships)
            if allowed_ids_str is not None:
                degree = 0  # storage degree includes edges from unreadable documents
            else:
                try:
                    degree = await storage.node_degree(node_id)
                except Exception:
                    degree = 0

            entities.append({
                "name": node_id,
                "entity_type": etype,
                "description": desc,
                "degree": degree,
            })

        # Sort by degree descending
        entities.sort(key=lambda e: e["degree"], reverse=True)

        offset = max(0, offset)
        limit = max(1, min(limit, settings.NEXUSRAG_KG_ENTITY_PAGE_MAX))
        return entities[offset:offset + limit]

    async def get_relationships(
        self,
        entity_name: str | None = None,
        limit: int = 500,
        allowed_doc_ids: list[int] | None = None,
    ) -> list[dict]:
        """
        List relationships in the knowledge graph.

        If allowed_doc_ids is provided, filters relationships belonging to those documents.
        """
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph

        try:
            all_edges = await storage.get_all_edges()
        except Exception as e:
            logger.error(f"Failed to get KG edges for workspace {self.workspace_id}: {e}")
            return []

        # Build allowed IDs set for fast lookup
        allowed_ids_str = set(str(id) for id in allowed_doc_ids) if allowed_doc_ids is not None else None
        chunk_map = await self._get_chunk_to_doc_map() if allowed_ids_str is not None else None
        allowed_node_names = None
        if allowed_ids_str is not None:
            try:
                nodes = await storage.get_all_nodes()
            except Exception as e:
                logger.error(f"Failed to verify KG edge endpoints for workspace {self.workspace_id}: {e}")
                return []
            allowed_node_names = {
                node.get("id") for node in nodes
                if self._source_allowed(node.get("source_id", ""), allowed_ids_str, chunk_map)
            }

        relationships = []
        for edge in all_edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            source_id = edge.get("source_id", "")
            
            # Filtering by allowed document IDs
            if allowed_ids_str is not None:
                if not self._source_allowed(source_id, allowed_ids_str, chunk_map):
                    continue
                if src not in allowed_node_names or tgt not in allowed_node_names:
                    continue

            if entity_name:
                if entity_name.lower() not in (src.lower(), tgt.lower()):
                    continue

            relationships.append({
                "source": src,
                "target": tgt,
                "description": edge.get("description", ""),
                "keywords": edge.get("keywords", ""),
                "weight": float(edge.get("weight", 1.0)),
            })

        limit = max(1, min(limit, settings.NEXUSRAG_KG_RELATIONSHIP_PAGE_MAX))
        return relationships[:limit]

    async def get_graph_data(
        self,
        center_entity: str | None = None,
        max_depth: int = 3,
        max_nodes: int = 150,
        allowed_doc_ids: list[int] | None = None,
    ) -> dict:
        """
        Export graph data for frontend visualization.
        """
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph
        max_depth = max(1, min(max_depth, settings.NEXUSRAG_KG_GRAPH_MAX_DEPTH))
        max_nodes = max(1, min(max_nodes, settings.NEXUSRAG_KG_GRAPH_MAX_NODES))

        try:
            label = center_entity if center_entity else "*"
            kg = await storage.get_knowledge_graph(
                node_label=label,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
        except Exception as e:
            logger.error(f"Failed to get KG graph for workspace {self.workspace_id}: {e}")
            return {"nodes": [], "edges": [], "is_truncated": False}

        # Filter nodes and edges based on allowed_doc_ids 
        allowed_ids_str = set(str(id) for id in allowed_doc_ids) if allowed_doc_ids is not None else None
        chunk_map = await self._get_chunk_to_doc_map() if allowed_ids_str is not None else None
        
        nodes = []
        allowed_node_ids = set()
        nodes_truncated = False
        for n in kg.nodes:
            # Type hinting for linter
            node_id = getattr(n, "id", None)
            if node_id is None:
                continue
                
            props = getattr(n, "properties", {})
            # Filtering by allowed domain if requested
            if allowed_ids_str is not None:
                source_id = props.get("source_id", "")
                if not self._source_allowed(source_id, allowed_ids_str, chunk_map):
                    continue
            if len(nodes) >= max_nodes:
                nodes_truncated = True
                break
            
            allowed_node_ids.add(node_id)
            if allowed_ids_str is not None:
                degree = 0
            else:
                try:
                    degree = await storage.node_degree(node_id)
                except Exception:
                    degree = 0
            nodes.append({
                "id": node_id,
                "label": node_id,
                "entity_type": props.get("entity_type", "Unknown"),
                "degree": degree,
            })

        edges = []
        edges_truncated = False
        for e in kg.edges:
            source = getattr(e, "source", None)
            target = getattr(e, "target", None)
            
            # Only include edges where both source and target are allowed (and the edge itself is from allowed doc)
            if source not in allowed_node_ids or target not in allowed_node_ids:
                continue
                
            props = getattr(e, "properties", {})
            if allowed_ids_str is not None:
                source_id = props.get("source_id", "")
                if not self._source_allowed(source_id, allowed_ids_str, chunk_map):
                    continue
            if len(edges) >= settings.NEXUSRAG_KG_GRAPH_MAX_EDGES:
                edges_truncated = True
                break

            edges.append({
                "source": source,
                "target": target,
                "label": props.get("description", "")[:80],
                "weight": float(props.get("weight", 1.0)),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "is_truncated": bool(getattr(kg, "is_truncated", False) or
                                 nodes_truncated or edges_truncated),
        }

    async def get_relevant_context(
        self,
        question: str,
        max_entities: int = 20,
        max_relationships: int = 30,
        allowed_doc_ids: list[int] | None = None,
    ) -> str:
        """
        Build RAG context from raw KG data (no LLM generation).

        Instead of calling LightRAG's aquery() which uses LLM to generate
        a narrative (and can hallucinate), this method:
          1. Tokenizes the question into keywords
          2. Finds entities whose names match any keyword
          3. Gets relationships connecting those entities
          4. Formats everything as structured factual text

        Returns:
            Structured string of entities + relationships, or "" if nothing found.
        """
        if allowed_doc_ids == []:
            return ""
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph

        try:
            all_nodes = await storage.get_all_nodes()
            all_edges = await storage.get_all_edges()
        except Exception as e:
            logger.error(f"Failed to get raw KG data for workspace {self.workspace_id}: {e}")
            return ""

        if allowed_doc_ids is not None:
            allowed = {str(doc_id) for doc_id in allowed_doc_ids}
            chunk_map = await self._get_chunk_to_doc_map()
            all_nodes = [node for node in all_nodes if self._source_allowed(node.get("source_id", ""), allowed, chunk_map)]
            allowed_names = {node.get("id") for node in all_nodes}
            all_edges = [edge for edge in all_edges if
                         edge.get("source") in allowed_names and edge.get("target") in allowed_names
                         and self._source_allowed(edge.get("source_id", ""), allowed, chunk_map)]

        if not all_nodes:
            return ""

        # -- 1. Extract keywords from question --
        # Simple but effective: split, lowercase, filter short words
        raw_tokens = question.lower().split()
        # Also handle hyphenated/versioned tokens like "deepseek-v3.2"
        keywords = set()
        for token in raw_tokens:
            # Remove punctuation at edges
            cleaned = token.strip(".,?!:;\"'()[]{}").lower()
            if len(cleaned) >= 2:
                keywords.add(cleaned)

        if not keywords:
            return ""

        # -- 2. Find matching entities --
        matched_entity_names: set[str] = set()
        entity_info: dict[str, dict] = {}  # name → {type, description}

        for node in all_nodes:
            node_id = node.get("id", "")
            node_lower = node_id.lower()

            # Check if any keyword is a substring of entity name OR vice versa
            matched = False
            for kw in keywords:
                if kw in node_lower or node_lower in kw:
                    matched = True
                    break
                # Also check multi-word keywords (e.g., "deepseek" matches "DEEPSEEK-V3.2")
                for part in node_lower.split("-"):
                    if kw in part or part in kw:
                        matched = True
                        break
                if matched:
                    break

            if matched:
                matched_entity_names.add(node_id)
                entity_info[node_id] = {
                    "entity_type": node.get("entity_type", "Unknown"),
                    "description": node.get("description", ""),
                }

        if not matched_entity_names and len(all_nodes) <= 50:
            # Small graph: include top entities by default
            for node in all_nodes[:10]:
                nid = node.get("id", "")
                matched_entity_names.add(nid)
                entity_info[nid] = {
                    "entity_type": node.get("entity_type", "Unknown"),
                    "description": node.get("description", ""),
                }

        if not matched_entity_names:
            return ""

        # Limit entities
        matched_list = list(matched_entity_names)[:max_entities]

        # -- 3. Find relationships involving matched entities --
        relevant_rels: list[dict] = []
        matched_lower = {n.lower() for n in matched_list}

        for edge in all_edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if src.lower() in matched_lower or tgt.lower() in matched_lower:
                relevant_rels.append({
                    "source": src,
                    "target": tgt,
                    "description": edge.get("description", ""),
                    "keywords": edge.get("keywords", ""),
                })
                # Also add connected entities we might have missed
                if src not in entity_info:
                    # Find node info
                    for n in all_nodes:
                        if n.get("id", "") == src:
                            entity_info[src] = {
                                "entity_type": n.get("entity_type", "Unknown"),
                                "description": n.get("description", ""),
                            }
                            break
                if tgt not in entity_info:
                    for n in all_nodes:
                        if n.get("id", "") == tgt:
                            entity_info[tgt] = {
                                "entity_type": n.get("entity_type", "Unknown"),
                                "description": n.get("description", ""),
                            }
                            break

            if len(relevant_rels) >= max_relationships:
                break

        # -- 4. Format as structured text --
        parts: list[str] = []

        # Entities section
        if matched_list:
            parts.append("Entities found in documents:")
            for name in matched_list:
                info = entity_info.get(name, {})
                etype = info.get("entity_type", "")
                desc = info.get("description", "")
                # Truncate long descriptions
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                type_str = f" [{etype}]" if etype and etype != "Unknown" else ""
                if desc:
                    parts.append(f"- {name}{type_str}: {desc}")
                else:
                    parts.append(f"- {name}{type_str}")

        # Relationships section
        if relevant_rels:
            parts.append("")
            parts.append("Relationships:")
            for rel in relevant_rels:
                desc = rel["description"]
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                if desc:
                    parts.append(f"- {rel['source']} → {rel['target']}: {desc}")
                else:
                    parts.append(f"- {rel['source']} → {rel['target']}")

        result = "\n".join(parts)
        logger.info(
            f"KG raw context: {len(matched_list)} entities, "
            f"{len(relevant_rels)} relationships for workspace {self.workspace_id}"
        )
        return result

    async def get_analytics(self, allowed_doc_ids: list[int] | None = None) -> dict:
        """
        Compute KG analytics summary.

        Returns: entity_count, relationship_count, entity_types, top_entities, avg_degree.
        """
        if allowed_doc_ids == []:
            return {"entity_count": 0, "relationship_count": 0, "entity_types": {}, "top_entities": [], "avg_degree": 0.0}
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph

        try:
            all_nodes = await storage.get_all_nodes()
            all_edges = await storage.get_all_edges()
        except Exception as e:
            logger.error(f"Failed to get KG analytics for workspace {self.workspace_id}: {e}")
            return {
                "entity_count": 0,
                "relationship_count": 0,
                "entity_types": {},
                "top_entities": [],
                "avg_degree": 0.0,
            }

        if allowed_doc_ids is not None:
            allowed = {str(doc_id) for doc_id in allowed_doc_ids}
            chunk_map = await self._get_chunk_to_doc_map()
            all_nodes = [node for node in all_nodes if self._source_allowed(node.get("source_id", ""), allowed, chunk_map)]
            names = {node.get("id") for node in all_nodes}
            all_edges = [edge for edge in all_edges if edge.get("source") in names
                         and edge.get("target") in names
                         and self._source_allowed(edge.get("source_id", ""), allowed, chunk_map)]

        entity_count = len(all_nodes)
        relationship_count = len(all_edges)

        # Count entity types
        type_counts: dict[str, int] = {}
        entities_with_degree = []
        for node in all_nodes:
            etype = node.get("entity_type", "Unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1
            if allowed_doc_ids is not None:
                degree = 0
            else:
                try:
                    degree = await storage.node_degree(node.get("id", ""))
                except Exception:
                    degree = 0
            entities_with_degree.append({
                "name": node.get("id", ""),
                "entity_type": etype,
                "description": node.get("description", ""),
                "degree": degree,
            })

        # Sort by degree for top entities
        entities_with_degree.sort(key=lambda e: e["degree"], reverse=True)
        top_entities = entities_with_degree[:10]

        avg_degree = (
            sum(e["degree"] for e in entities_with_degree) / entity_count
            if entity_count > 0
            else 0.0
        )

        return {
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "entity_types": type_counts,
            "top_entities": top_entities,
            "avg_degree": round(avg_degree, 2),
        }
