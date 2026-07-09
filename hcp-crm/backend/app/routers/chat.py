from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import run_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")
    try:
        result = run_agent(req.session_id, req.message, req.current_form)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
    return ChatResponse(**result)
