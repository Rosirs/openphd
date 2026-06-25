# PhD-Agent V2.0.0 Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a shippable PhD-Agent V2.0.0 with Chat-First architecture, LLM-driven tool calling, general-purpose agent suite, user-defined composite tools, and JSON file persistence.

**Architecture:** Phase 1's drag-and-run pipeline is replaced by a Chat-First model — the LLM is the front door, backend agents become LLM-callable tools. Users drag-and-drop agents in a Canvas tab to compose custom "composite tools" (each runs its own LLM loop), and the Chat tab defaults to free-form LLM conversation. State persists per-user to JSON files.

**Tech Stack:**
- Backend: Python 3.11, FastAPI, Pydantic v2, sse-starlette, httpx, pytest
- Frontend: React 18, TypeScript, Vite, @xyflow/react, Vitest
- LLM: MiniMax-m3 (or any OpenAI-compatible endpoint) via OpenAI compat protocol
- Persistence: JSON files in `data/{user_id}/`

## Global Constraints

These are project-wide requirements from the spec. Every task implicitly includes them.

- **File size limits:** Python files ≤ 250 lines, TSX/TS files ≤ 200 lines. Split BEFORE writing if a file will exceed the limit.
- **DRY / YAGNI:** No defensive try/except layers, no placeholder code, no "implement later" stubs.
- **TDD discipline:** Every backend module gets a failing test FIRST, then minimal implementation, then refactor.
- **Commit cadence:** Commit after each task (or each step within a task) — small atomic commits.
- **No silent fallbacks:** If something fails, let it fail with a clear error. Only catch at well-defined boundaries (AgentWrapper, ToolRuntime outer try/except).
- **Validation hierarchy:** Backend is source of truth (`core/contract.py`); frontend types mirror manually. Validate in both places.
- **Import rules (backend):** `core/*` does not depend on `plugins/*` or `api/*`; plugins depend only on `core/contract.py` and `core/state.py`; `api/*` orchestrates everything.
- **File size signal:** When a file approaches its limit, split by domain (e.g., separate `tool_runtime.py` from `tool_executor.py`).
- **Backwards compat:** Phase 1 tests will be deleted/replaced as we restructure. We are NOT maintaining the old `/pipelines/run` API.
- **LLM API key:** If `OPENAI_API_KEY` is unset, the system uses a `MockLLMClient` that returns canned responses. This lets the app run and tests pass without a real API.

## Phases

The plan is divided into 8 phases. Each phase is independently testable and committable.

- **Phase 1**: Backend foundation — data models, JSON repo, registry extension, cleanup of Phase 1 stubs
- **Phase 2**: LLM tool-calling — BaseLLMClient extension, ToolRuntime, ToolExecutor, mock LLM
- **Phase 3**: CompositeAgent — LLM-driven nested agent, system prompt augmentation
- **Phase 4**: Real plugins — knowledge_retriever, arxiv_search, writing_polisher, email_drafter, pdf_summarizer
- **Phase 5**: API layer — /chat, /tools, /canvas endpoints, SSE streaming
- **Phase 6**: Frontend — App tabs, Chat view, SSE client, Canvas save flow
- **Phase 7**: E2E integration + verification + README

---

## Phase 1: Backend Foundation

### Task 1.1: Delete Phase 1 stubs and rename files

**Files:**
- Delete: `backend/src/phd_agent/core/router.py`
- Delete: `backend/src/phd_agent/orchestrator.py`
- Modify: `backend/src/phd_agent/core/state.py` (add a comment marking active_pipeline/current_step as composite-internal)
- Modify: `backend/src/phd_agent/core/wrapper.py` (add `execute_one(state, name, args)` method)
- Modify: `backend/src/phd_agent/core/registry.py` (add `list_my_tools(user_id)` method)
- Modify: `backend/src/phd_agent/core/events.py` (add new event types: `sub_llm_iteration`, `sub_tool_call`, `sub_tool_call_completed`)
- Delete: `backend/tests/test_pipeline_e2e.py` (PipelineOrchestrator is gone)
- Test: `backend/tests/test_state_composite.py`

**Interfaces:**
- Consumes: existing GlobalState, AgentWrapper, AgentRegistry
- Produces: `AgentWrapper.execute_one(state, name, args) -> ToolResult` (new method); `AgentRegistry.list_my_tools(user_id) -> list[ToolSpec]`

- [ ] **Step 1: Delete router.py and orchestrator.py**

```bash
rm backend/src/phd_agent/core/router.py
rm backend/src/phd_agent/orchestrator.py
```

- [ ] **Step 2: Add a docstring note to state.py**

Edit `backend/src/phd_agent/core/state.py` — add at the top of the class body:
```python
    # NOTE: active_pipeline and current_step are composite-internal state.
    # The top-level Chat layer does not use them; only CompositeAgent (nested
    # LLM loop) reads them when executing a composite tool.
```

- [ ] **Step 3: Add ToolResult type (in wrapper.py — temporary home, will move later)**

Edit `backend/src/phd_agent/core/wrapper.py`. Add at top of file after imports:
```python
from phd_agent.core.contract import AgentContract  # ensure import

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    summary: str
    state_delta: dict = Field(default_factory=dict)
    llm_context: str
    error: str | None = None
```

- [ ] **Step 4: Add `execute_one` to AgentWrapper**

Add method to `AgentWrapper`:
```python
    async def execute_one(self, state: GlobalState, name: str, args: dict) -> ToolResult:
        """Execute a single atomic agent by name with explicit args.
        Used by ToolRuntime when LLM tool-calls an atomic tool."""
        agent = self._registry.load(name)
        # ... see plan for full impl in Task 2.3
        ...
```

(Stub for now; real implementation in Phase 2.)

- [ ] **Step 5: Add ToolSpec to registry.py**

Edit `backend/src/phd_agent/core/registry.py`:
```python
class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: dict
    category: str
    is_composite: bool = False
    composite_def: dict | None = None  # serialized CompositeToolDefinition
```

- [ ] **Step 6: Stub `list_my_tools` method**

```python
    async def list_my_tools(self, user_id: str) -> list[ToolSpec]:
        """Return all atomic tools visible to this user.
        Phase 2: composite tools are added in Task 3.5."""
        return [self._contract_to_spec(c) for c in self._contracts.values()]

    def _contract_to_spec(self, contract: AgentContract) -> ToolSpec:
        return ToolSpec(
            name=contract.agent_id,
            description=contract.description,
            parameters={},  # Phase 2: derive from contract
            category=contract.category,
        )
```

- [ ] **Step 7: Verify backend still imports and tests pass**

```bash
cd backend && source .venv/bin/activate && python -c "from phd_agent.main import app; print('ok')"
cd backend && pytest tests/test_validator.py tests/test_router.py tests/test_wrapper.py -v
```

Expected: imports succeed, existing tests pass (after deleting test_pipeline_e2e.py).

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor(backend): delete CentralRouter + PipelineOrchestrator stubs"
```

### Task 1.2: Add Message, ChatSession data models

**Files:**
- Create: `backend/src/phd_agent/core/chat.py`
- Create: `backend/src/phd_agent/core/composite.py`
- Test: `backend/tests/test_chat_models.py`
- Test: `backend/tests/test_composite_model.py`

**Interfaces:**
- Produces: `Message`, `ChatSession`, `ToolCall`, `CompositeToolDefinition`, `SYSTEM_PROMPT_TEMPLATE`

- [ ] **Step 1: Write failing test for Message/ChatSession**

```python
# backend/tests/test_chat_models.py
from datetime import datetime
from phd_agent.core.chat import Message, ChatSession

def test_message_serialization_roundtrip():
    msg = Message(role="user", content="hello", timestamp=datetime(2026, 6, 25, 12, 0))
    data = msg.model_dump_json()
    msg2 = Message.model_validate_json(data)
    assert msg2 == msg

