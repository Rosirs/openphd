# PhD-Agent V2.0.0 — Phase 2 Design Spec

| 字段     | 值                                                    |
| -------- | ----------------------------------------------------- |
| 版本     | V2.0.0-phase2                                         |
| 日期     | 2026-06-25                                            |
| 作者     | PhD-Agent 创始团队                                    |
| 状态     | 设计评审中 (In Review)                                |
| 阶段     | Chat-First 架构 + 通用 Agent 套装 + 自定义工具        |
| 上游文档 | `docs/PRD.md`, `docs/superpowers/specs/2026-06-25-phd-agent-v2-skeleton-design.md` |
| 提交状态 | 在 skeleton 设计基础上做重大架构调整（详见 §11 PRD 对齐） |

---

## 1. 范围与目标

### 1.1 本 spec 范围
将 PhD-Agent 从 Phase 1 的「拖拽 + 顺序 pipeline 执行」骨架,演进为 **Chat-First 架构**:LLM 是用户的主交互对象,通过 function calling 自由调用后端工具;画布降级为"自定义工具构建器"。

### 1.2 阶段目标
- ✅ 引入 Chat-First 交互(主入口),画布变 tab
- ✅ 通用 Agent 套装交付:`knowledge_retriever` (arxiv 后端)、`writing_polisher`、`email_drafter`、`pdf_summarizer`
- ✅ 真实 LLM 集成(MiniMax-m3,OpenAI 兼容协议)
- ✅ 动态 tool 列表(LLM 通过 `list_my_tools` 查可用工具)
- ✅ 用户自定义工具(画布拖拽 → 保存为 composite tool → 出现在 LLM 可用列表)
- ✅ JsonFileRepository 持久化(对话、状态、composite 工具)
- ✅ CentralRouter 删除,PipelineOrchestrator 重命名为 CompositeToolExecutor
- ❌ 不交付:多用户鉴权、SQLite 持久化、插件热加载、PubMed 等其他后端实现、生产部署

### 1.3 后续阶段(不在本 spec 范围)
- **Phase 3**:PubMed / OpenAlex / Semantic Scholar 后端实现 + PubMed 看板 widget
- **Phase 4**:SQLite 持久化 + 多用户鉴权 + 迁移工具
- **Phase 5**:插件市场 / 热加载 / 版本管理
- **Phase 6**:生产化(Docker / CI / 监控)

---

## 2. 关键决策一览

| 决策点 | 选择 | 理由 |
| --- | --- | --- |
| 主交互模式 | Chat-First,LLM 是前台 | 用户直接和 LLM 自由对话;backend agent 退化为 LLM 的工具 |
| 画布角色 | 降级为「自定义工具构建器」 | 用户拖出 composite tool,保存后出现在 LLM 工具列表 |
| LLM Provider | MiniMax-m3 (OpenAI 兼容协议) | 与 Phase 1 抽象对齐;env 配置切换 |
| Tool 列表 | 动态 (LLM 调 `list_my_tools`) | 启动时不预注入,支持运行时新增 composite |
| 持久化 | JsonFileRepository,`data/{user_id}/{conversation_id}.json` | 简单可调试;接口化便于 Phase 4 换 SQLite |
| CentralRouter | 删除 | 13 行 stub,被 LLM 循环取代 |
| PipelineOrchestrator | 重命名为 CompositeToolExecutor,仅服务于 composite tool | 复用顺序执行逻辑,不再作为主调度 |
| 通用 agent 范围 | 跨学科、跨国、无场景硬编码 | 用户明确要求"通用,不限学科" |
| 状态模型 | GlobalState 保留,扩展为同时服务 ChatSession | 单一状态源,向后兼容 |
| Chat 流式 | SSE(token 级或 message 级) | 与 Phase 1 一致;先做 message 级,Phase 3 升级 token 级 |

---

## 3. 架构总览

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                            │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐  │
│  │  Chat Tab (主入口)   │  │  Canvas Tab (次要)                  │  │
│  │  MessageList        │  │  Shelf → Canvas → Save as Tool     │  │
│  │  ChatInput          │  │  产出"我的工具"(composite)            │  │
│  │  ToolCallIndicator  │  │                                      │  │
│  └─────────────────────┘  └─────────────────────────────────────┘  │
│         │ SSE / REST                                              │
└─────────┼────────────────────────────────────────────────────────┘
          ↓
