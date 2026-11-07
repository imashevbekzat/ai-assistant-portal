import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_dashboards_catalog(client):
    r = await client.get("/api/dashboards")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 6
    ids = {d["id"] for d in data}
    assert {"sales", "pnl", "regions", "clients", "hr", "marketing"} == ids


@pytest.mark.asyncio
async def test_metrics_summary(client):
    r = await client.get("/api/metrics/revenue/summary")
    assert r.status_code == 200
    k = r.json()
    assert k["metric"] == "Выручка"
    assert k["ytd"] > k["ytd_prev"]
    assert k["yoy_pct"] is not None
    assert k["plan_pct"] is not None


@pytest.mark.asyncio
async def test_metric_not_found(client):
    r = await client.get("/api/metrics/unknown/summary")
    assert r.status_code == 404