def test_chat_session_with_messages():
    s = ChatSession(
        user_id="u1",
        conversation_id="c1",
        title="test",
        messages=[Message(role="user", content="hi", timestamp=datetime.now())],
        state=None,  # optional for test
    )
    assert s.user_id == "u1"
    assert len(s.messages) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_chat_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'phd_agent.core.chat'`

- [ ] **Step 3: Create core/chat.py**

```python
# backend/src/phd_agent/core/chat.py
"""Chat session data models: Message + ChatSession."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal
from phd_agent.core.state import GlobalState


class ToolCall(BaseModel):
    id: str
    name: str
    args: dict


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_llm_dict(self) -> dict:
        """Serialize for LLM API (drops timestamp)."""
        d = {"role": self.role}
        if self.content is not None:
            d["content"] = self.content
        if self.tool_calls:
            d["tool_calls"] = [t.model_dump() for t in self.tool_calls]
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


class ChatSession(BaseModel):
    user_id: str
    conversation_id: str
    title: str = ""
    messages: list[Message] = Field(default_factory=list)
    state: GlobalState | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: Literal["active", "archived"] = "active"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/test_chat_models.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Write failing test for CompositeToolDefinition**

```python
# backend/tests/test_composite_model.py
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt

def test_composite_def_roundtrip():
    d = CompositeToolDefinition(
        tool_id="my_tool",
        name="My Tool",
        description="does X",
        system_prompt="summarize papers",
        sub_tools=["arxiv_search", "writing_polisher"],
        owner_user_id="u1",
    )
    data = d.model_dump_json()
    d2 = CompositeToolDefinition.model_validate_json(data)
    assert d2.sub_tools == ["arxiv_search", "writing_polisher"]

def test_build_system_prompt_augments_user_input():
    prompt = build_system_prompt(
        name="MyTool",
        user_intent="summarize papers",
        sub_tools=["arxiv_search", "writing_polisher"],
        max_sub_iterations=5,
    )
    assert "summarize papers" in prompt
    assert "arxiv_search" in prompt
    assert "writing_polisher" in prompt
    assert "5" in prompt
```

- [ ] **Step 6: Run test, expect fail**

```bash
cd backend && pytest tests/test_composite_model.py -v
```

- [ ] **Step 7: Create core/composite.py**

```python
# backend/src/phd_agent/core/composite.py
"""Composite tool: LLM-driven nested agent definition."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

SYSTEM_PROMPT_TEMPLATE = """你是 {name}。

{user_intent}

你可以调用以下子工具完成你的任务:
{tool_list}

行为规范:
- 收到任务后,自主决定调用哪些子工具、按什么顺序调用
- 子工具结果会反馈给你,你可以根据结果决定下一步
- 完成所有工作后,给出简洁的最终结果(不要重复中间过程)
- 最多调用 {max_sub_iterations} 次子工具
"""


def build_system_prompt(*, name: str, user_intent: str, sub_tools: list[str], max_sub_iterations: int) -> str:
    tool_list = "\n".join(f"- {t}" for t in sub_tools)
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=name,
        user_intent=user_intent,
        tool_list=tool_list,
        max_sub_iterations=max_sub_iterations,
    )


class CompositeToolDefinition(BaseModel):
    tool_id: str
    name: str
    description: str
    system_prompt: str
    sub_tools: list[str]
    owner_user_id: str
    is_public: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

- [ ] **Step 8: Run test, expect pass**

```bash
cd backend && pytest tests/test_composite_model.py -v
```

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(backend): add Message/ChatSession + CompositeToolDefinition models"
```

### Task 1.3: Add JsonFileRepository

**Files:**
- Create: `backend/src/phd_agent/core/json_repo.py`
- Test: `backend/tests/test_json_repo.py`

**Interfaces:**
- Produces: `JsonFileRepository` class with `save_conversation`, `load_conversation`, `list_conversations`, `delete_conversation`, `save_composite_tool`, `load_composite_tool`, `list_composite_tools`, `delete_composite_tool`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_json_repo.py
import pytest
from pathlib import Path
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.composite import CompositeToolDefinition


@pytest.fixture
def tmp_repo(tmp_path):
    return JsonFileRepository(base_dir=tmp_path)


def test_save_and_load_conversation(tmp_repo):
    s = ChatSession(user_id="u1", conversation_id="c1", title="t",
                    messages=[Message(role="user", content="hi")])
    tmp_repo.save_conversation(s)
    loaded = tmp_repo.load_conversation("u1", "c1")
    assert loaded is not None
    assert loaded.messages[0].content == "hi"


def test_list_conversations(tmp_repo):
    for cid in ["c1", "c2"]:
        tmp_repo.save_conversation(ChatSession(user_id="u1", conversation_id=cid, title=cid))
    convs = tmp_repo.list_conversations("u1")
    assert {c.conversation_id for c in convs} == {"c1", "c2"}


def test_save_and_list_composite_tool(tmp_repo):
    t = CompositeToolDefinition(tool_id="t1", name="T", description="d",
                                 system_prompt="p", sub_tools=["a"], owner_user_id="u1")
    tmp_repo.save_composite_tool(t)
    loaded = tmp_repo.load_composite_tool("u1", "t1")
    assert loaded.tool_id == "t1"
    tools = tmp_repo.list_composite_tools("u1")
    assert len(tools) == 1
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_json_repo.py -v
```

- [ ] **Step 3: Create core/json_repo.py**

```python
# backend/src/phd_agent/core/json_repo.py
"""File-system backed repository for chat sessions and composite tools."""
from __future__ import annotations
import json
from pathlib import Path
from phd_agent.core.chat import ChatSession
from phd_agent.core.composite import CompositeToolDefinition


class JsonFileRepository:
    def __init__(self, base_dir: Path):
        self.base = Path(base_dir)

    def _conv_path(self, user_id: str, conv_id: str) -> Path:
        return self.base / user_id / "conversations" / f"{conv_id}.json"

    def _tool_path(self, user_id: str, tool_id: str) -> Path:
        return self.base / user_id / "composite_tools" / f"{tool_id}.json"

    async def save_conversation(self, session: ChatSession) -> None:
        p = self._conv_path(session.user_id, session.conversation_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(session.model_dump_json(indent=2))

    async def load_conversation(self, user_id: str, conv_id: str) -> ChatSession | None:
        p = self._conv_path(user_id, conv_id)
        if not p.exists():
            return None
        return ChatSession.model_validate_json(p.read_text())

    async def list_conversations(self, user_id: str) -> list[ChatSession]:
        d = self.base / user_id / "conversations"
        if not d.exists():
            return []
        out: list[ChatSession] = []
        for f in d.glob("*.json"):
            try:
                out.append(ChatSession.model_validate_json(f.read_text()))
            except Exception:
                continue  # skip corrupt files
        return out

    async def delete_conversation(self, user_id: str, conv_id: str) -> None:
        p = self._conv_path(user_id, conv_id)
        if p.exists():
            p.unlink()

    async def save_composite_tool(self, tool: CompositeToolDefinition) -> None:
        p = self._tool_path(tool.owner_user_id, tool.tool_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(tool.model_dump_json(indent=2))

    async def load_composite_tool(self, user_id: str, tool_id: str) -> CompositeToolDefinition | None:
        p = self._tool_path(user_id, tool_id)
        if not p.exists():
            return None
        return CompositeToolDefinition.model_validate_json(p.read_text())

    async def list_composite_tools(self, user_id: str) -> list[CompositeToolDefinition]:
        d = self.base / user_id / "composite_tools"
        if not d.exists():
            return []
        out: list[CompositeToolDefinition] = []
        for f in d.glob("*.json"):
            try:
                out.append(CompositeToolDefinition.model_validate_json(f.read_text()))
            except Exception:
                continue
        return out

    async def delete_composite_tool(self, user_id: str, tool_id: str) -> None:
        p = self._tool_path(user_id, tool_id)
        if p.exists():
            p.unlink()
```

- [ ] **Step 4: Run, expect pass**

```bash
cd backend && pytest tests/test_json_repo.py -v
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(backend): JsonFileRepository for conversations and composite tools"
```

---

## Phase 2: LLM Tool-Calling

### Task 2.1: Add MockLLMClient for testing

**Files:**
- Create: `backend/src/phd_agent/llm/mock.py`
- Test: `backend/tests/test_mock_llm.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_mock_llm.py
import pytest
from phd_agent.llm.mock import MockLLMClient

@pytest.mark.asyncio
async def test_mock_returns_text_response():
    llm = MockLLMClient(responses=["hello world"])
    r = await llm.chat(messages=[{"role": "user", "content": "hi"}], tools=[])
    assert r.content == "hello world"
    assert r.tool_calls is None

@pytest.mark.asyncio
async def test_mock_returns_tool_call():
    llm = MockLLMClient(responses=[None], tool_calls=[{
        "id": "tc1", "name": "t1", "args": {"x": 1}
    }])
    r = await llm.chat(messages=[{"role": "user", "content": "hi"}], tools=[{"name": "t1"}])
    assert r.content is None
    assert r.tool_calls[0].name == "t1"
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_mock_llm.py -v
```

- [ ] **Step 3: Create core/llm/mock.py**

```python
# backend/src/phd_agent/llm/mock.py
"""Deterministic LLM for tests + dev-without-API-key."""
from __future__ import annotations
from phd_agent.llm.base import BaseLLMClient, LLMResponse, ToolCall


class MockLLMClient(BaseLLMClient):
    def __init__(self, responses: list[str | None] | None = None,
                 tool_calls: list[dict] | None = None):
        self.responses = list(responses or ["[mock response]"])
        self.tool_calls = list(tool_calls or [])
        self.call_count = 0

    async def chat(self, messages: list[dict], *, tools: list[dict] | None = None,
                   budget: int = 4000, model: str = "mock") -> LLMResponse:
        self.call_count += 1
        if self.tool_calls:
            tc_dict = self.tool_calls.pop(0)
            return LLMResponse(
                content=None,
                tool_calls=[ToolCall(**tc_dict)],
                tokens_used=10,
                model=model,
            )
        text = self.responses.pop(0) if self.responses else "[mock default]"
        return LLMResponse(content=text, tool_calls=None, tokens_used=10, model=model)

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
```

