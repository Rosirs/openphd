# PhD-Agent V2.0.0 Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a runnable V2.0.0 architecture skeleton: backend boots, frontend loads, user can drag two mock Agent cards, see green validation lines, hit Run, and watch a mock pipeline execute with streamed logs.

**Architecture:** Python + FastAPI backend with importlib-based plugin isolation, custom CentralRouter that dispatches a single GlobalState through an AgentWrapper. React + React Flow frontend with TS mirror of the backend contract-validation algorithm for instant client-side feedback. Both layers share the same JSON catalog of Agent contracts.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pytest, importlib. TypeScript 5+, React 18, Vite, React Flow, Vitest.

## Global Constraints

These apply to every task below:

- **Spec:** `docs/superpowers/specs/2026-06-25-phd-agent-v2-skeleton-design.md` — implementer MUST read §4 (backend), §5 (frontend), §7 (plugin contract), §10 (DoD), §11 (testing), and Appendix B (engineering rules) before starting.
- **Python file size:** ≤ 250 lines per file (Appendix B).
- **TS/TSX file size:** ≤ 200 lines per file (Appendix B).
- **No over-engineering (Appendix B):** No redundant try/except fallbacks; let errors throw at appropriate places; no meaningless type assertions; no duplicate logging; prefer modern syntax (PEP 604 unions, structural pattern matching).
- **TDD discipline:** Write the failing test FIRST; verify it fails; implement minimal code; verify pass; commit. (Per spec §11.)
- **Frequent commits:** Every task ends with `git commit`. Repo is not yet initialized — Task 1 includes `git init`.
- **No placeholders:** Every code block contains the real code the implementer should write.
- **Test fixtures:** `docs/superpowers/specs/fixtures/pipelines.json` is the single source of truth for pipeline test cases; backend (pytest) and frontend (Vitest) both consume it.

---

## File Structure

Files this plan creates or touches. Each file has one responsibility; sizes stay under the global constraints.

### Root
- `README.md` — project entry, how to run dev
- `.gitignore` — Python + Node ignores
- `docs/superpowers/specs/fixtures/pipelines.json` — shared pipeline test fixtures

### Backend (`backend/`)
- `pyproject.toml` — deps + tool config
- `src/phd_agent/__init__.py` — package marker
- `src/phd_agent/main.py` — FastAPI app factory + startup wiring
- `src/phd_agent/core/__init__.py`
- `src/phd_agent/core/state.py` — `GlobalState` Pydantic model
- `src/phd_agent/core/contract.py` — `AgentContract` + `BaseAgent` ABC
- `src/phd_agent/core/repository.py` — `IStateRepository` + `InMemoryRepository`
- `src/phd_agent/core/validator.py` — `validate_pipeline()` pure function
- `src/phd_agent/core/registry.py` — `AgentRegistry` (scan + lazy load)
- `src/phd_agent/core/router.py` — `CentralRouter`
- `src/phd_agent/core/wrapper.py` — `AgentWrapper` (try/except + token guard)
- `src/phd_agent/core/events.py` — `EventBus` (async pub/sub for SSE)
- `src/phd_agent/llm/__init__.py`
- `src/phd_agent/llm/base.py` — `BaseLLMClient` + `LLMResponse`
- `src/phd_agent/llm/openai_compat.py` — `OpenAICompatClient`
- `src/phd_agent/llm/budget.py` — `TokenGuardrail`
- `src/phd_agent/plugins/__init__.py`
- `src/phd_agent/plugins/_base.py` — `BaseAgent` re-export (kept thin per spec §4.4)
- `src/phd_agent/plugins/mock_echo/__init__.py`
- `src/phd_agent/plugins/mock_echo/agent.py` — `MockEchoAgent`
- `src/phd_agent/plugins/mock_echo/contract.json`
- `src/phd_agent/plugins/mock_logger/__init__.py`
- `src/phd_agent/plugins/mock_logger/agent.py` — `MockLoggerAgent`
- `src/phd_agent/plugins/mock_logger/contract.json`
- `src/phd_agent/orchestrator.py` — `PipelineOrchestrator` (composes Validator+Registry+Router+Wrapper+EventBus)
- `src/phd_agent/api/__init__.py`
- `src/phd_agent/api/schemas.py` — request/response Pydantic models
- `src/phd_agent/api/agents.py` — `GET /agents/catalog`
- `src/phd_agent/api/pipelines.py` — `POST /pipelines/validate`, `/pipelines/run`, `GET /pipelines/{id}/events`
- `tests/__init__.py`
- `tests/conftest.py` — pytest fixtures
- `tests/test_state.py`
- `tests/test_contract.py`
- `tests/test_repository.py`
- `tests/test_validator.py`
- `tests/test_registry.py`
- `tests/test_router.py`
- `tests/test_wrapper.py`
- `tests/test_events.py`
- `tests/test_orchestrator.py`
- `tests/test_api.py`

### Frontend (`frontend/`)
- `package.json`
- `tsconfig.json`
- `vite.config.ts`
- `vitest.config.ts`
- `index.html`
- `src/main.tsx`
- `src/App.tsx`
- `src/api/client.ts`
- `src/api/types.ts`
- `src/validator/contract.ts`
- `src/validator/validate.ts`
- `src/validator/validate.test.ts`
- `src/validator/fixtures.ts` — loads shared `pipelines.json` for tests
- `src/shelf/AgentShelf.tsx`
- `src/shelf/AgentCard.tsx`
- `src/canvas/FlowCanvas.tsx`
- `src/canvas/AgentNode.tsx`
- `src/canvas/DependencyEdge.tsx`
- `src/canvas/usePipelineValidation.ts`
- `src/workspace/WorkspaceRoot.tsx`
- `src/workspace/PipelineRunLog.tsx`
- `src/workspace/MockWidget.tsx`

---

## Task 1: Project Bootstrap

**Files:**
- Create: `README.md`, `.gitignore`, `backend/pyproject.toml`, `backend/src/phd_agent/__init__.py`, `backend/src/phd_agent/main.py` (stub), `backend/tests/__init__.py`, `backend/tests/conftest.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: runnable `python -c "import phd_agent"` + `pytest` finds `tests/`

- [ ] **Step 1: Initialize git repo at project root**

Run from `/home/robin/Documents/Ryan/PhD/openphd/`:
```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git init
git config user.email "phd-agent@example.com"
git config user.name "PhD-Agent Dev"
```

- [ ] **Step 2: Create `.gitignore`**

Write `/home/robin/Documents/Ryan/PhD/openphd/.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
.venv/
dist/
build/
*.egg-info/

node_modules/
dist/
.vite/
coverage/

.DS_Store
*.swp
*.swo
.idea/
.vscode/

# Runtime data
data/
```

- [ ] **Step 3: Create root `README.md`**

Write `/home/robin/Documents/Ryan/PhD/openphd/README.md`:
```markdown
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
```

- [ ] **Step 4: Create `backend/pyproject.toml`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/pyproject.toml`:
```toml
[project]
name = "phd-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.6",
    "httpx>=0.27",  # for OpenAI compat calls + TestClient
    "sse-starlette>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/phd_agent"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.pyright]
include = ["src"]
```

- [ ] **Step 5: Create package skeleton**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/__init__.py`:
```python
"""PhD-Agent V2.0.0 — pluggable multi-agent system."""
__version__ = "0.1.0"
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/main.py`:
```python
"""FastAPI app entry point (stub; populated by Task 13)."""
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="PhD-Agent", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app

app = create_app()
```

- [ ] **Step 6: Create test skeleton**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/conftest.py`:
```python
"""Shared pytest fixtures."""
import pytest
from pathlib import Path

@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_smoke.py`:
```python
"""Smoke tests to verify package imports."""
def test_package_imports():
    import phd_agent
    assert phd_agent.__version__ == "0.1.0"

def test_health_endpoint():
    from fastapi.testclient import TestClient
    from phd_agent.main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
```

- [ ] **Step 7: Install backend deps and verify tests pass**

Run:
```bash
cd /home/robin/Documents/Ryan/PhD/openphd/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```
Expected: `2 passed`.

- [ ] **Step 8: Commit**

```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git add .
git commit -m "chore: bootstrap project structure with FastAPI skeleton"
```

---

## Task 2: Core Types — GlobalState, AgentContract, BaseAgent

**Files:**
- Create: `backend/src/phd_agent/core/__init__.py`, `backend/src/phd_agent/core/state.py`, `backend/src/phd_agent/core/contract.py`, `backend/src/phd_agent/plugins/__init__.py`, `backend/src/phd_agent/plugins/_base.py`
- Test: `backend/tests/test_state.py`, `backend/tests/test_contract.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `GlobalState(user_id, user_background, active_pipeline, current_step, dynamic_storage, error_log, status)`
  - `AgentContract(agent_id, name, description, category, required_fields, output_fields, token_budget, isolation)`
  - `BaseAgent(contract: ClassVar[AgentContract], run(state) -> state)`

- [ ] **Step 1: Write failing test for `GlobalState`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_state.py`:
```python
from phd_agent.core.state import GlobalState

def test_globalstate_defaults():
    state = GlobalState(user_id="u1")
    assert state.user_id == "u1"
    assert state.user_background == {}
    assert state.active_pipeline == []
    assert state.current_step == 0
    assert state.dynamic_storage == {}
    assert state.error_log == []
    assert state.status == "idle"

def test_globalstate_status_literals():
    # Pydantic enforces Literal; an invalid status must raise
    import pytest
    with pytest.raises(ValueError):
        GlobalState(user_id="u1", status="nonsense")

def test_globalstate_dynamic_storage_isolated_per_instance():
    a = GlobalState(user_id="a")
    b = GlobalState(user_id="b")
    a.dynamic_storage["k"] = 1
    assert "k" not in b.dynamic_storage
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_state.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.state'`

