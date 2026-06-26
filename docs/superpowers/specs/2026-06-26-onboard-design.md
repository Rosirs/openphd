# PhD-Agent — Onboard Design Spec

| 字段 | 值 |
|------|-----|
| 版本 | V2.1.0-onboard |
| 日期 | 2026-06-26 |
| 作者 | PhD-Agent 创始团队 |
| 状态 | 设计评审中 (In Review) |
| 阶段 | 用户引导 + LLM 配置 + 单人本地运行时切换 |
| 上游文档 | `docs/superpowers/specs/2026-06-25-phd-agent-v2-phase2-design.md`, `docs/PRD.md` |

---

## 1. 范围与目标

### 1.1 本 spec 范围
为 PhD-Agent 增加**首次访问引导 + LLM 配置 UI**,让用户无需编辑 env 文件、无需重启服务,就能在浏览器里配置自己的 LLM API key 并立即生效。

### 1.2 阶段目标
- ✅ 首次访问自动弹出引导 modal(双按钮:「设置 LLM」/「跳过,用 mock」)
- ✅ Chat 顶栏常驻设置按钮,随时可改
- ✅ LLM Config Form:Provider preset 列表 + base_url + model_name + api_key
- ✅ Provider preset:OpenAI / DeepSeek / Moonshot / Custom / Anthropic(暂不可选)
- ✅ 「测试连接」按钮,验证 API key 是否可用
- ✅ 配置存到后端 `data/profile.json`(全局单文件)
- ✅ 后端运行时切换 LLM client(profile 更新即生效,无需重启)
- ✅ Profile API key 返回前端时 mask(`sk-...xxxx`)

### 1.3 后续阶段(不在本 spec 范围)
- **Phase 4**:SQLite 持久化 + 多用户鉴权(届时 profile 也会按用户切分)
- **Phase 5**:Anthropic 实际调用支持(本阶段 preset 列出但 disabled)
- **Phase 6**:加密 API key 存储(本阶段明文,README 标注生产 TODO)
- **Phase 7**:i18n(目前 UI 文案中英混合)

---

## 2. 关键决策一览

| 决策点 | 选择 | 理由 |
|---|---|---|
| 触发时机 | 首次访问自动弹 + Chat 顶常驻设置 | 引导到位 + 可改 |
| 配置存储 | 后端 `data/profile.json`(全局单文件) | 本地单人应用;1 个 profile,无 per-user 隔离必要 |
| 运行时切换 | 进程内 profile cache + invalidate | 改完即生效,无需重启 |
| Provider preset | OpenAI / DeepSeek / Moonshot / Custom + Anthropic(列出但 disabled) | 覆盖主流 OpenAI 兼容 provider;Anthropic 留接口待后续 |
| 测试连接 | 是 | 保存前确认 key 可用,降低调试成本 |
| API key mask | 返回时 mask,前端不持有完整 | 减少泄漏面 |
| 多用户并发 | 不考虑 | 本地单人 |

---

## 3. 架构总览

```
┌──────────────────────────────────────────────────────────────┐
│ Frontend (React)                                              │
│                                                               │
│  ┌─ App.tsx ─────────────────────────────────────────────┐  │
│  │  onMount: GET /onboard/status                          │  │
│  │    → if !onboarded && !configured: <OnboardModal/>     │  │
│  │    → else: render normal Chat                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ ChatView ────────────────────────────────────────────┐  │
│  │  Header: [PhD-Agent]  [OpenAI · gpt-4o-mini]  [⚙]   │  │
│  │                                        ↓ click        │  │
│  │                              <SettingsModal/>          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─ OnboardModal / SettingsModal ────────────────────────┐  │
│  │  Step 1: 双按钮 (首次) 或直接进 Step 2 (设置)        │  │
│  │  Step 2: <LLMConfigForm/>                              │  │
│  │    - Provider 下拉 → 自动填 base_url + model           │  │
│  │    - Base URL input(可改)                              │  │
│  │    - Model input(可改)                                 │  │
│  │    - API Key password input                            │  │
│  │    - [测试连接] [保存] 按钮                            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                       │ REST
┌──────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                             │
│                                                               │
│  /onboard/*  (新增)                                           │
│    GET  /status           → {configured, onboarded, ...}      │
│    POST /save             → 写 profile.json + invalidate cache│
│    POST /test             → 用传入字段临时构造 client 测一次  │
│    POST /skip             → 写 onboarded=true                 │
│                                                               │
│  ┌─ ProfileCache (api/deps.py 新增) ─────────────────────┐  │
│  │  _profile: UserProfile | None                          │  │
│  │  _llm_client: BaseLLMClient | None                     │  │
│  │  _llm_model: str                                       │  │
│  │                                                       │  │
│  │  get_llm() → 读 cache 或重建                            │  │
│  │  invalidate() → 清 cache                               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ToolRuntime.run_turn(session, user_message)                  │
│    → deps.get_llm() → (client, model)                        │
│    → 用 client.chat(messages, tools, model=...)            │
│                                                               │
│  JsonFileRepository:                                          │
│    save_profile / load_profile → data/profile.json           │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. 数据模型

### 4.1 UserProfile

```python
# core/profile.py
from datetime import datetime
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    llm_provider: str                        # "openai" | "deepseek" | "moonshot" | "custom" | "anthropic"
    base_url: str
    api_key: str                            # 明文(v1);生产需加密
    model_name: str
    onboarded: bool = False                 # True 表示看过引导(即使选 mock 也算)
    onboarded_at: datetime | None = None
    updated_at: datetime = Field(default_factory=datetime.now)

    def masked_key(self) -> str:
        """Return API key masked for display: 'sk-...xxxx'."""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:3]}...{self.api_key[-4:]}"
