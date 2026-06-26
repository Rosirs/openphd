# MiniMax Provider + Chat-Wiring Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `MiniMax` as an onboard provider preset AND fix the bug where `/chat` always uses `MockLLMClient` despite onboard `/test` succeeding with the user's real key.

**Architecture:** Make `get_llm_async()` the single source of truth for LLM resolution. `get_runtime()` no longer hardcodes a default `llm`; it passes `llm_factory=get_llm_async` to `ToolRuntime`. The composite-agent factory becomes async and also resolves through `get_llm_async()`. `CompositeAgent.run` uses a model passed to its constructor instead of a hardcoded `"MiniMax-m3"`. Frontend `LLMConfigForm` autofill map grows by one entry.

**Tech Stack:** Python 3.11+ / FastAPI / pytest-asyncio / httpx (backend); React + TS + Vitest (frontend).

**Spec:** `docs/superpowers/specs/2026-06-26-minimax-provider-and-chat-wiring-design.md`

## Global Constraints

- `MiniMax` provider key (lowercase, used in JSON, URL paths, and frontend dropdown value): exactly `MiniMax`
- Display label: `"MiniMax"`
- Base URL: `https://api.MiniMax.chat/v1`
- Default model: `MiniMax-M3`
- `supported: True`
- All four required keys (`label`, `base_url`, `default_model`, `supported`) must be present — enforced by `test_providers.py::test_all_presets_have_required_keys`
- No new dependencies. No production code paths may import private `deps._*` attributes; tests may.

---

### Task 1: Add MiniMax to backend `PROVIDER_PRESETS`

**Files:**
- Modify: `backend/src/phd_agent/core/providers.py` (lines 3-36)

**Interfaces:**
- Consumes: nothing
- Produces: `PROVIDER_PRESETS["MiniMax"]` dict with all four required keys

- [ ] **Step 1: Add the MiniMax entry**

In `backend/src/phd_agent/core/providers.py`, insert a new entry after the `"moonshot"` block (after line 21, before `"custom"` on line 22):

```python
    "MiniMax": {
        "label": "MiniMax",
        "base_url": "https://api.MiniMax.chat/v1",
        "default_model": "MiniMax-M3",
        "supported": True,
    },
```

The final file shape (lines 3-37) should be:

```python
PROVIDER_PRESETS: dict[str, dict] = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "supported": True,
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "supported": True,
    },
    "moonshot": {
        "label": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "supported": True,
    },
    "MiniMax": {
        "label": "MiniMax",
        "base_url": "https://api.MiniMax.chat/v1",
        "default_model": "MiniMax-M3",
        "supported": True,
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "base_url": "",
        "default_model": "",
        "supported": True,
    },
    "anthropic": {
        "label": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-sonnet-20241022",
        "supported": False,
        "disabled_reason": "Anthropic uses a non-OpenAI API; will be supported in a later phase.",
    },
}
```

- [ ] **Step 2: Add a regression test for the MiniMax preset**

In `backend/tests/test_providers.py`, append at end of file:

```python
def test_minimax_supported():
    p = PROVIDER_PRESETS["MiniMax"]
    assert p["supported"] is True
    assert p["base_url"] == "https://api.MiniMax.chat/v1"
    assert p["default_model"] == "MiniMax-M3"
```

- [ ] **Step 3: Run the tests**

Run: `cd backend && python -m pytest tests/test_providers.py -v`
Expected: 6 tests pass (5 existing + 1 new).

- [ ] **Step 4: Commit**

```bash
git add backend/src/phd_agent/core/providers.py backend/tests/test_providers.py
git commit -m "feat(onboard): add MiniMax provider preset"
```

---

### Task 2: Failing test — `get_runtime()` must wire `get_llm_async` as factory

**Files:**
- Create: `backend/tests/test_chat_wiring.py`

