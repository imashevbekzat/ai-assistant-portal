import pytest


@pytest.mark.asyncio
async def test_chat_revenue(client):
    r = await client.post("/api/chat", json={"message": "покажи выручку с начала года"})
    assert r.status_code == 200
    data = r.json()
    assert data["recognized"] is True
    assert data["intent"] == "sales"
    assert data["dashboard"]["view_url"] == "/dashboards/sales"
    assert "Выручка" in data["reply"]
    assert data["session_id"]


@pytest.mark.asyncio
async def test_chat_ebitda(client):
    r = await client.post("/api/chat", json={"message": "какая у нас ебитда"})
    data = r.json()
    assert data["recognized"] is True
    assert data["intent"] == "pnl"
    assert "EBITDA" in data["reply"]


@pytest.mark.asyncio
async def test_chat_regions(client):
    r = await client.post("/api/chat", json={"message": "продажи по регионам"})
    data = r.json()
    assert data["recognized"] is True
    assert data["intent"] == "regions"
    assert "Москва" in data["reply"]


@pytest.mark.asyncio
async def test_chat_fallback(client):
    r = await client.post("/api/chat", json={"message": "абракадабра qwerty"})
    data = r.json()
    assert data["recognized"] is False
    assert data["fallback"] is True
    assert len(data["chips"]) >= 4
    assert data["dashboard"] is None


@pytest.mark.asyncio
async def test_chat_context_clarify(client):
    r1 = await client.post("/api/chat", json={"message": "покажи выручку"})
    sid = r1.json()["session_id"]
    r2 = await client.post(
        "/api/chat", json={"session_id": sid, "message": "а по регионам?"}
    )
    data = r2.json()
    assert data["recognized"] is True
    assert data["intent"] == "regions"
    assert data["session_id"] == sid