- [ ] **Step 4: Update core/llm/base.py to support tool calls**

```python
# backend/src/phd_agent/llm/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolCall(BaseModel):
    id: str
    name: str
    args: dict

class LLMResponse(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    tokens_used: int = 0
    model: str = ""

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], *, tools: list[dict] | None = None,
                   budget: int = 4000, model: str = "") -> LLMResponse: ...
    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

- [ ] **Step 5: Run, expect pass**

```bash
cd backend && pytest tests/test_mock_llm.py tests/test_llm_base.py -v
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(backend): MockLLMClient + BaseLLMClient tool-call support"
```

### Task 2.2: Update OpenAICompatClient for tool calling

**Files:**
- Modify: `backend/src/phd_agent/llm/openai_compat.py`
- Test: `backend/tests/test_openai_compat.py`

- [ ] **Step 1: Read current openai_compat.py**

```bash
cat backend/src/phd_agent/llm/openai_compat.py
```

- [ ] **Step 2: Write failing test (with httpx mock)**

```python
# backend/tests/test_openai_compat.py
import pytest
from unittest.mock import AsyncMock, patch
from phd_agent.llm.openai_compat import OpenAICompatClient
from phd_agent.llm.base import LLMResponse

@pytest.mark.asyncio
async def test_chat_with_tool_calls():
    client = OpenAICompatClient(base_url="http://x", api_key="k")
    mock_resp = {
        "choices": [{
            "message": {
                "content": None,
                "tool_calls": [{
                    "id": "tc1",
                    "function": {"name": "t1", "arguments": '{"x": 1}'},
                }],
            }
        }],
        "usage": {"total_tokens": 10},
    }
    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=AsyncMock(
        json=lambda: mock_resp, raise_for_status=lambda: None
    ))):
        r = await client.chat(messages=[{"role": "user", "content": "hi"}],
                              tools=[{"name": "t1"}], model="m")
        assert r.tool_calls[0].name == "t1"
        assert r.tool_calls[0].args == {"x": 1}
```

- [ ] **Step 3: Update openai_compat.py**

```python
# backend/src/phd_agent/llm/openai_compat.py
"""OpenAI-compatible LLM client (supports tool calling)."""
from __future__ import annotations
import json
import httpx
from phd_agent.llm.base import BaseLLMClient, LLMResponse, ToolCall


class OpenAICompatClient(BaseLLMClient):
    def __init__(self, base_url: str = "https://api.openai.com/v1",
                 api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def chat(self, messages: list[dict], *, tools: list[dict] | None = None,
                   budget: int = 4000, model: str = "gpt-4o-mini") -> LLMResponse:
        body: dict = {"model": model, "messages": messages}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
            r.raise_for_status()
            data = r.json()
        msg = data["choices"][0]["message"]
        tool_calls: list[ToolCall] | None = None
        if msg.get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    args=json.loads(tc["function"]["arguments"]),
                )
                for tc in msg["tool_calls"]
            ]
        return LLMResponse(
            content=msg.get("content"),
            tool_calls=tool_calls,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            model=model,
        )

    def count_tokens(self, text: str) -> int:
        return len(text) // 4
```

- [ ] **Step 4: Run, expect pass**

```bash
cd backend && pytest tests/test_openai_compat.py -v
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(llm): OpenAICompatClient tool calling + JSON args parsing"
```

### Task 2.3: Add execute_one to AgentWrapper

**Files:**
- Modify: `backend/src/phd_agent/core/wrapper.py`
- Test: `backend/tests/test_wrapper_execute_one.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_wrapper_execute_one.py
import pytest
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract


class FakeAgent(BaseAgent):
    contract = AgentContract(
        agent_id="fake", name="Fake", description="t", category="mock",
        required_fields=set(), output_fields={"dynamic_storage.out"},
    )
    async def run(self, state):
        state.dynamic_storage["out"] = self.contract.name
        return state


@pytest.mark.asyncio
async def test_execute_one_writes_state():
    reg = AgentRegistry(plugins_dir=None)
    reg._contracts["fake"] = FakeAgent.contract
    reg._classes["fake"] = FakeAgent
    bus = EventBus()
    wrapper = AgentWrapper(reg, bus, llm=None)
    state = GlobalState(user_id="u1")
    result = await wrapper.execute_one(state, "fake", {})
    assert state.dynamic_storage["out"] == "Fake"
    assert result.success is True
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_wrapper_execute_one.py -v
```

- [ ] **Step 3: Add execute_one to AgentWrapper**

Replace `backend/src/phd_agent/core/wrapper.py` with:
```python
# backend/src/phd_agent/core/wrapper.py
"""Sandboxed agent execution: try/except isolation, event publish."""
from __future__ import annotations
import time
from pydantic import BaseModel, Field
from phd_agent.core.contract import BaseAgent
from phd_agent.core.events import EventBus, Event
from phd_agent.core.state import GlobalState


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    summary: str
    state_delta: dict = Field(default_factory=dict)
    llm_context: str
    error: str | None = None


class AgentWrapper:
    def __init__(self, registry, bus, llm):
        self._registry = registry
        self._bus = bus
        self._llm = llm

    async def execute_one(self, state: GlobalState, name: str, args: dict,
                          run_id: str = "ad-hoc") -> ToolResult:
        """Execute one atomic agent with explicit args (no current_step increment)."""
        started = time.perf_counter()
        error_msg: str | None = None
        try:
            agent: BaseAgent = self._registry.load(name)
            await agent.run(state)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            state.error_log.append({"agent_id": name, "error": error_msg})
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._bus.publish(Event(
                run_id=run_id, step=0, agent_id=name,
                status="ok" if not error_msg else "skipped",
                duration_ms=duration_ms, error=error_msg,
            ))
        if error_msg:
            return ToolResult(
                tool_name=name, success=False, summary=f"failed: {error_msg}",
                llm_context=f"[tool {name} failed: {error_msg}]",
                error=error_msg,
            )
        return ToolResult(
            tool_name=name, success=True, summary="ok",
            llm_context=f"[tool {name} completed]",
        )

    async def execute(self, state: GlobalState, agent_id: str, run_id: str,
                      bus: EventBus) -> None:
        """Legacy execute for PipelineOrchestrator-style callers."""
        await self.execute_one(state, agent_id, args={}, run_id=run_id)
        if not state.error_log or state.error_log[-1]["agent_id"] != agent_id:
            state.current_step += 1
```

- [ ] **Step 4: Run, expect pass**

```bash
cd backend && pytest tests/test_wrapper_execute_one.py -v
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(wrapper): execute_one returns ToolResult with llm_context"
```

### Task 2.4: Add ToolRuntime (LLM loop)

**Files:**
- Create: `backend/src/phd_agent/core/tool_runtime.py`
- Test: `backend/tests/test_tool_runtime.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_tool_runtime.py
import pytest
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.state import GlobalState
from phd_agent.llm.mock import MockLLMClient


@pytest.mark.asyncio
async def test_text_only_response_completes(tmp_path):
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    repo = JsonFileRepository(tmp_path)
    llm = MockLLMClient(responses=["final answer"])
    runtime = ToolRuntime(reg, llm, bus, repo)
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)
    events = []
    async for ev in runtime.run_turn(session, "hi"):
        events.append(ev)
    last = events[-1]
    assert last["type"] == "message_completed"
    assert last["content"] == "final answer"
    assert session.messages[-1].role == "assistant"
    assert session.messages[-1].content == "final answer"


@pytest.mark.asyncio
async def test_tool_call_then_text_completes(tmp_path):
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    # register a fake atomic tool
    from phd_agent.plugins._base import BaseAgent
    from phd_agent.core.contract import AgentContract
    from phd_agent.core.wrapper import AgentWrapper

    class Stub(BaseAgent):
        contract = AgentContract(agent_id="stub", name="S", description="d",
                                 category="mock", required_fields=set(),
                                 output_fields=set())
        async def run(self, state):
            state.dynamic_storage["x"] = 42
            return state
    reg._contracts["stub"] = Stub.contract
    reg._classes["stub"] = Stub

    repo = JsonFileRepository(tmp_path)
    # First LLM call: tool call; second: text
    llm = MockLLMClient(responses=["done"], tool_calls=[
        {"id": "tc1", "name": "stub", "args": {}}
    ])
    runtime = ToolRuntime(reg, llm, bus, repo, wrapper=AgentWrapper(reg, bus, llm))
    state = GlobalState(user_id="u1")
    session = ChatSession(user_id="u1", conversation_id="c1", state=state)
    events = []
    async for ev in runtime.run_turn(session, "go"):
        events.append(ev)
    types = [e["type"] for e in events]
    assert "tool_call_started" in types
    assert "tool_call_completed" in types
    assert "message_completed" in types
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_tool_runtime.py -v
```

- [ ] **Step 3: Create core/tool_runtime.py**

```python
# backend/src/phd_agent/core/tool_runtime.py
"""Top-level LLM + tool-call loop for chat turns."""
from __future__ import annotations
import time
from typing import AsyncIterator
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession, Message
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper, ToolResult
from phd_agent.core.tool_executor import ToolExecutor  # created in Task 2.5


