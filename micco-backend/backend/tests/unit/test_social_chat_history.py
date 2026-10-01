"""Social replies round-trip through the same authorized history endpoint."""
from sqlalchemy import select

from app.api import rag
from app.models import ChatMessage
from test_fix_crossstack import bearer, scoped_api  # noqa: F401


async def test_social_chat_persists_for_only_its_user_and_workspace(scoped_api, monkeypatch):
    client, db, _ = scoped_api

    def no_retrieval(*args, **kwargs):
        raise AssertionError("A greeting must not invoke document retrieval")

    monkeypatch.setattr(rag, "get_rag_service", no_retrieval)
    endpoint = "/api/v1/rag/chat/11"
    denied = await client.post(endpoint, json={"message": "Xin chào"})
    assert denied.status_code == 401
    foreign = await client.post(endpoint, json={"message": "Xin chào"}, headers=bearer(6))
    assert foreign.status_code == 403

    response = await client.post(endpoint, json={"message": "Xin chào"}, headers=bearer(5))
    assert response.status_code == 200, response.text
    assert response.json()["sources"] == []
    answer = response.json()["answer"]

    history = await client.get(endpoint + "/history", headers=bearer(5))
    assert history.status_code == 200, history.text
    assert [(row["role"], row["content"]) for row in history.json()["messages"]] == [
        ("user", "Xin chào"), ("assistant", answer),
    ]
    rows = (await db.execute(select(ChatMessage).where(
        ChatMessage.workspace_id == 11).order_by(ChatMessage.id))).scalars().all()
    assert len(rows) == 2
    assert {row.user_id for row in rows} == {5}
    assert rows[1].sources is None

    other_user = await client.get(endpoint + "/history", headers=bearer(4))
    assert other_user.status_code == 200
    assert other_user.json()["messages"] == []