- [ ] **Step 3: Implement `core/state.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/state.py`:
```python
"""Global state shared across all agents in a pipeline run."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["idle", "running", "partial", "completed", "failed"]

class GlobalState(BaseModel):
    user_id: str
    user_background: dict = Field(default_factory=dict)
    active_pipeline: list[str] = Field(default_factory=list)
    current_step: int = 0
    dynamic_storage: dict = Field(default_factory=dict)
    error_log: list[dict] = Field(default_factory=list)
    status: Status = "idle"
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_state.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Write failing test for `AgentContract` + `BaseAgent`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_contract.py`:
```python
from phd_agent.core.contract import AgentContract, BaseAgent
from phd_agent.core.state import GlobalState
import pytest

def test_agent_contract_minimal_valid():
    c = AgentContract(
        agent_id="mock_echo",
        name="Mock Echo",
        description="echoes input",
        category="mock",
        required_fields={"dynamic_storage.echo_input"},
        output_fields={"dynamic_storage.echo_output"},
    )
    assert c.agent_id == "mock_echo"
    assert c.token_budget == 4000  # default from spec
    assert c.isolation == "in_process"  # default

def test_agent_contract_serializes_to_json():
    c = AgentContract(
        agent_id="x", name="X", description="d", category="mock",
        required_fields={"a"}, output_fields={"b"},
    )
    j = c.model_dump_json()
    restored = AgentContract.model_validate_json(j)
    assert restored.agent_id == "x"

def test_base_agent_subclass_must_declare_contract():
    class Bad(BaseAgent):
        async def run(self, state):
            return state
    with pytest.raises(TypeError):
        Bad()  # contract is required

def test_base_agent_subclass_runs():
    class Echo(BaseAgent):
        contract = AgentContract(
            agent_id="e", name="E", description="d", category="mock",
            required_fields=set(), output_fields=set(),
        )
        async def run(self, state: GlobalState) -> GlobalState:
            state.dynamic_storage["ok"] = True
            return state
    a = Echo()
    state = GlobalState(user_id="u1")
    import asyncio
    asyncio.run(a.run(state))
    assert state.dynamic_storage["ok"] is True
```

- [ ] **Step 6: Run, verify failure**

Run: `cd backend && pytest tests/test_contract.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.contract'`

- [ ] **Step 7: Implement `core/contract.py` and `plugins/_base.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/contract.py`:
```python
"""Agent contract declaration (input/output schema + metadata)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import ClassVar, Literal
from pydantic import BaseModel

Category = Literal["academic", "writing", "admin", "mock"]
Isolation = Literal["in_process"]

class AgentContract(BaseModel):
    agent_id: str
    name: str
    description: str
    category: Category
    required_fields: set[str]
    output_fields: set[str]
    token_budget: int = 4000
    isolation: Isolation = "in_process"

class BaseAgent(ABC):
    """Abstract base class all plugins must subclass."""
    contract: ClassVar[AgentContract]

    @abstractmethod
    async def run(self, state) -> object:
        """Execute business logic; do not catch your own exceptions."""
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/__init__.py`:
```python
"""Plugins package — auto-scanned by AgentRegistry."""
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/_base.py`:
```python
"""Re-export BaseAgent for plugin authors. Kept thin per spec §4.4."""
from phd_agent.core.contract import BaseAgent

__all__ = ["BaseAgent"]
```

- [ ] **Step 8: Run, verify pass**

Run: `cd backend && pytest tests/test_state.py tests/test_contract.py -v`
Expected: `7 passed`.

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat(core): add GlobalState, AgentContract, BaseAgent"
```

---

## Task 3: IStateRepository + InMemoryRepository

**Files:**
- Create: `backend/src/phd_agent/core/repository.py`
- Test: `backend/tests/test_repository.py`

**Interfaces:**
- Consumes: `GlobalState` (from Task 2)
- Produces: `IStateRepository` ABC with `save`, `load`, `list_user_pipelines` (per spec §4.2: takes `user_id`, returns pipeline IDs); `InMemoryRepository` impl

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_repository.py`:
```python
import pytest
from phd_agent.core.repository import InMemoryRepository
from phd_agent.core.state import GlobalState

@pytest.mark.asyncio
async def test_save_and_load_round_trip():
    repo = InMemoryRepository()
    s = GlobalState(user_id="u1", active_pipeline=["a", "b"])
    await repo.save("u1", s)
    loaded = await repo.load("u1")
    assert loaded is not None
    assert loaded.active_pipeline == ["a", "b"]

@pytest.mark.asyncio
async def test_load_missing_user_returns_none():
    repo = InMemoryRepository()
    assert await repo.load("ghost") is None

@pytest.mark.asyncio
async def test_save_overwrites():
    repo = InMemoryRepository()
    await repo.save("u1", GlobalState(user_id="u1", active_pipeline=["a"]))
    await repo.save("u1", GlobalState(user_id="u1", active_pipeline=["a", "b"]))
    loaded = await repo.load("u1")
    assert loaded.active_pipeline == ["a", "b"]

@pytest.mark.asyncio
async def test_list_user_pipelines_returns_ids_for_user():
    repo = InMemoryRepository()
    await repo.save("u1", GlobalState(user_id="u1"))
    assert await repo.list_user_pipelines("u1") == ["default"]
    assert await repo.list_user_pipelines("ghost") == []  # per-user, per spec §4.2
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_repository.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.repository'`

- [ ] **Step 3: Implement `core/repository.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/repository.py`:
```python
"""Pluggable state persistence."""
from __future__ import annotations
from abc import ABC, abstractmethod
from phd_agent.core.state import GlobalState

class IStateRepository(ABC):
    @abstractmethod
    async def save(self, user_id: str, state: GlobalState) -> None: ...
    @abstractmethod
    async def load(self, user_id: str) -> GlobalState | None: ...
    @abstractmethod
    async def list_user_pipelines(self) -> list[str]: ...

class InMemoryRepository(IStateRepository):
    """Default impl; lost on process restart."""
    def __init__(self) -> None:
        self._store: dict[str, GlobalState] = {}

    async def save(self, user_id: str, state: GlobalState) -> None:
        self._store[user_id] = state.model_copy(deep=True)

    async def load(self, user_id: str) -> GlobalState | None:
        s = self._store.get(user_id)
        return s.model_copy(deep=True) if s else None

    async def list_user_pipelines(self, user_id: str) -> list[str]:
        """Skeleton: at most one pipeline ('default') per user."""
        return ["default"] if user_id in self._store else []  # per spec §4.2
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_repository.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add IStateRepository + InMemoryRepository"
```

---

## Task 4: Shared Test Fixtures

**Files:**
- Create: `docs/superpowers/specs/fixtures/pipelines.json`

**Interfaces:**
- Consumes: nothing
- Produces: JSON fixture file consumed by both backend (Task 6 validator test) and frontend (Task 15 validator test)

- [ ] **Step 1: Create fixtures file**

Write `/home/robin/Documents/Ryan/PhD/openphd/docs/superpowers/specs/fixtures/pipelines.json`:
```json
{
  "agents": [
    {
      "agent_id": "intent_parser",
      "name": "Intent Parser",
      "description": "Identifies user intent",
      "category": "academic",
      "required_fields": ["raw_user_input"],
      "output_fields": ["intent", "is_ambiguous"],
      "token_budget": 500,
      "isolation": "in_process"
    },
    {
      "agent_id": "mock_echo",
      "name": "Mock Echo",
      "description": "Echoes dynamic_storage.echo_input",
      "category": "mock",
      "required_fields": ["dynamic_storage.echo_input"],
      "output_fields": ["dynamic_storage.echo_output"],
      "token_budget": 0,
      "isolation": "in_process"
    },
    {
      "agent_id": "mock_logger",
      "name": "Mock Logger",
      "description": "Appends echo_output to run_log",
      "category": "mock",
      "required_fields": ["dynamic_storage.echo_output"],
      "output_fields": ["dynamic_storage.run_log"],
      "token_budget": 0,
      "isolation": "in_process"
    },
    {
      "agent_id": "jargon_polisher",
      "name": "Jargon Polisher",
      "description": "Rewrites email_draft in academic style",
      "category": "writing",
      "required_fields": ["email_draft"],
      "output_fields": ["email_draft"],
      "token_budget": 2000,
      "isolation": "in_process"
    },
    {
      "agent_id": "csc_matcher",
      "name": "CSC Matcher",
      "description": "Evaluates CSC scholarship fit",
      "category": "admin",
      "required_fields": ["user_background"],
      "output_fields": ["dynamic_storage.csc_report"],
      "token_budget": 1000,
      "isolation": "in_process"
    }
  ],
  "pipelines": {
    "happy_path": ["mock_echo", "mock_logger"],
    "missing_field": ["mock_logger"],
    "chain_ok": ["intent_parser", "mock_echo", "mock_logger"],
    "chain_broken": ["mock_logger", "intent_parser"]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/fixtures/
git commit -m "chore(spec): add shared pipeline test fixtures"
```

---

## Task 5: validate_pipeline() Algorithm

**Files:**
- Create: `backend/src/phd_agent/core/validator.py`
- Test: `backend/tests/test_validator.py`

**Interfaces:**
- Consumes: `AgentContract` (Task 2), registry-shaped object with `get_contract(agent_id) -> AgentContract`
- Produces: `validate_pipeline(active_pipeline, registry, bootstrap_fields=None) -> ValidationResult`

