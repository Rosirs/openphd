# PhD-Agent

A pluggable multi-agent system that helps global PhD applicants research,
write, and email on the same surface. The LLM is the front door: it calls
atomic backend tools (`arxiv_search`, `writing_polisher`, `email_drafter`,
…) and you can assemble new tools in the Canvas tab that the LLM calls
like any other.

## What's inside

- **Chat** — a single chat surface where the LLM calls tools to answer.
- **Canvas** — chain atomic tools into a pipeline, save it as a composite
  tool that runs its own LLM loop.
- **Backend** — FastAPI with a `ToolRuntime` loop, a `CompositeAgent`
  sub-loop, an `AgentWrapper` sandbox, and per-user JSON persistence.

The frontend ships with a "research desk" visual identity — warm ink
background, parchment text, a brass highlighter bar that pulses on the
left edge of the chat while a tool is running, and a serif page-number
anchor on every message bubble.

## Architecture

```
┌─ Frontend (React + Vite) ────────────────────────────────┐
│  Chat                  Canvas                            │
│  free-form LLM         chain atomic tools                │
│  tool-call markers     save as composite tool            │
│  SSE streaming         preview augmented prompt          │
└──────────────────────────────────────────────────────────┘
                       │ REST + SSE
┌─ Backend (FastAPI) ──────────────────────────────────────┐
│  /chat/*   /tools/*   /canvas/*   /onboard/*   /health   │
│                                                          │
│  ToolRuntime    — top-level LLM + tool-call loop         │
│  CompositeAgent — nested LLM loop (composite tools)      │
│  AgentWrapper   — sandboxed atomic tool execution        │
│  JsonFileRepository — per-user persistence              │
└──────────────────────────────────────────────────────────┘
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Optional: real LLM via any OpenAI-compatible endpoint
export OPENAI_API_KEY=sk-...
export LLM_BACKEND=openai               # default: mock
export LLM_MODEL=gpt-4o-mini           # default
export DATA_DIR=./data                  # default

uvicorn phd_agent.main:app --reload     # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                             # http://localhost:4018
```

The frontend dev server proxies `/api`, `/chat`, `/tools`, `/canvas`,
`/onboard`, `/pipelines`, and `/health` to the backend on `:8000`.

## Default flow

1. **Chat tab** (default) — ask anything. The LLM calls backend tools to
   answer. Examples: "find me 3 recent ML papers", "draft an email to
   Prof X about my research".
2. **Canvas tab** — click `arxiv_search` + `writing_polisher`, "Save as
   my tool", fill in a system prompt. The composite tool is now visible
   in `/tools/catalog`.
3. **Back to Chat** — "use my_finder on the latest papers". The LLM
   calls your composite tool, its sub-LLM runs the sub-pipeline, the
   result bubbles back into the chat.

## Plugins shipped

| Tool                  | Category  | Backend                            |
|-----------------------|-----------|------------------------------------|
| `arxiv_search`        | academic  | arXiv API (real)                   |
| `knowledge_retriever` | academic  | dispatcher (default: arxiv)        |
| `writing_polisher`    | writing   | LLM                                |
| `email_drafter`       | writing   | LLM                                |
| `pdf_summarizer`      | writing   | LLM                                |
| `mock_echo`           | mock      | in-process                         |
| `mock_logger`         | mock      | in-process                         |

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET`    | `/health` | health check |
| `GET`    | `/tools/catalog?user_id=` | list atomic + composite tools |
| `GET`    | `/tools/{id}?user_id=` | tool details |
| `POST`   | `/chat/conversations` | create conversation |
| `GET`    | `/chat/conversations?user_id=` | list user's conversations |
| `GET`    | `/chat/conversations/{id}?user_id=` | read conversation |
| `DELETE` | `/chat/conversations/{id}?user_id=` | delete conversation |
| `POST`   | `/chat/conversations/{id}/messages?user_id=` | send message (SSE stream) |
| `POST`   | `/canvas/preview-prompt` | preview augmented system_prompt |
| `POST`   | `/canvas/composite?user_id=` | save composite tool |
| `DELETE` | `/canvas/composite/{id}?user_id=` | delete composite tool |
| `GET`    | `/canvas/composites?user_id=` | list user's composite tools |
| `GET`    | `/onboard/status` | LLM profile + supported providers |
| `POST`   | `/onboard/test` | test connection with a candidate profile |
| `POST`   | `/onboard/save` | save profile |
| `POST`   | `/onboard/skip` | skip onboard (use mock LLM) |

## SSE event types (chat stream)

- `message_received` — user message saved
- `tool_call_started` — LLM decided to call a tool
- `tool_call_completed` — tool execution finished
- `tool_call_skipped` — `max_tool_calls` exceeded
- `sub_iter` / `sub_call` / `sub_call_done` — composite sub-LLM trace
- `turn_continued` — sub-tool done, LLM will continue
- `message_completed` — LLM gave final text
- `error` — exception (LLM will recover if possible)

## Tests

```bash
# Backend
cd backend && source .venv/bin/activate
pytest tests/ -v                         # pytest suite, all green

# Frontend
cd frontend
npm test -- --run                        # vitest, all green
npm run build                            # TypeScript + Vite
```

## Configuration (env vars)

| Var              | Default         | Description                                          |
|------------------|-----------------|------------------------------------------------------|
| `LLM_BACKEND`    | `mock`          | `mock` or `openai` (any OpenAI-compatible endpoint)  |
| `LLM_MODEL`      | `gpt-4o-mini`   | model name sent to the LLM                          |
| `OPENAI_BASE_URL`| OpenAI default  | API endpoint                                         |
| `OPENAI_API_KEY` | (empty)         | API key                                              |
| `DATA_DIR`       | `./data`        | per-user JSON persistence                           |

If `OPENAI_API_KEY` is empty, the system uses `MockLLMClient` (returns
canned responses) so the app runs end-to-end with no real API. You can
wire up a real key from the gear icon in the header — supported
providers include OpenAI, DeepSeek, Moonshot, MiniMax, Anthropic, plus
any custom OpenAI-compatible endpoint.

## Project layout

```
backend/                FastAPI service
  src/phd_agent/        main, config, core (tool_runtime, composite_agent, …)
  tests/                pytest suite
frontend/               React + Vite UI
  src/chat/             Chat tab
  src/canvas/           Canvas (tool builder) tab
  src/onboard/          LLM setup modals
  src/api/              typed API client
docs/                   PRD + specs + plans
```

## Docs

- PRD: `docs/PRD.md`
- Spec: `docs/superpowers/specs/2026-06-25-phd-agent-v2-phase2-design.md`
- Plan: `docs/superpowers/plans/2026-06-25-phd-agent-v2-phase2.md`
