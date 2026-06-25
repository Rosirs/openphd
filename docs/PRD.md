产品需求文档 (PRD) - 博士申请多智能体助手 (PhD-Agent)

版本

日期

作者

状态

备注

V2.0.0

2026-06-25

PhD-Agent 创始团队

评审中 (In Review)

引入可插拔 Agent 架构与契约化依赖校验

1. 项目背景与愿景 (Project Background & Vision)

1.1 痛点分析

博士（PhD）申请具有极高的专业垂直度。不同学科（如计算机、生物医学、历史学）对于导师检索、文献阅读和文书撰写的关注点完全不同。传统的“一刀切”式 AI 助手无法同时满足各学科个性化的申请诉求：

学科壁垒高：CS 申请者强依赖 arXiv 预印本和 GitHub 仓库；生信/医学强依赖 PubMed 和临床数据；人文社科更偏向专著检索与复杂的学术长文风格。

阶段性差异大：早期需要海选导师（Scout），中期需要精准分析论文和套磁（Paper & Writing），后期需要模拟面试（Interview）和奖学金申请（CSC/Scholarship）。

1.2 产品定位与核心突破

PhD-Agent 是一款面向全球博士申请者的自研 可插拔多智能体（Pluggable Multi-Agent）系统。
本版本核心突破在于：不再提供固定的流水线，而是提供一个“Agent 货架（市场）”。用户可以像乐高积木一样，根据自己的专业（如生物、计算机）和阶段（如找导师、改文书），自由拖拽组装专属的申请流水线，并在现代化 WebUI 中进行可视化运行。

2. 核心用户与个性化场景 (User Personas & Pluggable Scenarios)

2.1 典型用户群

STEM 领域申请者：关注前沿顶会、arXiv 动态、工程背景（GitHub）包装。

生物/医学领域申请者：高度依赖 PubMed 检索、影响因子匹配，套磁信需强调实验技能（Wet/Dry Lab）。

社科人文领域申请者：强调写作逻辑、思想深度与专著引用。

2.2 用户自组装工作流场景（示例）

场景 A：计算机视觉方向（快速套磁流）
意图解析 $\rightarrow$ arXiv 检索器 $\rightarrow$ 学术黑话润色 $\rightarrow$ 套磁信生成 $\rightarrow$ 人工校验

场景 B：生物医学方向（深度分析流）
意图解析 $\rightarrow$ PubMed 检索器 $\rightarrow$ CSC 奖学金匹配 $\rightarrow$ 深度医学文书生成 $\rightarrow$ 人工校验

3. 系统架构与可插拔设计 (System Architecture & Pluggability)

系统基于有状态的动态 DAG 拓扑，核心编排架构引入了“契约声明”与“中转路由”机制。

3.1 契约化全局状态模型 (Flexible Global State)

系统状态（State）采用松散且安全的结构化字典设计，引入 dynamic_storage 字段作为各插拔 Agent 的数据隔离沙盒，避免数据互相覆盖。

Structure GlobalState:
    user_id: String               # 用户唯一标识
    user_background: Map          # 用户简历、科研背景、GPA 等
    active_pipeline: List[String] # 用户在前端组装的 Agent 顺序列表 (e.g., ["arxiv_scout", "jargon_polisher"])
    current_step: Integer         # 当前执行到 pipeline 的第几步 (从 0 开始)
    dynamic_storage: Map          # 插件沙盒：存放插拔 Agent 产生的非标准化临时数据 (e.g., {"pubmed_papers": [...]})


3.2 智能体注册中心与契约声明 (Agent Registry & Contract)

所有 Agent（无论是系统核心还是外部插件）都必须在注册中心进行“能力和依赖声明”：

输入契约（Required Fields）：声明该 Agent 执行前，State 中必须已存在的数据（如 email_draft）。

输出契约（Output Fields）：承诺执行完毕后，会写入或更新的 State 字段。

核心与插拔智能体角色注册表：

Agent ID

级别

核心职责

输入契约（Required）

输出契约（Outputs）

intent_parser

系统核心

1. 识别用户意图



2. 补充缺失槽位

raw_user_input

intent, is_ambiguous

arxiv_scout

学术插件

检索 arXiv 预印本仓库，抓取最新文献

user_background

dynamic_storage (arxiv_papers)

pubmed_scout

学术插件

检索 PubMed 数据库，匹配教授 PMID

user_background

dynamic_storage (pubmed_papers)

jargon_polisher

写作插件

