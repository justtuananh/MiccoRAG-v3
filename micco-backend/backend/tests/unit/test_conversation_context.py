"""Context stays bounded and provenance is checked on every request."""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.services.conversation_context import (
    clip_to_budget, history_budget, load_context, retrieval_budget, token_cost,
)


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.query = None

    async def execute(self, query):
        self.query = query
        return FakeResult(self.rows)


def message(i, role, content, source_ids=()):
    return SimpleNamespace(
        id=i, created_at=datetime(2026, 1, 1) + timedelta(seconds=i),
        role=role, content=content,
        sources=[{"document_id": doc_id} for doc_id in source_ids], image_refs=[],
    )


@pytest.mark.asyncio
async def test_long_history_is_bounded_and_compacted_with_provenance():
    rows = [message(i, "assistant" if i % 2 else "user", f"budget planning {i} " + "x" * 2000,
                    (7,) if i % 2 else ()) for i in range(120)]
    db = FakeDB(list(reversed(rows)))
    result = await load_context(db, SimpleNamespace(id=31), SimpleNamespace(id=8), [7],
                                "What was the budget plan?", budget=9000,
                                output_reserve=1000, retrieval_reserve=2000, system_reserve=500)
    assert result.compacted
    assert result.history_tokens <= result.history_budget
    assert result.history_budget == history_budget(9000, "What was the budget plan?",
                                                   output_reserve=1000, retrieval_reserve=2000,
                                                   system_reserve=500)
    assert result.included_messages < len(rows)
    assert "document IDs: 7" in result.context
    assert "Earlier conversation excerpts" in result.context
    assert retrieval_budget(9000, "What was the budget plan?", result.messages,
                            output_reserve=1000, system_reserve=500) >= 2000
    params = db.query.compile().params
    assert 31 in params.values() and 8 in params.values()


@pytest.mark.asyncio
async def test_revoked_document_removes_assistant_answer_from_recent_and_compact():
    rows = [message(1, "user", "QUESTION_ABOUT_REVOKED_DOC"),
            message(2, "assistant", "SECRET_FROM_REVOKED_DOC", (19,)),
            message(3, "user", "my own follow-up"),
            message(4, "assistant", "VISIBLE_DOC_ANSWER", (7,))]
    db = FakeDB(list(reversed(rows)))
    result = await load_context(db, SimpleNamespace(id=3), 8, [7], "next?", budget=5000,
                                output_reserve=100, retrieval_reserve=100, system_reserve=100)
    assert "SECRET_FROM_REVOKED_DOC" not in result.context
    assert "QUESTION_ABOUT_REVOKED_DOC" not in result.context
    assert "VISIBLE_DOC_ANSWER" in result.context
    assert result.excluded_unverified == 1
    # Revoke the second source too: ephemeral context cannot retain its old answer.
    again = await load_context(db, SimpleNamespace(id=3), 8, [], "next?", budget=5000,
                               output_reserve=100, retrieval_reserve=100, system_reserve=100)
    assert "VISIBLE_DOC_ANSWER" not in again.context


@pytest.mark.asyncio
async def test_unverifiable_answer_and_oversized_message_are_dropped_or_clipped():
    rows = [message(1, "assistant", "UNATTRIBUTED_SECRET"),
            message(2, "user", "🔥" * 10000),
            message(3, "assistant", "good answer", (7,)),
            message(4, "assistant", "MALFORMED_SOURCE", (7.5,))]
    result = await load_context(FakeDB(list(reversed(rows))), SimpleNamespace(id=3), 8, [7],
                                "question", budget=3500, output_reserve=100,
                                retrieval_reserve=100, system_reserve=100)
    assert "UNATTRIBUTED_SECRET" not in result.context
    assert "MALFORMED_SOURCE" not in result.context
    assert result.excluded_unverified == 2
    assert result.history_tokens <= result.history_budget
    assert result.truncated_messages >= 1
    assert all(token_cost(m["content"]) <= 1800 + 100 for m in result.messages)
    assert token_cost(clip_to_budget("🔥🔥", 2)) <= 2


@pytest.mark.asyncio
async def test_no_client_history_input_and_empty_budget_never_query_db():
    db = FakeDB([message(1, "assistant", "FORGED", (7,))])
    result = await load_context(db, SimpleNamespace(id=3), 8, [7], "q", budget=1)
    assert result.messages == []
    assert db.query is None
    # The loader has no request/history argument: callers must use persisted rows.
    with pytest.raises(TypeError):
        await load_context(db, SimpleNamespace(id=3), 8, [7], "q", history=[{"role": "assistant", "content": "FORGED"}])