```

### 4.2 ProviderPreset(后端常量)

```python
# core/providers.py
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
        "supported": False,  # v1 not implemented
        "disabled_reason": "Anthropic uses a non-OpenAI API; will be supported in a later phase.",
    },
}
```

---

## 5. 后端实现

### 5.1 新增文件

```
backend/src/phd_agent/
├── core/
│   ├── profile.py            🆕 UserProfile + masked_key()
│   └── providers.py          🆕 PROVIDER_PRESETS 常量
├── api/
│   └── onboard.py            🆕 4 个端点
└── llm/
    └── (无新增 — 复用现有 MockLLMClient / OpenAICompatClient)
```

### 5.2 修改文件

```
backend/src/phd_agent/
├── core/json_repo.py        ⚠️ 加 save_profile / load_profile
├── core/tool_runtime.py     ⚠️ run_turn 接受 user_id,内部调 deps.get_llm()
├── api/deps.py              ⚠️ 加 ProfileCache + get_llm() + invalidate_profile_cache()
└── api/chat.py              ⚠️ post_message 传 user_id 给 runtime
```

### 5.3 JsonFileRepository 扩展

```python
# core/json_repo.py (新增方法,文件本身 ≤ 250 行)
async def save_profile(self, profile: UserProfile) -> None:
    p = self.base / "profile.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(profile.model_dump_json(indent=2))

async def load_profile(self) -> UserProfile | None:
    p = self.base / "profile.json"
    if not p.exists():
        return None
    return UserProfile.model_validate_json(p.read_text())

async def delete_profile(self) -> None:
    p = self.base / "profile.json"
    if p.exists():
        p.unlink()
```

### 5.4 api/deps.py 改动

```python
# api/deps.py
_profile: UserProfile | None = None
_llm_client: BaseLLMClient | None = None
_llm_model: str = "mock"


def _build_llm_from_profile(profile: UserProfile) -> tuple[BaseLLMClient, str]:
    """Build LLM client + model name from a profile."""
    client = OpenAICompatClient(base_url=profile.base_url, api_key=profile.api_key)
    return client, profile.model_name


def get_llm() -> tuple[BaseLLMClient, str]:
    """Return (client, model_name). Uses cached values, falls back to mock."""
    global _llm_client, _llm_model
    if _llm_client is not None:
        return _llm_client, _llm_model
    profile = asyncio.run(get_repo().load_profile())  # sync wrapper at startup
    # ^ actually we use lazy init: see async get_llm_async below
    if profile and profile.api_key:
        _llm_client, _llm_model = _build_llm_from_profile(profile)
    else:
        _llm_client = MockLLMClient()
        _llm_model = "mock"
    return _llm_client, _llm_model


async def get_llm_async() -> tuple[BaseLLMClient, str]:
    """Async version for use in async contexts (tool_runtime)."""
    global _llm_client, _llm_model
    if _llm_client is not None:
        return _llm_client, _llm_model
    profile = await get_repo().load_profile()
    if profile and profile.api_key:
        _llm_client, _llm_model = _build_llm_from_profile(profile)
    else:
        _llm_client = MockLLMClient()
        _llm_model = "mock"
    return _llm_client, _llm_model


