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
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings
from app.services.llm import get_embedding_provider, get_llm_provider
from app.services.llm.types import LLMMessage

logger = logging.getLogger(__name__)


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
    """LightRAG-compatible LLM function using the configured provider."""
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

    return await provider.acomplete(
        messages, temperature=0.0, max_tokens=4096,
    )


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
        # Path to kv_storage_text_chunks.json
        storage_path = Path(self.working_dir) / "kv_storage_text_chunks.json"
        
        if storage_path.exists():
            try:
                import json
                with open(storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for chunk_id, chunk_info in data.items():
                        # In LightRAG, chunk_info usually has 'doc_id' 
                        # if ingested with ids parameter.
                        doc_id = chunk_info.get("doc_id")
                        if doc_id:
                            mapping[chunk_id] = str(doc_id)
            except Exception as e:
                logger.error(f"Failed to load chunk-to-doc mapping: {e}")
        
        self._chunk_to_doc_map = mapping
        return mapping

    async def _get_rag(self):
        """Lazy-initialize LightRAG instance."""
        if self._rag is not None and self._initialized:
            return self._rag

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

        self._rag = LightRAG(
            working_dir=self.working_dir,
            llm_model_func=_kg_llm_complete,
            embedding_func=embedding_func,
            chunk_token_size=settings.NEXUSRAG_KG_CHUNK_TOKEN_SIZE,
            enable_llm_cache=True,
            kv_storage="JsonKVStorage",
            vector_storage="NanoVectorDBStorage",
            graph_storage="NetworkXStorage",
            doc_status_storage="JsonDocStatusStorage",
            addon_params={
                "language": self.kg_language,
                "entity_types": self.kg_entity_types,
            },
        )

        await self._rag.initialize_storages()
        await initialize_pipeline_status()
        self._initialized = True

        logger.info(
            f"LightRAG initialized for workspace {self.workspace_id} "
            f"(embedding_dim={embedding_dim})"
        )
        return self._rag

    async def ingest(self, markdown_content: str, document_id: int | None = None) -> None:
        """
        Ingest markdown content into the knowledge graph.
        LightRAG extracts entities and relationships automatically.
        """
        rag = await self._get_rag()

        if not markdown_content.strip():
            logger.warning(f"Empty content for workspace {self.workspace_id}, skipping KG ingest")
            return

        try:
            doc_ids = [str(document_id)] if document_id else None
            await rag.ainsert(markdown_content, ids=doc_ids)
            logger.info(
                f"KG ingested {len(markdown_content)} chars for doc {document_id} in workspace {self.workspace_id}"
            )

            # Check if entities were actually extracted
            try:
                all_nodes = await rag.chunk_entity_relation_graph.get_all_nodes()
                if not all_nodes:
                    from app.core.config import settings
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
                is_allowed = False
                # Nodes in LightRAG often have source_id which is a comma-separated list of chunks
                node_chunks = [c.strip() for c in source_id.split(",") if c.strip()]
                for chunk in node_chunks:
                    # Strip "chunk-" prefix if present
                    cid = chunk.replace("chunk-", "") if chunk.startswith("chunk-") else chunk
                    doc_id = chunk_map.get(cid)
                    if doc_id in allowed_ids_str:
                        is_allowed = True
                        break
                
                if not is_allowed:
                    continue

            # Existing filters
            if entity_type and etype.lower() != entity_type.lower():
                continue
            if search and search.lower() not in node_id.lower():
                continue

            # Get degree (number of relationships)
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

        relationships = []
        for edge in all_edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            source_id = edge.get("source_id", "")
            
            # Filtering by allowed document IDs
            if allowed_ids_str is not None:
                is_allowed = False
                edge_chunks = [c.strip() for c in source_id.split(",") if c.strip()]
                for chunk in edge_chunks:
                    cid = chunk.replace("chunk-", "") if chunk.startswith("chunk-") else chunk
                    doc_id = chunk_map.get(cid)
                    if doc_id in allowed_ids_str:
                        is_allowed = True
                        break
                
                if not is_allowed:
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
        for n in kg.nodes:
            # Type hinting for linter
            node_id = getattr(n, "id", None)
            if node_id is None:
                continue
                
            props = getattr(n, "properties", {})
            # Filtering by allowed domain if requested
            if allowed_ids_str is not None:
                source_id = props.get("source_id", "")
                is_allowed = False
                chunks = [c.strip() for c in source_id.split(",") if c.strip()]
                for chunk in chunks:
                    cid = chunk.replace("chunk-", "") if chunk.startswith("chunk-") else chunk
                    doc_id = chunk_map.get(cid)
                    if doc_id in allowed_ids_str:
                        is_allowed = True
                        break
                if not is_allowed:
                    continue
            
            allowed_node_ids.add(node_id)
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
        for e in kg.edges:
            source = getattr(e, "source", None)
            target = getattr(e, "target", None)
            
            # Only include edges where both source and target are allowed (and the edge itself is from allowed doc)
            if source not in allowed_node_ids or target not in allowed_node_ids:
                continue
                
            props = getattr(e, "properties", {})
            if allowed_ids_str is not None:
                source_id = props.get("source_id", "")
                is_allowed = False
                chunks = [c.strip() for c in source_id.split(",") if c.strip()]
                for chunk in chunks:
                    cid = chunk.replace("chunk-", "") if chunk.startswith("chunk-") else chunk
                    doc_id = chunk_map.get(cid)
                    if doc_id in allowed_ids_str:
                        is_allowed = True
                        break
                if not is_allowed:
                    continue

            edges.append({
                "source": source,
                "target": target,
                "label": props.get("description", "")[:80],
                "weight": float(props.get("weight", 1.0)),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "is_truncated": kg.is_truncated if hasattr(kg, "is_truncated") else False,
        }

    async def get_relevant_context(
        self,
        question: str,
        max_entities: int = 20,
        max_relationships: int = 30,
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
        rag = await self._get_rag()
        storage = rag.chunk_entity_relation_graph

        try:
            all_nodes = await storage.get_all_nodes()
            all_edges = await storage.get_all_edges()
        except Exception as e:
            logger.error(f"Failed to get raw KG data for workspace {self.workspace_id}: {e}")
            return ""

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

    async def get_analytics(self) -> dict:
        """
        Compute KG analytics summary.

        Returns: entity_count, relationship_count, entity_types, top_entities, avg_degree.
        """
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

        entity_count = len(all_nodes)
        relationship_count = len(all_edges)

        # Count entity types
        type_counts: dict[str, int] = {}
        entities_with_degree = []
        for node in all_nodes:
            etype = node.get("entity_type", "Unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1
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
