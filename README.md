# PhD-Agent (V2.0.0)

Pluggable multi-agent system for global PhD applicants.

The LLM is the front door. Backend agents are LLM-callable tools. The Canvas tab is a
custom-tool builder — drag atomic tools to compose a "composite tool" that runs its
own LLM loop, then the LLM in Chat can call it like any other tool.

## Architecture (Phase 2)

```
┌─ Frontend (React) ─────────────────────────────────────┐
│  Chat tab (default)        Canvas tab                  │
│  - free-form LLM chat      - drag atomic tools         │
│  - tool-call indicators    - save as composite tool    │
│  - SSE streaming           - preview augmented prompt  │
└─────────────────────────────────────────────────────────┘
                       │ REST + SSE
┌─ Backend (FastAPI) ────────────────────────────────────┐
│  /chat/*   /tools/*   /canvas/*   /health              │
│                                                         │
│  ToolRuntime   — top-level LLM + tool-call loop        │
│  CompositeAgent — nested LLM loop (composite tools)    │
│  AgentWrapper  — sandboxed atomic tool execution       │
│  JsonFileRepository — per-user persistence             │
└─────────────────────────────────────────────────────────┘
```

## Quick start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Optional: real LLM via OpenAI-compatible API (e.g. MiniMax-m3)
export OPENAI_API_KEY=sk-...
export LLM_BACKEND=openai   # default: mock
export LLM_MODEL=MiniMax-m3
export DATA_DIR=./data      # default: ./data

uvicorn phd_agent.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:4018.

## Default flow

1. **Chat tab** (default): ask anything. The LLM calls backend tools to answer.
   Examples: "find me 3 recent ML papers", "draft an email to Prof X about my research".
2. **Canvas tab**: drag `arxiv_search` + `writing_polisher`, click "Save as my tool",
   fill in a system prompt. The composite tool is now visible in `/tools/catalog`.
3. **Back to Chat**: "use my_finder on the latest papers". The LLM calls your
   composite tool → its sub-LLM runs the sub-pipeline → returns the result.

## Plugins shipped

| Tool | Category | Backend |
|------|----------|---------|
| `arxiv_search` | academic | arXiv API (real) |
| `knowledge_retriever` | academic | dispatcher (default: arxiv) |
| `writing_polisher` | writing | LLM (Phase 2 stub, Phase 3 real call) |
| `email_drafter` | writing | LLM (stub) |
| `pdf_summarizer` | writing | LLM (stub) |
| `mock_echo` | mock | in-process |
| `mock_logger` | mock | in-process |

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | health check |
| `GET` | `/tools/catalog?user_id=` | list atomic + composite tools |
| `GET` | `/tools/{id}?user_id=` | tool details |
| `POST` | `/chat/conversations` | create conversation |
| `GET` | `/chat/conversations?user_id=` | list user's conversations |
| `GET` | `/chat/conversations/{id}?user_id=` | read conversation |
| `DELETE` | `/chat/conversations/{id}?user_id=` | delete |
| `POST` | `/chat/conversations/{id}/messages?user_id=` | send message (SSE stream) |
| `POST` | `/canvas/preview-prompt` | preview augmented system_prompt |
| `POST` | `/canvas/composite?user_id=` | save composite tool |
| `DELETE` | `/canvas/composite/{id}?user_id=` | delete composite tool |
| `GET` | `/canvas/composites?user_id=` | list user's composite tools |

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
pytest tests/ -v                       # 55+ tests, all green
pytest tests/test_api.py -v            # API integration tests

# Frontend
cd frontend
npm test -- --run                      # Vitest
npm run build                          # TypeScript + Vite
```

## Docs

- Spec: `docs/superpowers/specs/2026-06-25-phd-agent-v2-phase2-design.md`
- Plan: `docs/superpowers/plans/2026-06-25-phd-agent-v2-phase2.md`
- Original PRD: `docs/PRD.md`

## Configuration (env vars)

| Var | Default | Description |
|-----|---------|-------------|
| `LLM_BACKEND` | `mock` | `mock` or `openai` |
| `LLM_MODEL` | `MiniMax-m3` | LLM model name |
| `OPENAI_BASE_URL` | OpenAI default | API endpoint |
| `OPENAI_API_KEY` | (empty) | API key |
| `DATA_DIR` | `./data` | Per-user JSON persistence |

If `OPENAI_API_KEY` is empty, the system uses `MockLLMClient` (returns canned
responses) so the app runs end-to-end with no real API.
