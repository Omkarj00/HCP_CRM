import json
import datetime as dt
from typing import Optional, List

from dateutil import parser as date_parser
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.models import Interaction, HCP, FollowUpTask
from app.agent.llm import get_llm
from app.agent.session_store import set_last_interaction, get_session


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _parse_date(value: Optional[str]) -> Optional[dt.date]:
    if not value:
        return None
    try:
        return date_parser.parse(value, fuzzy=True, default=dt.datetime.now()).date()
    except Exception:
        return None


def _parse_time(value: Optional[str]) -> Optional[dt.time]:
    if not value:
        return None
    try:
        return date_parser.parse(value, fuzzy=True).time()
    except Exception:
        return None


def _interaction_to_form_dict(i: Interaction) -> dict:
    """Shape returned to the frontend to populate the left-hand form."""
    return {
        "id": i.id,
        "hcpName": i.hcp_name,
        "hospital": i.hospital,
        "specialty": i.specialty,
        "interactionType": i.interaction_type,
        "date": i.interaction_date.isoformat() if i.interaction_date else None,
        "time": i.interaction_time.strftime("%H:%M") if i.interaction_time else None,
        "attendees": i.attendees or [],
        "topicsDiscussed": i.topics_discussed,
        "sentiment": i.sentiment,
        "materialsShared": i.materials_shared or [],
        "followUpActions": i.follow_up_actions,
        "followUpDate": i.follow_up_date.isoformat() if i.follow_up_date else None,
        "notes": i.notes,
        "summary": i.summary,
        "keyPoints": i.key_points or [],
        "entities": i.entities or {},
        "suggestedNextSteps": i.suggested_next_steps or [],
        "meetingOutcome": i.meeting_outcome,
        "status": i.status,
    }


def _enrich_with_llm(topics: Optional[str], notes: Optional[str], sentiment: Optional[str]) -> dict:
    """Ask the LLM to summarize the free-text into structured CRM fields."""
    text = "\n".join(filter(None, [topics, notes]))
    if not text.strip():
        return {}

    llm = get_llm(temperature=0.1)
    prompt = f"""You are a pharmaceutical CRM assistant. Read the field-rep's notes below and
return ONLY a compact JSON object (no markdown, no commentary) with these keys:
- "summary": one or two sentence summary of the interaction
- "key_points": array of short bullet strings of key discussion points
- "entities": object with keys "drugs", "medical_topics", "requests" each an array of strings found in the text
- "suggested_next_steps": array of short actionable follow-up suggestions
- "meeting_outcome": one short phrase describing the outcome (e.g. "Positive - requested studies")

Sentiment reported by rep: {sentiment or "unspecified"}

Notes:
\"\"\"{text}\"\"\"

Respond with raw JSON only."""
    try:
        resp = llm.invoke(prompt)
        content = resp.content.strip()
        # strip accidental code fences
        if content.startswith("```"):
            content = content.strip("`")
            content = content.split("\n", 1)[-1] if "\n" in content else content
            if content.lower().startswith("json"):
                content = content[4:]
        data = json.loads(content)
        return data
    except Exception:
        return {}


# --------------------------------------------------------------------------
# tool factory - builds tools bound to a chat session so the LLM never has
# to know about session_ids / db plumbing, it only ever sees business args
# --------------------------------------------------------------------------

