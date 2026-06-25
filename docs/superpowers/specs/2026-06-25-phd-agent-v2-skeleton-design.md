# PhD-Agent V2.0.0 — Skeleton Design Spec

| 字段     | 值                                                    |
| -------- | ----------------------------------------------------- |
| 版本     | V2.0.0-skeleton                                       |
| 日期     | 2026-06-25                                            |
| 作者     | PhD-Agent 创始团队                                    |
| 状态     | 设计评审中 (In Review)                                |
| 阶段     | 整体架构设计 + 最小可交互骨架                          |
| 上游文档 | `docs/PRD.md`, `docs/Instruction.md`                  |
| 提交状态 | 当前工作目录未初始化为 git 仓库；spec 已落盘待用户审阅，批准后再 `git init` 并提交 |

---

## 1. 范围与目标

### 1.1 本 spec 范围
本文档定义 PhD-Agent V2.0.0 的**完整架构**，并明确"骨架（skeleton）"阶段要交付什么、不交付什么。

### 1.2 阶段目标
- ✅ 交付完整 V2.0.0 架构（覆盖 PRD 中所有子系统）
- ✅ 交付可运行的最小交互骨架：后端启动 + 前端拖拽 + 跑一次 mock pipeline
- ❌ 不交付：真实 PubMed/arXiv/LLM 接入、完整生产级前端、复杂用户系统、多用户持久化

### 1.3 后续阶段（不在本 spec 范围）
每个后续阶段单独 spec：
- **Phase 2**：实现 1 个真实插件（如 `pubmed_scout`）+ 真实 LLM 接入
- **Phase 3**：完整前端 Workspace widgets（PubMed 看板、Diff View）
- **Phase 4**：多用户 / SQLite 持久化 / 鉴权
- **Phase 5**：插件市场（外部插件上传、热加载、版本管理）

---

## 2. 关键决策一览

| 决策点 | 选择 | 理由 |
| --- | --- | --- |
| 后端语言/框架 | Python 3.11 + FastAPI | AI/ML 生态主流、异步、Pydantic 强类型 |
| 前端框架 | React 18 + TypeScript + Vite + React Flow | 拖拽画布开箱即用、组件库丰富 |
| 插件隔离 | 进程内 `importlib` 动态加载 + try/except wrapper | 与骨架规模匹配；未来可升级到 subprocess |
| LLM 抽象 | 自建 `BaseLLMClient` + OpenAI 兼容实现 | 零锁定、轻量、可换任意 provider |
| State 持久化 | `IStateRepository` 接口 + 内存默认实现 | 与"可插拔"哲学一致 |
| 实时校验 | REST 拉契约 + 前后端双重校验 | 架构最简、客户端零延迟 |
| 执行日志推送 | SSE（骨架阶段） / WebSocket（未来） | SSE 浏览器友好、单向够用 |
| 测试 | pytest（后端）+ Vitest（前端 validator 镜像） | 与语言栈对齐 |

---

## 3. 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
│  ┌───────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Agent    │  │   Flow Canvas    │  │    Dynamic       │  │
│  │  Shelf    │→ │  (React Flow)    │→ │   Workspace      │  │
│  │ (Market)  │  │  + Validator.ts  │  │  (Widgets)       │  │
│  └───────────┘  └──────────────────┘  └──────────────────┘  │
│         ↑              │ ↓ REST                   ↑        │
└─────────┼──────────────┼──────────────────────────┼────────┘
          │              ↓                           │
