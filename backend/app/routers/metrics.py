from fastapi import APIRouter, HTTPException

from ..services import analytics

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def list_metrics() -> list[dict]:
    from ..services.data import METRICS
    return [
        {"id": mid, "title": m["title"], "unit": m["unit"], "dashboard": m["dashboard"]}
        for mid, m in METRICS.items()
    ]


@router.get("/metrics/{metric_id}/summary")
async def metric_summary(metric_id: str) -> dict:
    k = analytics.kpi_summary(metric_id)
    if not k:
        raise HTTPException(status_code=404, detail="metric not found")
    return k
