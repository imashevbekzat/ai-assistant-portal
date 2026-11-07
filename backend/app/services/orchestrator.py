"""Оркестрация диалога: intent routing (LLM → словарь) → аналитика → формулировка."""

from __future__ import annotations

import uuid

from .catalog import FALLBACK_CHIPS
from ..schemas import ChatRequest, ChatResponse, DashboardRef, SuggestionChip
from . import analytics, router
from .llm import llm_service

_SESSIONS: dict[str, dict] = {}


def _get_session(session_id: str | None) -> tuple[str, dict]:
    sid = session_id or uuid.uuid4().hex[:12]
    state = _SESSIONS.setdefault(sid, {"history": [], "last_intent": None})
    return sid, state


def _dashboard_ref(dashboard_id: str) -> DashboardRef | None:
    d = router.get_dashboard(dashboard_id)
    if not d:
        return None
    return DashboardRef(
        id=d["id"],
        title=d["title"],
        section=d["section"],
        view_url=d["view_url"],
        description=d["description"],
    )


def _intent_metrics(dashboard_id: str) -> list[str]:
    d = router.get_dashboard(dashboard_id)
    return d["metrics"] if d else []


FALLBACK_TEXT = (
    "Не удалось распознать запрос. Я могу показать ключевые показатели компании — "
    "выберите направление ниже или уточните формулировку."
)


async def handle_chat(req: ChatRequest) -> ChatResponse:
    sid, state = _get_session(req.session_id)
    text = req.message.strip()

    # 1. Intent routing: LLM-классификация → словарный роутинг (fallback)
    intent: str | None = None
    llm_used = False
    if llm_service.available:
        intent = await llm_service.classify_intent(text, router.catalog_for_llm())
        llm_used = intent is not None
    if intent is None:
        intent = router.route_with_context(text, state.get("last_intent"))

    state["history"].append({"role": "user", "text": text})

    # 2. Fallback при нераспознанном запросе (FR-4)
    if intent is None:
        reply = FALLBACK_TEXT
        state["history"].append({"role": "assistant", "text": reply})
        return ChatResponse(
            session_id=sid,
            recognized=False,
            reply=reply,
            chips=[SuggestionChip(**c) for c in FALLBACK_CHIPS],
            fallback=True,
            llm_used=llm_service.available,
        )

    state["last_intent"] = intent
    metrics = router.route_metrics(text, intent)
    facts = analytics.build_insight_text(intent, metrics)

    # 3. Формулировка: LLM из готовых цифр → шаблонный текст (fallback)
    reply: str | None = None
    if llm_service.available:
        dash = router.get_dashboard(intent)
        reply = await llm_service.formulate(dash["title"] if dash else intent, facts, text)
    if not reply:
        reply = facts

    state["history"].append({"role": "assistant", "text": reply})
    return ChatResponse(
        session_id=sid,
        recognized=True,
        intent=intent,
        reply=reply,
        dashboard=_dashboard_ref(intent),
        chips=[],
        fallback=False,
        llm_used=llm_service.available,
    )