┌─────────┼──────────────────────────────────────────┼────────┐
│ Backend (FastAPI)              ↓                  │        │
│  ┌──────────────┐    ┌──────────────────────┐    │        │
│  │  /agents/    │    │  /pipelines/run      │────┘        │
│  │   catalog    │    │  /pipelines/validate │             │
│  └──────────────┘    └──────────────────────┘             │
│           ↓                    ↓                           │
│  ┌────────────────────────────────────────────────┐        │
│  │             Pipeline Orchestrator              │        │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │        │
│  │  │ Validator│→│ Registry │→│   Central    │    │        │
│  │  │ (契约校验)│ │(Agent注册)│ │   Router     │    │        │
│  │  └──────────┘ └──────────┘ └──────────────┘    │        │
│  │                                       ↓         │        │
│  │  ┌──────────────────────────────────────────┐  │        │
│  │  │     AgentWrapper (统一执行 + 沙盒)        │  │        │
│  │  │     - 动态 importlib 加载                │  │        │
│  │  │     - try/except 隔离                     │  │        │
│  │  │     - Token 预算截断                      │  │        │
│  │  └──────────────────────────────────────────┘  │        │
│  └────────────────────────────────────────────────┘        │
│           ↓                    ↓                           │
│  ┌────────────────┐    ┌──────────────────┐               │
│  │ GlobalState    │    │ LLMClient        │               │
│  │ (IStateRepo)   │    │ (BaseLLMClient)  │               │
│  └────────────────┘    └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 三大核心组件职责
- **AgentRegistry**：启动时扫描 `plugins/` 目录，收集所有 `AgentContract` 元数据；提供按 `agent_id` 懒加载具体实现的接口。
- **GlobalState + IStateRepository**：唯一数据源；通过 Repository 接口隔离具体存储。
- **CentralRouter**：唯一调度点；不实现任何业务逻辑，只读 `state.current_step` 决定下一节点或 END。

### 3.2 数据流单一来源
- 后端 `core/contract.py` 是 Agent 契约的 **single source of truth**
- Pydantic schema 通过 `/agents/catalog` JSON 化
- 前端 `validator/types.ts` 镜像同一份契约类型
- 关键 schema 变更时由 PR review 同步，骨架阶段不引入 OpenAPI codegen

---

## 4. 后端设计

### 4.1 目录组织
```
backend/
├── pyproject.toml              # uv/pip 依赖，Python 3.11+
├── README.md
├── src/phd_agent/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app 入口，挂载 router
│   │
│   ├── core/                   # 核心编排（不依赖具体插件）
│   │   ├── state.py            # GlobalState Pydantic model
│   │   ├── repository.py       # IStateRepository + InMemory/JsonFile
│   │   ├── registry.py         # AgentRegistry：扫描/加载/查询
│   │   ├── contract.py         # AgentContract / Required / Output 类型
│   │   ├── validator.py        # validate_pipeline() 纯函数
│   │   ├── router.py           # CentralRouter：current_step 调度
│   │   └── wrapper.py          # AgentWrapper：try/except + Token 截断
│   │
│   ├── api/                    # HTTP 边界
│   │   ├── agents.py           # GET /agents/catalog
│   │   ├── pipelines.py        # POST /pipelines/validate, /run, /events
│   │   └── schemas.py          # 请求/响应 Pydantic schemas
│   │
│   ├── llm/                    # LLM 抽象
│   │   ├── base.py             # BaseLLMClient abstract
│   │   ├── openai_compat.py    # OpenAI 兼容协议实现
│   │   └── budget.py           # TokenGuardrail
│   │
│   └── plugins/                # 插拔插件目录
│       ├── _base.py            # BaseAgent 抽象类
│       ├── mock_echo/          # MVP 演示插件 1
│       │   ├── __init__.py
│       │   ├── agent.py        # class MockEchoAgent(BaseAgent)
│       │   └── contract.json
│       └── mock_logger/        # MVP 演示插件 2
│           ├── __init__.py
│           ├── agent.py
│           └── contract.json
└── tests/
    ├── test_validator.py
    ├── test_router.py
    ├── test_wrapper.py
    └── test_pipeline_e2e.py
```

### 4.2 核心接口定义