`ValidationResult(valid: bool, failed_at: int | None, steps: list[StepValidation])`
`StepValidation(step: int, agent_id: str, required: set[str], provided_at_step: set[str], missing: set[str], ok: bool)`

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_validator.py`:
```python
import pytest
from phd_agent.core.contract import AgentContract
from phd_agent.core.validator import validate_pipeline

class _FakeRegistry:
    def __init__(self, contracts: dict[str, AgentContract]) -> None:
        self._c = contracts
    def get_contract(self, agent_id: str) -> AgentContract:
        return self._c[agent_id]

def _c(aid: str, req: set[str], out: set[str]) -> AgentContract:
    return AgentContract(
        agent_id=aid, name=aid, description="d", category="mock",
        required_fields=req, output_fields=out,
    )

def test_happy_path_no_extras():
    reg = _FakeRegistry({
        "a": _c("a", {"x"}, {"y"}),
        "b": _c("b", {"y"}, {"z"}),
    })
    r = validate_pipeline(["a", "b"], reg, bootstrap_fields={"x"})
    assert r.valid is True
    assert r.failed_at is None
    assert all(s.ok for s in r.steps)

def test_missing_field_fails_at_step():
    reg = _FakeRegistry({
        "a": _c("a", {"x"}, {"y"}),
        "b": _c("b", {"not_provided"}, set()),
    })
    r = validate_pipeline(["a", "b"], reg, bootstrap_fields={"x"})
    assert r.valid is False
    assert r.failed_at == 1
    assert r.steps[1].missing == {"not_provided"}

def test_chain_ok_uses_intermediate_outputs():
    reg = _FakeRegistry({
        "intent_parser": _c("intent_parser", {"raw_user_input"}, {"intent"}),
        "mock_echo": _c("mock_echo", {"intent"}, {"dynamic_storage.echo_output"}),
        "mock_logger": _c("mock_echo", {"dynamic_storage.echo_output"}, {"dynamic_storage.run_log"}),
    })
    r = validate_pipeline(["intent_parser", "mock_echo", "mock_logger"], reg)
    # Bootstrap doesn't include raw_user_input → fails at step 0
    assert r.valid is False
    assert r.failed_at == 0

def test_chain_with_bootstrap_ok():
    reg = _FakeRegistry({
        "intent_parser": _c("intent_parser", {"raw_user_input"}, {"intent"}),
        "mock_echo": _c("mock_echo", {"intent"}, {"dynamic_storage.echo_output"}),
        "mock_logger": _c("mock_logger", {"dynamic_storage.echo_output"}, {"dynamic_storage.run_log"}),
    })
    r = validate_pipeline(["intent_parser", "mock_echo", "mock_logger"], reg)
    assert r.valid is True

def test_unknown_agent_raises():
    reg = _FakeRegistry({})
    with pytest.raises(KeyError):
        validate_pipeline(["does_not_exist"], reg)

def test_empty_pipeline_is_valid():
    reg = _FakeRegistry({})
    r = validate_pipeline([], reg)
    assert r.valid is True
    assert r.steps == []
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_validator.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.validator'`

- [ ] **Step 3: Implement `core/validator.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/validator.py`:
```python
"""Contract validation: spec §4.1 algorithm. Pure function."""
from __future__ import annotations
from dataclasses import dataclass, field
from phd_agent.core.contract import AgentContract

DEFAULT_BOOTSTRAP = frozenset({"user_id", "user_background"})

@dataclass
class StepValidation:
    step: int
    agent_id: str
    required: set[str]
    provided_at_step: set[str]
    missing: set[str]
    ok: bool

@dataclass
class ValidationResult:
    valid: bool
    failed_at: int | None
    steps: list[StepValidation] = field(default_factory=list)

class _RegistryLike:
    def get_contract(self, agent_id: str) -> AgentContract: ...

def validate_pipeline(
    active_pipeline: list[str],
    registry: _RegistryLike,
    bootstrap_fields: set[str] | None = None,
) -> ValidationResult:
    provided = set(bootstrap_fields) if bootstrap_fields else set(DEFAULT_BOOTSTRAP)
    steps: list[StepValidation] = []

    for idx, agent_id in enumerate(active_pipeline):
        contract = registry.get_contract(agent_id)
        missing = contract.required_fields - provided
        steps.append(StepValidation(
            step=idx,
            agent_id=agent_id,
            required=set(contract.required_fields),
            provided_at_step=set(provided),
            missing=set(missing),
            ok=not missing,
        ))
        if missing:
            return ValidationResult(valid=False, failed_at=idx, steps=steps)
        provided |= contract.output_fields

    return ValidationResult(valid=True, failed_at=None, steps=steps)
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_validator.py -v`
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add validate_pipeline() with full algorithm coverage"
```

---

## Task 6: AgentRegistry (scan + lazy load)

**Files:**
- Create: `backend/src/phd_agent/core/registry.py`
- Test: `backend/tests/test_registry.py`

**Interfaces:**
- Consumes: `AgentContract` (Task 2), filesystem path to `plugins/`
- Produces: `AgentRegistry(plugins_dir)` with:
  - `get_contract(agent_id) -> AgentContract`
  - `load(agent_id) -> BaseAgent` (lazy: imports module on first call)
  - `list_agent_ids() -> list[str]`

- [ ] **Step 1: Write failing test (uses tmp_path for fake plugin fixtures)**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_registry.py`:
```python
import json
from pathlib import Path
import pytest
from phd_agent.core.registry import AgentRegistry

def _write_plugin(parent: Path, agent_id: str, contract: dict, agent_code: str) -> None:
    p = parent / agent_id
    p.mkdir()
    (p / "contract.json").write_text(json.dumps(contract))
    (p / "__init__.py").write_text("")
    (p / "agent.py").write_text(agent_code)

@pytest.fixture
def plugins_dir(tmp_path: Path) -> Path:
    _write_plugin(
        tmp_path, "echo_test",
        {"agent_id": "echo_test", "name": "Echo Test", "description": "d",
         "category": "mock", "required_fields": [], "output_fields": []},
        "from phd_agent.plugins._base import BaseAgent\n"
        "from phd_agent.core.contract import AgentContract\n"
        "from phd_agent.core.state import GlobalState\n"
        "CONTRACT = AgentContract(agent_id='echo_test', name='Echo Test', description='d', category='mock', required_fields=set(), output_fields=set())\n"
        "class EchoTestAgent(BaseAgent):\n"
        "    contract = CONTRACT\n"
        "    async def run(self, state: GlobalState) -> GlobalState:\n"
        "        state.dynamic_storage['marker'] = 'echo_test_ran'\n"
        "        return state\n",
    )
    return tmp_path

def test_scan_finds_contracts(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    c = reg.get_contract("echo_test")
    assert c.agent_id == "echo_test"

def test_list_agent_ids(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    assert reg.list_agent_ids() == ["echo_test"]

def test_unknown_agent_raises_keyerror(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    with pytest.raises(KeyError):
        reg.get_contract("ghost")

def test_lazy_load_creates_instance(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    agent = reg.load("echo_test")
    assert agent.contract.agent_id == "echo_test"

@pytest.mark.asyncio
async def test_loaded_agent_can_execute(plugins_dir: Path):
    reg = AgentRegistry(plugins_dir)
    from phd_agent.core.state import GlobalState
    agent = reg.load("echo_test")
    state = GlobalState(user_id="u1")
    await agent.run(state)
    assert state.dynamic_storage["marker"] == "echo_test_ran"
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_registry.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.registry'`

- [ ] **Step 3: Implement `core/registry.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/registry.py`:
```python
"""Discovers plugin contracts at startup; lazy-loads plugin classes on demand."""
from __future__ import annotations
import importlib
import json
from inspect import isclass
from pathlib import Path
from phd_agent.core.contract import AgentContract, BaseAgent

class AgentRegistry:
    def __init__(self, plugins_dir: Path) -> None:
        self._dir = plugins_dir
        self._contracts: dict[str, AgentContract] = {}
        self._classes: dict[str, type[BaseAgent]] = {}
        self._scan()

    def _scan(self) -> None:
        for plugin_dir in self._dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith("_"):
                continue
            contract_file = plugin_dir / "contract.json"
            if not contract_file.exists():
                continue
            contract = AgentContract.model_validate_json(contract_file.read_text())
            self._contracts[contract.agent_id] = contract

    def list_agent_ids(self) -> list[str]:
        return sorted(self._contracts.keys())

    def get_contract(self, agent_id: str) -> AgentContract:
        return self._contracts[agent_id]

    def load(self, agent_id: str) -> BaseAgent:
        if agent_id not in self._classes:
            module = importlib.import_module(f"phd_agent.plugins.{agent_id}.agent")
            cls = next(
                v for v in vars(module).values()
                if isclass(v) and issubclass(v, BaseAgent) and v is not BaseAgent
            )
            self._classes[agent_id] = cls
        return self._classes[agent_id]()
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_registry.py -v`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add AgentRegistry with scan + lazy load"
```

---

## Task 7: CentralRouter

**Files:**
- Create: `backend/src/phd_agent/core/router.py`
- Test: `backend/tests/test_router.py`

**Interfaces:**
- Consumes: `GlobalState` (Task 2), `AgentRegistry` (Task 6)
- Produces: `CentralRouter.dispatch(state) -> str | None` — returns next agent_id, or `None` if END

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_router.py`:
```python
import pytest
from phd_agent.core.router import CentralRouter
from phd_agent.core.state import GlobalState

@pytest.fixture
def router():
    # No registry needed for pure dispatch logic
    return CentralRouter(registry=None)

def test_dispatch_returns_first_agent_when_step_zero(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b", "c"], current_step=0)
    assert router.dispatch(state) == "a"

def test_dispatch_returns_next_agent_in_sequence(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b", "c"], current_step=1)
    assert router.dispatch(state) == "b"

def test_dispatch_returns_none_when_out_of_bounds(router):
    state = GlobalState(user_id="u", active_pipeline=["a", "b"], current_step=2)
    assert router.dispatch(state) is None

def test_dispatch_returns_none_for_empty_pipeline(router):
    state = GlobalState(user_id="u", active_pipeline=[], current_step=0)
    assert router.dispatch(state) is None
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_router.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.router'`