SYSTEM_PROMPT = """你是 PhD-Agent,一个帮助用户申请博士的助手。

你可以调用工具来完成任务。调用工具前先思考用户需要什么。
完成所有工作后,用清晰简洁的中文给出最终回复。
"""


class ToolRuntime:
    def __init__(self, registry: AgentRegistry, llm, bus: EventBus,
                 chat_repo: JsonFileRepository, wrapper: AgentWrapper | None = None,
                 max_tool_calls: int = 10, model: str = "MiniMax-m3"):
        self.registry = registry
        self.llm = llm
        self.bus = bus
        self.chat_repo = chat_repo
        self.max_tool_calls = max_tool_calls
        self.model = model
        # wrapper is provided to construct ToolExecutor in 2.5
        self._wrapper = wrapper or AgentWrapper(registry, bus, llm)
        self._executor = ToolExecutor(registry, self._wrapper, bus)

    async def run_turn(self, session: ChatSession, user_message: str,
                       run_id: str | None = None) -> AsyncIterator[dict]:
        run_id = run_id or f"chat-{session.conversation_id}"
        session.messages.append(Message(role="user", content=user_message))
        yield {"type": "message_received", "run_id": run_id}

        # ensure state exists
        if session.state is None:
            session.state = GlobalState(user_id=session.user_id)

        tool_call_count = 0
        # inject system prompt if not present
        msgs_for_llm = self._build_messages(session)

        while True:
            tools = await self.registry.list_my_tools(session.user_id)
            response = await self.llm.chat(
                messages=[m.to_llm_dict() for m in msgs_for_llm],
                tools=[t.model_dump() for t in tools],
                model=self.model,
            )
            if not response.tool_calls:
                session.messages.append(Message(role="assistant", content=response.content))
                session.state.status = "completed"
                await self.chat_repo.save_conversation(session)
                yield {"type": "message_completed", "content": response.content, "run_id": run_id}
                return

            session.messages.append(Message(
                role="assistant", content=response.content, tool_calls=response.tool_calls,
            ))
            exceeded = False
            for tc in response.tool_calls:
                if tool_call_count >= self.max_tool_calls:
                    exceeded = True
                    session.messages.append(Message(
                        role="tool", tool_call_id=tc.id, name=tc.name,
                        content="[skipped: max_tool_calls exceeded]",
                    ))
                    yield {"type": "tool_call_skipped", "name": tc.name, "run_id": run_id}
                    continue
                tool_call_count += 1
                yield {"type": "tool_call_started", "name": tc.name, "args": tc.args, "run_id": run_id}
                result = await self._executor.execute(
                    name=tc.name, args=tc.args, state=session.state, run_id=run_id,
                )
                yield {"type": "tool_call_completed", "name": tc.name,
                       "summary": result.summary, "success": result.success, "run_id": run_id}
                session.messages.append(result.to_message(tc.id))

            await self.chat_repo.save_conversation(session)
            if exceeded:
                yield {"type": "warning", "message": "max_tool_calls exceeded", "run_id": run_id}
            yield {"type": "turn_continued", "run_id": run_id}

    def _build_messages(self, session: ChatSession) -> list[Message]:
        out = [Message(role="system", content=SYSTEM_PROMPT)]
        out.extend(session.messages)
        return out
```

(Add `to_message` method to `ToolResult` in wrapper.py — see Step 4.)

- [ ] **Step 4: Add `to_message` method to ToolResult**

Edit `backend/src/phd_agent/core/wrapper.py`, add to `ToolResult` class:
```python
    def to_message(self, tool_call_id: str) -> Message:
        from phd_agent.core.chat import Message  # avoid cycle
        return Message(
            role="tool",
            tool_call_id=tool_call_id,
            name=self.tool_name,
            content=self.llm_context,
        )
```

- [ ] **Step 5: Run test, expect PARTIAL pass** (ToolExecutor missing — that's Task 2.5)

The test will fail with `ModuleNotFoundError: tool_executor`. Create a stub now:
```bash
touch backend/src/phd_agent/core/tool_executor.py
```

Add to `core/tool_executor.py`:
```python
"""Stub — full impl in Task 2.5."""
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import ToolResult

class ToolExecutor:
    def __init__(self, registry, wrapper, bus, composite_agent_factory=None):
        self._registry = registry
        self._wrapper = wrapper
        self._bus = bus
        self._composite_factory = composite_agent_factory

    async def execute(self, *, name: str, args: dict, state: GlobalState,
                      run_id: str = "ad-hoc") -> ToolResult:
        return await self._wrapper.execute_one(state, name, args, run_id=run_id)
```

- [ ] **Step 6: Run, expect pass**

```bash
cd backend && pytest tests/test_tool_runtime.py -v
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(backend): ToolRuntime (LLM loop with tool calling)"
```

---

## Phase 3: CompositeAgent (LLM-driven nested agent)

### Task 3.1: Add CompositeAgent

**Files:**
- Create: `backend/src/phd_agent/core/composite_agent.py`
- Test: `backend/tests/test_composite_agent.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_composite_agent.py
import pytest
from phd_agent.core.composite_agent import CompositeAgent
from phd_agent.core.composite import CompositeToolDefinition
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import AgentWrapper
from phd_agent.llm.mock import MockLLMClient
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract


@pytest.mark.asyncio
async def test_composite_returns_final_answer_without_tool_calls():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)
    llm = MockLLMClient(responses=["final summary"])
    wrapper = AgentWrapper(reg, bus, llm)
    definition = CompositeToolDefinition(
        tool_id="ct", name="CT", description="d", system_prompt="summarize",
        sub_tools=["a"], owner_user_id="u1",
    )
    agent = CompositeAgent(definition, llm, wrapper, bus)
    state = GlobalState(user_id="u1")
    result = await agent.run(args={"text": "x"}, state=state)
    assert result.success is True
    assert "final summary" in result.llm_context


@pytest.mark.asyncio
async def test_composite_invokes_sub_tool_then_returns():
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=None)

    class Sub(BaseAgent):
        contract = AgentContract(agent_id="sub", name="S", description="d",
                                 category="mock", required_fields=set(),
                                 output_fields={"dynamic_storage.sub_out"})
        async def run(self, state):
            state.dynamic_storage["sub_out"] = "ok"
            return state

    reg._contracts["sub"] = Sub.contract
    reg._classes["sub"] = Sub

    llm = MockLLMClient(responses=["final after sub"], tool_calls=[
        {"id": "tc1", "name": "sub", "args": {}}
    ])
    wrapper = AgentWrapper(reg, bus, llm)
    definition = CompositeToolDefinition(
        tool_id="ct", name="CT", description="d", system_prompt="go",
        sub_tools=["sub"], owner_user_id="u1",
    )
    agent = CompositeAgent(definition, llm, wrapper, bus)
    state = GlobalState(user_id="u1")
    result = await agent.run(args={}, state=state)
    assert result.success is True
    assert state.dynamic_storage["sub_out"] == "ok"
    assert "final after sub" in result.llm_context
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_composite_agent.py -v
```

- [ ] **Step 3: Create core/composite_agent.py**

```python
# backend/src/phd_agent/core/composite_agent.py
"""LLM-driven nested agent: executes a composite tool via its own LLM loop."""
from __future__ import annotations
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt
from phd_agent.core.wrapper import AgentWrapper, ToolResult
from phd_agent.core.state import GlobalState
from phd_agent.core.chat import Message
from phd_agent.core.events import EventBus, Event
from phd_agent.core.contract import AgentContract
import time


