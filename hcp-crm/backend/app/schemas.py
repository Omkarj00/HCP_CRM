import datetime as dt
from typing import Optional, List, Any, Dict

from pydantic import BaseModel


class InteractionBase(BaseModel):
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[dt.date] = None
    interaction_time: Optional[dt.time] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    materials_shared: Optional[List[str]] = None
    follow_up_actions: Optional[str] = None
    follow_up_date: Optional[dt.date] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    entities: Optional[Dict[str, Any]] = None
    suggested_next_steps: Optional[List[str]] = None
    meeting_outcome: Optional[str] = None
    status: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class InteractionCreate(InteractionBase):
    pass


class ChatRequest(BaseModel):
    session_id: str
    message: str
    # the current state of the left-hand form, so the agent has context
    # about what's already filled in / which interaction is being edited
    current_form: Optional[Dict[str, Any]] = None
    current_interaction_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    form_update: Optional[Dict[str, Any]] = None
    interaction_id: Optional[int] = None
    tool_calls: List[str] = []
    data: Optional[Dict[str, Any]] = None