将草稿重构为资深审稿人风格的学术黑话

email_draft

email_draft (覆盖更新)

csc_matcher

行政插件

评估国家留学基金委（CSC）公派项目契合度

user_background

dynamic_storage (csc_report)

4. 业务流程与核心控制逻辑 (Core Control Flows)

4.1 动态依赖校验算法 (Pipeline Validation)

在用户点击“运行”或在 WebUI 拖拽智能体卡片时，后端会自动执行依赖校验算法。只有当校验通过时，才允许启动 DAG。

校验公式：


$$ProvidedFields_{t} = ProvidedFields_{t-1} \cup OutputFields_{t-1}$$


对于管道中的第 $t$ 个智能体，其输入契约 $Required_t$ 必须满足：


$$Required_t \subseteq ProvidedFields_{t}$$

逻辑说明：

初始化 provided_fields 为基础状态（包含用户简历和背景）。

顺序遍历用户拖拽出的 active_pipeline。

检查当前 Agent 所需的 required_fields 是否是 provided_fields 的子集。若不是，立即向前端抛出异常，阻止运行，并高亮缺失字段。

校验通过后，将该 Agent 声明的 output_fields 并入 provided_fields，继续校验下一个。

4.2 动态中转路由机制 (Central Router Loop)

系统在编译 DAG 时，不配置硬编码的顺序边，而是通过一个中转路由器节点 (Central Router) 动态分发控制权。

                 [ 启动 DAG ]
                      │
                      ▼
             ┌──> [ 中转路由器 ] 
             │    (判断 current_step 是否越界?)
             │         │
             │         ├────────────── (越界) ──────────────┐
             │         │ (未越界)                           │
             │         ▼                                    ▼
             │   [ 动态跳转至: ]                                [ 流程结束 ]
             │   active_pipeline[current_step]               (END)
             │         │
             │         ▼
             └── [ 执行具体的 Agent ]
                 (自动执行 current_step += 1)


统一包装器 (Wrapper)：当动态加载一个 Agent 时，系统自动用包装器将其包裹。该包装器在 Agent 业务执行完毕后，会自动将 current_step 累加 1。

回流中转：每个可插拔 Agent 执行完后，无条件流向中转路由器，由路由器读取新的 current_step 指向下一个节点。

5. WebUI 交互设计需求 (WebUI Workspace Design)

为了支撑可插拔架构，前端交互从“单轴对话”升级为“工作流画布 + 动态面板”。

5.1 智能体货架与编排画布 (Agent Shelf & Canvas)

左侧：智能体货架（Agent Market）

分类展示所有可用的 Agent 插件卡片（如：医学检索、CSC匹配、黑话润色）。

悬停卡片时，展示该 Agent 的依赖条件（例如：“需要前置有：套磁信草稿”）。

中间：流式画布（Flow Canvas）

支持用户自由拖拽 Agent 卡片组合成链。

实时兼容性校验：如果用户先拖入了 学术黑话润色（需要套磁信草稿），但在其前面没有放置 套磁信撰写器，则两个卡片之间会显示一条带有警告符号的红色断线，并提示：“依赖未满足：黑话润色需要先生成套磁信草稿。”

5.2 动态数据工作空间 (Dynamic Workspace)

右侧：根据执行状态动态生成的看板

如果工作流中激活了 pubmed_scout，右侧自动出现“PubMed 文献精读看板”，展示检索到的文献详情与 PDF 摘要。

如果激活了 csc_matcher，右侧自动渲染出“CSC 申报可行性分析图表”。

统一保留文书版本对比（Diff View），展示 jargon_polisher 等写作插件修改前后的高亮对比。

6. 非功能性需求 (Non-Functional Requirements)

插件执行沙盒化 (Sandboxed Execution)：

插拔 Agent 执行时，其内部异常必须被捕获。即使某个插件由于 API 超时或网络爬虫被封锁而报错，也只能导致该节点输出为空（或者向用户弹出局部跳过提示），不得导致全局状态机和核心路由崩溃。

按需延迟加载 (Lazy Loading)：

后端插件采用动态导入（Dynamic Import）机制。只有当用户的工作流中确实包含了该 Agent 时，系统才加载对应的代码和权重，减少不必要的内存开销。

Token 隔离与成本预算 (Token Guardrail)：

每个可插拔 Agent 必须在配置中声明自己的 Token 预算上限。在调用大模型前，对输入上下文进行强制裁剪，防止不受控的插件产生巨额账单。