**AgentContract**（插件作者必须声明）
```python
# core/contract.py
from pydantic import BaseModel, Field
from typing import ClassVar, Literal

class AgentContract(BaseModel):
    agent_id: str
    name: str
    description: str
    category: Literal["academic", "writing", "admin", "mock"]
    required_fields: set[str]              # 输入契约（核心字段用裸名，
                                            # 如 "email_draft"；
                                            # dynamic_storage 字段用点路径，
                                            # 如 "dynamic_storage.pubmed_papers"）
    output_fields: set[str]                # 输出契约（命名约定同上）
    token_budget: int = 4000               # PRD §6
    isolation: Literal["in_process"] = "in_process"  # 未来扩展位

class BaseAgent(ABC):
    contract: ClassVar[AgentContract]

    @abstractmethod
    async def run(self, state: "GlobalState") -> "GlobalState":
        """业务逻辑；不得直接抛出异常给外层（wrapper 会捕获）"""
```

**GlobalState**
```python
# core/state.py
class GlobalState(BaseModel):
    user_id: str
    user_background: dict = Field(default_factory=dict)
    active_pipeline: list[str] = Field(default_factory=list)
    current_step: int = 0
    dynamic_storage: dict = Field(default_factory=dict)
    error_log: list[dict] = Field(default_factory=list)
    status: Literal["idle", "running", "partial", "completed", "failed"] = "idle"
```

**IStateRepository**
```python
# core/repository.py
class IStateRepository(ABC):
    @abstractmethod
    async def save(self, user_id: str, state: GlobalState) -> None: ...
    @abstractmethod
    async def load(self, user_id: str) -> GlobalState | None: ...
    @abstractmethod
    async def list_user_pipelines(self, user_id: str) -> list[str]: ...

class InMemoryRepository(IStateRepository):
    """默认实现；进程重启即丢失"""
    _store: dict[str, GlobalState]

class JsonFileRepository(IStateRepository):
    """本地文件持久化到 data/{user_id}.json；骨架阶段可选"""
```

**BaseLLMClient**
```python
# llm/base.py
class LLMResponse(BaseModel):
    content: str
    tokens_used: int
    model: str

class BaseLLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], *, budget: int) -> LLMResponse: ...
    @abstractmethod
    def count_tokens(self, text: str) -> int: ...

class OpenAICompatClient(BaseLLMClient):
    """走 OpenAI 兼容协议：OpenAI / DeepSeek / Moonshot / 自部署 vLLM"""
```

### 4.3 契约校验算法
```python
# core/validator.py
def validate_pipeline(
    active_pipeline: list[str],
    registry: AgentRegistry,
    bootstrap_fields: set[str] = None,
) -> ValidationResult:
    """PRD §4.1 算法；纯函数，便于前端 TS 镜像"""
    bootstrap = bootstrap_fields or {"user_id", "user_background"}
    provided = set(bootstrap)
    steps: list[StepValidation] = []

    for idx, agent_id in enumerate(active_pipeline):
        contract = registry.get_contract(agent_id)
        missing = contract.required_fields - provided
        steps.append(StepValidation(
            step=idx, agent_id=agent_id,
            required=contract.required_fields,
            provided_at_step=set(provided),
            missing=missing,
            ok=len(missing) == 0,
        ))
        if missing:
            return ValidationResult(valid=False, failed_at=idx, steps=steps)
        provided |= contract.output_fields

    return ValidationResult(valid=True, steps=steps)
```

### 4.4 依赖关系（无环）
- `core/*` 不依赖 `plugins/*` 或 `api/*`
- `plugins/*` 只能依赖 `core/contract.py` 和 `llm/base.py`
- `api/*` 编排 `core/*` 和 `plugins/*`
- 插件作者 import path：`from phd_agent.plugins._base import BaseAgent`

---

## 5. 前端设计

