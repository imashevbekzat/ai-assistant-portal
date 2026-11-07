from fastapi import APIRouter

from ..services import router as router_service

router = APIRouter(tags=["catalog"])


@router.get("/dashboards")
async def list_dashboards() -> list[dict]:
    return router_service.all_dashboards()