**Interfaces:**
- Consumes: `phd_agent.api.deps.get_runtime`, `phd_agent.api.deps.get_llm_async`, `phd_agent.core.profile.UserProfile`, `phd_agent.llm.openai_compat.OpenAICompatClient`, `phd_agent.llm.mock.MockLLMClient`
- Produces: a test module that catches the regression where `get_runtime()` uses a hardcoded mock LLM

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_chat_wiring.py` with this content:

```python
"""Regression tests: /chat must resolve LLM through the user profile, not a hardcoded mock.

Background: previously `api.deps.get_runtime()` hardcoded `llm=MockLLMClient()` and
`composite_factory=lambda d: CompositeAgent(d, MockLLMClient(), ...)` and never passed
`llm_factory` to `ToolRuntime`. As a result /chat always returned `[mock default]`
even when /onboard/test against the user's real key succeeded.
"""
import pytest
from phd_agent.api import deps
from phd_agent.core.json_repo import JsonFileRepository
from phd_agent.core.profile import UserProfile
from phd_agent.core.composite_agent import CompositeAgent
from phd_agent.core.composite import CompositeToolDefinition
from phd_agent.llm.mock import MockLLMClient
from phd_agent.llm.openai_compat import OpenAICompatClient


@pytest.fixture(autouse=True)
def reset_deps(tmp_path):
    deps._repo = JsonFileRepository(tmp_path)
    deps._runtime = None
    deps.invalidate_profile_cache()
    yield
    deps._repo = None
    deps._runtime = None
    deps.invalidate_profile_cache()


def test_get_runtime_passes_llm_factory_to_tool_runtime():
    runtime = deps.get_runtime()
    assert runtime._llm_factory is deps.get_llm_async, (
        "get_runtime() must wire get_llm_async as ToolRuntime._llm_factory; "
        "otherwise /chat ignores the user's profile."
    )


def test_get_runtime_does_not_hardcode_mock_llm():
    runtime = deps.get_runtime()
    assert not isinstance(runtime.llm, MockLLMClient), (
        "get_runtime() must not bake a MockLLMClient into ToolRuntime.llm; "
        "the per-turn factory is the only source of truth."
    )


@pytest.mark.asyncio
async def test_llm_factory_returns_real_client_when_profile_has_key():
    deps._repo.save_profile_sync = None  # ensure clean fixture (no-op line for clarity)
    repo = deps.get_repo()
    await repo.save_profile(UserProfile(
        llm_provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-realkey1234",
        model_name="gpt-4o-mini",
    ))
    deps.invalidate_profile_cache()
    client, model = await deps.get_llm_async()
    assert isinstance(client, OpenAICompatClient)
    assert model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_llm_factory_falls_back_to_mock_when_no_profile():
    client, model = await deps.get_llm_async()
    assert isinstance(client, MockLLMClient)
    assert model == "mock"


@pytest.mark.asyncio
async def test_composite_factory_uses_user_llm_not_hardcoded_mock():
    repo = deps.get_repo()
    await repo.save_profile(UserProfile(
        llm_provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="sk-realkey1234",
        model_name="gpt-4o-mini",
    ))
    deps.invalidate_profile_cache()
    runtime = deps.get_runtime()

    definition = CompositeToolDefinition(
        tool_id="x", name="x", description="x", system_prompt="x", sub_tools=[]
    )
    agent = await runtime._executor._composite_factory(definition)
    assert isinstance(agent, CompositeAgent)
    assert isinstance(agent.llm, OpenAICompatClient), (
        "composite_factory must resolve LLM through get_llm_async, not hardcode MockLLMClient"
    )
    assert agent.model == "gpt-4o-mini", (
        "CompositeAgent must use the model from get_llm_async, not hardcode 'MiniMax-m3'"
    )
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `cd backend && python -m pytest tests/test_chat_wiring.py -v`
Expected: All 5 tests FAIL. The first two fail because `runtime._llm_factory is None` and `runtime.llm` IS a `MockLLMClient`. The 3rd, 4th, 5th may also fail for various reasons — that's fine; the assertion messages tell us what to fix.