┌──────────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                                  │
│                                                                    │
│  /chat/*        → ChatSession + ToolRuntime                        │
│  /tools/*       → ToolRegistry + CompositeToolRepo                 │
│  /canvas/*      → (画布辅助:保存 composite tool)                   │
│  /agents/catalog → 保留,改名 /tools/catalog                        │
│                                                                    │
│  ┌────────────────────────────────────────────────┐               │
│  │  ToolRuntime (核心循环)                          │               │
│  │  loop:                                          │               │
│  │    1. 收集 LLM 可见 inputs:                     │               │
│  │       - system prompt                           │               │
│  │       - conversation history (messages)         │               │
│  │       - tool list (动态:list_my_tools)          │               │
│  │    2. LLM chat(messages, tools, model=m3)      │               │
│  │    3. 解析 response:                            │               │
│  │       - 纯文本 → 推给前端,结束                   │               │
│  │       - tool_call(name, args)                   │               │
│  │         ↓                                       │               │
│  │       ToolExecutor.execute(name, args, state)  │               │
│  │         (composite tool → CompositeToolExecutor)│               │
│  │         (atomic tool → AgentWrapper)            │               │
│  │         ↓                                       │               │
│  │       tool_result 注入 history → 回到 step 2     │               │
│  │    4. 超过 max_tool_calls → 强制结束 + 警告      │               │
│  └────────────────────────────────────────────────┘               │
│           ↓                                                        │
│  ┌────────────────────────────────────────────────┐               │
│  │  ChatSession (per user, per conversation)        │               │
│  │  - conversation_id                              │               │
│  │  - messages: list[Message]                      │               │
│  │  - state: GlobalState (含 dynamic_storage)      │               │
│  └────────────────────────────────────────────────┘               │
│           ↓                                                        │
│  ┌────────────────────────────────────────────────┐               │
│  │  JsonFileRepository                              │               │
│  │  data/{user_id}/                                │               │
│  │    ├─ conversations/{conv_id}.json              │               │
│  │    └─ composite_tools/{tool_id}.json            │               │
│  └────────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 关键架构变化(相对 Phase 1)
- **LLM 移出 Agent 内部** → LLM 是 ChatSession 顶层调度者,不再藏在 `agent.run()` 里
- **PipelineOrchestrator 降级** → 改名为 CompositeToolExecutor,只为 composite tool 服务
- **CentralRouter 删除** → 13 行 stub,ToolRuntime 内部循环取代
- **active_pipeline / current_step 退到 composite 内部** → ChatSession 顶层不感知 pipeline 概念

---

## 4. 后端设计

### 4.1 目录组织(变更部分用 🆕 / ⚠️ / ❌ 标记)

```
backend/
├── src/phd_agent/
│   ├── main.py                  ⚠️ 调整(挂新 router)
│   │
│   ├── core/                    ⚠️ 部分调整
│   │   ├── state.py             ⚠️ active_pipeline/current_step 标记为 composite-internal
│   │   ├── repository.py        ⚠️ 加 JsonFileRepository 实现
│   │   ├── registry.py          ⚠️ 加 list_my_tools(user_id) 动态查询
│   │   ├── contract.py          (不变)
│   │   ├── validator.py         (不变,但调用方从 PipelineOrchestrator 变为 CompositeToolExecutor)
│   │   ├── router.py            ❌ 删除
│   │   ├── wrapper.py           (不变,改名为 agent_wrapper.py 更准确但保持兼容)
│   │   ├── events.py            ⚠️ 加新事件类型:tool_call_started/completed, message_received
│   │   ├── orchestrator.py      ❌ 删除(被 CompositeToolExecutor 替代)
│   │   ├── chat.py              🆕 ChatSession 数据模型 + 持久化
│   │   ├── tool_runtime.py      🆕 LLM 循环 + 工具调度(核心新文件)
│   │   ├── tool_executor.py     🆕 工具执行分发(atomic → wrapper, composite → executor)
│   │   ├── composite.py         🆕 CompositeTool 定义 + 持久化
│   │   └── composite_executor.py 🆕 顺序执行 composite 子图(原 PipelineOrchestrator 改名)
│   │
│   ├── api/                     ⚠️ 调整
│   │   ├── chat.py              🆕 POST /chat/messages, GET /chat/conversations
│   │   ├── tools.py             🆕 GET /tools/catalog, POST /tools/composite, GET /tools/{id}
│   │   ├── canvas.py            🆕 POST /canvas/validate-composite(画布辅助)
│   │   ├── agents.py            ⚠️ 保留但标记 deprecated(转 /tools/catalog)
│   │   ├── pipelines.py         ⚠️ 保留作为 composite 工具的运行入口(内部使用)
│   │   └── schemas.py           ⚠️ 扩展
│   │
│   ├── llm/
│   │   ├── base.py              ⚠️ 加 tool calling 抽象(tools 参数 + tool_call 解析)
│   │   ├── openai_compat.py     ⚠️ 实现 tool calling(OpenAI function calling 格式)
│   │   └── budget.py            (不变)
│   │
│   └── plugins/                 🆕 新增真实插件
│       ├── _base.py             (不变)
│       ├── mock_echo/           (保留,作为示例)
│       ├── mock_logger/         (保留,作为示例)
│       ├── arxiv_search/        🆕 真实 arxiv API 实现
│       ├── knowledge_retriever/ 🆕 抽象 dispatch(默认后端:arxiv_search,可换)
│       ├── writing_polisher/    🆕 LLM 通用写作润色
│       ├── email_drafter/       🆕 LLM 通用文书生成
│       └── pdf_summarizer/      🆕 LLM 通用 PDF/文本总结
```

### 4.2 核心数据模型

**Message**(聊天消息)
```python
# core/chat.py
class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[ToolCall] | None = None      # assistant 发出
    tool_call_id: str | None = None                # tool 响应时关联
    name: str | None = None                        # tool 名称
    timestamp: datetime
```

**ChatSession**
```python
# core/chat.py
class ChatSession(BaseModel):
    user_id: str
    conversation_id: str                          # UUID
    title: str                                     # 第一次 user 消息截取
    messages: list[Message]
    state: GlobalState                             # 含 dynamic_storage
    created_at: datetime
    updated_at: datetime
    status: Literal["active", "archived"] = "active"
```

**CompositeToolDefinition**
```python
# core/composite.py
class CompositeToolDefinition(BaseModel):
    tool_id: str                                   # user 给的友好名,如 "my_research_finder"
    name: str
    description: str                               # LLM 看到这个就懂怎么调
    owner_user_id: str                             # 谁的工具
    sub_pipeline: list[str]                        # agent_id 列表,如 ["arxiv_search", "writing_polisher"]
    is_public: bool = False                        # 未来:用户分享工具
    created_at: datetime
    updated_at: datetime
```

**ToolSpec**(LLM 看到的工具 schema)
```python
# core/registry.py
class ToolSpec(BaseModel):
    name: str                                      # agent_id
    description: str
    parameters: dict                               # JSON Schema(从 AgentContract.required_fields 推导)
    category: str
    is_composite: bool = False
    composite_def: CompositeToolDefinition | None = None  # composite 工具才有
```

**ToolCall**(LLM 发出的工具调用)
```python
# core/chat.py
class ToolCall(BaseModel):
    id: str                                        # OpenAI tool_call_id
    name: str                                      # tool 名称
    args: dict                                     # tool 参数
```

**ToolResult**(工具执行结果)
```python
# core/tool_executor.py
class ToolResult(BaseModel):
    tool_name: str
    success: bool
    summary: str                                   # 给人看的简短摘要
    state_delta: dict                              # 写入 GlobalState 的字段
    llm_context: str                               # 注入 LLM context 的字符串(tool role message)
    error: str | None = None

    def to_message(self, tool_call_id: str) -> Message:
        return Message(
            role="tool",
            tool_call_id=tool_call_id,
            name=self.tool_name,
            content=self.llm_context,
            timestamp=datetime.now(),
        )
```

### 4.3 ToolRuntime 核心循环

```python
# core/tool_runtime.py
class ToolRuntime:
    def __init__(self, registry, llm, executor, bus, chat_repo, max_tool_calls=10):
        self.registry = registry
        self.llm = llm
        self.executor = executor          # ToolExecutor
        self.bus = bus
        self.chat_repo = chat_repo
        self.max_tool_calls = max_tool_calls

    async def run_turn(self, session: ChatSession, user_message: str) -> AsyncIterator[Event]:
        """处理一轮 user → assistant(可能含多次 tool_call)→ user。"""
        # 1. 追加 user 消息
        session.messages.append(Message(role="user", content=user_message, timestamp=now()))
        yield Event(type="message_received", ...)

        # 2. 循环直到 LLM 给出纯文本或超限
        tool_call_count = 0
        while True:
            tools = await self.registry.list_my_tools(session.user_id)
            response = await self.llm.chat(
                messages=_to_llm_messages(session.messages),
                tools=[t.model_dump() for t in tools],
                model="MiniMax-m3",
            )

            if not response.tool_calls:
                # LLM 给出最终文本回复
                session.messages.append(Message(role="assistant", content=response.content, timestamp=now()))
                session.state.status = "completed"
                yield Event(type="message_completed", content=response.content, ...)
                return

            # 处理 tool_calls
            session.messages.append(Message(
                role="assistant", content=response.content,
                tool_calls=response.tool_calls, timestamp=now(),
            ))
            exceeded = False
            for tc in response.tool_calls:
                if tool_call_count >= self.max_tool_calls:
                    exceeded = True
                    # 仍追加 tool 消息(空结果 + 错误)以满足 OpenAI 协议
                    session.messages.append(Message(
                        role="tool", tool_call_id=tc.id, name=tc.name,
                        content="[skipped: max_tool_calls exceeded]",
                        timestamp=now(),
                    ))
                    continue
                tool_call_count += 1
                yield Event(type="tool_call_started", name=tc.name, args=tc.args, ...)

                result = await self.executor.execute(
                    name=tc.name, args=tc.args, state=session.state,
                )
                yield Event(type="tool_call_completed", name=tc.name, summary=result.summary, ...)

                # 注入 tool 结果到 history
                session.messages.append(result.to_message(tc.id))

            # 持久化 + 回到 LLM
            await self.chat_repo.save(session)
            if exceeded:
                yield Event(type="warning", message=f"max_tool_calls={self.max_tool_calls} exceeded,后续 tool_call 已跳过", ...)
            yield Event(type="turn_continued", ...)
```

### 4.4 ToolExecutor 调度

```python
# core/tool_executor.py
class ToolExecutor:
    def __init__(self, registry, wrapper, composite_executor, bus):
        self.registry = registry
        self.wrapper = wrapper                    # AgentWrapper
        self.composite_executor = composite_executor  # CompositeToolExecutor
        self.bus = bus

    async def execute(self, *, name: str, args: dict, state: GlobalState) -> ToolResult:
        spec = await self.registry.get_tool(name, state.user_id)
        if spec.is_composite:
            # composite tool 走子图顺序执行
            return await self.composite_executor.run(
                tool=spec.composite_def, state=state,
            )
        # atomic tool 走 AgentWrapper
        return await self.wrapper.execute_one(state, name, args)
```

### 4.5 CompositeToolExecutor(原 PipelineOrchestrator 改名)

签名变化:
```python
# 旧
async def run(self, user_id: str, active_pipeline: list[str], ...) -> str

# 新
async def run(self, *, tool: CompositeToolDefinition, state: GlobalState) -> ToolResult
```

内部逻辑保持不变(validate → 顺序执行 wrapper),只是:
- 接收 CompositeToolDefinition 而不是 list[str]
- 操作传入的 state 而不是新建
- 返回 ToolResult 而不是 run_id
- active_pipeline / current_step 仅在 composite 内部使用,顶层 ChatSession 不感知

### 4.6 JsonFileRepository

```python
# core/repository.py
class JsonFileRepository(IStateRepository, IChatRepository, ICompositeRepository):
    def __init__(self, base_dir: Path = Path("data")):
        self.base = base_dir

    async def save_conversation(self, session: ChatSession) -> None:
        path = self.base / session.user_id / "conversations" / f"{session.conversation_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.model_dump_json(indent=2))

    async def load_conversation(self, user_id: str, conv_id: str) -> ChatSession | None: ...

    async def list_conversations(self, user_id: str) -> list[ChatSession]: ...

    async def save_composite_tool(self, tool: CompositeToolDefinition) -> None:
        path = self.base / tool.owner_user_id / "composite_tools" / f"{tool.tool_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tool.model_dump_json(indent=2))

    async def list_composite_tools(self, user_id: str) -> list[CompositeToolDefinition]: ...
```

---

## 5. 通用 Agent 套装

| 工具 ID | 类别 | 实现 | 契约示例 | 说明 |
|--------|------|------|---------|------|
| `arxiv_search` | 检索 | 调 arxiv.org API | `q: str, max_results: int=10` | knowledge_retriever 的默认后端 |
| `knowledge_retriever` | 检索 | 抽象 dispatch | `query: str, backend: str="arxiv"` | 通用检索接口,Phase 2 仅 arxiv 一个后端,Phase 3+ 加 pubmed/openalex |
| `writing_polisher` | LLM | MiniMax-m3 | `text: str, style: str="academic"` | 通用润色,prompt 模板可换 |
| `email_drafter` | LLM | MiniMax-m3 | `purpose: str, context: dict, target: str` | 通用邮件生成(套磁、CSC、咨询等) |
| `pdf_summarizer` | LLM | MiniMax-m3 | `text: str, focus: str=""` | 通用文本/PDF 总结 |
| `mock_echo` | mock | 原样返回 | `text: str` | 教学示例,保留 |
| `mock_logger` | mock | 追加到 log | `event: str` | 教学示例,保留 |

**`mock_echo` / `mock_logger` 保留**:演示如何写插件,作为新插件作者的参考。

**`intent_parser` / `clarify_node` / `human_review` 不再独立**:LLM 在 chat 里直接处理意图澄清、草稿审批。

---

## 6. HTTP API 契约

| Method | Path | 用途 | Request | Response |
| --- | --- | --- | --- | --- |
| `POST` | `/chat/conversations` | 新建对话 | `{user_id, title?}` | `{conversation_id, session}` |
| `GET` | `/chat/conversations` | 列出用户所有对话 | `?user_id=` | `{conversations: [...]}` |
| `GET` | `/chat/conversations/{id}` | 读取对话 | — | `{session}` |
| `POST` | `/chat/conversations/{id}/messages` | 发送消息(SSE 流) | `{content}` | SSE stream |
| `DELETE` | `/chat/conversations/{id}` | 删除对话 | — | `{ok}` |
| `GET` | `/tools/catalog` | 列出所有可用工具(含 atomic + 用户 composite) | `?user_id=` | `{tools: [ToolSpec]}` |
| `GET` | `/tools/{tool_id}` | 工具详情 | — | `{spec}` |
| `POST` | `/canvas/composite` | 保存 composite tool(画布提交) | `{tool_id, name, description, sub_pipeline, is_public?}` | `{tool}` |
| `DELETE` | `/canvas/composite/{tool_id}` | 删除 composite tool | — | `{ok}` |
| `POST` | `/canvas/validate-composite` | 画布拖拽时实时校验 | `{sub_pipeline}` | `{valid, steps}` |
| `GET` | `/health` | 健康检查 | — | `{ok}` |

**SSE 事件类型**(chat 流):
- `message_received` — 用户消息已收到
- `tool_call_started` — LLM 决定调用工具
- `tool_call_completed` — 工具执行完成
- `tool_call_skipped` — 超过 max_tool_calls,跳过
- `turn_continued` — 一轮 tool_call 结束,LLM 继续生成
- `message_completed` — LLM 给出最终文本
- `error` — 异常

---

## 7. 核心数据流(端到端时序)

### 7.1 场景:用户问"帮我找一个关于 X 的工作"

| 时刻 | 浏览器侧 | 后端侧 |
| --- | --- | --- |
| t=0 | 用户在 Chat 输入"帮我找 CS 方向 X 的工作" | — |
| t=10ms | POST /chat/conversations/{id}/messages | ToolRuntime.run_turn 启动 |
| t=15ms | SSE: message_received | session.messages append user msg |
| t=20ms | — | registry.list_my_tools(user_id) → 返回 7 个 tool specs |
| t=120ms | — | LLM.chat(messages, tools, model=m3) |
| t=1.2s | SSE: tool_call_started name=knowledge_retriever args={query: "X"} | — |
| t=1.3s | ToolCallIndicator 显示"正在检索..." | ToolExecutor.execute → knowledge_retriever.run |
| t=2.8s | SSE: tool_call_completed summary="找到 8 篇论文" | tool_result 注入 messages |
| t=2.9s | SSE: turn_continued | 回到 LLM |
| t=3.8s | SSE: message_completed content="我帮你找到..." | session 持久化 |
| t=3.9s | ChatInput 重新可输入 | — |

### 7.2 场景:用户保存自定义工具"my_research_finder"

| 时刻 | 浏览器侧 | 后端侧 |
| --- | --- | --- |
| t=0 | Canvas tab,拖 arxiv_search → writing_polisher | — |
| t=1s | usePipelineValidation(TS) 实时校验 → 绿线 | — |
| t=2s | 点 "Save as my tool",填 tool_id="my_research_finder" | — |
| t=2.1s | POST /canvas/validate-composite | CompositeToolExecutor.validate |
| t=2.2s | POST /canvas/composite | 持久化到 JsonFileRepository |
| t=2.3s | 切回 Chat,问"用 my_research_finder 找..." | — |
| t=2.4s | — | list_my_tools 返回 8 个(含新 composite) |
| t=2.5s | LLM 看到 my_research_finder,决定调用 | — |
| t=2.6s | SSE: tool_call_started name=my_research_finder | CompositeToolExecutor.run |
| t=2.7s | — | 顺序执行 arxiv_search → writing_polisher |
| t=3.5s | SSE: tool_call_completed summary="..." | 返回 ToolResult |

---

## 8. 前端设计

### 8.1 目录组织
```
frontend/src/
├── App.tsx                     ⚠️ 改为 Tab 容器
├── main.tsx
├── chat/                       🆕 Chat 模式
│   ├── ChatView.tsx
│   ├── MessageList.tsx
│   ├── MessageBubble.tsx
│   ├── ChatInput.tsx
│   └── ToolCallIndicator.tsx
├── canvas/                     ⚠️ 功能调整
│   ├── FlowCanvas.tsx          (保留,改名为 ToolBuilderCanvas)
│   ├── usePipelineValidation.ts (保留,功能不变)
│   └── AgentNode.tsx           (保留)
├── shelf/                      (保留,功能不变)
│   ├── AgentShelf.tsx
│   └── AgentCard.tsx
├── workspace/                  ⚠️ 改为 tool 结果展示
│   ├── WorkspaceRoot.tsx
│   └── widgets/
│       ├── PipelineRunLog.tsx  (改名 ToolCallLog,显示 tool_call 历史)
│       ├── AgentCatalogInfo.tsx
│       └── MockWidget.tsx
├── api/                        ⚠️ 扩展
│   ├── client.ts               (加 chat / tools / canvas API)
│   └── types.ts                (加 Message / ToolSpec / CompositeToolDefinition)
└── validator/                  (保留,功能不变)
```

### 8.2 App.tsx 顶层结构
```typescript
type Tab = "chat" | "canvas";

function App() {
  const [tab, setTab] = useState<Tab>("chat");
  const [conversationId, setConversationId] = useState<string | null>(null);

  return (
    <div>
      <Tabs value={tab} onChange={setTab}>
        <Tab value="chat">Chat</Tab>
        <Tab value="canvas">Canvas</Tab>
      </Tabs>
      {tab === "chat" && <ChatView conversationId={conversationId} ... />}
      {tab === "canvas" && <ToolBuilderCanvas ... />}
    </div>
  );
}
```

### 8.3 ChatView 关键交互
- 左侧:历史对话列表
- 中间:MessageList(MessageBubble 按 role 渲染:user 右对齐、assistant 左对齐、tool 灰色)
- 底部:ChatInput + 工具状态指示器(ToolCallIndicator:当前正在调哪个工具)
- SSE 实时追加消息,打字机效果(Message 级别,Phase 3 升级 token 级别)

### 8.4 ToolBuilderCanvas 调整
- 拖拽逻辑保留(Phase 1 已实现)
- 画布顶部加 "Save as my tool" 按钮(替代 "Run" 按钮)
- "Run" 按钮保留(仅作为 composite tool 的本地测试,可选)

---

## 9. 状态持久化布局

```
data/
└── {user_id}/
    ├── conversations/
    │   ├── {conv_id_1}.json    # ChatSession
    │   ├── {conv_id_2}.json
    │   └── ...
    ├── composite_tools/
    │   ├── {tool_id_1}.json    # CompositeToolDefinition
    │   └── ...
    └── profile.json            # 用户档案(预留,Phase 4 用)
```

**ChatSession JSON 结构**:
```json
{
  "user_id": "user_123",
  "conversation_id": "conv_abc",
  "title": "帮我找 CS 方向工作",
  "messages": [...],
  "state": {
    "user_id": "user_123",
    "user_background": {"major": "CS", "gpa": 3.8},
    "active_pipeline": [],          // composite 内部使用,顶层常为空
    "current_step": 0,
    "dynamic_storage": {},          // 工具间传数据
    "error_log": [],
    "status": "completed"
  },
  "created_at": "...",
  "updated_at": "...",
  "status": "active"
}
```

**Concurrent 写入安全**:Phase 2 单进程假设,文件锁留接口,Phase 4 实现。

---

## 10. 错误处理策略

| 错误类型 | 处理位置 | 用户感知 |
|--------|---------|---------|
| LLM API 失败 | ToolRuntime try/except | 流中断,显示 "LLM 调用失败, 请重试" |
| Tool 执行异常 | ToolExecutor try/except | tool_call_completed 带 error,LLM 收到错误上下文,可能自我恢复 |
| Composite 内部异常 | CompositeToolExecutor try/except | 整个 composite 标 failed,工具返回错误摘要给 LLM |
| JsonFile 写入失败 | repository try/except | 5xx,前端提示"保存失败" |
| max_tool_calls 超限 | ToolRuntime 强制结束 | 警告事件,前端显示"工具调用次数过多,对话已强制结束" |
| 未知 tool_id | ToolExecutor 抛 ToolNotFound | tool_call_completed 带 error,LLM 收到错误 |

**核心原则**(与 PRD §6 一致):任何错误不得导致全局崩溃,LLM 永远能从错误中恢复(收到 tool 错误 → 改用其他工具 / 道歉 / 询问用户)。

---

## 11. PRD 对齐

### 11.1 Phase 1 skeleton spec 中明确列出的后续阶段
原 spec §13 写:"Phase 2:实现 1 个真实插件(如 pubmed_scout)+ 真实 LLM 接入"。

**本 spec 与原 spec 的关键出入**:

| 维度 | 原 spec | 本 spec | 原因 |
|------|--------|--------|------|
| Phase 2 范围 | 单插件 + LLM | 整套通用 agent + Chat-First 架构 | 用户要求"通用 + 可修改 + 开箱即用" |
| 主交互 | 画布(延续 Phase 1) | Chat 优先,画布降级 | 用户要求"用户直接和 LLM 自由交互" |
| 真实插件示例 | pubmed_scout | knowledge_retriever (arxiv 后端) | 用户要求"通用,不限学科" |
| 持续化 | InMemoryRepository | JsonFileRepository | 用户要求"先 JSON 后续换 SQLite" |
| CentralRouter | 保留(预留扩展) | 删除 | 实际代码 13 行 stub,被 LLM 循环取代 |
| PipelineOrchestrator | 保留为主调度 | 重命名为 CompositeToolExecutor | 让 LLM 接管主调度 |

### 11.2 与 PRD §3.2 / §4 的关系
- §3.2 中列出的 intent_parser / arxiv_scout / pubmed_scout / jargon_polisher / csc_matcher → 全部移除,通用 agent 替代
- §4.1 校验算法 → 保留,作为 composite tool 校验使用(同算法,新调用方)
- §4.2 CentralRouter → 删除
- §5 WebUI 拖拽画布 → 保留但降级为"自定义工具构建器"
- §6 沙盒化 / Token 隔离 / 懒加载 → 全部保留

### 11.3 PRD 是否需要更新
建议在 Phase 2 完成后,更新 PRD 反映:
- §1.2 加入"Chat-First"产品定位
- §3.2 改写为通用 agent 模型
- §4.2 改写为"LLM-driven 调度"
- §5 加入 Chat tab 设计

本 spec 不修改 PRD,仅在 §11 标注出入;PRD 更新是 Phase 2 完成后的 follow-up。

---

## 12. 验收标准(Definition of Done)

### 12.1 后端
- `uvicorn phd_agent.main:app` 启动成功,`curl /health` 返回 `{ok: true}`
- `curl /tools/catalog` 返回 ≥ 5 个工具(4 个通用 + 2 个 mock)
- Chat 端到端:用户发消息 → LLM 调 arxiv_search → LLM 给最终回复(SSE 流)
- 用户在画布保存 composite tool → 出现在 `/tools/catalog` → LLM 可调用
- 真实 arxiv API 调用成功(用 `python-arxiv` 或裸 HTTP)
- pytest 通过:Phase 1 测试 + 新增 chat / tool_runtime / composite_executor 测试(覆盖率 ≥ 70% on `core/`)

### 12.2 前端
- 启动后默认进入 Chat tab
- Chat 端到端:发消息 → 看到 tool_call_started / tool_call_completed 指示器 → 看到 LLM 文本回复
- 切到 Canvas tab → 拖 2 个工具 → 绿线 → 填 tool_id → 保存 → 切回 Chat → 验证 LLM 看到新工具
- 控制台无报错

### 12.3 架构
- CentralRouter 文件已删除
- PipelineOrchestrator 重命名为 CompositeToolExecutor
- LLM 调用通过 OpenAI 兼容协议指向 MiniMax-m3
- 数据持久化到 `data/{user_id}/` JSON 文件

### 12.4 文档
- `docs/superpowers/specs/2026-06-25-phd-agent-v2-phase2-design.md` (本文件) 提交
- `docs/superpowers/plans/2026-06-25-phd-agent-v2-phase2.md` 由 writing-plans 流程生成
- README.md 更新 Quick start 与 Phase 2 用法

---

## 13. 测试策略

### 13.1 后端(pytest)
- `test_chat.py` — ChatSession 持久化、Message 序列化
- `test_tool_runtime.py` — LLM 循环、tool_call 处理、max_tool_calls 超限
- `test_composite_executor.py` — 子图顺序执行(原 test_pipeline_e2e.py 改名)
- `test_composite_repo.py` — 画布保存/读取
- `test_knowledge_retriever.py` — arxiv API mock 测试
- `test_writing_polisher.py` / `test_email_drafter.py` — LLM mock 测试

### 13.2 前端(Vitest)
- `chat/MessageList.test.tsx` — 消息渲染
- `canvas/usePipelineValidation.test.ts` — 保留 Phase 1 测试
- `api/types.test.ts` — 镜像后端 schema

### 13.3 集成测试
- E2E:用户发消息 → LLM 调 tool → 收到回复(用 mock LLM,验证流程)
- E2E:画布保存 composite → Chat 调用 composite → 验证子图被顺序执行

---

## 14. 文件和代码约束(沿用 Phase 1 附录 B)
- 单个 Python 文件不超过 250 行
- 单个 TSX/TS 文件不超过 200 行
- 超过即拆分,预计会导致超限时必须**在编写前**直接拆分
- 严禁过度设计:除非业务明确要求,不添加多层 try/except

---

## 15. 开放问题(Phase 2 内决策 / 后续阶段)

### 15.1 Phase 2 内必须决策
1. **MiniMax-m3 实际 API 接入细节**:base_url、api_key 来源(env 变量名)、model 字段值 → 实施时确认
2. **max_tool_calls 默认值**:暂定 10,需测试调优
3. **System prompt 内容**:LLM 的 system prompt 模板(包含工具使用指南、领域知识) → 实施时设计
4. **composite tool 校验时机**:Phase 1 画布已有前端校验(TS 版 validate),保存时后端再次校验。是否需要额外的"运行时"校验(composite tool 被 LLM 调用时)?暂定不需要,保存时校验足够

### 15.2 后续阶段
- Phase 3:PubMed / OpenAlex 后端、widget 增强、token 级 streaming
- Phase 4:SQLite、多用户鉴权、composite tool 共享
- Phase 5:插件市场、热加载、版本管理
- Phase 6:Docker / CI / 监控

---

## 附录 A:术语表

| 术语 | 含义 |
|------|------|
| ChatSession | 用户的单次对话(含 messages + state) |
| ToolRuntime | LLM + tool 调用的核心循环(取代 Phase 1 的 PipelineOrchestrator) |
| ToolExecutor | 单个 tool 调用的执行分发(atomic → wrapper, composite → executor) |
| CompositeTool | 用户在画布上组合的自定义工具 |
| CompositeToolExecutor | composite tool 的顺序执行器(原 PipelineOrchestrator 改名) |
| list_my_tools | LLM 调用的动态工具发现接口 |
| ToolSpec | LLM 看到的工具 schema(JSON Schema 格式) |

## 附录 B:迁移影响清单

| Phase 1 文件 | Phase 2 状态 | 备注 |
|-------------|-------------|------|
| `core/router.py` | 删除 | — |
| `orchestrator.py` | 重命名为 `core/composite_executor.py` | 函数签名改 |
| `core/wrapper.py` | 保留 + 加 `execute_one(state, name, args)` 便捷方法 | 适配 composite 内调用 |
| `core/state.py` | 保留 + 加注释说明 active_pipeline/current_step 是 composite-internal | — |
| `core/registry.py` | 加 `list_my_tools(user_id)` 动态方法 | — |
| `core/events.py` | 加新事件类型 | — |
| `core/repository.py` | 加 `JsonFileRepository` 实现 + 拆出 `IChatRepository` / `ICompositeRepository` | 接口分离 |
| `api/agents.py` | 标记 deprecated,内部转 /tools/catalog | — |
| `api/pipelines.py` | 保留作为 composite tool 内部调用入口(内部 API) | — |
| `frontend/App.tsx` | 改为 Tab 容器 | — |
| `frontend/canvas/*` | 保留 + 顶部按钮改 "Save as my tool" | — |
| `frontend/workspace/*` | 改为 tool 结果展示 | — |

所有 Phase 1 测试需要更新 import path(`PipelineOrchestrator` → `CompositeToolExecutor`)。