- [ ] **Step 3: Implement `core/router.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/router.py`:
```python
"""Central dispatcher: reads state.current_step, returns next agent_id or None=END."""
from __future__ import annotations
from phd_agent.core.state import GlobalState

class CentralRouter:
    def __init__(self, registry) -> None:
        self._registry = registry  # held for future validation hooks

    def dispatch(self, state: GlobalState) -> str | None:
        if state.current_step >= len(state.active_pipeline):
            return None
        return state.active_pipeline[state.current_step]
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_router.py -v`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add CentralRouter dispatch logic"
```

---

## Task 8: EventBus (async pub/sub for SSE)

**Files:**
- Create: `backend/src/phd_agent/core/events.py`
- Test: `backend/tests/test_events.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `Event(run_id, step, agent_id, status, duration_ms, output, error)`
  - `EventBus.publish(event)`, `subscribe(run_id) -> AsyncIterator[Event]`

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_events.py`:
```python
import asyncio
import pytest
from phd_agent.core.events import EventBus, Event

@pytest.mark.asyncio
async def test_subscriber_receives_published_events():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-1", step=0, agent_id="a", status="ok", duration_ms=10))
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "a"
    assert event.status == "ok"

@pytest.mark.asyncio
async def test_subscriber_does_not_receive_other_run_events():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-2", step=0, agent_id="a", status="ok", duration_ms=10))
    bus.publish(Event(run_id="run-1", step=0, agent_id="b", status="ok", duration_ms=10))
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "b"

@pytest.mark.asyncio
async def test_multiple_subscribers_to_same_run():
    bus = EventBus()
    s1 = bus.subscribe("run-1")
    s2 = bus.subscribe("run-1")
    bus.publish(Event(run_id="run-1", step=0, agent_id="a", status="ok", duration_ms=10))
    e1 = await asyncio.wait_for(s1.__anext__(), timeout=0.5)
    e2 = await asyncio.wait_for(s2.__anext__(), timeout=0.5)
    assert e1.agent_id == "a"
    assert e2.agent_id == "a"
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_events.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.core.events'`

- [ ] **Step 3: Implement `core/events.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/events.py`:
```python
"""In-process async pub/sub for streaming pipeline events to SSE."""
from __future__ import annotations
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class Event:
    run_id: str
    step: int
    agent_id: str
    status: str  # "ok" | "skipped" | "failed" | "end"
    duration_ms: int = 0
    output: dict = field(default_factory=dict)
    error: str | None = None

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Event]]] = defaultdict(list)

    def subscribe(self, run_id: str) -> AsyncIterator[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers[run_id].append(queue)

        async def gen() -> AsyncIterator[Event]:
            while True:
                yield await queue.get()

        return gen()

    def publish(self, event: Event) -> None:
        for q in self._subscribers.get(event.run_id, []):
            q.put_nowait(event)
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_events.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add EventBus async pub/sub"
```

---

## Task 9: AgentWrapper (try/except + token guard)

**Files:**
- Create: `backend/src/phd_agent/core/wrapper.py`, `backend/src/phd_agent/llm/__init__.py`, `backend/src/phd_agent/llm/base.py`, `backend/src/phd_agent/llm/budget.py`
- Test: `backend/tests/test_wrapper.py`

**Interfaces:**
- Consumes: `GlobalState`, `AgentRegistry`, `EventBus`, `BaseLLMClient`
- Produces: `AgentWrapper.execute(state, agent_id, run_id, bus) -> GlobalState`
  - Catches exceptions from `agent.run(state)` and writes to `state.error_log`
  - Records duration, publishes event to bus, increments `current_step`

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_wrapper.py`:
```python
import asyncio
import pytest
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState
from phd_agent.core.contract import AgentContract, BaseAgent

class _Exploder(BaseAgent):
    contract = AgentContract(
        agent_id="exploder", name="E", description="d", category="mock",
        required_fields=set(), output_fields=set(),
    )
    async def run(self, state):
        raise RuntimeError("kaboom")

class _Writer(BaseAgent):
    contract = AgentContract(
        agent_id="writer", name="W", description="d", category="mock",
        required_fields=set(), output_fields={"dynamic_storage.k"},
    )
    async def run(self, state):
        state.dynamic_storage["k"] = "v"
        return state

class _FakeRegistry:
    def __init__(self, m):
        self._m = m
    def load(self, agent_id):
        return self._m[agent_id]()

class _NoopLLM:
    def count_tokens(self, text): return 0

@pytest.mark.asyncio
async def test_wrapper_executes_and_increments_step():
    bus = EventBus()
    reg = _FakeRegistry({"writer": _Writer})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["writer"], current_step=0)
    await w.execute(state, "writer", "run-1", bus)
    assert state.current_step == 1
    assert state.dynamic_storage["k"] == "v"
    assert state.status != "failed"

@pytest.mark.asyncio
async def test_wrapper_isolates_exceptions_and_marks_step():
    bus = EventBus()
    reg = _FakeRegistry({"exploder": _Exploder})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["exploder"], current_step=0)
    await w.execute(state, "exploder", "run-1", bus)
    assert state.current_step == 1
    assert len(state.error_log) == 1
    assert state.error_log[0]["agent_id"] == "exploder"
    assert "kaboom" in state.error_log[0]["error"]

@pytest.mark.asyncio
async def test_wrapper_publishes_event():
    bus = EventBus()
    sub = bus.subscribe("run-1")
    reg = _FakeRegistry({"writer": _Writer})
    w = AgentWrapper(reg, bus, _NoopLLM())
    state = GlobalState(user_id="u", active_pipeline=["writer"])
    await w.execute(state, "writer", "run-1", bus)
    event = await asyncio.wait_for(sub.__anext__(), timeout=0.5)
    assert event.agent_id == "writer"
    assert event.status == "ok"
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_wrapper.py -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement `llm/base.py` + `llm/budget.py` + `core/wrapper.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/llm/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/llm/base.py`:
```python
"""LLM client abstraction (spec §4.2)."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    tokens_used: int
    model: str

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], *, budget: int) -> LLMResponse: ...
    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/llm/budget.py`:
```python
"""Per-agent token budget enforcement (spec §6)."""
from __future__ import annotations

class TokenGuardrail:
    def __init__(self, llm) -> None:
        self._llm = llm

    def truncate_to_budget(self, text: str, budget: int) -> str:
        if budget <= 0:
            return ""
        tokens = self._llm.count_tokens(text)
        if tokens <= budget:
            return text
        # Approximate: 4 chars per token; preserve head (more important than tail)
        char_budget = budget * 4
        return text[:char_budget]
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/core/wrapper.py`:
```python
"""Sandboxed agent execution: try/except isolation, step increment, event publish."""
from __future__ import annotations
import time
from phd_agent.core.contract import BaseAgent
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState

class AgentWrapper:
    def __init__(self, registry, bus, llm) -> None:
        self._registry = registry
        self._bus = bus
        self._llm = llm

    async def execute(self, state: GlobalState, agent_id: str, run_id: str, bus: EventBus) -> None:
        from phd_agent.core.events import Event  # local import to avoid cycle in test
        started = time.perf_counter()
        status = "ok"
        error_msg: str | None = None
        try:
            agent: BaseAgent = self._registry.load(agent_id)
            await agent.run(state)
        except Exception as e:
            status = "skipped"
            error_msg = f"{type(e).__name__}: {e}"
            state.error_log.append({
                "step": state.current_step,
                "agent_id": agent_id,
                "error": error_msg,
            })
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            state.current_step += 1
            bus.publish(Event(
                run_id=run_id,
                step=state.current_step - 1,
                agent_id=agent_id,
                status=status,
                duration_ms=duration_ms,
                error=error_msg,
            ))
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_wrapper.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add AgentWrapper + TokenGuardrail + BaseLLMClient"
```

---

## Task 10: mock_echo + mock_logger Plugins

**Files:**
- Create: `backend/src/phd_agent/plugins/mock_echo/{__init__.py,contract.json,agent.py}`, `backend/src/phd_agent/plugins/mock_logger/{__init__.py,contract.json,agent.py}`
- Test: extend `backend/tests/test_registry.py` (already covers load+execute)

**Interfaces:**
- Consumes: `BaseAgent`, `GlobalState` (Task 2)
- Produces: two real plugins discoverable by `AgentRegistry` in production (not just tmp_path)