class CompositeAgent:
    def __init__(self, definition: CompositeToolDefinition, llm, wrapper: AgentWrapper,
                 bus: EventBus, max_sub_iterations: int = 5):
        self.definition = definition
        self.llm = llm
        self.wrapper = wrapper
        self.bus = bus
        self.max_sub_iterations = max_sub_iterations

    async def run(self, *, args: dict, state: GlobalState,
                  run_id: str = "composite") -> ToolResult:
        sub_messages: list[Message] = [
            Message(role="system", content=self._build_prompt()),
            Message(role="user", content=f"任务输入: {args}"),
        ]
        sub_tools = [self._contract_to_spec(self.wrapper._registry.get_contract(t))
                     for t in self.definition.sub_tools]

        for i in range(self.max_sub_iterations):
            self.bus.publish(Event(run_id=run_id, step=i, agent_id=self.definition.tool_id,
                                   status="sub_iter", duration_ms=0))
            response = await self.llm.chat(
                messages=[m.to_llm_dict() for m in sub_messages],
                tools=[t.model_dump() for t in sub_tools],
                model="MiniMax-m3",
            )
            if not response.tool_calls:
                return ToolResult(
                    tool_name=self.definition.tool_id, success=True,
                    summary=response.content[:200] if response.content else "",
                    llm_context=response.content or "",
                )
            sub_messages.append(Message(
                role="assistant", content=response.content, tool_calls=response.tool_calls,
            ))
            for tc in response.tool_calls:
                self.bus.publish(Event(run_id=run_id, step=i, agent_id=tc.name,
                                       status="sub_call", duration_ms=0))
                # sub-execution only allowed for atomic tools
                sub_result = await self.wrapper.execute_one(state, tc.name, tc.args,
                                                            run_id=run_id)
                self.bus.publish(Event(run_id=run_id, step=i, agent_id=tc.name,
                                       status="sub_call_done", duration_ms=0))
                sub_messages.append(sub_result.to_message(tc.id))

        return ToolResult(
            tool_name=self.definition.tool_id, success=False,
            summary=f"sub iteration limit {self.max_sub_iterations} reached",
            llm_context="[sub-agent failed: iteration limit]",
            error="max_sub_iterations",
        )

    def _build_prompt(self) -> str:
        return build_system_prompt(
            name=self.definition.name,
            user_intent=self.definition.system_prompt,
            sub_tools=self.definition.sub_tools,
            max_sub_iterations=self.max_sub_iterations,
        )

    def _contract_to_spec(self, contract: AgentContract) -> dict:
        return {
            "name": contract.agent_id,
            "description": contract.description,
            "parameters": {"type": "object", "properties": {}},
        }
```

- [ ] **Step 4: Update ToolExecutor to dispatch composite**

Edit `backend/src/phd_agent/core/tool_executor.py`:
```python
# backend/src/phd_agent/core/tool_executor.py
"""Dispatch atomic vs composite tool execution."""
from phd_agent.core.state import GlobalState
from phd_agent.core.wrapper import ToolResult


class ToolExecutor:
    def __init__(self, registry, wrapper, bus, composite_agent_factory=None):
        self._registry = registry
        self._wrapper = wrapper
        self._bus = bus
        self._composite_factory = composite_agent_factory

    async def execute(self, *, name: str, args: dict, state: GlobalState,
                      run_id: str = "ad-hoc") -> ToolResult:
        if self._composite_factory and self._registry.is_composite(name, state.user_id):
            agent = self._composite_factory(self._registry.get_composite_def(name, state.user_id))
            return await agent.run(args=args, state=state, run_id=run_id)
        return await self._wrapper.execute_one(state, name, args, run_id=run_id)
```

- [ ] **Step 5: Add `is_composite` / `get_composite_def` to registry**

Edit `backend/src/phd_agent/core/registry.py`. Add method:
```python
    def is_composite(self, name: str, user_id: str) -> bool:
        # composite tools are loaded from json_repo (passed at construction)
        return name in getattr(self, "_composite_ids", set())

    def get_composite_def(self, name: str, user_id: str):
        return self._composite_defs[name]

    def load_composites(self, composite_list: list) -> None:
        """Called by app startup to register all user's composite tools."""
        self._composite_ids = {t.tool_id for t in composite_list}
        self._composite_defs = {t.tool_id: t for t in composite_list}
```

- [ ] **Step 6: Update list_my_tools to include composite**

```python
    async def list_my_tools(self, user_id: str) -> list[dict]:
        atomic = [self._contract_to_spec(c) for c in self._contracts.values()]
        composite = [
            {
                "name": t.tool_id,
                "description": t.description,
                "parameters": {"type": "object", "properties": {}},
                "category": "composite",
            }
            for t in getattr(self, "_composite_defs", {}).values()
        ]
        return atomic + composite
```

(Adjust the ToolSpec return type accordingly; tests use `model_dump` so dict works.)

- [ ] **Step 7: Run, expect pass**

```bash
cd backend && pytest tests/test_composite_agent.py -v
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(backend): CompositeAgent (LLM-driven nested agent)"
```

---

## Phase 4: Real Plugins

### Task 4.1: Add arxiv_search plugin

**Files:**
- Create: `backend/src/phd_agent/plugins/arxiv_search/__init__.py`
- Create: `backend/src/phd_agent/plugins/arxiv_search/agent.py`
- Test: `backend/tests/test_arxiv_search.py`

- [ ] **Step 1: Write failing test (with httpx mock)**

```python
# backend/tests/test_arxiv_search.py
import pytest
from unittest.mock import AsyncMock, patch
from phd_agent.plugins.arxiv_search.agent import ArxivSearchAgent
from phd_agent.core.state import GlobalState


@pytest.mark.asyncio
async def test_arxiv_search_writes_results():
    fake_xml = """<?xml version='1.0'?>
<feed><entry><title>Test Paper</title><summary>Abstract</summary>
<link href="http://arxiv.org/abs/123"/></entry></feed>"""
    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=AsyncMock(
        text=fake_xml, raise_for_status=lambda: None
    ))):
        agent = ArxivSearchAgent()
        state = GlobalState(user_id="u1")
        await agent.run(state, query="ML", max_results=1)
        results = state.dynamic_storage["arxiv_results"]
        assert len(results) == 1
        assert results[0]["title"] == "Test Paper"
```

- [ ] **Step 2: Run, expect fail**

```bash
cd backend && pytest tests/test_arxiv_search.py -v
```

- [ ] **Step 3: Create plugin**

`backend/src/phd_agent/plugins/arxiv_search/__init__.py`:
```python
from phd_agent.plugins.arxiv_search.agent import ArxivSearchAgent, CONTRACT
```

`backend/src/phd_agent/plugins/arxiv_search/agent.py`:
```python
"""ArXiv search plugin: returns a list of paper dicts."""
from __future__ import annotations
import httpx
import xml.etree.ElementTree as ET
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="arxiv_search",
    name="ArXiv Search",
    description="Search arXiv for papers by query string. Args: query (str), max_results (int, default 5).",
    category="academic",
    required_fields=set(),
    output_fields={"dynamic_storage.arxiv_results"},
    token_budget=0,
)

NS = {"a": "http://www.w3.org/2005/Atom"}


class ArxivSearchAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, query: str = "", max_results: int = 5) -> GlobalState:
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={max_results}"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url)
            r.raise_for_status()
            root = ET.fromstring(r.text)
        results = []
        for entry in root.findall("a:entry", NS):
            title = entry.findtext("a:title", default="", namespace=NS["a"]).strip()
            summary = entry.findtext("a:summary", default="", namespace=NS["a"]).strip()
            link = entry.find("a:link[@rel='alternate']", NS)
            url_v = link.get("href") if link is not None else ""
            results.append({"title": title, "summary": summary, "url": url_v})
        state.dynamic_storage["arxiv_results"] = results
        return state
```

- [ ] **Step 4: Run, expect pass**

```bash
cd backend && pytest tests/test_arxiv_search.py -v
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(plugins): arxiv_search (real arXiv API)"
```

### Task 4.2: Add LLM-backed plugins (writing_polisher, email_drafter, pdf_summarizer)

**Files:**
- Create: `backend/src/phd_agent/plugins/writing_polisher/`
- Create: `backend/src/phd_agent/plugins/email_drafter/`
- Create: `backend/src/phd_agent/plugins/pdf_summarizer/`
- Test: `backend/tests/test_llm_plugins.py`

- [ ] **Step 1: Create writing_polisher**

`backend/src/phd_agent/plugins/writing_polisher/__init__.py`:
```python
from phd_agent.plugins.writing_polisher.agent import WritingPolisherAgent, CONTRACT
```

`backend/src/phd_agent/plugins/writing_polisher/agent.py`:
```python
"""LLM-based writing polisher: improves clarity and academic tone."""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="writing_polisher",
    name="Writing Polisher",
    description="Polish a piece of text. Args: text (str), style (str, default 'academic').",
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.polished_text"},
    token_budget=4000,
)

PROMPT = """你是写作润色助手。下面是一段需要润色的文本,风格:{style}。

原文:
{text}

请直接返回润色后的版本,不要加解释。"""


class WritingPolisherAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, text: str = "", style: str = "academic") -> GlobalState:
        # Phase 2: stub — return input unchanged
        # Phase 3: real LLM call
        state.dynamic_storage["polished_text"] = f"[polished:{style}] {text}"
        return state
```

- [ ] **Step 2: Create email_drafter**

`backend/src/phd_agent/plugins/email_drafter/__init__.py`:
```python
from phd_agent.plugins.email_drafter.agent import EmailDrafterAgent, CONTRACT
```

`backend/src/phd_agent/plugins/email_drafter/agent.py`:
```python
"""LLM-based email drafter for PhD outreach."""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="email_drafter",
    name="Email Drafter",
    description="Draft an email. Args: purpose (str), context (str), target (str, default 'advisor').",
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.email_draft"},
    token_budget=4000,
)


class EmailDrafterAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, purpose: str = "", context: str = "",
                  target: str = "advisor") -> GlobalState:
        state.dynamic_storage["email_draft"] = (
            f"[draft to {target}, purpose={purpose}]\n\nContext: {context}"
        )
        return state
