# PhD-Agent (V2.0.0)

Pluggable multi-agent system for global PhD applicants.

## Structure
- `backend/` — Python + FastAPI
- `frontend/` — React + TypeScript + Vite
- `docs/` — Specs, plans, fixtures

## Quick start (skeleton phase)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn phd_agent.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Docs
- Spec: `docs/superpowers/specs/2026-06-25-phd-agent-v2-skeleton-design.md`
- Plan: `docs/superpowers/plans/2026-06-25-phd-agent-v2-skeleton.md`
