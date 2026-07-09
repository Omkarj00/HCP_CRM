# AI-First CRM — HCP Interaction Module

![AI-First CRM Dashboard](assets/dashboard-screenshot.png)

An AI-first CRM screen for pharmaceutical field reps. The rep never fills the
structured form by hand — they describe the visit (or a correction to it) in
plain English to the **AI Assistant**, and a **LangGraph agent** backed by
**Groq (`gemma2-9b-it`)** decides which tool to run, extracts the structured
data, and writes it straight into the form on the left.

```
"Met Dr. Sharma today. Discussed our diabetes medication.
 He requested additional clinical studies and asked for a
 follow-up meeting next Tuesday."
                    │
                    ▼
        LangGraph agent (Groq LLM) ──► log_interaction tool
                    │
                    ▼
        Form auto-fills: HCP Name, Date, Sentiment,
        Topics, Follow-up date, AI Summary, Key Points...
```

## Screenshot referencea

The layout mirrors the provided mock: a two-column "Log HCP Interaction"
screen — structured form on the left, ChatGPT-style AI Assistant on the
right — plus a sidebar and an Interaction History timeline.

## Architecture

```
frontend/            React 19 + Redux Toolkit (Vite)
  src/components/     InteractionForm, ChatPanel, HistoryView, Sidebar
  src/store/          interactionSlice, chatSlice, historySlice
  src/api/client.js   talks to the FastAPI backend

backend/              FastAPI
  app/main.py          app entrypoint, CORS, table creation
  app/routers/         /api/chat, /api/interactions, /api/hcps
  app/agent/
    graph.py            LangGraph react-agent (system prompt + tool loop)
    tools.py            6 LangGraph tools (see below)
    llm.py               Groq client factory (gemma2-9b-it)
    session_store.py    in-memory session -> last-interaction-id map
  app/models.py         SQLAlchemy models (HCP, Interaction, FollowUpTask)
```

### Request flow

1. Rep types a message in the chat panel → `POST /api/chat`.
2. `run_agent()` builds a fresh set of LangGraph tools bound to the caller's
   `session_id`, and hands them + the message to a
   `langgraph.prebuilt.create_react_agent` running on Groq.
3. The agent decides (via tool-calling) which tool fits the intent, calls it.
4. The tool reads/writes Postgres via SQLAlchemy, optionally calls the LLM a
   second time to summarize/extract entities, and returns a JSON string
   containing a `form_update` (only the fields that changed) plus a
   human-readable `message`.
5. The API layer collects every tool's `form_update`/`data` and the agent's
   final natural-language reply, and returns them together.
6. The frontend merges `form_update` into Redux (`interactionSlice`), which
   flashes the newly-changed fields with a small "AI" badge, and appends the
   reply to the chat transcript.

The rep **can** also edit fields by hand (per the assignment's UX note) — manual
edits are tracked with a "Save changes" button that calls `PUT
/api/interactions/{id}` directly, bypassing the agent.

### LangGraph tools (6 total — 2 mandatory + 4 more)

| Tool | Purpose |
|---|---|
| `log_interaction` | **(mandatory)** Create a brand-new interaction from freeform text. Runs a second LLM pass to generate `summary`, `key_points`, `entities`, `suggested_next_steps`, `meeting_outcome`. |
| `edit_interaction` | **(mandatory)** Patch specific fields on the most recent (or a named) interaction — "actually his name is Dr. John". |
| `view_interaction_history` | List past interactions, optionally filtered by HCP name. |
| `search_hcp` | Look up HCPs by name / hospital / specialty. |
| `generate_followup_suggestions` | LLM call that proposes 3–5 next-best-actions for an interaction. |
| `schedule_followup_visit` | Creates a `FollowUpTask` row and sets the interaction's follow-up date. |

## Tech stack

- **Frontend**: React 19, Redux Toolkit, Vite, lucide-react icons, Inter font
- **Backend**: Python, FastAPI
- **Agent framework**: LangGraph (`create_react_agent`) + LangChain tool-calling
- **LLM**: Groq — `gemma2-9b-it` (required), `llama-3.3-70b-versatile` (optional, swap via `GROQ_MODEL`)
- **Database**: PostgreSQL (SQLAlchemy ORM)

## Setup

### 1. Database

```bash
docker compose up -d          # starts Postgres on localhost:5432
```

(No Docker? Point `DATABASE_URL` at any Postgres/MySQL instance you have, or
even a local `sqlite:///./dev.db` for quick manual testing — the ORM code is
database-agnostic.)

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your Groq API key (https://console.groq.com/keys)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev          # http://localhost:5173
```

Open `http://localhost:5173`, go to **Log Interaction**, and talk to the AI
Assistant on the right.

## Environment variables

**`backend/.env`**

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | *(required)* |
| `GROQ_MODEL` | Model id used by the agent | `gemma2-9b-it` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg2://hcp_user:hcp_password@localhost:5432/hcp_crm` |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |

**`frontend/.env`**

| Variable | Description | Default |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend | `http://localhost:8000` |


