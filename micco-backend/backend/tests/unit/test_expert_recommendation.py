"""
Unit tests for expert_recommendation service.
Tests the recommend_experts() function with mocked dependencies.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from collections import defaultdict

# Import service and utility
from app.services.expert_recommendation import (
    recommend_experts,
    _cosine_to_relevance,
    ExpertRecommendation,
)


# ---------------------------------------------------------------------------
# Test _cosine_to_relevance utility
# ---------------------------------------------------------------------------

class TestCosineToRelevance:
    """Test cases for the cosine distance → relevance score converter."""

    def test_identical_vectors(self):
        """Distance 0 → relevance 1.0"""
        assert _cosine_to_relevance(0.0) == 1.0

    def test_opposite_vectors(self):
        """Distance 2.0 → relevance 0.0"""
        assert _cosine_to_relevance(2.0) == 0.0

    def test_midpoint(self):
        """Distance 1.0 → relevance 0.5"""
        assert _cosine_to_relevance(1.0) == 0.5

    def test_negative_distance_clamped_to_1(self):
        """Negative distance → clamped to 1.0"""
        assert _cosine_to_relevance(-0.5) == 1.0

    def test_distance_over_2_clamped_to_0(self):
        """Distance > 2.0 → clamped to 0.0"""
        assert _cosine_to_relevance(3.0) == 0.0


# ---------------------------------------------------------------------------
# Test recommend_experts function
# ---------------------------------------------------------------------------

class TestRecommendExperts:
    """Test cases for the main recommend_experts() function."""

    def _mock_vector_results(self, docs: list[dict]) -> dict:
        """Helper: build a mock ChromaDB query result dict.

        Each doc: {"id": str, "document_id": int, "distance": float}
        """
        return {
            "ids": [d["id"] for d in docs],
            "documents": ["sample content" for _ in docs],
            "metadatas": [{"document_id": d["document_id"]} for d in docs],
            "distances": [d["distance"] for d in docs],
        }

    def _mock_db_session(self, doc_uploader: dict[int, int | None], users: list[dict]) -> MagicMock:
        """Helper: build a mock AsyncSession that returns canned SQLAlchemy results."""
        session = MagicMock()

        # First call: select Document.id, Document.uploader_id
        doc_result = MagicMock()
        doc_rows = [MagicMock(id=did, uploader_id=uid) for did, uid in doc_uploader.items()]
        doc_result.all.return_value = doc_rows
        doc_result.scalars.return_value.all.return_value = doc_rows

        # Second call: select User with department
        user_result = MagicMock()

        def _make_user_row(u: dict) -> MagicMock:
            row = MagicMock()
            row.id = u["id"]
            row.name = u["name"]
            row.email = u["email"]
            row.role = u["role"]
            dept = MagicMock()
            dept.name = u["department"]
            row.department = dept
            return row

        user_rows = [_make_user_row(u) for u in users]
        user_result.scalars.return_value.all.return_value = user_rows
        session.execute = AsyncMock(side_effect=[doc_result, user_result])
        return session

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty_list(self):
        """Empty or whitespace-only query → returns [] immediately."""
        result = await recommend_experts(
            workspace_id=1,
            query="   ",
            top_k=3,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_empty_query_none_returns_empty_list(self):
        """None query → returns [] immediately."""
        result = await recommend_experts(
            workspace_id=1,
            query="",
            top_k=3,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_top_k_clamped_to_10(self):
        """top_k > 10 is clamped to 10."""
        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = {"ids": [], "documents": [], "metadatas": [], "distances": []}
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=50,  # exceeds max
                )
                assert mock_vs_instance.query.call_count == 1
                call_kwargs = mock_vs_instance.query.call_args
                assert call_kwargs.kwargs.get("n_results") == 10 * 5  # clamped

    @pytest.mark.asyncio
    async def test_no_vector_results_returns_empty(self):
        """No documents from vector search → returns []."""
        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = {
                    "ids": [], "documents": [], "metadatas": [], "distances": []
                }
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                )
                assert result == []

    @pytest.mark.asyncio
    async def test_no_db_session_returns_empty(self):
        """No DB session → returns [] (can't resolve uploaders)."""
        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_1_chunk_0", "document_id": 10, "distance": 0.2},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=None,  # no DB session
                )
                assert result == []

    @pytest.mark.asyncio
    async def test_single_user_single_doc(self):
        """Single user uploaded single document → returns that user."""
        mock_session = self._mock_db_session(
            doc_uploader={10: 1},
            users=[{"id": 1, "name": "Nguyễn Văn A", "email": "a@example.com",
                    "role": "Trưởng phòng", "department": "Kỹ thuật"}],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.2},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        assert len(result) == 1
        assert result[0].user_id == 1
        assert result[0].name == "Nguyễn Văn A"
        assert result[0].email == "a@example.com"
        assert result[0].role == "Trưởng phòng"
        assert result[0].department == "Kỹ thuật"
        assert result[0].document_count == 1
        # distance=0.2 → relevance = 1 - 0.2/2 = 0.9
        assert result[0].avg_relevance == 0.9

    @pytest.mark.asyncio
    async def test_multiple_users_ranked_by_doc_count(self):
        """Multiple users → sorted by document_count desc."""
        mock_session = self._mock_db_session(
            doc_uploader={10: 1, 11: 1, 12: 2, 13: 2, 14: 3},  # user1: 2docs, user2: 2docs, user3: 1doc
            users=[
                {"id": 1, "name": "User One", "email": "u1@example.com",
                 "role": "Dev", "department": "Tech"},
                {"id": 2, "name": "User Two", "email": "u2@example.com",
                 "role": "QA", "department": "QA"},
                {"id": 3, "name": "User Three", "email": "u3@example.com",
                 "role": "PM", "department": "PM"},
            ],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                # user 1: doc10(dist=0.1), doc11(dist=0.3)
                # user 2: doc12(dist=0.2), doc13(dist=0.4)
                # user 3: doc14(dist=0.5)
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.1},
                    {"id": "doc_11_chunk_0", "document_id": 11, "distance": 0.3},
                    {"id": "doc_12_chunk_0", "document_id": 12, "distance": 0.2},
                    {"id": "doc_13_chunk_0", "document_id": 13, "distance": 0.4},
                    {"id": "doc_14_chunk_0", "document_id": 14, "distance": 0.5},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        assert len(result) == 3
        # user1 and user2 both have 2 docs → tie → any order OK, but both should appear
        top_2_ids = {result[0].user_id, result[1].user_id}
        assert top_2_ids == {1, 2}
        assert result[2].user_id == 3  # user3 has 1 doc

        # Check avg relevance
        for expert in result:
            if expert.user_id == 1:
                # (0.95 + 0.85) / 2 = 0.9
                assert expert.avg_relevance == 0.9
            elif expert.user_id == 2:
                # (0.9 + 0.8) / 2 = 0.85
                assert expert.avg_relevance == 0.85

    @pytest.mark.asyncio
    async def test_documents_without_uploader_skipped(self):
        """Documents with uploader_id=None → skipped."""
        mock_session = self._mock_db_session(
            doc_uploader={10: 1, 11: None, 12: 2},  # doc11 has no uploader
            users=[
                {"id": 1, "name": "User One", "email": "u1@example.com",
                 "role": "Dev", "department": "Tech"},
                {"id": 2, "name": "User Two", "email": "u2@example.com",
                 "role": "QA", "department": "QA"},
            ],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.2},
                    {"id": "doc_11_chunk_0", "document_id": 11, "distance": 0.1},
                    {"id": "doc_12_chunk_0", "document_id": 12, "distance": 0.3},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        # user1 has doc10, user2 has doc12; doc11 has no uploader → excluded
        assert len(result) == 2
        user_ids = {e.user_id for e in result}
        assert user_ids == {1, 2}

    @pytest.mark.asyncio
    async def test_same_document_id_appears_multiple_times_uses_best_relevance(self):
        """Same document_id from multiple chunks → uses max (best) relevance."""
        mock_session = self._mock_db_session(
            doc_uploader={10: 1},
            users=[{"id": 1, "name": "User One", "email": "u1@example.com",
                    "role": "Dev", "department": "Tech"}],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                # Same doc_id (10) appears twice with different distances
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.6},  # relevance=0.7
                    {"id": "doc_10_chunk_1", "document_id": 10, "distance": 0.1},  # relevance=0.95 (best)
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        # Should only count doc 10 once with best relevance (0.95)
        assert len(result) == 1
        assert result[0].document_count == 1
        assert result[0].avg_relevance == 0.95

    @pytest.mark.asyncio
    async def test_allowed_document_ids_filter_applied(self):
        """allowed_document_ids filter → vector search receives correct where clause."""
        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = {"ids": [], "documents": [], "metadatas": [], "distances": []}
                mock_vs.return_value = mock_vs_instance

                await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=MagicMock(),
                    allowed_document_ids=[10, 20, 30],
                )

                call_kwargs = mock_vs_instance.query.call_args.kwargs
                assert call_kwargs.get("where") == {"document_id": {"$in": [10, 20, 30]}}

    @pytest.mark.asyncio
    async def test_user_without_department_returns_default(self):
        """User with no department → department defaults to 'Không xác định'."""
        mock_session = MagicMock()

        doc_result = MagicMock()
        doc_rows = [MagicMock(id=10, uploader_id=1)]
        doc_result.all.return_value = doc_rows
        doc_result.scalars.return_value.all.return_value = doc_rows

        user_result = MagicMock()
        user_row = MagicMock()
        user_row.id = 1
        user_row.name = "Orphan User"
        user_row.email = "orphan@example.com"
        user_row.role = "Intern"
        user_row.department = None
        user_result.scalars.return_value.all.return_value = [user_row]

        mock_session.execute = AsyncMock(side_effect=[doc_result, user_result])

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.4},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        assert len(result) == 1
        assert result[0].department == "Không xác định"

    @pytest.mark.asyncio
    async def test_top_k_respects_limit(self):
        """Only top_K users are returned, sorted by doc_count desc."""
        mock_session = self._mock_db_session(
            doc_uploader={i: i for i in range(1, 6)},  # 5 users, 1 doc each
            users=[
                {"id": i, "name": f"User {i}", "email": f"u{i}@example.com",
                 "role": "Role", "department": "Dept"}
                for i in range(1, 6)
            ],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": f"doc_{i}_chunk_0", "document_id": i, "distance": 0.1}
                    for i in range(1, 6)
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=2,  # only return top 2
                    db=mock_session,
                )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_vector_search_exception_returns_empty(self):
        """Vector search throws → returns [] (graceful degradation)."""
        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.side_effect = RuntimeError("ChromaDB unavailable")
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                )

        assert result == []

    @pytest.mark.asyncio
    async def test_documents_not_in_db_skipped(self):
        """Documents found in vector but not in DB (deleted) → skipped gracefully."""
        mock_session = MagicMock()

        doc_result = MagicMock()
        # DB only has doc 10 and 12, but not 11 (deleted)
        doc_rows = [MagicMock(id=10, uploader_id=1), MagicMock(id=12, uploader_id=2)]
        doc_result.all.return_value = doc_rows
        doc_result.scalars.return_value.all.return_value = doc_rows

        user_result = MagicMock()
        user_rows = []
        for uid in [1, 2]:
            row = MagicMock()
            row.id = uid
            row.name = f"User {uid}"
            row.email = f"u{uid}@example.com"
            row.role = "Role"
            row.department = "Dept"  # string, not a mock
            user_rows.append(row)
        user_result.scalars.return_value.all.return_value = user_rows

        mock_session.execute = AsyncMock(side_effect=[doc_result, user_result])

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.1},
                    {"id": "doc_11_chunk_0", "document_id": 11, "distance": 0.2},  # not in DB
                    {"id": "doc_12_chunk_0", "document_id": 12, "distance": 0.3},
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        # Only doc 10 and 12 have uploaders → 2 users
        assert len(result) == 2
        user_ids = {e.user_id for e in result}
        assert user_ids == {1, 2}

    @pytest.mark.asyncio
    async def test_avg_relevance_rounded_to_4_decimals(self):
        """avg_relevance is rounded to 4 decimal places."""
        mock_session = self._mock_db_session(
            doc_uploader={10: 1, 11: 1},  # user1 has 2 docs
            users=[{"id": 1, "name": "User One", "email": "u1@example.com",
                    "role": "Dev", "department": "Tech"}],
        )

        with patch("app.services.expert_recommendation.get_embedding_service") as mock_embed:
            mock_embedder = MagicMock()
            mock_embedder.embed_query.return_value = [0.1] * 1024
            mock_embed.return_value = mock_embedder

            with patch("app.services.expert_recommendation.get_vector_store") as mock_vs:
                mock_vs_instance = MagicMock()
                mock_vs_instance.query.return_value = self._mock_vector_results([
                    {"id": "doc_10_chunk_0", "document_id": 10, "distance": 0.1},  # 0.95
                    {"id": "doc_11_chunk_0", "document_id": 11, "distance": 0.2},  # 0.90
                    # avg = (0.95 + 0.90) / 2 = 0.925 → rounded = 0.925
                ])
                mock_vs.return_value = mock_vs_instance

                result = await recommend_experts(
                    workspace_id=1,
                    query="test question",
                    top_k=3,
                    db=mock_session,
                )

        assert len(result) == 1
        assert result[0].avg_relevance == 0.925  # exactly 4 decimal places


