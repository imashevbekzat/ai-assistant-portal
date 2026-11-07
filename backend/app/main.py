from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import catalog, chat, metrics

BASE_DIR = Path(__file__).resolve().parents[2]

app = FastAPI(title="AI Assistant Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# Раздача виджета как статического JS-модуля (этап 4 дорожной карты).
widget_dir = BASE_DIR / "widget"
if widget_dir.exists():
    app.mount("/widget", StaticFiles(directory=widget_dir), name="widget")


@app.get("/portal", include_in_schema=False)
async def portal() -> FileResponse:
    return FileResponse(BASE_DIR / "portal-view" / "index.html")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse(BASE_DIR / "portal-view" / "index.html")