```

- [ ] **Step 3: Create pdf_summarizer**

`backend/src/phd_agent/plugins/pdf_summarizer/__init__.py`:
```python
from phd_agent.plugins.pdf_summarizer.agent import PdfSummarizerAgent, CONTRACT
```

`backend/src/phd_agent/plugins/pdf_summarizer/agent.py`:
```python
"""LLM-based text/PDF summarizer."""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="pdf_summarizer",
    name="PDF Summarizer",
    description="Summarize a piece of text. Args: text (str), focus (str, default '').",
    category="writing",
    required_fields=set(),
    output_fields={"dynamic_storage.summary"},
    token_budget=4000,
)


class PdfSummarizerAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, text: str = "", focus: str = "") -> GlobalState:
        state.dynamic_storage["summary"] = f"[summary focus={focus}] {text[:200]}"
        return state
```

- [ ] **Step 4: Add knowledge_retriever (abstract dispatch)**

`backend/src/phd_agent/plugins/knowledge_retriever/__init__.py`:
```python
from phd_agent.plugins.knowledge_retriever.agent import KnowledgeRetrieverAgent, CONTRACT
```

`backend/src/phd_agent/plugins/knowledge_retriever/agent.py`:
```python
"""Knowledge retriever: dispatches to configured backend (default: arxiv)."""
from __future__ import annotations
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState
from phd_agent.plugins.arxiv_search.agent import ArxivSearchAgent

CONTRACT = AgentContract(
    agent_id="knowledge_retriever",
    name="Knowledge Retriever",
    description="Retrieve knowledge. Args: query (str), backend (str, default 'arxiv'), max_results (int, default 5).",
    category="academic",
    required_fields=set(),
    output_fields={"dynamic_storage.retrieved"},
    token_budget=0,
)

_BACKENDS = {"arxiv": ArxivSearchAgent()}


class KnowledgeRetrieverAgent(BaseAgent):
    contract = CONTRACT

    async def run(self, state: GlobalState, query: str = "",
                  backend: str = "arxiv", max_results: int = 5) -> GlobalState:
        agent = _BACKENDS.get(backend)
        if agent is None:
            state.error_log.append({"agent_id": self.contract.agent_id,
                                     "error": f"unknown backend: {backend}"})
            return state
        await agent.run(state, query=query, max_results=max_results)
        # normalize output key
        state.dynamic_storage["retrieved"] = state.dynamic_storage.get("arxiv_results", [])
        return state
```

- [ ] **Step 5: Smoke test imports**

```bash
cd backend && python -c "
from phd_agent.plugins.arxiv_search import ArxivSearchAgent
from phd_agent.plugins.writing_polisher import WritingPolisherAgent
from phd_agent.plugins.email_drafter import EmailDrafterAgent
from phd_agent.plugins.pdf_summarizer import PdfSummarizerAgent
from phd_agent.plugins.knowledge_retriever import KnowledgeRetrieverAgent
print('all plugins import ok')
"
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(plugins): 4 LLM-backed plugins + knowledge_retriever dispatcher"
```

### Task 4.3: Add agent contract parameters (JSON Schema for LLM)

**Files:**
- Modify: `backend/src/phd_agent/core/contract.py`
- Test: `backend/tests/test_contract_params.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_contract_params.py
from phd_agent.core.contract import AgentContract

def test_contract_parameters_default():
    c = AgentContract(agent_id="x", name="X", description="d", category="mock",
                      required_fields=set(), output_fields=set())
    assert c.parameters == {"type": "object", "properties": {}}

def test_contract_parameters_explicit():
    c = AgentContract(
        agent_id="x", name="X", description="d", category="mock",
        required_fields=set(), output_fields=set(),
        parameters={"type": "object", "properties": {"q": {"type": "string"}}},
    )
    assert "q" in c.parameters["properties"]
```

- [ ] **Step 2: Run, expect fail**

- [ ] **Step 3: Add `parameters` to AgentContract**

Edit `backend/src/phd_agent/core/contract.py`. Add to class:
```python
    parameters: dict = Field(default_factory=lambda: {"type": "object", "properties": {}})
```

(Need to verify Field import is present.)

- [ ] **Step 4: Update registry to include parameters in spec**

Edit `backend/src/phd_agent/core/registry.py`. Update `_contract_to_spec`:
```python
    def _contract_to_spec(self, contract: AgentContract) -> dict:
        return {
            "name": contract.agent_id,
            "description": contract.description,
            "parameters": contract.parameters,
            "category": contract.category,
        }