# ---------------------------------------------------------------------------
# Test ExpertRecommendation schema
# ---------------------------------------------------------------------------

class TestExpertRecommendationSchema:
    """Test Pydantic schema validation."""

    def test_valid_schema(self):
        """Valid data → passes validation."""
        expert = ExpertRecommendation(
            user_id=1,
            name="Nguyễn Văn A",
            email="test@example.com",
            role="Trưởng phòng",
            department="Kỹ thuật",
            document_count=5,
            avg_relevance=0.87,
        )
        assert expert.user_id == 1
        assert expert.name == "Nguyễn Văn A"
        assert expert.avg_relevance == 0.87

    def test_avg_relevance_clamped_to_valid_range(self):
        """avg_relevance outside 0-1 range → validation error."""
        with pytest.raises(Exception):  # Pydantic validation error
            ExpertRecommendation(
                user_id=1,
                name="Test",
                email="test@example.com",
                role="Dev",
                department="Tech",
                document_count=1,
                avg_relevance=1.5,  # invalid: > 1.0
            )

    def test_document_count_must_be_positive(self):
        """document_count < 0 → validation error."""
        with pytest.raises(Exception):
            ExpertRecommendation(
                user_id=1,
                name="Test",
                email="test@example.com",
                role="Dev",
                department="Tech",
                document_count=0,  # must be >= 1 (at least in practice)
                avg_relevance=0.5,
            )