def invalidate_profile_cache() -> None:
    """Drop cached client (called after /onboard/save)."""
    global _llm_client, _llm_model
    _llm_client = None
    _llm_model = "mock"
```

### 5.5 api/onboard.py(完整新文件)

```python
# api/onboard.py
"""Onboarding endpoints: status, save, test, skip."""
from __future__ import annotations
import asyncio
import time
from fastapi import APIRouter, HTTPException
from phd_agent.core.profile import UserProfile
from phd_agent.core.providers import PROVIDER_PRESETS
from phd_agent.api.deps import get_repo, invalidate_profile_cache
from phd_agent.llm.openai_compat import OpenAICompatClient

router = APIRouter()


@router.get("/onboard/status")
async def get_status() -> dict:
    repo = get_repo()
    profile = await repo.load_profile()
    if profile is None:
        return {
            "configured": False,
            "onboarded": False,
            "profile": None,
            "providers": [
                {"key": k, "label": v["label"], "supported": v["supported"]}
                for k, v in PROVIDER_PRESETS.items()
            ],
        }
    return {
        "configured": bool(profile.api_key),
        "onboarded": profile.onboarded,
        "profile": {
            "llm_provider": profile.llm_provider,
            "base_url": profile.base_url,
            "model_name": profile.model_name,
            "api_key_masked": profile.masked_key(),
            "onboarded": profile.onboarded,
        },
        "providers": [
            {"key": k, "label": v["label"], "supported": v["supported"]}
            for k, v in PROVIDER_PRESETS.items()
        ],
    }


@router.post("/onboard/save")
async def save_profile(body: dict) -> dict:
    provider = body.get("llm_provider", "openai")
    if provider not in PROVIDER_PRESETS:
        raise HTTPException(400, f"unknown provider: {provider}")
    if not PROVIDER_PRESETS[provider]["supported"]:
        raise HTTPException(400, f"provider not supported yet: {provider}")

    repo = get_repo()
    existing = await repo.load_profile()
    profile = UserProfile(
        llm_provider=provider,
        base_url=body.get("base_url", PROVIDER_PRESETS[provider]["base_url"]),
        api_key=body.get("api_key", ""),
        model_name=body.get("model_name", PROVIDER_PRESETS[provider]["default_model"]),
        onboarded=True,
        onboarded_at=existing.onboarded_at if existing else None,
    )
    await repo.save_profile(profile)
    invalidate_profile_cache()
    return {
        "profile": {
            "llm_provider": profile.llm_provider,
            "base_url": profile.base_url,
            "model_name": profile.model_name,
            "api_key_masked": profile.masked_key(),
        },
        "message": "saved",
    }


