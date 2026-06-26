# MiniMax Provider + Chat-Wiring Fix

| 字段 | 值 |
|------|-----|
| 版本 | V2.1.1-minimax-wiring |
| 日期 | 2026-06-26 |
| 上游 | `docs/superpowers/specs/2026-06-26-onboard-design.md` |

---

## 1. 范围

### 1.1 包含
- 新增 MiniMax provider preset(后端 `PROVIDER_PRESETS` + 前端 `PRESETS`)
- 修复 chat 路径永远走 mock 的 bug:`get_llm_async()` 升级为唯一的 LLM 解析来源
- 修复 `CompositeAgent.run` 硬编码 `model="MiniMax-m3"`
- 加回归测试,确保 wiring 不会再次断裂

### 1.2 不包含
- profile 加密、Anthropic 真实支持、多 profile

---

## 2. 根因

`backend/src/phd_agent/api/deps.py` 维护了两套相互独立的 LLM 解析路径:
- `get_llm_async()` → 读 profile → `OpenAICompatClient` / `MockLLMClient`(带缓存)
- `get_runtime()` → 硬编码 `llm=MockLLMClient()`、`model="mock"`,从不调 `get_llm_async`

`chat.py` 只调 `get_runtime()`,所以即便 onboard `/test` 通过,chat 仍走 mock。`composite_factory` 同样硬编码 mock,`CompositeAgent.run:38` 硬编码 `"MiniMax-m3"`。

---

## 3. 设计

### 3.1 单一来源
```
       profile.json
            │
            ▼
   get_llm_async() ─── 唯一的 LLM 解析路径(缓存 + invalidate)
            │
            ├──→ ToolRuntime.llm_factory       (顶层 chat)
            │
            └──→ composite_factory (async)     (嵌套 composite 工具)
                        │
                        ▼
                  CompositeAgent(model=self.model)
```

### 3.2 改动清单
| 文件 | 改动 |
|---|---|
| `backend/src/phd_agent/api/deps.py` | `get_runtime()` 删除硬编码 `llm=MockLLMClient()`/`model="mock"`,传 `llm_factory=get_llm_async`;`composite_factory` 改 `async def`,内部调 `get_llm_async()` |
| `backend/src/phd_agent/core/composite_agent.py` | `__init__` 新增 `model: str`;`run()` 用 `self.model` 替换硬编码 `"MiniMax-m3"` |
| `backend/src/phd_agent/core/providers.py` | `PROVIDER_PRESETS` 新增 `"MiniMax": { label: "MiniMax", base_url: "https://api.MiniMax.chat/v1", default_model: "MiniMax-M3", supported: True }` |
| `frontend/src/onboard/LLMConfigForm.tsx` | `PRESETS` 加 `MiniMax` 条目 |
| `frontend/src/onboard/LLMConfigForm.js` | 同上 |
| `backend/tests/test_chat_wiring.py` (新) | 回归测试:profile 有 key 时,断言 `ToolRuntime._llm_factory is get_llm_async` 且 `get_llm_async()` 返回 `OpenAICompatClient`;profile 无 key 时返回 `MockLLMClient` |

### 3.3 错误处理
- 无 profile / api_key 为空 → `get_llm_async` 返回 `MockLLMClient()`(兜底,与现状一致)
- `OpenAICompatClient` 调用失败 → 走 `MockLLMClient` 的现有错误路径(SSE `error` event)

### 3.4 测试策略
TDD 顺序:
1. 写 `test_chat_wiring.py` 红测
2. 改 `deps.py` + `composite_agent.py` 到绿
3. 加 MiniMax 到 `providers.py`,加 frontend `PRESETS`
4. 跑全套 backend 测试 + frontend 测试