### 5.1 目录组织
```
frontend/
├── package.json                # Vite + React 18 + TS + React Flow
├── tsconfig.json
├── vite.config.ts
├── index.html
├── README.md
└── src/
    ├── main.tsx
    ├── App.tsx                 # 顶层布局：左 Shelf / 中 Canvas / 右 Workspace
    │
    ├── api/
    │   ├── client.ts           # fetch 封装
    │   └── types.ts            # 后端 schema 镜像
    │
    ├── validator/              # 客户端契约校验
    │   ├── contract.ts
    │   ├── validate.ts         # 后端算法的 TS 镜像
    │   └── validate.test.ts
    │
    ├── shelf/
    │   ├── AgentShelf.tsx
    │   └── AgentCard.tsx
    │
    ├── canvas/
    │   ├── FlowCanvas.tsx
    │   ├── nodes/AgentNode.tsx
    │   ├── edges/DependencyEdge.tsx
    │   └── usePipelineValidation.ts
    │
    └── workspace/
        ├── WorkspaceRoot.tsx
        └── widgets/
            ├── PipelineRunLog.tsx
            ├── AgentCatalogInfo.tsx
            └── MockWidget.tsx
```

### 5.2 关键交互流

**启动**
```
App 挂载
  → GET /agents/catalog
  → 缓存到 React Query / Zustand
  → <AgentShelf> 渲染所有 Agent 卡片
  → <FlowCanvas> 渲染空画布
```

**拖拽（实时校验）**
```
拖入卡片
  → onNodesChange/onEdgesChange
  → usePipelineValidation 节流(100ms) 后跑 validatePipeline()
       result.missing → 红线 + 红框
       result.ready   → 绿线
```

**运行**
```
点击 Run
  → POST /pipelines/validate          (后端再校验一次)
  → POST /pipelines/run               → { run_id }
  → GET  /pipelines/{run_id}/events   (SSE)
  → <PipelineRunLog> 实时追加
  → <WorkspaceRoot> 收到 activated_agents 列表
       → 动态挂载对应 widget
```

### 5.3 动态挂载机制
```typescript
// workspace/WorkspaceRoot.tsx
const widgetMap: Record<string, ComponentType<any>> = {
  mock_echo: MockWidget,
  mock_logger: MockWidget,
  // pubmed_scout: PubMedWidget,   // Phase 2+
  // csc_matcher: CscWidget,        // Phase 2+
};

export function WorkspaceRoot({ activatedAgents, runResult }) {
  return activatedAgents
    .map(id => {
      const W = widgetMap[id];
      return W ? <W key={id} data={runResult} /> : null;
    });
}
```

### 5.4 前后端类型同步
- 后端 Pydantic schema 是 single source of truth
- 前端手写镜像类型（避免引入 OpenAPI codegen）
- schema 变更时由 PR review 同步；骨架阶段可接受

---

## 6. 核心数据流（端到端时序）

### 6.1 场景：用户拖出 `mock_echo → mock_logger`，点击"运行"

| 时刻 | 浏览器侧 | 后端侧 |
| --- | --- | --- |
| t=0 | 拖拽两个卡片到画布 | — |
| t=0+ε | `usePipelineValidation` 跑 TS 版 `validatePipeline()` 返回 `{ready:true}` | — |
| t=100ms | 绿线渲染 | — |
| t=200ms | 点 [Run] 按钮 | — |
| t=205ms | `POST /pipelines/validate` | Validator 跑后端版 `validate_pipeline()` → 200 OK |
| t=210ms | `POST /pipelines/run` | Orchestrator 创建 GlobalState，存 Repository |
| t=211ms | — | CentralRouter 读 step=0 → 返回 `"mock_echo"` |
| t=212ms | — | AgentWrapper 懒加载 `MockEchoAgent`，执行 |
| t=224ms | — | step += 1，回流 Router |
| t=225ms | — | Router 读 step=1 → 返回 `"mock_logger"` |
| t=226ms | — | Wrapper 执行 mock_logger |
| t=234ms | — | step=2，越界 → END |
| t=235ms | SSE 事件 `step=0/1/END` 流式到达 | — |
| t=236ms | `<PipelineRunLog>` 显示每步日志 | — |
| t=237ms | `<WorkspaceRoot>` 挂载 `MockWidget × 2` | — |