- [ ] **Step 1: Write plugin contract.json files**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_echo/contract.json`:
```json
{
  "agent_id": "mock_echo",
  "name": "Mock Echo",
  "description": "Echoes dynamic_storage.echo_input into dynamic_storage.echo_output",
  "category": "mock",
  "required_fields": ["dynamic_storage.echo_input"],
  "output_fields": ["dynamic_storage.echo_output"],
  "token_budget": 0,
  "isolation": "in_process"
}
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_logger/contract.json`:
```json
{
  "agent_id": "mock_logger",
  "name": "Mock Logger",
  "description": "Appends dynamic_storage.echo_output to dynamic_storage.run_log",
  "category": "mock",
  "required_fields": ["dynamic_storage.echo_output"],
  "output_fields": ["dynamic_storage.run_log"],
  "token_budget": 0,
  "isolation": "in_process"
}
```

- [ ] **Step 2: Write plugin agent.py files**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_echo/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_echo/agent.py`:
```python
"""Mock plugin: echoes dynamic_storage.echo_input."""
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="mock_echo",
    name="Mock Echo",
    description="Echoes dynamic_storage.echo_input into dynamic_storage.echo_output",
    category="mock",
    required_fields={"dynamic_storage.echo_input"},
    output_fields={"dynamic_storage.echo_output"},
    token_budget=0,
)

class MockEchoAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState) -> GlobalState:
        text = state.dynamic_storage.get("echo_input", "")
        state.dynamic_storage["echo_output"] = f"echo: {text}"
        return state
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_logger/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/plugins/mock_logger/agent.py`:
```python
"""Mock plugin: logs dynamic_storage.echo_output into dynamic_storage.run_log."""
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="mock_logger",
    name="Mock Logger",
    description="Appends dynamic_storage.echo_output to dynamic_storage.run_log",
    category="mock",
    required_fields={"dynamic_storage.echo_output"},
    output_fields={"dynamic_storage.run_log"},
    token_budget=0,
)

class MockLoggerAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState) -> GlobalState:
        echo = state.dynamic_storage.get("echo_output", "")
        log = state.dynamic_storage.get("run_log", [])
        log.append(f"logged: {echo}")
        state.dynamic_storage["run_log"] = log
        return state
```

- [ ] **Step 3: Write integration test using real plugins dir**

Append to `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_registry.py` (at end of file):
```python
def test_real_plugins_dir_scans_mock_agents():
    real_plugins = Path(__file__).resolve().parent.parent / "src" / "phd_agent" / "plugins"
    reg = AgentRegistry(real_plugins)
    assert "mock_echo" in reg.list_agent_ids()
    assert "mock_logger" in reg.list_agent_ids()
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_registry.py -v`
Expected: `6 passed` (5 from Task 6 + 1 new).

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(plugins): add mock_echo and mock_logger demo plugins"
```

---

## Task 11: PipelineOrchestrator (ties it all together)

**Files:**
- Create: `backend/src/phd_agent/orchestrator.py`
- Test: `backend/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: `GlobalState`, `AgentRegistry` (Task 6), `CentralRouter` (Task 7), `AgentWrapper` (Task 9), `EventBus` (Task 8), `validate_pipeline` (Task 5), `BaseLLMClient`
- Produces: `PipelineOrchestrator(registry, llm, bus).run(user_id, active_pipeline, initial_dynamic_storage) -> str (run_id)`
  - Validates pipeline (raises if invalid)
  - Stores initial state in repository
  - Loops: dispatch → execute → repeat until dispatch returns None
  - Publishes final `status="end"` event

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_orchestrator.py`:
```python
import pytest
from pathlib import Path
from phd_agent.orchestrator import PipelineOrchestrator
from phd_agent.core.repository import InMemoryRepository
from phd_agent.llm.base import BaseLLMClient, LLMResponse

class _NoopLLM(BaseLLMClient):
    async def chat(self, messages, *, budget):
        return LLMResponse(content="", tokens_used=0, model="noop")
    def count_tokens(self, text):
        return 0

def _orch(real_plugins: bool = True) -> PipelineOrchestrator:
    plugins_dir = (
        Path(__file__).resolve().parent.parent / "src" / "phd_agent" / "plugins"
        if real_plugins else None
    )
    from phd_agent.core.registry import AgentRegistry
    reg = AgentRegistry(plugins_dir) if real_plugins else AgentRegistry(Path("/tmp/empty"))
    bus = EventBus()
    return PipelineOrchestrator(
        registry=reg, llm=_NoopLLM(), bus=bus, repo=InMemoryRepository(),
    )

@pytest.mark.asyncio
async def test_happy_path_pipeline_completes():
    orch = _orch()
    run_id = await orch.run(
        user_id="u1",
        active_pipeline=["mock_echo", "mock_logger"],
        initial_dynamic_storage={"echo_input": "hello"},
    )
    final = await orch.repo.load("u1")
    assert final is not None
    assert final.status in ("completed", "partial")
    assert final.current_step == 2
    assert final.dynamic_storage["echo_output"] == "echo: hello"
    assert final.dynamic_storage["run_log"] == ["logged: echo: hello"]

@pytest.mark.asyncio
async def test_invalid_pipeline_raises():
    orch = _orch()
    with pytest.raises(ValueError):
        await orch.run(
            user_id="u1",
            active_pipeline=["mock_logger"],  # missing echo_output upstream
            initial_dynamic_storage={},
        )

@pytest.mark.asyncio
async def test_pipeline_state_transitions_to_completed():
    orch = _orch()
    run_id = await orch.run(
        user_id="u1",
        active_pipeline=["mock_echo"],
        initial_dynamic_storage={"echo_input": "x"},
    )
    final = await orch.repo.load("u1")
    assert final.status in ("completed", "partial")
    assert final.current_step == 1
    # Event publishing is covered by test_wrapper.py; here we only check state
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_orchestrator.py -v`
Expected: `ModuleNotFoundError: No module named 'phd_agent.orchestrator'`

- [ ] **Step 3: Implement `orchestrator.py`**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/orchestrator.py`:
```python
"""Composes Validator + Registry + Router + Wrapper + EventBus + Repository."""
from __future__ import annotations
import uuid
from phd_agent.core.contract import BaseLLMClient
from phd_agent.core.events import EventBus, Event
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.repository import IStateRepository, InMemoryRepository
from phd_agent.core.router import CentralRouter
from phd_agent.core.state import GlobalState
from phd_agent.core.validator import validate_pipeline
from phd_agent.core.wrapper import AgentWrapper

class PipelineOrchestrator:
    def __init__(
        self,
        registry: AgentRegistry,
        llm: BaseLLMClient,
        bus: EventBus | None = None,
        repo: IStateRepository | None = None,
    ) -> None:
        self.registry = registry
        self.llm = llm
        self.bus = bus or EventBus()
        self.repo = repo or InMemoryRepository()
        self.router = CentralRouter(registry)
        self.wrapper = AgentWrapper(registry, self.bus, llm)

    async def run(
        self,
        user_id: str,
        active_pipeline: list[str],
        initial_dynamic_storage: dict | None = None,
        user_background: dict | None = None,
    ) -> str:
        # 1. Validate
        result = validate_pipeline(active_pipeline, self.registry)
        if not result.valid:
            raise ValueError(f"Pipeline invalid at step {result.failed_at}")

        # 2. Init state
        run_id = str(uuid.uuid4())
        state = GlobalState(
            user_id=user_id,
            user_background=user_background or {},
            active_pipeline=list(active_pipeline),
            current_step=0,
            dynamic_storage=dict(initial_dynamic_storage or {}),
            status="running",
        )
        await self.repo.save(user_id, state)

        # 3. Execute loop
        try:
            while True:
                next_id = self.router.dispatch(state)
                if next_id is None:
                    state.status = "completed"
                    break
                await self.wrapper.execute(state, next_id, run_id, self.bus)
                await self.repo.save(user_id, state)
        except Exception:
            state.status = "failed"
            await self.repo.save(user_id, state)
            raise

        if state.error_log:
            state.status = "partial"
            await self.repo.save(user_id, state)

        # 4. End event
        self.bus.publish(Event(
            run_id=run_id, step=state.current_step,
            agent_id="", status="end",
        ))
        return run_id
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_orchestrator.py -v`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(core): add PipelineOrchestrator tying validator+router+wrapper+bus"
```

---

## Task 12: FastAPI App + Endpoints

**Files:**
- Modify: `backend/src/phd_agent/main.py` (replace stub)
- Create: `backend/src/phd_agent/api/{__init__.py,schemas.py,agents.py,pipelines.py}`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: `AgentRegistry` (Task 6), `PipelineOrchestrator` (Task 11), `EventBus` (Task 8)
- Produces: HTTP endpoints per spec §8:
  - `GET /health` (exists from Task 1)
  - `GET /agents/catalog` → `{agents: [AgentContract]}`
  - `POST /pipelines/validate` → `{valid, failed_at?, steps}`
  - `POST /pipelines/run` → `{run_id, status}`
  - `GET /pipelines/{run_id}/events` → SSE stream

- [ ] **Step 1: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/tests/test_api.py`:
```python
import json
import pytest
from fastapi.testclient import TestClient
from phd_agent.main import create_app

@pytest.fixture
def client():
    return TestClient(create_app())

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}

def test_agents_catalog_returns_real_plugins(client):
    r = client.get("/api/agents/catalog")
    assert r.status_code == 200
    body = r.json()
    ids = {a["agent_id"] for a in body["agents"]}
    assert "mock_echo" in ids
    assert "mock_logger" in ids

def test_validate_happy_path(client):
    r = client.post("/api/pipelines/validate", json={
        "active_pipeline": ["mock_echo", "mock_logger"],
        "user_id": "u1",
        "dynamic_storage": {"echo_input": "hi"},
    })
    assert r.status_code == 200
    assert r.json()["valid"] is True

def test_validate_invalid_pipeline_returns_422(client):
    r = client.post("/api/pipelines/validate", json={
        "active_pipeline": ["mock_logger"],
        "user_id": "u1",
        "dynamic_storage": {},
    })
    assert r.status_code == 200  # we return 200 with valid:false, not 422
    body = r.json()
    assert body["valid"] is False
    assert body["failed_at"] == 0

def test_run_returns_run_id(client):
    r = client.post("/api/pipelines/run", json={
        "user_id": "u1",
        "active_pipeline": ["mock_echo", "mock_logger"],
        "dynamic_storage": {"echo_input": "hello"},
    })
    assert r.status_code == 200
    assert "run_id" in r.json()
```