@router.post("/onboard/test")
async def test_connection(body: dict) -> dict:
    """Send a tiny ping to validate the API key. 5s timeout."""
    provider = body.get("llm_provider", "openai")
    if provider not in PROVIDER_PRESETS or not PROVIDER_PRESETS[provider]["supported"]:
        raise HTTPException(400, f"provider not testable: {provider}")

    base_url = body.get("base_url") or PROVIDER_PRESETS[provider]["base_url"]
    api_key = body.get("api_key", "")
    model_name = body.get("model_name") or PROVIDER_PRESETS[provider]["default_model"]

    if not api_key:
        raise HTTPException(400, "api_key required")

    client = OpenAICompatClient(base_url=base_url, api_key=api_key, timeout=5.0)
    started = time.perf_counter()
    try:
        r = await client.chat(
            messages=[{"role": "user", "content": "ping"}],
            tools=None, budget=10, model=model_name,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {"ok": True, "message": "connected", "latency_ms": latency_ms,
                "model": r.model}
    except Exception as e:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {"ok": False, "message": str(e), "latency_ms": latency_ms}


@router.post("/onboard/skip")
async def skip_onboard(body: dict) -> dict:
    """User chose to skip; mark onboarded=True with no LLM config."""
    repo = get_repo()
    existing = await repo.load_profile()
    if existing:
        existing.onboarded = True
        await repo.save_profile(existing)
    else:
        # Write a minimal profile just to mark onboarded
        await repo.save_profile(UserProfile(
            llm_provider="openai", base_url="", api_key="", model_name="",
            onboarded=True,
        ))
    invalidate_profile_cache()
    return {"ok": True}
```

### 5.6 ToolRuntime 改动

最小改动 —— `run_turn` 内部把 `self.llm` / `self.model` 替换为 `await deps.get_llm_async()`:

```python
# core/tool_runtime.py - run_turn 改动
async def run_turn(self, session: ChatSession, user_message: str,
                   run_id: str | None = None) -> AsyncIterator[dict]:
    # ... existing setup ...
    while True:
        llm, model = await self._get_llm()  # NEW: per-turn, may pick up new profile
        tools = await self.registry.list_my_tools(session.user_id)
        response = await llm.chat(
            messages=[m.to_llm_dict() for m in self._build_messages(session)],
            tools=tools,
            model=model,
        )
        # ... rest unchanged ...
```

`_get_llm` 通过工厂调用,简单包装 `deps.get_llm_async`。

### 5.7 api/chat.py 改动

`post_message` 不需要改 —— `run_turn` 内部调 deps.get_llm_async,自动用最新 profile。

### 5.8 main.py 改动

挂载新 router:

```python
from phd_agent.api.onboard import router as onboard_router
app.include_router(onboard_router)
```

---

## 6. 前端实现

### 6.1 新增文件

```
frontend/src/
├── onboard/
│   ├── OnboardModal.tsx       🆕 首次访问引导
│   ├── SettingsModal.tsx      🆕 Chat 顶栏 ⚙ 触发的配置 modal
│   ├── LLMConfigForm.tsx      🆕 共享表单(两个 modal 都用)
│   ├── ProviderPicker.tsx     🆕 provider 下拉
│   └── onboard.css            🆕(或合并到 App.css)
```

### 6.2 修改文件

```
frontend/src/
├── App.tsx                    ⚠️ mount 时拉 /onboard/status,决定是否弹 OnboardModal
├── chat/ChatView.tsx          ⚠️ 顶栏加设置按钮 + provider/model 显示
├── api/client.ts              ⚠️ 加 onboardApi
├── api/types.ts               ⚠️ 加 ProviderInfo / ProfileInfo
└── App.css                    ⚠️ 加 modal / 设置按钮样式
```

### 6.3 OnboardModal UX

```
┌─ OnboardModal ──────────────────────────────────┐
│                                                   │
│            Welcome to PhD-Agent                  │
│                                                   │
│   帮您配置 LLM 后,即可开始和 AI 助手对话。       │
│                                                   │
│   没有 API key? 选「跳过」用本地 mock LLM       │
│   体验功能(之后随时可改)。                      │
│                                                   │
│   ┌────────────────────────────────────────┐    │
│   │      [ 设置 LLM ]                       │    │
│   └────────────────────────────────────────┘    │
│   ┌────────────────────────────────────────┐    │
│   │      [ 跳过,用 mock LLM ]              │    │
│   └────────────────────────────────────────┘    │
│                                                   │
└───────────────────────────────────────────────────┘
```

### 6.4 LLMConfigForm UX

```
┌─ LLMConfigForm ────────────────────────────────────┐
│                                                    │
│   Provider:    [OpenAI ▼]                          │
│                                                    │
│   Base URL:    [https://api.openai.com/v1    ]    │
│                                                    │
│   Model:       [gpt-4o-mini                  ]    │
│                                                    │
│   API Key:     [sk-...xxxxxxx              ] 👁    │
│                                                    │
│   Status: ✅ Connected (234ms)                      │
│                                                    │
│   ┌────────────────────┐  ┌────────────────────┐  │
│   │   [ 测试连接 ]      │  │     [ 保存 ]       │  │
│   └────────────────────┘  └────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

字段联动规则:
- 改 provider → 自动填 base_url 和 model(用户后续手动改覆盖)
- Anthropic 选项 disabled + tooltip「暂不支持」
- API Key 输入框 password 类型,有 👁 切换显示/隐藏
- 测试按钮调用 `/onboard/test`,显示延迟和 ok/fail
- 保存按钮调用 `/onboard/save`,成功后关闭 modal + 刷新 chat 顶栏显示

### 6.5 ChatView 顶栏

```tsx
<header className="chat-header">
  <span className="logo">PhD-Agent</span>
  <span className="provider-tag">
    {providerLabel ? `${providerLabel} · ${modelName}` : 'mock LLM'}
  </span>
  <button onClick={() => setShowSettings(true)}>⚙</button>
</header>
```

`providerLabel` 和 `modelName` 从 `/onboard/status` 读;保存后刷新。

### 6.6 api/client.ts 扩展

```typescript
// api/client.ts - 添加
export const onboardApi = {
  async getStatus(): Promise<OnboardStatus> {
    const r = await fetch('/onboard/status');
    return r.json();
  },
  async save(body: SaveProfileBody): Promise<SaveProfileResponse> { ... },
  async test(body: SaveProfileBody): Promise<TestResponse> { ... },
  async skip(): Promise<{ ok: boolean }> { ... },
};
```

### 6.7 App.tsx 改动

```tsx
// App.tsx - 简化版
function App() {
  const [showOnboard, setShowOnboard] = useState(false);
  const [profile, setProfile] = useState<ProfileInfo | null>(null);
  const userId = 'default-user';

  useEffect(() => {
    onboardApi.getStatus().then((s) => {
      setProfile(s.profile);
      if (!s.onboarded) setShowOnboard(true);
    });
  }, []);

  return (
    <div>
      <Tabs>...</Tabs>
      {showOnboard && (
        <OnboardModal
          onSkip={async () => { await onboardApi.skip(); setShowOnboard(false); /* refresh */ }}
          onSave={async (data) => { await onboardApi.save(data); setShowOnboard(false); /* refresh */ }}
        />
      )}
      {/* existing ChatView / Canvas */}
    </div>
  );
}
```

---

## 7. 测试策略

### 7.1 后端(11 个新测试)

| 测试 | 验证 |
|---|---|
| `test_profile_roundtrip` | save/load profile.json |
| `test_profile_masked_key` | masked_key() 输出格式正确 |
| `test_onboard_status_initial` | 无 profile → configured=false, onboarded=false |
| `test_onboard_status_after_save` | 有 profile → configured=true, onboarded=true |
| `test_onboard_status_api_key_masked` | 返回的 profile 不含完整 api_key |
| `test_onboard_save_persists` | save 后 status 反映新值 |
| `test_onboard_test_ok` | 假 client 返回 ok=true |
| `test_onboard_test_invalid_key` | 假 client 返回 ok=false |
| `test_onboard_test_unsupported_provider` | anthropic → 400 |
| `test_onboard_skip_marks_onboarded` | skip 后 status.onboarded=true |
| `test_invalidate_cache_reloads` | save 后 invalidate,下次 get 看到新 client |
| `test_tool_runtime_uses_profile` | run_turn 用 profile 中的 model,而非硬编码 |

### 7.2 前端(4 个新测试)

| 测试 | 验证 |
|---|---|
| `OnboardModal.test.tsx` | 渲染双按钮;点击「跳过」调 API;点击「设置」切换到 form |
| `LLMConfigForm.test.tsx` | 选 provider 自动填 base_url + model;点击「测试连接」显示状态 |
| `ProviderPicker.test.tsx` | Anthropic disabled,其他可选 |
| `SettingsModal.test.tsx` | 打开显示当前 profile(api_key 已 mask) |

---

## 8. 错误处理

| 错误 | 行为 |
|---|---|
| 用户填错 API key | `/onboard/test` 返回 ok=false,前端显示错误信息,保存按钮仍可用(让用户先验证再保存) |
| `/onboard/save` 时 provider 不支持 | 400 + 不写 profile |
| `/onboard/test` 超时(>5s) | 客户端 timeout,返回 ok=false + "timeout" |
| profile.json 损坏 | 启动 fallback 到 mock,不阻塞 |
| 保存后立即发消息 | invalidate → 下次 `run_turn` 读新 profile → 用新 client |
| Chat 顶栏显示 provider 信息为空 | 显示 "mock LLM" 占位 |

---

## 9. 验收标准(DoD)

### 9.1 后端
- `GET /onboard/status` 返回正确状态
- `POST /onboard/save` 写 `data/profile.json` + invalidate cache
- `POST /onboard/test` 5s 内返回 ok/fail
- `POST /onboard/skip` 标记 onboarded=true
- 11 个新 pytest 全部通过
- Chat 接口不受影响(原有 55 测试全过)
- 真实 LLM(用真 key)+ 手动改 profile 后,下次发消息用新 LLM

### 9.2 前端
- 首次访问自动弹 OnboardModal
- Chat 顶栏显示 provider 信息
- ⚙ 设置按钮打开 SettingsModal
- LLMConfigForm 选 provider 自动填字段
- 「测试连接」按钮显示 ok/fail + 延迟
- 保存后 Chat 顶栏更新,无需刷新页面
- 4 个新 vitest 全部通过
- 现有 3 个 vitest + build 不破

### 9.3 文档
- README 更新:onboard 流程截图 + 常见 provider 配置示例

---

## 10. 范围边界(重申)

### ✅ v1 包含
- UserProfile 数据模型 + 文件持久化
- 4 个 onboard API 端点
- Profile cache + invalidate 机制
- OnboardModal / SettingsModal / LLMConfigForm
- 4 个 provider preset(OpenAI / DeepSeek / Moonshot / Custom + Anthropic-disabled)
- 测试连接
- API key mask

### ❌ v1 不包含
- 加密存储(明文;README 标注生产 TODO)
- Anthropic 实际调用
- i18n
- Profile 历史 / 切换多 profile
- 用户引导之外的设置项(主题、字体等)

---

## 11. 文件改动清单

### 后端
- 新增:`backend/src/phd_agent/core/profile.py`
- 新增:`backend/src/phd_agent/core/providers.py`
- 新增:`backend/src/phd_agent/api/onboard.py`
- 修改:`backend/src/phd_agent/core/json_repo.py`(加 profile 方法)
- 修改:`backend/src/phd_agent/core/tool_runtime.py`(LLM 获取改为异步+按需)
- 修改:`backend/src/phd_agent/api/deps.py`(加 ProfileCache + get_llm_async)
- 修改:`backend/src/phd_agent/api/chat.py`(无,run_turn 内部处理)
- 修改:`backend/src/phd_agent/main.py`(挂 onboard_router)
- 新增:`backend/tests/test_profile.py`
- 新增:`backend/tests/test_onboard_api.py`
- 新增:`backend/tests/test_tool_runtime_profile.py`

### 前端
- 新增:`frontend/src/onboard/OnboardModal.tsx`
- 新增:`frontend/src/onboard/SettingsModal.tsx`
- 新增:`frontend/src/onboard/LLMConfigForm.tsx`
- 新增:`frontend/src/onboard/ProviderPicker.tsx`
- 新增:`frontend/src/onboard/onboard.test.tsx`(合并测试)
- 修改:`frontend/src/App.tsx`(onboard 状态机)
- 修改:`frontend/src/chat/ChatView.tsx`(顶栏设置按钮)
- 修改:`frontend/src/api/client.ts`(加 onboardApi)
- 修改:`frontend/src/api/types.ts`(加 OnboardStatus / ProfileInfo)
- 修改:`frontend/src/App.css`(modal 样式)

---

## 12. 附录:端到端时序(首次访问 → 配置 → 使用)

```
T0  [浏览器] App mount
T1  [前端] GET /onboard/status
T2  [后端] profile.json 不存在 → {configured:false, onboarded:false, providers:[...]}
T3  [前端] 渲染 OnboardModal(双按钮)
T4  [用户]  点击「设置 LLM」
T5  [前端]  modal 切到 LLMConfigForm
T6  [用户]  选 OpenAI、填 sk-...
T7  [用户]  点「测试连接」
T8  [前端]  POST /onboard/test {provider, base_url, api_key, model_name}
T9  [后端]  临时构造 OpenAICompatClient,发 ping 请求
T10 [后端]  返回 {ok:true, latency_ms:234}
T11 [前端]  显示 ✅ Connected (234ms)
T12 [用户]  点「保存」
T13 [前端]  POST /onboard/save {...}
T14 [后端]  写 data/profile.json, invalidate cache
T15 [前端]  关闭 OnboardModal,刷新 status
T16 [前端]  Chat 顶栏显示 "OpenAI · gpt-4o-mini"
T17 [用户]  在 Chat 输入"找 3 篇 ML 论文"
T18 [前端]  POST /chat/conversations/{id}/messages (SSE)
T19 [后端]  ToolRuntime.run_turn → deps.get_llm_async() → 读 profile → 用真 LLM
T20 [后端]  SSE: tool_call_started (knowledge_retriever)
T21 [后端]  SSE: tool_call_completed
T22 [后端]  SSE: message_completed "我找到了 3 篇..."
T23 [前端]  Chat 显示完整对话
```