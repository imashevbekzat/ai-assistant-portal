from fastapi import APIRouter

from ..schemas import ChatRequest, ChatResponse
from ..services import orchestrator
from ..services.audit import log_event

router = APIRouter(tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    resp = await orchestrator.handle_chat(req)
    log_event({
        "type": "chat",
        "session_id": resp.session_id,
        "message": req.message,
        "recognized": resp.recognized,
        "intent": resp.intent,
        "llm_used": resp.llm_used,
    })
    return resp