- [ ] **Step 2: Run, verify failure**

Run: `cd backend && pytest tests/test_api.py -v`
Expected: failures (catalog returns empty, validate endpoint missing).

- [ ] **Step 3: Implement API layer**

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/api/__init__.py`:
```python
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/api/schemas.py`:
```python
"""Request/response Pydantic models for the HTTP boundary."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field

class ValidateRequest(BaseModel):
    user_id: str
    active_pipeline: list[str]
    dynamic_storage: dict = Field(default_factory=dict)
    user_background: dict = Field(default_factory=dict)

class StepValidationOut(BaseModel):
    step: int
    agent_id: str
    required: list[str]
    provided_at_step: list[str]
    missing: list[str]
    ok: bool

class ValidateResponse(BaseModel):
    valid: bool
    failed_at: int | None = None
    steps: list[StepValidationOut] = Field(default_factory=list)

class RunRequest(BaseModel):
    user_id: str
    active_pipeline: list[str]
    dynamic_storage: dict = Field(default_factory=dict)
    user_background: dict = Field(default_factory=dict)

class RunResponse(BaseModel):
    run_id: str
    status: Literal["running", "completed", "partial", "failed"]
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/api/agents.py`:
```python
"""GET /agents/catalog."""
from __future__ import annotations
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class CatalogResponse(BaseModel):
    agents: list[dict]

@router.get("/agents/catalog", response_model=CatalogResponse)
def get_catalog(request: Request) -> CatalogResponse:
    reg = request.app.state.registry
    return CatalogResponse(
        agents=[c.model_dump() for c in (reg.get_contract(a) for a in reg.list_agent_ids())]
    )
```

Write `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/api/pipelines.py`:
```python
"""POST /pipelines/validate, /pipelines/run, GET /pipelines/{id}/events."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from phd_agent.api.schemas import (
    RunRequest, RunResponse,
    ValidateRequest, ValidateResponse, StepValidationOut,
)

router = APIRouter()