- [ ] **Step 3: Commit the failing test**

```bash
git add backend/tests/test_chat_wiring.py
git commit -m "test(deps): add regression tests for /chat LLM wiring"
```

---

### Task 3: Fix `deps.py` — make `get_llm_async` the only LLM source

**Files:**
- Modify: `backend/src/phd_agent/api/deps.py` (lines 56-73)

**Interfaces:**
- Consumes: existing `get_llm_async`, `get_repo`, `_plugins_dir`
- Produces: `get_runtime()` returns a `ToolRuntime` whose `_llm_factory is get_llm_async`, whose `llm` is `None` (factory is sole source), and whose composite factory resolves LLM via `get_llm_async`

- [ ] **Step 1: Rewrite `get_runtime`**

Replace `backend/src/phd_agent/api/deps.py` lines 56-73 with:

```python
def get_runtime() -> ToolRuntime:
    global _runtime
    if _runtime is not None:
        return _runtime
    bus = EventBus()
    registry = AgentRegistry(plugins_dir=_plugins_dir())
    repo = get_repo()
    wrapper = AgentWrapper(registry, bus, llm=None)

    async def composite_factory(definition):
        llm, _ = await get_llm_async()
        return CompositeAgent(definition, llm, wrapper, bus)

    _runtime = ToolRuntime(
        registry=registry,
        llm=None,                          # factory is the only source
        bus=bus,
        chat_repo=repo,
        wrapper=wrapper,
        composite_agent_factory=composite_factory,
        llm_factory=get_llm_async,         # per-turn resolution
    )
    return _runtime
```