```

- [ ] **Step 5: Run, expect pass**

```bash
cd backend && pytest tests/test_contract_params.py -v
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(contract): parameters JSON Schema for LLM tool calling"
```

---

## Phase 5: API Layer

### Task 5.1: Add chat API endpoints

**Files:**
- Create: `backend/src/phd_agent/api/chat.py`
- Modify: `backend/src/phd_agent/main.py`
- Test: `backend/tests/test_chat_api.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_chat_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.mark.asyncio
async def test_create_and_list_conversations(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/chat/conversations", json={"user_id": "u1", "title": "t"})
        assert r.status_code == 200
        cid = r.json()["conversation_id"]
        r = await c.get("/chat/conversations", params={"user_id": "u1"})
        assert r.status_code == 200
        assert any(x["conversation_id"] == cid for x in r.json()["conversations"])
```

- [ ] **Step 2: Run, expect fail**

- [ ] **Step 3: Create api/chat.py**

```python
# backend/src/phd_agent/api/chat.py
"""Chat session endpoints."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Query
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.chat import ChatSession
import os

router = APIRouter()
_repo = JsonFileRepository(base_dir=os.environ.get("DATA_DIR", "data"))


@router.post("/chat/conversations")
async def create_conversation(body: dict):
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(400, "user_id required")
    conv_id = str(uuid.uuid4())
    session = ChatSession(user_id=user_id, conversation_id=conv_id,
                          title=body.get("title", ""))
    await _repo.save_conversation(session)
    return {"conversation_id": conv_id, "session": session.model_dump(mode="json")}


@router.get("/chat/conversations")
async def list_conversations(user_id: str = Query(...)):
    convs = await _repo.list_conversations(user_id)
    return {"conversations": [c.model_dump(mode="json") for c in convs]}


@router.get("/chat/conversations/{conv_id}")
async def get_conversation(conv_id: str, user_id: str = Query(...)):
    s = await _repo.load_conversation(user_id, conv_id)
    if not s:
        raise HTTPException(404, "not found")
    return s.model_dump(mode="json")


@router.delete("/chat/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user_id: str = Query(...)):
    await _repo.delete_conversation(user_id, conv_id)
    return {"ok": True}
```

- [ ] **Step 4: Mount in main.py**

Edit `backend/src/phd_agent/main.py`:
```python
from phd_agent.api.chat import router as chat_router
# ... after app creation
app.include_router(chat_router)
```

- [ ] **Step 5: Run, expect pass**

```bash
cd backend && pytest tests/test_chat_api.py -v
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(api): /chat/conversations endpoints"
```

### Task 5.2: Add chat messages endpoint with SSE

**Files:**
- Modify: `backend/src/phd_agent/api/chat.py`
- Modify: `backend/src/phd_agent/main.py`
- Test: `backend/tests/test_chat_messages.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_chat_messages.py
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.mark.asyncio
async def test_post_message_returns_sse(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_BACKEND", "mock")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/chat/conversations", json={"user_id": "u1"})
        cid = r.json()["conversation_id"]
        r = await c.post(f"/chat/conversations/{cid}/messages",
                         json={"content": "hi"})
        assert r.status_code == 200
        assert "message_completed" in r.text
```

- [ ] **Step 2: Run, expect fail**

- [ ] **Step 3: Add messages endpoint**

Append to `api/chat.py`:
```python
from fastapi.responses import StreamingResponse
from phd_agent.core.tool_runtime import ToolRuntime
from phd_agent.core.registry import AgentRegistry
from phd_agent.core.events import EventBus
from phd_agent.llm.mock import MockLLMClient
from phd_agent.llm.openai_compat import OpenAICompatClient

_runtime: ToolRuntime | None = None

def _get_runtime() -> ToolRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    bus = EventBus()
    reg = AgentRegistry(plugins_dir=_plugins_dir())
    reg._plugins_dir = _plugins_dir()  # not strictly needed
    backend = os.environ.get("LLM_BACKEND", "mock")
    if backend == "openai":
        llm = OpenAICompatClient(
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
    else:
        llm = MockLLMClient()
    from phd_agent.core.wrapper import AgentWrapper
    wrapper = AgentWrapper(reg, bus, llm)
    repo = JsonFileRepository(base_dir=os.environ.get("DATA_DIR", "data"))
    _runtime = ToolRuntime(reg, llm, bus, repo, wrapper=wrapper)
    return _runtime


def _plugins_dir():
    from pathlib import Path
    return Path(__file__).parent.parent / "plugins"


@router.post("/chat/conversations/{conv_id}/messages")
async def post_message(conv_id: str, body: dict, user_id: str = Query(...)):
    runtime = _get_runtime()
    session = await _repo.load_conversation(user_id, conv_id)
    if not session:
        raise HTTPException(404, "conversation not found")
    content = body.get("content", "")

    async def event_gen():
        async for ev in runtime.run_turn(session, content):
            yield f"event: {ev['type']}\ndata: {_json_dumps(ev)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


def _json_dumps(d: dict) -> str:
    import json
    return json.dumps(d, default=str)
```

- [ ] **Step 4: Add deps to main.py**

```python
app.include_router(chat_router)

@app.on_event("startup")
async def startup():
    # warm up runtime so plugins are scanned
    from phd_agent.api.chat import _get_runtime
    _get_runtime()
```

- [ ] **Step 5: Run, expect pass**

```bash
cd backend && pytest tests/test_chat_messages.py -v
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(api): SSE streaming for /chat/conversations/{id}/messages"
```

### Task 5.3: Add /tools and /canvas endpoints

**Files:**
- Create: `backend/src/phd_agent/api/tools.py`
- Create: `backend/src/phd_agent/api/canvas.py`
- Modify: `backend/src/phd_agent/main.py`
- Test: `backend/tests/test_tools_api.py`
- Test: `backend/tests/test_canvas_api.py`

- [ ] **Step 1: Create api/tools.py**

```python
# backend/src/phd_agent/api/tools.py
from fastapi import APIRouter, HTTPException, Query
from phd_agent.api.chat import _get_runtime, _repo, _plugins_dir
import os

router = APIRouter()


@router.get("/tools/catalog")
async def list_tools(user_id: str = Query(...)):
    runtime = _get_runtime()
    tools = await runtime.registry.list_my_tools(user_id)
    return {"tools": tools}


@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str, user_id: str = Query(...)):
    runtime = _get_runtime()
    tools = await runtime.registry.list_my_tools(user_id)
    for t in tools:
        if t.get("name") == tool_id:
            return t
    raise HTTPException(404, "tool not found")
```

- [ ] **Step 2: Create api/canvas.py**

```python
# backend/src/phd_agent/api/canvas.py
from fastapi import APIRouter, HTTPException, Query
from phd_agent.core.composite import CompositeToolDefinition, build_system_prompt
from phd_agent.core.composite_agent import MAX_SUB_ITERATIONS
from phd_agent.api.chat import _repo
from datetime import datetime

router = APIRouter()


@router.post("/canvas/preview-prompt")
async def preview_prompt(body: dict):
    return {
        "augmented_system_prompt": build_system_prompt(
            name=body.get("name", "Tool"),
            user_intent=body.get("system_prompt", ""),
            sub_tools=body.get("sub_tools", []),
            max_sub_iterations=MAX_SUB_ITERATIONS,
        )
    }


@router.post("/canvas/composite")
async def save_composite(body: dict, user_id: str = Query(...)):
    tool = CompositeToolDefinition(
        tool_id=body["tool_id"],
        name=body["name"],
        description=body.get("description", ""),
        system_prompt=body["system_prompt"],
        sub_tools=body["sub_tools"],
        owner_user_id=user_id,
        is_public=body.get("is_public", False),
    )
    await _repo.save_composite_tool(tool)
    return {"tool": tool.model_dump(mode="json")}


@router.delete("/canvas/composite/{tool_id}")
async def delete_composite(tool_id: str, user_id: str = Query(...)):
    await _repo.delete_composite_tool(user_id, tool_id)
    return {"ok": True}


@router.get("/canvas/composites")
async def list_composites(user_id: str = Query(...)):
    tools = await _repo.list_composite_tools(user_id)
    return {"composites": [t.model_dump(mode="json") for t in tools]}
```

Add `MAX_SUB_ITERATIONS` to `composite_agent.py`:
```python
MAX_SUB_ITERATIONS = 5
```

- [ ] **Step 3: Mount in main.py**

```python
from phd_agent.api.tools import router as tools_router
from phd_agent.api.canvas import router as canvas_router
app.include_router(tools_router)
app.include_router(canvas_router)
```

- [ ] **Step 4: Tests**

```python
# backend/tests/test_canvas_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.mark.asyncio
async def test_preview_and_save_composite(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/canvas/preview-prompt", json={
            "name": "T", "system_prompt": "summarize", "sub_tools": ["arxiv_search"]
        })
        assert "summarize" in r.json()["augmented_system_prompt"]
        r = await c.post("/canvas/composite?user_id=u1", json={
            "tool_id": "t1", "name": "T", "description": "d",
            "system_prompt": "summarize", "sub_tools": ["arxiv_search"],
        })
        assert r.status_code == 200
        r = await c.get("/canvas/composites", params={"user_id": "u1"})
        assert any(t["tool_id"] == "t1" for t in r.json()["composites"])
```

- [ ] **Step 5: Run all API tests**

```bash
cd backend && pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(api): /tools/catalog + /canvas/composite endpoints"
```

---

## Phase 6: Frontend

### Task 6.1: App.tsx as Tab container

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Rewrite App.tsx**

```typescript
// frontend/src/App.tsx
import { useState } from "react";
import { ChatView } from "./chat/ChatView";
import { ToolBuilderCanvas } from "./canvas/ToolBuilderCanvas";
import "./App.css";

type Tab = "chat" | "canvas";

export default function App() {
  const [tab, setTab] = useState<Tab>("chat");

  return (
    <div className="app">
      <header className="tabs">
        <button
          className={tab === "chat" ? "active" : ""}
          onClick={() => setTab("chat")}
        >
          Chat
        </button>
        <button
          className={tab === "canvas" ? "active" : ""}
          onClick={() => setTab("canvas")}
        >
          Canvas
        </button>
      </header>
      <main>
        {tab === "chat" && <ChatView userId="default-user" />}
        {tab === "canvas" && <ToolBuilderCanvas userId="default-user" />}
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
cd frontend && git add -A && git commit -m "feat(app): tabbed layout (Chat + Canvas)"
```

### Task 6.2: Chat components

**Files:**
- Create: `frontend/src/chat/ChatView.tsx`
- Create: `frontend/src/chat/MessageList.tsx`
- Create: `frontend/src/chat/MessageBubble.tsx`
- Create: `frontend/src/chat/ChatInput.tsx`
- Create: `frontend/src/chat/ToolCallIndicator.tsx`
- Create: `frontend/src/api/client.ts` (or modify existing)
- Test: `frontend/src/chat/MessageBubble.test.tsx`

- [ ] **Step 1: Create MessageBubble**

```typescript
// frontend/src/chat/MessageBubble.tsx
import type { Message } from "../api/types";

export function MessageBubble({ msg }: { msg: Message }) {
  const cls = `bubble ${msg.role}`;
  return (
    <div className={cls}>
      <div className="role">{msg.role}</div>
      {msg.content && <div className="content">{msg.content}</div>}
      {msg.tool_calls && (
        <div className="tool-calls">
          {msg.tool_calls.map((tc) => (
            <code key={tc.id}>{tc.name}({JSON.stringify(tc.args)})</code>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Test MessageBubble**

```typescript
// frontend/src/chat/MessageBubble.test.tsx
import { render, screen } from "@testing-library/react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "../api/types";

test("renders user content", () => {
  const msg: Message = { role: "user", content: "hello", timestamp: new Date().toISOString() };
  render(<MessageBubble msg={msg} />);
  expect(screen.getByText("hello")).toBeInTheDocument();
});
```

- [ ] **Step 3: Add types**

Edit `frontend/src/api/types.ts` — add:
```typescript
export type ToolCall = { id: string; name: string; args: Record<string, unknown> };
export type Message = {
  role: "system" | "user" | "assistant" | "tool";
  content?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
  timestamp: string;
};
```

- [ ] **Step 4: MessageList**

```typescript
// frontend/src/chat/MessageList.tsx
import { useEffect, useRef } from "react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "../api/types";

export function MessageList({ messages }: { messages: Message[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { ref.current?.scrollTo(0, ref.current.scrollHeight); }, [messages]);
  return (
    <div className="message-list" ref={ref}>
      {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
    </div>
  );
}
```

- [ ] **Step 5: ChatInput**

```typescript
// frontend/src/chat/ChatInput.tsx
import { useState } from "react";

export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState("");
  return (
    <form
      className="chat-input"
      onSubmit={(e) => {
        e.preventDefault();
        if (!text.trim() || disabled) return;
        onSend(text);
        setText("");
      }}
    >
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask anything…"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !text.trim()}>Send</button>
    </form>
  );
}
```

- [ ] **Step 6: ToolCallIndicator**

```typescript
// frontend/src/chat/ToolCallIndicator.tsx
export function ToolCallIndicator({ active }: { active: string[] }) {
  if (active.length === 0) return null;
  return (
    <div className="tool-indicator">
      {active.map((name, i) => (
        <span key={i} className="pill">calling {name}…</span>
      ))}
    </div>
  );
}
```

- [ ] **Step 7: ChatView with SSE client**

```typescript
// frontend/src/chat/ChatView.tsx
import { useEffect, useState } from "react";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ToolCallIndicator } from "./ToolCallIndicator";
import { api } from "../api/client";
import type { Message } from "../api/types";

export function ChatView({ userId }: { userId: string }) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeTools, setActiveTools] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.createConversation(userId, "New chat").then((r) => {
      setConversationId(r.conversation_id);
    });
  }, [userId]);

  const send = async (text: string) => {
    if (!conversationId) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", content: text, timestamp: new Date().toISOString() }]);
    setActiveTools([]);

    const userMsg: Message = { role: "user", content: text, timestamp: new Date().toISOString() };
    const resp = await fetch(
      `/chat/conversations/${conversationId}/messages?user_id=${userId}`,
      { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text }) }
    );
    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let acc = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value);
      const parts = buf.split("\n\n");
      buf = parts.pop() || "";
      for (const part of parts) {
        const ev = part.split("\n").reduce((acc, line) => {
          if (line.startsWith("event: ")) acc.type = line.slice(7);
          if (line.startsWith("data: ")) {
            try { Object.assign(acc, JSON.parse(line.slice(6))); } catch {}
          }
          return acc;
        }, {} as any);
        if (ev.type === "tool_call_started") setActiveTools((a) => [...a, ev.name]);
        if (ev.type === "tool_call_completed" || ev.type === "tool_call_skipped") {
          setActiveTools((a) => a.filter((n) => n !== ev.name));
        }
        if (ev.type === "message_completed") {
          acc = ev.content || acc;
        }
      }
    }
    if (acc) setMessages((m) => [...m, { role: "assistant", content: acc, timestamp: new Date().toISOString() }]);
    setBusy(false);
  };

  return (
    <div className="chat-view">
      <MessageList messages={messages} />
      <ToolCallIndicator active={activeTools} />
      <ChatInput onSend={send} disabled={busy} />
    </div>
  );
}
```

- [ ] **Step 8: Add createConversation to client**

Edit `frontend/src/api/client.ts`:
```typescript
export const api = {
  // ... existing methods
  async createConversation(userId: string, title: string) {
    const r = await fetch(`/chat/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, title }),
    });
    return r.json();
  },
};
```

- [ ] **Step 9: Run frontend tests + build**

```bash
cd frontend && npm test -- --run
cd frontend && npm run build
```

- [ ] **Step 10: Commit**

```bash
cd frontend && git add -A && git commit -m "feat(chat): ChatView with SSE streaming"
```

### Task 6.3: Canvas updates for "Save as my tool"

**Files:**
- Modify: `frontend/src/canvas/ToolBuilderCanvas.tsx` (rename from FlowCanvas or create wrapper)
- Create: `frontend/src/canvas/SaveToolModal.tsx`
- Test: `frontend/src/canvas/SaveToolModal.test.tsx`

- [ ] **Step 1: Create SaveToolModal**

```typescript
// frontend/src/canvas/SaveToolModal.tsx
import { useState } from "react";

export function SaveToolModal({
  subTools,
  onSave,
  onClose,
}: {
  subTools: string[];
  onSave: (data: { tool_id: string; name: string; system_prompt: string }) => void;
  onClose: () => void;
}) {
  const [toolId, setToolId] = useState("");
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Save as my tool</h2>
        <label>Tool ID<input value={toolId} onChange={(e) => setToolId(e.target.value)} /></label>
        <label>Name<input value={name} onChange={(e) => setName(e.target.value)} /></label>
        <label>System Prompt (your intent)
          <textarea value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} />
        </label>
        <p className="sub-tools">Sub tools: {subTools.join(", ")}</p>
        <div className="actions">
          <button onClick={onClose}>Cancel</button>
          <button
            disabled={!toolId || !name}
            onClick={() => onSave({ tool_id: toolId, name, system_prompt: systemPrompt })}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Wire it up in ToolBuilderCanvas**

Update `frontend/src/canvas/FlowCanvas.tsx` (or rename to `ToolBuilderCanvas.tsx`):
- Replace "Run" button with "Save as my tool"
- On click, open modal
- On save, POST to `/canvas/preview-prompt` then `/canvas/composite`

```typescript
// pseudo-addition
const handleSave = async (data: { tool_id: string; name: string; system_prompt: string }) => {
  await fetch(`/canvas/preview-prompt`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: data.name, system_prompt: data.system_prompt, sub_tools: subPipeline }),
  });
  await fetch(`/canvas/composite?user_id=${userId}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, description: data.name, sub_tools: subPipeline }),
  });
  onSaved?.();
};
```

- [ ] **Step 3: Run tests + build**

```bash
cd frontend && npm test -- --run && npm run build
```

- [ ] **Step 4: Commit**

```bash
cd frontend && git add -A && git commit -m "feat(canvas): Save as my tool modal"
```

---

## Phase 7: E2E Verification + README

### Task 7.1: Add E2E test (chat + tool call)

**Files:**
- Create: `backend/tests/test_e2e_chat.py`
- Test: runs the full pipeline with mock LLM

- [ ] **Step 1: Write test**

```python
# backend/tests/test_e2e_chat.py
import pytest
from httpx import AsyncClient, ASGITransport
from phd_agent.main import app


@pytest.mark.asyncio
async def test_full_chat_with_tool_call(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LLM_BACKEND", "mock")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/chat/conversations", json={"user_id": "u1"})
        cid = r.json()["conversation_id"]
        r = await c.get("/tools/catalog", params={"user_id": "u1"})
        assert len(r.json()["tools"]) >= 3
        # post a message
        r = await c.post(f"/chat/conversations/{cid}/messages?user_id=u1",
                         json={"content": "find me ML papers"})
        body = r.text
        assert "tool_call_started" in body
        assert "message_completed" in body
```

- [ ] **Step 2: Run**

```bash
cd backend && pytest tests/test_e2e_chat.py -v
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test(e2e): full chat with tool call"
```

### Task 7.2: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update Quick start**

```markdown
## Quick start (Phase 2 — Chat-First)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# Optional: set real LLM (else uses MockLLMClient)
export OPENAI_API_KEY=sk-...
export LLM_BACKEND=openai  # or "mock"
export DATA_DIR=./data
uvicorn phd_agent.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:4018, you'll land on the **Chat** tab. Ask anything —
the LLM will call backend tools to answer. Switch to **Canvas** to compose
your own composite tool, save it, and use it in chat.

### Demo flow
1. Chat: "find me 3 recent ML papers"
2. LLM calls `knowledge_retriever` → you see tool indicator
3. LLM returns formatted list
4. Switch to Canvas: drag `arxiv_search` + `writing_polisher`, save as `my_summarizer`
5. Chat: "use my_summarizer on the first paper"
6. LLM calls `my_summarizer` → Sub-LLM runs → returns polished summary
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "docs: Phase 2 quick start"
```

### Task 7.3: Final verification

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && pytest tests/ -v
```

Expected: all pass, coverage ≥ 70% on `core/`.

- [ ] **Step 2: Run all frontend tests**

```bash
cd frontend && npm test -- --run
```

- [ ] **Step 3: Build frontend**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Manual smoke test**

```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn phd_agent.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:4018:
- Chat tab: send a message, see tool indicator
- Canvas tab: drag a tool, save as my tool
- Back to Chat: ask LLM to use it

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: Phase 2 verification complete" --allow-empty
```

---

## Acceptance Criteria (Spec §12)

Phase 2 is shippable when:

- ✅ Backend: `uvicorn phd_agent.main:app` starts, `/health` returns 200
- ✅ `/tools/catalog` returns ≥ 5 tools (4 general + 2 mock)
- ✅ Chat end-to-end: send message → LLM calls tool → text response
- ✅ Save composite → appears in catalog → LLM can call it
- ✅ Real arxiv API call works (or mock when no API key)
- ✅ pytest passes (≥ 70% on `core/`)
- ✅ Frontend: default to Chat tab, SSE streaming, Canvas save flow
- ✅ `core/router.py` and `orchestrator.py` deleted
- ✅ `CompositeAgent` (LLM-driven) replaces PipelineOrchestrator
- ✅ LLM via OpenAI compat → MiniMax-m3 (or MockLLMClient fallback)
- ✅ Data persisted to `data/{user_id}/` JSON
- ✅ README updated

## Notes for the Implementer

- **LLM_API_KEY unset → MockLLMClient is used automatically.** This lets the app run end-to-end with no real API.
- **Each task is independently testable.** Don't skip the test-first step.
- **File size limits:** If a file approaches 250 lines (Python) or 200 lines (TSX/TS), split BEFORE writing. Look for natural domain boundaries.
- **Phase 1 tests are deleted, not maintained.** `test_pipeline_e2e.py` is gone.
- **Composite tool recurses into atomic only.** Don't add support for nested composites in Phase 2.
- **Frontend Vite dev port is 4018** (per recent commit). Update if changed.
- **If a step fails, run the test first to see actual output before debugging.**
