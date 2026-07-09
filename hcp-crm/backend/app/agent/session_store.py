"""
In-memory session context.

The assignment explicitly excludes authentication, so we keep a lightweight
in-memory map from a frontend-generated session_id -> the last interaction
that session touched. This lets the user say "actually his name is Dr. John"
right after logging an interaction, without having to repeat the interaction id.

This is process-local (fine for a single-instance demo). Swap for Redis if you
need multi-worker deployment.
"""
from typing import Dict, Any

_SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_session(session_id: str) -> Dict[str, Any]:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {"last_interaction_id": None}
    return _SESSIONS[session_id]


def set_last_interaction(session_id: str, interaction_id: int) -> None:
    ctx = get_session(session_id)
    ctx["last_interaction_id"] = interaction_id
