from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DashboardId(str, Enum):
    sales = "sales"
    pnl = "pnl"
    regions = "regions"
    clients = "clients"
    hr = "hr"
    marketing = "marketing"


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=2000)


class DashboardRef(BaseModel):
    id: DashboardId
    title: str
    section: str
    view_url: str
    description: str = ""


class SuggestionChip(BaseModel):
    label: str
    query: str


class KpiSummary(BaseModel):
    metric: str
    unit: str
    ytd: float
    ytd_prev: float
    yoy_pct: Optional[float] = None
    plan_ytd: Optional[float] = None
    plan_pct: Optional[float] = None
    quality: str = ""
    comment: str = ""
    updated_at: str = ""
    source: str = ""


class ChatResponse(BaseModel):
    session_id: str
    recognized: bool
    intent: Optional[DashboardId] = None
    reply: str
    dashboard: Optional[DashboardRef] = None
    chips: list[SuggestionChip] = []
    fallback: bool = False
    llm_used: bool = False


class SessionState(BaseModel):
    session_id: str
    history: list[dict] = []
    last_intent: Optional[DashboardId] = None