@router.post("/pipelines/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest, request: Request) -> ValidateResponse:
    from phd_agent.core.validator import validate_pipeline
    reg = request.app.state.registry
    result = validate_pipeline(req.active_pipeline, reg)
    return ValidateResponse(
        valid=result.valid,
        failed_at=result.failed_at,
        steps=[
            StepValidationOut(
                step=s.step,
                agent_id=s.agent_id,
                required=sorted(s.required),
                provided_at_step=sorted(s.provided_at_step),
                missing=sorted(s.missing),
                ok=s.ok,
            )
            for s in result.steps
        ],
    )

@router.post("/pipelines/run", response_model=RunResponse)
async def run(req: RunRequest, request: Request) -> RunResponse:
    orch = request.app.state.orchestrator
    try:
        run_id = await orch.run(
            user_id=req.user_id,
            active_pipeline=req.active_pipeline,
            initial_dynamic_storage=req.dynamic_storage,
            user_background=req.user_background,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    final = await orch.repo.load(req.user_id)
    return RunResponse(run_id=run_id, status=final.status)

@router.get("/pipelines/{run_id}/events")
async def events(run_id: str, request: Request) -> StreamingResponse:
    bus = request.app.state.bus

    async def gen():
        async for event in bus.subscribe(run_id):
            yield {
                "event": "step",
                "id": str(event.step),
                "data": (
                    f'{{"step":{event.step},"agent_id":"{event.agent_id}",'
                    f'"status":"{event.status}","duration_ms":{event.duration_ms},'
                    f'"error":{json_str(event.error)}}}'
                ),
            }
            if event.status == "end":
                break

    return EventSourceResponse(gen())

def json_str(s) -> str:
    import json
    return json.dumps(s)
```

Replace `/home/robin/Documents/Ryan/PhD/openphd/backend/src/phd_agent/main.py`:
```python
"""FastAPI app factory: wires registry, orchestrator, bus, and routers."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from phd_agent.core.events import EventBus
from phd_agent.core.registry import AgentRegistry
from phd_agent.llm.base import BaseLLMClient, LLMResponse
from phd_agent.orchestrator import PipelineOrchestrator

class _StubLLM(BaseLLMClient):
    """Skeleton-phase LLM that returns empty responses (real impl in Phase 2)."""
    async def chat(self, messages, *, budget):
        return LLMResponse(content="", tokens_used=0, model="stub")
    def count_tokens(self, text):
        return len(text) // 4

def create_app() -> FastAPI:
    app = FastAPI(title="PhD-Agent", version="0.1.0")

    plugins_dir = Path(__file__).parent / "plugins"
    registry = AgentRegistry(plugins_dir)
    bus = EventBus()
    llm = _StubLLM()
    orchestrator = PipelineOrchestrator(registry=registry, llm=llm, bus=bus)

    app.state.registry = registry
    app.state.bus = bus
    app.state.llm = llm
    app.state.orchestrator = orchestrator

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from phd_agent.api.agents import router as agents_router
    from phd_agent.api.pipelines import router as pipelines_router
    app.include_router(agents_router, prefix="/api")    # /api/agents/catalog
    app.include_router(pipelines_router, prefix="/api")  # /api/pipelines/*

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app

app = create_app()
```

- [ ] **Step 4: Run, verify pass**

Run: `cd backend && pytest tests/test_api.py -v`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat(api): wire FastAPI endpoints (catalog, validate, run, SSE events)"
```

---

## Task 13: Frontend Bootstrap (Vite + React + TS + Vitest)

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/vitest.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx` (stub), `frontend/src/setupTests.ts`

**Interfaces:**
- Consumes: nothing
- Produces: `npm run dev` boots; `npm run test` runs Vitest

- [ ] **Step 1: Create `package.json`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/package.json`:
```json
{
  "name": "phd-agent-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@xyflow/react": "^12.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "jsdom": "^24.0.0",
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "vitest": "^1.6.0"
  }
}
```

- [ ] **Step 2: Create TS + Vite + Vitest configs**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "types": ["vitest/globals"]
  },
  "include": ["src"]
}
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>PhD-Agent</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/setupTests.ts`:
```typescript
```

- [ ] **Step 3: Create React entry + stub App**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/main.tsx`:
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/App.tsx`:
```typescript
export default function App() {
  return <div data-testid="app">PhD-Agent</div>;
}
```

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/App.test.tsx`:
```typescript
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app', () => {
  render(<App />);
  expect(screen.getByTestId('app')).toBeInTheDocument();
});
```

- [ ] **Step 4: Install deps and verify dev + test work**

Run:
```bash
cd /home/robin/Documents/Ryan/PhD/openphd/frontend
npm install
npm test -- --run
```
Expected: `1 passed`.

For dev server (verify it boots, then kill):
```bash
timeout 8 npm run dev &
sleep 5
curl -s http://localhost:5173 | grep -q "PhD-Agent" && echo "DEV OK"
wait
```
Expected: `DEV OK`.

- [ ] **Step 5: Commit**

```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git add frontend/
git commit -m "chore(frontend): bootstrap Vite + React + TS + Vitest"
```

---

## Task 14: Frontend Types + Validator (TS mirror)

**Files:**
- Create: `frontend/src/api/types.ts`, `frontend/src/api/client.ts`, `frontend/src/validator/contract.ts`, `frontend/src/validator/validate.ts`, `frontend/src/validator/fixtures.ts`, `frontend/src/validator/validate.test.ts`

**Interfaces:**
- Consumes: shared fixture `docs/superpowers/specs/fixtures/pipelines.json`
- Produces:
  - `AgentContract` TS type
  - `validatePipeline(pipeline, contracts, bootstrap?) => ValidationResult` (behavior-equivalent to backend)
  - `apiClient.catalog()` → `AgentContract[]`

- [ ] **Step 1: Write types**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/api/types.ts`:
```typescript
export type Category = 'academic' | 'writing' | 'admin' | 'mock';

export interface AgentContract {
  agent_id: string;
  name: string;
  description: string;
  category: Category;
  required_fields: string[];
  output_fields: string[];
  token_budget: number;
  isolation: 'in_process';
}

export interface StepValidation {
  step: number;
  agent_id: string;
  required: string[];
  provided_at_step: string[];
  missing: string[];
  ok: boolean;
}

export interface ValidationResult {
  valid: boolean;
  failed_at: number | null;
  steps: StepValidation[];
}

export interface RunResponse {
  run_id: string;
  status: 'running' | 'completed' | 'partial' | 'failed';
}

export interface SseEvent {
  step: number;
  agent_id: string;
  status: string;
  duration_ms: number;
  error: string | null;
}
```

- [ ] **Step 2: Write validator contract types**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/validator/contract.ts`:
```typescript
import type { AgentContract, ValidationResult, StepValidation } from '../api/types';

export type { AgentContract, ValidationResult, StepValidation };
```

- [ ] **Step 3: Write fixtures loader**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/validator/fixtures.ts`:
```typescript
import type { AgentContract } from '../api/types';
import fixturesRaw from '../../../docs/superpowers/specs/fixtures/pipelines.json';

interface FixturesShape {
  agents: AgentContract[];
  pipelines: Record<string, string[]>;
}

export const FIXTURES: FixturesShape = fixturesRaw as FixturesShape;
```

- [ ] **Step 4: Write failing test**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/validator/validate.test.ts`:
```typescript
import { describe, test, expect } from 'vitest';
import { validatePipeline } from './validate';
import { FIXTURES } from './fixtures';

const contracts = new Map(FIXTURES.agents.map(a => [a.agent_id, a]));

describe('validatePipeline', () => {
  test('happy path mock_echo -> mock_logger with bootstrap', () => {
    const r = validatePipeline(['mock_echo', 'mock_logger'], contracts, new Set(['dynamic_storage.echo_input']));
    expect(r.valid).toBe(true);
    expect(r.failed_at).toBeNull();
    expect(r.steps.every(s => s.ok)).toBe(true);
  });

  test('missing field fails at first step', () => {
    const r = validatePipeline(['mock_logger'], contracts, new Set(['dynamic_storage.echo_input']));
    expect(r.valid).toBe(false);
    expect(r.failed_at).toBe(0);
    expect(r.steps[0].missing).toContain('dynamic_storage.echo_output');
  });

  test('chain broken when order wrong', () => {
    const r = validatePipeline(
      ['mock_logger', 'mock_echo'],
      contracts,
      new Set(['dynamic_storage.echo_input']),
    );
    expect(r.valid).toBe(false);
  });

  test('empty pipeline is valid', () => {
    const r = validatePipeline([], contracts);
    expect(r.valid).toBe(true);
  });

  test('unknown agent throws', () => {
    expect(() => validatePipeline(['ghost'], contracts)).toThrow();
  });
});
```

- [ ] **Step 5: Run, verify failure**

Run: `cd frontend && npm test`
Expected: `Cannot find module './validate'`.

- [ ] **Step 6: Implement validator**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/validator/validate.ts`:
```typescript
import type { AgentContract, ValidationResult, StepValidation } from '../api/types';

const DEFAULT_BOOTSTRAP = new Set(['user_id', 'user_background']);

export function validatePipeline(
  pipeline: string[],
  contracts: Map<string, AgentContract>,
  bootstrap?: Set<string>,
): ValidationResult {
  const provided = new Set(bootstrap ?? DEFAULT_BOOTSTRAP);
  const steps: StepValidation[] = [];

  pipeline.forEach((agentId, idx) => {
    const c = contracts.get(agentId);
    if (!c) throw new Error(`Unknown agent: ${agentId}`);
    const required = new Set(c.required_fields);
    const missing = [...required].filter(f => !provided.has(f));
    steps.push({
      step: idx,
      agent_id: agentId,
      required: [...required],
      provided_at_step: [...provided],
      missing,
      ok: missing.length === 0,
    });
    if (missing.length > 0) {
      return { valid: false, failed_at: idx, steps };
    }
    c.output_fields.forEach(f => provided.add(f));
  });

  return { valid: true, failed_at: null, steps };
}
```

- [ ] **Step 7: Write API client stub**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/api/client.ts`:
```typescript
import type { AgentContract, RunResponse } from './types';

const BASE = '/api';

export const apiClient = {
  async catalog(): Promise<AgentContract[]> {
    const r = await fetch(`${BASE}/agents/catalog`);
    if (!r.ok) throw new Error(`catalog failed: ${r.status}`);
    const body = await r.json();
    return body.agents;
  },

  async runPipeline(payload: {
    user_id: string;
    active_pipeline: string[];
    dynamic_storage?: Record<string, unknown>;
  }): Promise<RunResponse> {
    const r = await fetch(`${BASE}/pipelines/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!r.ok) throw new Error(`run failed: ${r.status}`);
    return r.json();
  },
};
```

- [ ] **Step 8: Run, verify pass**

Run: `cd frontend && npm test`
Expected: `5 passed` (validate.test.ts).

- [ ] **Step 9: Commit**

```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git add frontend/ docs/
git commit -m "feat(frontend): add TS types, validator mirror, API client"
```

---

## Task 15: Frontend UI Components — Shelf + Canvas + Workspace

**Files:**
- Create: `frontend/src/shelf/AgentShelf.tsx`, `frontend/src/shelf/AgentCard.tsx`, `frontend/src/canvas/FlowCanvas.tsx`, `frontend/src/canvas/AgentNode.tsx`, `frontend/src/canvas/DependencyEdge.tsx`, `frontend/src/canvas/usePipelineValidation.ts`, `frontend/src/workspace/WorkspaceRoot.tsx`, `frontend/src/workspace/PipelineRunLog.tsx`, `frontend/src/workspace/MockWidget.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `AgentContract` (from Task 14), `validatePipeline()` (from Task 14), `apiClient` (from Task 14)
- Produces: 3-pane layout with working drag/drop, live green/red validation, run button + log streaming

- [ ] **Step 1: Write `AgentCard`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/shelf/AgentCard.tsx`:
```typescript
import type { AgentContract } from '../api/types';

interface Props {
  contract: AgentContract;
  onDragStart: (agentId: string) => void;
}

export function AgentCard({ contract, onDragStart }: Props) {
  return (
    <div
      draggable
      onDragStart={e => {
        e.dataTransfer.setData('application/phd-agent-id', contract.agent_id);
        onDragStart(contract.agent_id);
      }}
      style={{
        border: '1px solid #444',
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
        cursor: 'grab',
        background: '#1a1a1a',
      }}
      title={`Requires: ${contract.required_fields.join(', ') || '(none)'}`}
    >
      <div style={{ fontWeight: 600 }}>{contract.name}</div>
      <div style={{ fontSize: 12, color: '#aaa' }}>{contract.category}</div>
      <div style={{ fontSize: 11, color: '#888', marginTop: 4 }}>
        {contract.required_fields.length > 0
          ? `Needs: ${contract.required_fields.join(', ')}`
          : 'No prerequisites'}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `AgentShelf`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/shelf/AgentShelf.tsx`:
```typescript
import type { AgentContract, Category } from '../api/types';
import { AgentCard } from './AgentCard';

interface Props {
  contracts: AgentContract[];
  onDragStart: (agentId: string) => void;
}

const CATEGORY_ORDER: Category[] = ['academic', 'writing', 'admin', 'mock'];

export function AgentShelf({ contracts, onDragStart }: Props) {
  const grouped = CATEGORY_ORDER.map(cat => ({
    cat,
    items: contracts.filter(c => c.category === cat),
  })).filter(g => g.items.length > 0);

  return (
    <aside style={{ width: 240, padding: 12, borderRight: '1px solid #333', overflowY: 'auto' }}>
      <h3 style={{ margin: '0 0 12px' }}>Agent Shelf</h3>
      {grouped.map(g => (
        <div key={g.cat} style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, textTransform: 'uppercase', color: '#888', marginBottom: 6 }}>
            {g.cat}
          </div>
          {g.items.map(c => (
            <AgentCard key={c.agent_id} contract={c} onDragStart={onDragStart} />
          ))}
        </div>
      ))}
    </aside>
  );
}
```

- [ ] **Step 3: Write `usePipelineValidation` hook**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/canvas/usePipelineValidation.ts`:
```typescript
import { useMemo } from 'react';
import type { AgentContract, ValidationResult } from '../api/types';
import { validatePipeline } from '../validator/validate';

export function usePipelineValidation(
  pipeline: string[],
  contracts: Map<string, AgentContract>,
  bootstrap?: Set<string>,
): ValidationResult {
  return useMemo(
    () => validatePipeline(pipeline, contracts, bootstrap),
    [pipeline, contracts, bootstrap],
  );
}
```

- [ ] **Step 4: Write `AgentNode`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/canvas/AgentNode.tsx`:
```typescript
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { AgentContract } from '../api/types';

interface AgentNodeData extends AgentContract {
  hasMissingDeps: boolean;
}

export function AgentNode({ data }: NodeProps<{ data: AgentNodeData }>) {
  const border = data.hasMissingDeps ? '#e53935' : '#43a047';
  return (
    <div
      style={{
        background: '#222',
        border: `2px solid ${border}`,
        borderRadius: 6,
        padding: 10,
        minWidth: 160,
        color: '#fff',
      }}
    >
      <Handle type="target" position={Position.Left} />
      <div style={{ fontWeight: 600 }}>{data.name}</div>
      <div style={{ fontSize: 11, color: '#aaa' }}>{data.agent_id}</div>
      {data.hasMissingDeps && (
        <div style={{ fontSize: 11, color: '#e53935', marginTop: 4 }}>
          ⚠ missing inputs
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
```

- [ ] **Step 5: Write `FlowCanvas`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/canvas/FlowCanvas.tsx`:
```typescript
import { useCallback, useMemo, useState } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  type Node,
  type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { AgentContract } from '../api/types';
import { AgentNode } from './AgentNode';
import { usePipelineValidation } from './usePipelineValidation';

const nodeTypes = { agent: AgentNode };

interface Props {
  contracts: AgentContract[];
  onRun: (pipeline: string[]) => void;
}

export function FlowCanvas({ contracts, onRun }: Props) {
  const contractMap = useMemo(
    () => new Map(contracts.map(c => [c.agent_id, c])),
    [contracts],
  );
  const [pipeline, setPipeline] = useState<string[]>([]);

  const validation = usePipelineValidation(pipeline, contractMap);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const id = e.dataTransfer.getData('application/phd-agent-id');
    if (id) setPipeline(p => [...p, id]);
  }, []);

  const nodes: Node[] = useMemo(
    () =>
      pipeline.map((id, idx) => {
        const c = contractMap.get(id);
        const step = validation.steps[idx];
        return {
          id: `${idx}-${id}`,
          type: 'agent',
          position: { x: idx * 220, y: 100 },
          data: {
            ...c,
            hasMissingDeps: step ? !step.ok : false,
          },
        };
      }),
    [pipeline, contractMap, validation],
  );

  const edges: Edge[] = useMemo(
    () =>
      pipeline.slice(0, -1).map((_, idx) => ({
        id: `e${idx}-${idx + 1}`,
        source: `${idx}-${pipeline[idx]}`,
        target: `${idx + 1}-${pipeline[idx + 1]}`,
        style: {
          stroke:
            validation.steps[idx + 1]?.ok === false
              ? '#e53935'
              : validation.steps.every(s => s.ok)
                ? '#43a047'
                : '#888',
          strokeWidth: 2,
        },
      })),
    [pipeline, validation],
  );

  return (
    <div style={{ flex: 1, position: 'relative' }} onDrop={onDrop} onDragOver={e => e.preventDefault()}>
      <ReactFlowProvider>
        <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
          <Background />
        </ReactFlow>
      </ReactFlowProvider>
      <div style={{ position: 'absolute', top: 12, right: 12 }}>
        <button
          data-testid="run-btn"
          disabled={!validation.valid || pipeline.length === 0}
          onClick={() => onRun(pipeline)}
          style={{
            padding: '8px 16px',
            background: validation.valid ? '#43a047' : '#555',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: validation.valid ? 'pointer' : 'not-allowed',
          }}
        >
          {validation.valid ? '▶ Run Pipeline' : 'Fix errors to run'}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 6: Write `PipelineRunLog`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/workspace/PipelineRunLog.tsx`:
```typescript
import type { SseEvent } from '../api/types';

interface Props {
  events: SseEvent[];
}

export function PipelineRunLog({ events }: Props) {
  return (
    <div data-testid="run-log" style={{ marginBottom: 16 }}>
      <h4 style={{ margin: '0 0 8px' }}>Run Log</h4>
      <div
        style={{
          background: '#000',
          color: '#0f0',
          fontFamily: 'monospace',
          fontSize: 12,
          padding: 8,
          borderRadius: 4,
          maxHeight: 200,
          overflowY: 'auto',
        }}
      >
        {events.length === 0
          ? <div style={{ color: '#666' }}>(no events yet)</div>
          : events.map((e, i) => (
              <div key={i}>
                [{e.step}] {e.agent_id || '(end)'} — {e.status} ({e.duration_ms}ms)
                {e.error && <span style={{ color: '#e53935' }}> ⚠ {e.error}</span>}
              </div>
            ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 7: Write `MockWidget`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/workspace/MockWidget.tsx`:
```typescript
interface Props {
  data: Record<string, unknown>;
  agentId: string;
}

export function MockWidget({ data, agentId }: Props) {
  return (
    <div
      data-testid={`widget-${agentId}`}
      style={{
        background: '#1a1a1a',
        border: '1px solid #444',
        borderRadius: 6,
        padding: 12,
        marginBottom: 12,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{agentId} widget</div>
      <pre style={{ fontSize: 11, color: '#aaa', margin: 0, overflow: 'auto' }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
```

- [ ] **Step 8: Write `WorkspaceRoot`**

Write `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/workspace/WorkspaceRoot.tsx`:
```typescript
import type { AgentContract, SseEvent } from '../api/types';
import { PipelineRunLog } from './PipelineRunLog';
import { MockWidget } from './MockWidget';

interface Props {
  activatedAgents: string[];
  contracts: AgentContract[];
  events: SseEvent[];
  finalData: Record<string, unknown>;
}

export function WorkspaceRoot({ activatedAgents, contracts, events, finalData }: Props) {
  return (
    <aside
      style={{
        width: 360,
        padding: 12,
        borderLeft: '1px solid #333',
        overflowY: 'auto',
        background: '#0e0e0e',
      }}
    >
      <h3 style={{ margin: '0 0 12px' }}>Workspace</h3>
      <PipelineRunLog events={events} />
      {activatedAgents.map(id => {
        const c = contracts.find(x => x.agent_id === id);
        return c ? <MockWidget key={id} agentId={id} data={finalData} /> : null;
      })}
    </aside>
  );
}
```

- [ ] **Step 9: Wire everything in `App.tsx`**

Replace `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/App.tsx`:
```typescript
import { useEffect, useState } from 'react';
import { AgentShelf } from './shelf/AgentShelf';
import { FlowCanvas } from './canvas/FlowCanvas';
import { WorkspaceRoot } from './workspace/WorkspaceRoot';
import { apiClient } from './api/client';
import type { AgentContract, SseEvent } from './api/types';

export default function App() {
  const [contracts, setContracts] = useState<AgentContract[]>([]);
  const [events, setEvents] = useState<SseEvent[]>([]);
  const [finalData, setFinalData] = useState<Record<string, unknown>>({});
  const [activatedAgents, setActivatedAgents] = useState<string[]>([]);

  useEffect(() => {
    apiClient.catalog().then(setContracts).catch(console.error);
  }, []);

  const onRun = async (pipeline: string[]) => {
    setEvents([]);
    setFinalData({});
    setActivatedAgents(pipeline);
    try {
      const result = await apiClient.runPipeline({
        user_id: 'demo-user',
        active_pipeline: pipeline,
        dynamic_storage: { echo_input: 'hello from frontend' },
      });
      setFinalData({ run_id: result.run_id, status: result.status });
    } catch (e) {
      console.error(e);
    }
  };

  if (contracts.length === 0) {
    return <div style={{ padding: 24 }}>Loading agent catalog…</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100vh', color: '#fff', background: '#0a0a0a' }}>
      <AgentShelf contracts={contracts} onDragStart={() => {}} />
      <FlowCanvas contracts={contracts} onRun={onRun} />
      <WorkspaceRoot
        activatedAgents={activatedAgents}
        contracts={contracts}
        events={events}
        finalData={finalData}
      />
    </div>
  );
}
```

Update `/home/robin/Documents/Ryan/PhD/openphd/frontend/src/App.test.tsx`:
```typescript
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders loading state initially', () => {
  render(<App />);
  expect(screen.getByText(/loading/i)).toBeInTheDocument();
});
```

- [ ] **Step 10: Run, verify pass**

Run: `cd frontend && npm test`
Expected: `1 passed` (App.test.tsx — the validator tests from Task 14 should still pass: total 6 passed).

- [ ] **Step 11: Commit**

```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git add frontend/
git commit -m "feat(frontend): add Shelf, Canvas, Workspace components"
```

---

## Task 16: End-to-End Smoke Test

**Files:**
- Modify: `README.md` (add run instructions)

**Interfaces:**
- Consumes: full backend + frontend
- Produces: documented verification that the skeleton works (per spec §10 DoD)

- [ ] **Step 1: Boot backend, hit endpoints manually**

Terminal A:
```bash
cd /home/robin/Documents/Ryan/PhD/openphd/backend
source .venv/bin/activate
uvicorn phd_agent.main:app --reload
```

Terminal B:
```bash
curl -s http://localhost:8000/health | grep -q '"ok":true' && echo "HEALTH OK"
curl -s http://localhost:8000/api/agents/catalog | grep -q mock_echo && echo "CATALOG OK"
curl -s -X POST http://localhost:8000/api/pipelines/validate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","active_pipeline":["mock_echo","mock_logger"],"dynamic_storage":{"echo_input":"hi"}}' \
  | grep -q '"valid":true' && echo "VALIDATE OK"
curl -s -X POST http://localhost:8000/api/pipelines/run \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","active_pipeline":["mock_echo","mock_logger"],"dynamic_storage":{"echo_input":"hi"}}' \
  | grep -q '"run_id"' && echo "RUN OK"
```
Expected: all four `OK` lines print.

- [ ] **Step 2: Boot frontend, verify it loads**

Terminal C:
```bash
cd /home/robin/Documents/Ryan/PhD/openphd/frontend
npm run dev
```

Terminal D:
```bash
sleep 5
curl -s http://localhost:5173 | grep -q "PhD-Agent" && echo "FRONTEND OK"
```
Expected: `FRONTEND OK`.

- [ ] **Step 3: Document verification in `README.md`**

Append to `/home/robin/Documents/Ryan/PhD/openphd/README.md`:
```markdown
## Skeleton Verification (spec §10 DoD)

Run these commands in two terminals after `pip install -e ".[dev]"`:

**Terminal A** (backend):
```bash
cd backend
source .venv/bin/activate
uvicorn phd_agent.main:app --reload
```

**Terminal B** (frontend):
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173, drag `mock_echo` then `mock_logger` from the left shelf to the canvas, see a green line, click ▶ Run, and observe the right-side workspace populate with widgets.
```

- [ ] **Step 4: Commit**

```bash
cd /home/robin/Documents/Ryan/PhD/openphd
git add README.md
git commit -m "docs: document skeleton verification steps"
```

---

## Self-Review Checklist (run before handing off)

After writing, the plan author must verify:

1. **Spec coverage:** Each spec section (§4 backend, §5 frontend, §7 plugin contract, §10 DoD, §11 testing) has at least one task implementing it.
2. **No placeholders:** No "TBD"/"TODO"/"fill in details". Every code block is complete.
3. **Type consistency:** `GlobalState` defined Task 2, consumed everywhere; `AgentContract` Task 2, consumed everywhere; `validate_pipeline` signature matches between Tasks 5 and 14.
4. **Test coverage:** Backend has 12+ test files; frontend has at least 5 validate tests + 1 App test.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-25-phd-agent-v2-skeleton.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