### 6.2 关键状态转换
| 时刻 | current_step | dynamic_storage 关键字段 |
| --- | --- | --- |
| 启动 | 0 | `{}` |
| mock_echo 完成 | 1 | `{echo_output: "..."}` |
| mock_logger 完成 | 2 (越界) | `{echo_output, log: "..."}` |
| Router END | — | 终态 |

### 6.3 异常路径（PRD §6 沙盒化）
```
mock_logger.run() 抛 PubmedAPIError
  → AgentWrapper 捕获
  → state.error_log.append({step, agent, error})
  → 该节点 output_fields 不写入 state
  → current_step += 1   (继续)
  → PipelineRunLog 显示: "⚠ mock_logger skipped: timeout"
  → HTTP 响应 status="partial"
```
**不变量**：单个插件崩溃，pipeline 不会中断，全局状态机不崩溃。

---

## 7. 插件契约规范（给插件作者的指南）

### 7.1 一个完整插件示例（mock_echo）
```python
# backend/src/phd_agent/plugins/mock_echo/agent.py
from phd_agent.plugins._base import BaseAgent
from phd_agent.core.contract import AgentContract
from phd_agent.core.state import GlobalState

CONTRACT = AgentContract(
    agent_id="mock_echo",
    name="Mock Echo",
    description="原样回显 dynamic_storage.echo_input",
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

`mock_logger` 契约（用于端到端串联演示）：
```python
CONTRACT = AgentContract(
    agent_id="mock_logger",
    name="Mock Logger",
    description="把上游 echo_output 追加到 dynamic_storage.run_log",
    category="mock",
    required_fields={"dynamic_storage.echo_output"},
    output_fields={"dynamic_storage.run_log"},
    token_budget=0,
)
```

### 7.2 编写约束
1. 必须继承 `BaseAgent`，声明 `contract` ClassVar
2. 必须实现 `async def run(state) -> state`
3. **不要**捕获自己的异常 —— 让 wrapper 统一处理
4. **不要**直接 import 其他插件 —— 通过 state 通信
5. **不要**持有长生命周期对象（DB 连接等），通过 `state.dynamic_storage` 共享
6. 私有数据全部进 `dynamic_storage`，避免污染核心字段

### 7.3 加载机制
```python
# core/registry.py
class AgentRegistry:
    def __init__(self, plugins_dir: Path):
        self._contracts: dict[str, AgentContract] = {}
        self._classes: dict[str, type[BaseAgent]] = {}
        self._scan(plugins_dir)              # 启动时只扫元数据

    def _scan(self, plugins_dir: Path) -> None:
        """扫描每个 plugin 目录的 contract.json；不实例化"""
        for plugin_dir in plugins_dir.iterdir():
            contract = AgentContract.model_validate_json(
                (plugin_dir / "contract.json").read_text()
            )
            self._contracts[contract.agent_id] = contract

    def get_contract(self, agent_id: str) -> AgentContract: ...

    def load(self, agent_id: str) -> BaseAgent:
        """懒加载：首次调用时 importlib 加载具体类"""
        if agent_id not in self._classes:
            module_path = f"phd_agent.plugins.{agent_id}.agent"
            module = importlib.import_module(module_path)
            cls = next(
                v for v in vars(module).values()
                if isinstance(v, type) and issubclass(v, BaseAgent)
                and v is not BaseAgent
            )
            self._classes[agent_id] = cls
        return self._classes[agent_id]()