Notes:
- Removed imports of `MockLLMClient` and `OpenAICompatClient` from the `get_runtime` body (they are no longer referenced inside it). Keep the top-level imports if `get_llm_async` still needs `OpenAICompatClient` (yes it does, line 39) and `MockLLMClient` (yes, line 44). Do not delete the imports.
- Removed `model="mock"` parameter since the factory supplies the model.
- Wrapper now uses `llm=None`. Verify `AgentWrapper.__init__` accepts `llm=None` — open `backend/src/phd_agent/core/wrapper.py` and confirm. If it does not, keep wrapper at the previous default (mock) but make sure the chat path still uses the factory. (Wrapper is for tool execution only and shouldn't matter for chat.)

- [ ] **Step 2: Check `AgentWrapper` tolerates `llm=None`**

Read `backend/src/phd_agent/core/wrapper.py`. If its `__init__` signature is `def __init__(self, registry, bus, llm)` and `llm` is used in non-tool-execution paths, change to `llm=None` and either skip or guard the usage. Most likely `llm` is only used as a default for the wrapper's own LLM, which the chat path bypasses via the factory. If the wrapper strictly requires a non-None llm, pass `MockLLMClient()` to wrapper (NOT to runtime) and document in a one-line comment that wrapper's llm is unused for chat (factory wins).

- [ ] **Step 3: Run the wiring tests**

Run: `cd backend && python -m pytest tests/test_chat_wiring.py -v`
Expected: All 5 tests PASS. If `test_composite_factory_uses_user_llm_not_hardcoded_mock` fails on `agent.model` (because `CompositeAgent` doesn't yet accept `model`), proceed to Task 4 — the test will pass after Task 4.

- [ ] **Step 4: Run the full backend test suite**

Run: `cd backend && python -m pytest -q`
Expected: All previous tests still pass (no regressions in `test_tool_runtime_profile.py`, `test_deps_cache.py`, `test_onboard_save.py`, etc).

- [ ] **Step 5: Commit**

```bash
git add backend/src/phd_agent/api/deps.py
git commit -m "fix(deps): wire get_llm_async into ToolRuntime factory; /chat now uses user LLM"
```

---

### Task 4: Make `CompositeAgent` use the resolved model

**Files:**
- Modify: `backend/src/phd_agent/core/composite_agent.py` (lines 14-39)

**Interfaces:**
- Consumes: `definition`, `llm`, `wrapper`, `bus`, optional `max_sub_iterations`, NEW `model: str = "MiniMax-m3"` (kept as fallback for existing callers)
- Produces: `self.model` attribute; `run()` uses `self.model` instead of literal `"MiniMax-m3"`

- [ ] **Step 1: Add `model` constructor parameter**

In `backend/src/phd_agent/core/composite_agent.py`, change the `__init__` signature (line 14):

```python
    def __init__(self, definition: CompositeToolDefinition, llm, wrapper: AgentWrapper,
                 bus: EventBus, model: str = "MiniMax-m3",
                 max_sub_iterations: int = MAX_SUB_ITERATIONS):
        self.definition = definition
        self.llm = llm
        self.wrapper = wrapper
        self.bus = bus
        self.model = model
        self.max_sub_iterations = max_sub_iterations
```

- [ ] **Step 2: Use `self.model` in `run()`**

Replace line 38:

```python
            response = await self.llm.chat(
                messages=[m.to_llm_dict() for m in sub_messages],
                tools=sub_tools,
                model=self.model,
            )
```

(Only the `model=` argument changes from `"MiniMax-m3"` to `self.model`.)

- [ ] **Step 3: Update `deps.py` composite_factory to pass model**

In `backend/src/phd_agent/api/deps.py`, update the `composite_factory` (added in Task 3) to pass the model:

```python
    async def composite_factory(definition):
        llm, model = await get_llm_async()
        return CompositeAgent(definition, llm, wrapper, bus, model=model)
```

- [ ] **Step 4: Run wiring tests + full suite**

Run: `cd backend && python -m pytest tests/test_chat_wiring.py tests/test_tool_runtime_profile.py tests/test_deps_cache.py tests/test_providers.py -v`
Expected: All pass.

Run: `cd backend && python -m pytest -q`
Expected: Full suite green, no regressions.

- [ ] **Step 5: Commit**

```bash
git add backend/src/phd_agent/core/composite_agent.py backend/src/phd_agent/api/deps.py
git commit -m "fix(composite): use resolved model in CompositeAgent.run; no more hardcoded 'MiniMax-m3'"
```

---

### Task 5: Add MiniMax to frontend `LLMConfigForm` autofill presets

**Files:**
- Modify: `frontend/src/onboard/LLMConfigForm.tsx` (PRESETS constant near top of file)
- Modify: `frontend/src/onboard/LLMConfigForm.js` (mirror the same change in compiled .js)

**Interfaces:**
- Consumes: nothing (constant)
- Produces: `PRESETS.MiniMax = { base_url, default_model }` so when the user selects `MiniMax` from the picker and no initial value is set, the form autofills `https://api.MiniMax.chat/v1` and `MiniMax-M3`

- [ ] **Step 1: Read the TS source to locate PRESETS**

Read `frontend/src/onboard/LLMConfigForm.tsx` and locate the `PRESETS` constant (it should be near lines 5-10, mirroring the .js shape).

- [ ] **Step 2: Add the entry to the TS PRESETS map**

Add this entry alongside `deepseek` and `moonshot`:

```ts
  MiniMax: { base_url: 'https://api.MiniMax.chat/v1', default_model: 'MiniMax-M3' },
```

- [ ] **Step 3: Mirror the same entry in the compiled .js**

Open `frontend/src/onboard/LLMConfigForm.js`. It contains a hand-maintained compiled mirror with the same `PRESETS` constant. Add the identical line in the same position so the JS build stays in sync with the TS source. Preserve the existing `Object.freeze` wrapping if present (TSX often freezes; JS may not — match local style).

- [ ] **Step 4: Add a frontend regression test**

Append to `frontend/src/onboard/onboard.test.tsx`:

```tsx
test('selecting MiniMax autofills MiniMax base_url and model', async () => {
  const user = userEvent.setup();
  render(
    <LLMConfigForm
      providers={[
        { key: 'openai', label: 'OpenAI', supported: true },
        { key: 'MiniMax', label: 'MiniMax', supported: true },
      ]}
      onSave={() => {}}
      onCancel={() => {}}
    />
  );
  const select = screen.getByTestId('provider-picker') as HTMLSelectElement;
  await user.selectOptions(select, 'MiniMax');
  const baseUrl = screen.getByTestId('base-url') as HTMLInputElement;
  const model = screen.getByTestId('model-name') as HTMLInputElement;
  expect(baseUrl.value).toBe('https://api.MiniMax.chat/v1');
  expect(model.value).toBe('MiniMax-M3');
});
```

- [ ] **Step 5: Run frontend tests**

Run: `cd frontend && npx vitest run src/onboard/onboard.test.tsx`
Expected: 4 tests pass (3 existing + 1 new).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/onboard/LLMConfigForm.tsx frontend/src/onboard/LLMConfigForm.js frontend/src/onboard/onboard.test.tsx
git commit -m "feat(onboard): add MiniMax to frontend autofill presets"
```

---

### Task 6: End-to-end smoke verification

**Files:** none (manual verification)

- [ ] **Step 1: Start the backend and frontend dev servers**

In two terminals (or backgrounded):
```bash
cd backend && uvicorn phd_agent.main:app --reload --port 8000
cd frontend && npm run dev
```

- [ ] **Step 2: Open the app, configure MiniMax, send a message**

1. Open `http://localhost:5173` (or the Vite port shown).
2. In the onboard modal, select `MiniMax`, paste a real `MiniMax` API key, click **Test Connection**.
3. Expect: ✅ green status with a non-zero `latency_ms` and `model: "MiniMax-M3"`.
4. Click **Save**.
5. Open Settings from the chat header, confirm "Current: MiniMax · MiniMax-M3".
6. Type `hi` in the chat, send.

- [ ] **Step 3: Verify the response is NOT `[mock default]`**

The assistant bubble should contain a real model reply (not `[mock default]` and not `[mock response]`). If it still says `[mock default]`, the wiring is wrong — re-check Tasks 3 and 4.

- [ ] **Step 4: Stop dev servers and confirm nothing left running**

```bash
pkill -f "uvicorn phd_agent.main" || true
pkill -f "vite" || true
```

- [ ] **Step 5: Final commit (only if a smoke-fix was needed)**

If Steps 2-3 revealed a wiring gap (e.g., `AgentWrapper` couldn't tolerate `llm=None`), fix it inline, re-run the full backend test suite (`pytest -q`), and commit:

```bash
git add -A
git commit -m "fix: smoke-test follow-up"
```

---

## Self-Review

1. **Spec coverage:**
   - MiniMax provider preset in `PROVIDER_PRESETS` → Task 1 ✓
   - `get_llm_async` as single LLM source → Task 3 ✓
   - `composite_factory` async, resolves through `get_llm_async` → Task 3 + Task 4 ✓
   - `CompositeAgent.run` uses passed model → Task 4 ✓
   - Frontend `LLMConfigForm` autofill → Task 5 ✓
   - Regression tests → Task 2 + Task 5 ✓
2. **Placeholder scan:** No "TBD", no "similar to Task N" stubs; every code step shows exact code.
3. **Type consistency:**
   - `CompositeAgent.__init__` parameter is named `model` in Task 4 and accessed as `agent.model` in Task 2's test and `self.model` in Task 4's body — consistent.
   - `ToolRuntime._llm_factory` referenced in Task 2's test and set in Task 3's deps rewrite — same attribute name.
   - Frontend `PRESETS.MiniMax` referenced in Task 5's test (`baseUrl.value === 'https://api.MiniMax.chat/v1'`) matches what Task 5's code change sets.
