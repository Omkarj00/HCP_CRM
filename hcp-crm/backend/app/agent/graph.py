import json
from datetime import date
from typing import Any, Dict, List, Optional

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage

from app.agent.llm import get_llm
from app.agent.tools import build_tools

SYSTEM_PROMPT_TEMPLATE = """You are the AI Assistant embedded in an AI-first pharmaceutical CRM,
inside the "Log HCP Interaction" screen. A field rep talks to you in natural language and
you control the structured form on their behalf using tools - the rep should almost never
need to touch the form directly.

Today's date is {today} (format: YYYY-MM-DD). Whenever a date field is needed, resolve
relative references like "today", "yesterday", "next Tuesday", "last week" into an actual
calendar date in YYYY-MM-DD format before calling any tool. NEVER pass words like "today"
or "yesterday" literally as a date argument - always compute the real date first.

Ground rules:
1. If the rep describes a meeting/call/email that has NOT been logged yet in this
   conversation, call `log_interaction` and extract every detail you can (HCP name,
   hospital, specialty, date/time, sentiment, topics, materials shared, follow-up asks).
2. If an interaction was already logged in this conversation and the rep corrects,
   clarifies, or adds information ("actually his name is...", "also mention...", "change
   the date to..."), call `edit_interaction` with ONLY the changed fields.
3. Use `view_interaction_history`, `search_hcp`, `generate_followup_suggestions`, or
   `schedule_followup_visit` when the rep's request matches those intents.
4. Always make a reasonable decision instead of asking clarifying questions when intent is
   reasonably clear - infer sensible defaults (e.g. today's actual date for an unspecified
   date, "Meeting" for interaction type when unclear).
5. After any tool call, reply to the rep in a short, natural, friendly confirmation of what
   you just did to the form (1-2 sentences). Do not read back a JSON blob.
6. If the rep is just chit-chatting or asking a general question unrelated to any tool,
   answer briefly and helpfully without calling a tool.
7. Always call a tool with well-formed, valid arguments only. Never emit partial or
   malformed function syntax. If you are not fully sure of a value, use your best
   reasonable inference rather than leaving the call malformed.
"""

# Max attempts if the model/provider produces a malformed or rejected tool call
# (e.g. Groq's strict function-calling parser returning a 400 tool_use_failed error).
MAX_TOOL_CALL_ATTEMPTS = 2

# Fallback reply shown to the rep if every attempt fails - keeps the UI from
# ever surfacing a raw stack trace / provider error message.
FALLBACK_REPLY = (
    "I had trouble understanding that one - could you try rephrasing it, "
    "or breaking it into a couple of shorter sentences?"
)


def run_agent(session_id: str, message: str, current_form: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    tools, db = build_tools(session_id)
    try:
        # Lower temperature = more reliable, well-formed tool-call syntax.
        # Structured tool calling doesn't need creativity, so we bias hard
        # toward determinism here rather than the 0.2 used previously.
        llm = get_llm(temperature=0.1)
        agent = create_react_agent(llm, tools)

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(today=date.today().isoformat())

        context_note = ""
        if current_form:
            context_note = f"\n\nCurrent form state on screen (may be partially filled): {json.dumps(current_form, default=str)}"

        messages: List[Any] = [
            SystemMessage(content=system_prompt + context_note),
            HumanMessage(content=message),
        ]

        result = None
        last_error: Optional[Exception] = None

        for attempt in range(MAX_TOOL_CALL_ATTEMPTS):
            try:
                result = agent.invoke({"messages": messages})
                last_error = None
                break
            except Exception as e:
                # This catches provider-level tool-call rejections (e.g. Groq's
                # 400 invalid_request_error / tool_use_failed for malformed
                # function-call syntax) that happen before our own tool code
                # ever runs, so they can't be handled inside tools.py.
                last_error = e
                if attempt < MAX_TOOL_CALL_ATTEMPTS - 1:
                    messages.append(HumanMessage(
                        content=(
                            "(system note: your previous tool call could not be processed "
                            "because it was malformed. Please try again, calling exactly one "
                            "tool with complete, valid, well-formatted arguments.)"
                        )
                    ))

        if result is None:
            # Every attempt failed - degrade gracefully instead of raising,
            # so the frontend never sees a raw 400/500 provider error.
            return {
                "reply": FALLBACK_REPLY,
                "form_update": None,
                "interaction_id": None,
                "tool_calls": [],
                "data": None,
                "error": str(last_error) if last_error else None,
            }

        out_messages = result["messages"]

        tool_calls: List[str] = []
        form_update: Dict[str, Any] = {}
        data: Dict[str, Any] = {}
        interaction_id: Optional[int] = None
        final_reply = ""

        for m in out_messages:
            if isinstance(m, ToolMessage):
                tool_calls.append(m.name)
                try:
                    payload = json.loads(m.content)
                except Exception:
                    continue
                if payload.get("form_update"):
                    form_update.update(payload["form_update"])
                if payload.get("data"):
                    data.update(payload["data"])
                if payload.get("interaction_id"):
                    interaction_id = payload["interaction_id"]
            elif isinstance(m, AIMessage) and m.content:
                final_reply = m.content

        if not final_reply:
            final_reply = "Done."

        return {
            "reply": final_reply,
            "form_update": form_update or None,
            "interaction_id": interaction_id,
            "tool_calls": tool_calls,
            "data": data or None,
        }
    finally:
        db.close()