```

---

## 8. HTTP API 契约

| Method | Path | 用途 | Request | Response |
| --- | --- | --- | --- | --- |
| GET | `/agents/catalog` | 获取所有可用 Agent 契约 | — | `{agents: [AgentContract]}` |
| POST | `/pipelines/validate` | 服务端二次校验 | `{user_id, active_pipeline}` | `{valid, failed_at?, steps}` |
| POST | `/pipelines/run` | 启动 pipeline | `{user_id, active_pipeline}` | `{run_id, status: "running"}` |
| GET | `/pipelines/{run_id}/events` | SSE 流式日志 | — | `event: step=0 ...` |
| GET | `/pipelines/{run_id}` | 查 pipeline 最终态 | — | `{run_id, status, final_state}` |
| GET | `/health` | 健康检查 | — | `{ok: true}` |

错误响应统一格式：`{error: {code, message, details?}}`

---

## 9. 骨架阶段交付清单

### 9.1 必须实现 ✅
- [x] 后端 FastAPI 启动 + 健康检查
- [x] `core/*` 全部模块（state/repository/registry/contract/validator/router/wrapper）
- [x] `api/agents.py` + `api/pipelines.py`
- [x] `llm/base.py` + `llm/openai_compat.py` + `llm/budget.py`（实现完整，调用留 mock）
- [x] 2 个 mock 插件（`mock_echo`、`mock_logger`）
- [x] pytest 单元测试（validator/router/wrapper）
- [x] 前端 Vite + React + TS 启动
- [x] `App.tsx` 三栏布局
- [x] `validator/validate.ts` 与后端算法行为一致
- [x] `canvas/FlowCanvas.tsx` 拖拽 + 绿/红线渲染
- [x] `shelf/AgentShelf.tsx` 卡片展示
- [x] `workspace/PipelineRunLog.tsx` + `MockWidget.tsx`
- [x] 端到端 demo：拖两张卡 → 绿线 → Run → 看日志 → 看 widget

### 9.2 留接口不实现（stub）⚠
- [ ] 真实 PubMed / arXiv API 接入（仅定义接口）
- [ ] 真实 LLM 调用（`OpenAICompatClient.chat` 返回 mock 字符串）
- [ ] 多用户鉴权
- [ ] SQLite / Redis 持久化（仅留 `IStateRepository` 接口）
- [ ] Diff View / PubMed 看板等复杂 widget
- [ ] 插件市场 / 热加载 / 版本管理

### 9.3 不在本阶段 ❌
- 性能调优
- 部署 / CI / Docker
- 国际化

---

## 10. 验收标准（Definition of Done）

骨架阶段完成的判定：

1. **后端**
   - `uvicorn phd_agent.main:app` 启动成功
   - `curl /health` 返回 `{ok: true}`
   - `curl /agents/catalog` 返回 ≥ 2 个 Agent
   - `pytest tests/` 全部通过（覆盖率 ≥ 70% on `core/`）
   - `POST /pipelines/run` 跑完 `mock_echo → mock_logger` 后 `GET /pipelines/{id}` 返回 `status=completed`

2. **前端**
   - `npm run dev` 启动，浏览器可访问
   - 左侧看到 ≥ 2 张 Agent 卡片
   - 拖两张卡到画布 → 出现绿线
   - 点击 Run → 右侧出现 2 条日志 + 2 个 widget
   - 控制台无报错

3. **架构**
   - 所有 PRD 中提到的子系统都有对应的目录 / 文件
   - 前后端契约校验算法行为一致（同一份测试用例）

---

## 11. 测试策略

### 11.1 后端（pytest）
- `test_validator.py`：validate_pipeline 算法的所有边界（缺字段、闭环、孤立字段）
- `test_router.py`：current_step 越界、单步、跳过
- `test_wrapper.py`：异常捕获、Token 超预算截断
- `test_pipeline_e2e.py`：用 TestClient 跑完整 `/pipelines/run`

### 11.2 前端（Vitest）
- `validate.test.ts`：与后端 `test_validator.py` 用同一份测试 fixture（确保行为一致）

### 11.3 共享测试夹具
- 在 `docs/superpowers/specs/fixtures/pipelines.json` 维护：
  - happy_path：`mock_echo → mock_logger`
  - missing_field：`mock_logger` 无前置
  - chain_ok：`a → b → c` 链式

---

## 12. 错误处理策略

| 错误类型 | 处理位置 | 用户感知 |
| --- | --- | --- |
| Agent 业务异常 | `AgentWrapper` try/except | 节点 SKIPPED，pipeline 继续 |
| 插件加载失败（import 错） | `Registry.load` try/except | 节点标 FAILED，pipeline 继续 |
| Token 超预算 | `LLMBudget.check` | 截断输入 + warn log |
| 契约校验失败 | `Validator` 抛 ValidationError | 422，前端高亮缺字段 |
| State 损坏 | `Pydantic` ValidationError | 500，error_log 记录 |
| SSE 连接断开 | 前端 EventSource 自动重连 | 短暂显示"reconnecting" |

**核心原则**：任何错误都不得导致全局状态机崩溃（PRD §6）。

---

## 13. 后续 Phase 路线图

| Phase | 名称 | 关键交付 |
| --- | --- | --- |
| 2 | 真实插件 | `pubmed_scout` 接 PubMed API、`jargon_polisher` 接真实 LLM |
| 3 | 完整前端 | PubMed 看板、Diff View、CSC 图表 widget |
| 4 | 多用户 | SQLite 持久化、简单 session 鉴权 |
| 5 | 插件市场 | 外部插件上传、热加载、版本管理、灰度 |
| 6 | 生产化 | Docker、CI、监控、文档站 |

每个 Phase 独立 spec → plan → 实现。

---

## 14. 开放问题（待 Phase 1 之后决策）

1. **前端状态管理**：用 Zustand、Redux Toolkit 还是 React Query only？
   - 骨架阶段先用 React useState + Context，Phase 2 评估
2. **CORS 策略**：开发期 `allow_origins=["*"]`，生产期收敛？
   - 骨架阶段先放开
3. **错误日志聚合**：要不要接 Sentry？
   - Phase 4+ 考虑
4. **i18n**：PRD 没提国际化，骨架不实现

---

## 附录 A：术语表

| 术语 | 含义 |
| --- | --- |
| Agent | 可插拔的业务能力单元 |
| AgentContract | Agent 的输入/输出契约声明 |
| GlobalState | 全局唯一状态对象 |
| CentralRouter | 调度器，按 current_step 分发下一个 Agent |
| AgentWrapper | 统一执行壳：懒加载 + 异常隔离 + Token 截断 |
| IStateRepository | 状态持久化抽象接口 |
| BaseLLMClient | LLM 调用抽象接口 |
| dynamic_storage | GlobalState 中的插件私有数据沙盒 |
| validate_pipeline | 契约校验算法，纯函数 |
| active_pipeline | 用户在前端组装的 Agent 顺序列表 |

## 附录 B：文件和代码约束

为保证"isolation and clarity"，建议：
- 单个 Python 文件不超过 250 行
- 单个 TSX/TS 文件不超过 200 行
- 超过即拆分, 一旦预计新代码会导致文件超限，必须在编写前直接拆分，严禁事后重构

超出时优先拆分的信号：
- 多个 import 块服务于不同子领域
- 类/函数前缀高度重复
- 单元测试无法聚焦于单文件

拆分信号与优先级
- 当文件逼近上限时，必须按以下优先级和信号进行物理拆分，严禁将所有逻辑塞在单个文件中：
- 领域分流：若发现多个 import 块服务于不同的业务子领域，优先按领域拆分。
- 命名空间聚合：若类或函数前缀高度重复（例如 user_auth、user_profile），说明其本应属于独立模块，立刻提取。
- 职责内聚：
    TSX/TS：将独立的 UI 子组件、纯工具函数（Utils）、自定义 Hooks（useHooks）或常量定义（Constants）强制抽离到独立文件。
    Python：将数据模型（Models）、核心业务逻辑（Services）与辅助工具（Utils）彻底分离。
- 试聚焦：如果单个文件的单元测试由于依赖过多而无法聚焦，说明该文件必须拆分。

严禁过度设计
- 拒绝冗长 Fallback：除非业务明确要求，否则不要添加多层嵌套的 try-catch 或保守的兜底逻辑。允许让错误在合适的地方抛出。
- 保持代码精简：多使用现代语法特性，避免为了凑行数而写出繁琐的条件判断。
- 禁止“过度防御”：不要生成无意义的类型断言或重复的日志记录。