def build_tools(session_id: str):
    db = SessionLocal()

    class LogInteractionArgs(BaseModel):
        hcp_name: str = Field(..., description="Name of the healthcare professional, e.g. 'Dr. Sharma'")
        hospital: Optional[str] = Field(None, description="Hospital or clinic name")
        specialty: Optional[str] = Field(None, description="HCP's medical specialty")
        interaction_type: Optional[str] = Field(
            "Meeting", description="Type of interaction: Meeting, Call, Email, Conference, Virtual"
        )
        interaction_date: Optional[str] = Field(
            None, description="Date of the interaction in natural language, e.g. 'today', 'April 19 2025'"
        )
        interaction_time: Optional[str] = Field(None, description="Time of interaction, e.g. '3:30 PM'")
        attendees: Optional[List[str]] = Field(None, description="Names of people who attended")
        topics_discussed: Optional[str] = Field(None, description="Key discussion points / what was discussed")
        sentiment: Optional[str] = Field(
            None, description="Overall sentiment of the meeting: Positive, Neutral, or Negative"
        )
        materials_shared: Optional[List[str]] = Field(
            None, description="Materials or samples shared, e.g. ['Brochure', 'Sample Pack']"
        )
        follow_up_actions: Optional[str] = Field(None, description="Follow-up actions agreed upon")
        follow_up_date: Optional[str] = Field(None, description="Follow-up date in natural language")
        notes: Optional[str] = Field(None, description="Any additional freeform notes")

    @tool("log_interaction", args_schema=LogInteractionArgs)
    def log_interaction(
        hcp_name: str,
        hospital: Optional[str] = None,
        specialty: Optional[str] = None,
        interaction_type: Optional[str] = "Meeting",
        interaction_date: Optional[str] = None,
        interaction_time: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        topics_discussed: Optional[str] = None,
        sentiment: Optional[str] = None,
        materials_shared: Optional[List[str]] = None,
        follow_up_actions: Optional[str] = None,
        follow_up_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Log a brand new HCP interaction. Use this the FIRST time a rep describes a
        meeting/call/email that hasn't been saved yet. Extract every field you can from
        their message; leave a field out if it wasn't mentioned. This tool also runs the
        LLM to auto-generate a summary, key points, extracted entities, and suggested
        next steps, then stores everything and populates the left-hand form."""

        hcp = db.query(HCP).filter(HCP.name.ilike(hcp_name)).first()
        if not hcp:
            hcp = HCP(name=hcp_name, hospital=hospital, specialty=specialty)
            db.add(hcp)
            db.flush()
        else:
            hcp.hospital = hospital or hcp.hospital
            hcp.specialty = specialty or hcp.specialty

        enrichment = _enrich_with_llm(topics_discussed, notes, sentiment)

        interaction = Interaction(
            hcp_id=hcp.id,
            hcp_name=hcp_name,
            hospital=hospital or hcp.hospital,
            specialty=specialty or hcp.specialty,
            interaction_type=interaction_type or "Meeting",
            interaction_date=_parse_date(interaction_date) or dt.date.today(),
            interaction_time=_parse_time(interaction_time),
            attendees=attendees or [],
            topics_discussed=topics_discussed,
            sentiment=sentiment,
            materials_shared=materials_shared or [],
            follow_up_actions=follow_up_actions,
            follow_up_date=_parse_date(follow_up_date),
            notes=notes,
            summary=enrichment.get("summary"),
            key_points=enrichment.get("key_points", []),
            entities=enrichment.get("entities", {}),
            suggested_next_steps=enrichment.get("suggested_next_steps", []),
            meeting_outcome=enrichment.get("meeting_outcome"),
            status="Logged",
            session_id=session_id,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        set_last_interaction(session_id, interaction.id)

        result = {
            "action": "logged",
            "interaction_id": interaction.id,
            "form_update": _interaction_to_form_dict(interaction),
            "message": f"Logged interaction with {hcp_name}.",
        }
        return json.dumps(result, default=str)

    class EditInteractionArgs(BaseModel):
        interaction_id: Optional[int] = Field(
            None, description="ID of the interaction to edit. Omit to edit the most recently logged one in this session."
        )
        hcp_name: Optional[str] = Field(None, description="Corrected HCP name")
        hospital: Optional[str] = Field(None)
        specialty: Optional[str] = Field(None)
        interaction_type: Optional[str] = Field(None)
        interaction_date: Optional[str] = Field(None)
        interaction_time: Optional[str] = Field(None)
        attendees: Optional[List[str]] = Field(None)
        topics_discussed: Optional[str] = Field(None)
        sentiment: Optional[str] = Field(None)
        materials_shared: Optional[List[str]] = Field(None)
        follow_up_actions: Optional[str] = Field(None)
        follow_up_date: Optional[str] = Field(None)
        notes: Optional[str] = Field(None)

    @tool("edit_interaction", args_schema=EditInteractionArgs)
    def edit_interaction(
        interaction_id: Optional[int] = None,
        hcp_name: Optional[str] = None,
        hospital: Optional[str] = None,
        specialty: Optional[str] = None,
        interaction_type: Optional[str] = None,
        interaction_date: Optional[str] = None,
        interaction_time: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        topics_discussed: Optional[str] = None,
        sentiment: Optional[str] = None,
        materials_shared: Optional[List[str]] = None,
        follow_up_actions: Optional[str] = None,
        follow_up_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Correct or update fields on an ALREADY LOGGED interaction. Use this when the
        rep says something was wrong or wants to change/add details, e.g. 'actually his
        name is Dr. John' or 'the sentiment was negative, not positive'. Only pass the
        fields that changed - everything else is left untouched. If no interaction_id is
        given, the most recently logged interaction in this conversation is updated."""

        target_id = interaction_id or get_session(session_id).get("last_interaction_id")
        if not target_id:
            return json.dumps({
                "action": "error",
                "message": "There's no interaction logged yet in this conversation to edit. Please log one first.",
            })

        interaction = db.query(Interaction).filter(Interaction.id == target_id).first()
        if not interaction:
            return json.dumps({"action": "error", "message": f"No interaction found with id {target_id}."})

        changed = {}
        field_map = {
            "hcp_name": hcp_name,
            "hospital": hospital,
            "specialty": specialty,
            "interaction_type": interaction_type,
            "topics_discussed": topics_discussed,
            "sentiment": sentiment,
            "follow_up_actions": follow_up_actions,
            "notes": notes,
        }
        for field, value in field_map.items():
            if value is not None:
                setattr(interaction, field, value)
                changed[field] = value

        if attendees is not None:
            interaction.attendees = attendees
            changed["attendees"] = attendees
        if materials_shared is not None:
            interaction.materials_shared = materials_shared
            changed["materials_shared"] = materials_shared
        if interaction_date is not None:
            interaction.interaction_date = _parse_date(interaction_date)
            changed["interaction_date"] = interaction_date
        if interaction_time is not None:
            interaction.interaction_time = _parse_time(interaction_time)
            changed["interaction_time"] = interaction_time
        if follow_up_date is not None:
            interaction.follow_up_date = _parse_date(follow_up_date)
            changed["follow_up_date"] = follow_up_date

        # re-run enrichment if the substantive text changed
        if topics_discussed is not None or notes is not None or sentiment is not None:
            enrichment = _enrich_with_llm(
                interaction.topics_discussed, interaction.notes, interaction.sentiment
            )
            if enrichment:
                interaction.summary = enrichment.get("summary", interaction.summary)
                interaction.key_points = enrichment.get("key_points", interaction.key_points)
                interaction.entities = enrichment.get("entities", interaction.entities)
                interaction.suggested_next_steps = enrichment.get(
                    "suggested_next_steps", interaction.suggested_next_steps
                )
                interaction.meeting_outcome = enrichment.get("meeting_outcome", interaction.meeting_outcome)

        db.commit()
        db.refresh(interaction)
        set_last_interaction(session_id, interaction.id)

        result = {
            "action": "edited",
            "interaction_id": interaction.id,
            "changed_fields": list(changed.keys()),
            "form_update": _interaction_to_form_dict(interaction),
            "message": f"Updated {', '.join(changed.keys()) if changed else 'the interaction'}.",
        }
        return json.dumps(result, default=str)

    class ViewHistoryArgs(BaseModel):
        hcp_name: Optional[str] = Field(None, description="Filter history to a specific HCP name")
        limit: Optional[int] = Field(5, description="Max number of past interactions to return")

    @tool("view_interaction_history", args_schema=ViewHistoryArgs)
    def view_interaction_history(hcp_name: Optional[str] = None, limit: Optional[int] = 5) -> str:
        """View past logged interactions, optionally filtered to one HCP. Use this when
        the rep asks things like 'what did we discuss with Dr. Sharma last time' or
        'show my recent interactions'."""
        q = db.query(Interaction).order_by(Interaction.created_at.desc())
        if hcp_name:
            q = q.filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
        rows = q.limit(limit or 5).all()
        items = [_interaction_to_form_dict(r) for r in rows]
        result = {
            "action": "history",
            "message": f"Found {len(items)} interaction(s)." if items else "No past interactions found.",
            "data": {"interactions": items},
        }
        return json.dumps(result, default=str)

    class SearchHCPArgs(BaseModel):
        query: str = Field(..., description="Name, hospital, or specialty to search for")

    @tool("search_hcp", args_schema=SearchHCPArgs)
    def search_hcp(query: str) -> str:
        """Search HCP records by name, hospital, or specialty. Use this when the rep is
        looking up a doctor or wants to check if an HCP already exists in the system."""
        like = f"%{query}%"
        rows = (
            db.query(HCP)
            .filter((HCP.name.ilike(like)) | (HCP.hospital.ilike(like)) | (HCP.specialty.ilike(like)))
            .limit(10)
            .all()
        )
        items = [
            {"id": h.id, "name": h.name, "hospital": h.hospital, "specialty": h.specialty}
            for h in rows
        ]
        result = {
            "action": "search_hcp",
            "message": f"Found {len(items)} matching HCP(s)." if items else "No matching HCPs found.",
            "data": {"hcps": items},
        }
        return json.dumps(result, default=str)

    class FollowUpSuggestionsArgs(BaseModel):
        interaction_id: Optional[int] = Field(
            None, description="Interaction to generate suggestions for. Defaults to the most recent one."
        )

    @tool("generate_followup_suggestions", args_schema=FollowUpSuggestionsArgs)
    def generate_followup_suggestions(interaction_id: Optional[int] = None) -> str:
        """Use the LLM to generate smart follow-up / next-best-action suggestions for a
        logged interaction. Use this when the rep asks 'what should I do next' or 'give
        me follow-up ideas'."""
        target_id = interaction_id or get_session(session_id).get("last_interaction_id")
        interaction = db.query(Interaction).filter(Interaction.id == target_id).first()
        if not interaction:
            return json.dumps({"action": "error", "message": "No interaction found to generate suggestions for."})

        llm = get_llm(temperature=0.4)
        prompt = f"""You are a pharma sales strategy assistant. Given this HCP interaction,
suggest 3-5 concrete next-best-actions for the field rep. Return ONLY a JSON array of short strings.

HCP: {interaction.hcp_name}, {interaction.specialty or "unknown specialty"}
Sentiment: {interaction.sentiment}
Topics discussed: {interaction.topics_discussed}
Notes: {interaction.notes}
Existing follow-up actions: {interaction.follow_up_actions}
"""
        try:
            resp = llm.invoke(prompt)
            content = resp.content.strip().strip("`")
            if content.lower().startswith("json"):
                content = content[4:]
            suggestions = json.loads(content)
        except Exception:
            suggestions = ["Schedule a follow-up call within 2 weeks", "Share requested clinical studies"]

        interaction.suggested_next_steps = suggestions
        db.commit()
        db.refresh(interaction)

        result = {
            "action": "followup_suggestions",
            "interaction_id": interaction.id,
            "form_update": {"suggestedNextSteps": suggestions},
            "message": "Here are some suggested next steps.",
            "data": {"suggestions": suggestions},
        }
        return json.dumps(result, default=str)

    class ScheduleFollowUpArgs(BaseModel):
        interaction_id: Optional[int] = Field(None, description="Interaction this follow-up relates to")
        follow_up_date: str = Field(..., description="When the follow-up should happen, natural language ok")
        description: Optional[str] = Field(None, description="What the follow-up visit/call is about")

    @tool("schedule_followup_visit", args_schema=ScheduleFollowUpArgs)
    def schedule_followup_visit(
        follow_up_date: str, interaction_id: Optional[int] = None, description: Optional[str] = None
    ) -> str:
        """Create a scheduled follow-up task/visit tied to an interaction, e.g. 'schedule
        a follow-up meeting next Tuesday' or 'remind me to call him back in 2 weeks'."""
        target_id = interaction_id or get_session(session_id).get("last_interaction_id")
        interaction = db.query(Interaction).filter(Interaction.id == target_id).first()
        if not interaction:
            return json.dumps({"action": "error", "message": "No interaction found to schedule a follow-up for."})

        parsed_date = _parse_date(follow_up_date)
        task = FollowUpTask(
            interaction_id=interaction.id,
            description=description or f"Follow-up with {interaction.hcp_name}",
            due_date=parsed_date,
            status="Pending",
        )
        db.add(task)
        interaction.follow_up_date = parsed_date
        if description:
            interaction.follow_up_actions = description
        db.commit()
        db.refresh(interaction)

        result = {
            "action": "scheduled_followup",
            "interaction_id": interaction.id,
            "form_update": {
                "followUpDate": parsed_date.isoformat() if parsed_date else None,
                "followUpActions": interaction.follow_up_actions,
            },
            "message": f"Scheduled a follow-up for {parsed_date.isoformat() if parsed_date else follow_up_date}.",
        }
        return json.dumps(result, default=str)

    tools = [
        log_interaction,
        edit_interaction,
        view_interaction_history,
        search_hcp,
        generate_followup_suggestions,
        schedule_followup_visit,
    ]
    return tools, db
