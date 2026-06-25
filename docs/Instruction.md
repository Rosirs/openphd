PhD-Agent 可插拔智能体系统工作原理详解

本手册旨在深度拆解 PhD-Agent (V2.0.0) 系统的底层运转逻辑。通过本手册，你将了解一个用户自定义的“积木式”工作流，是如何在后端完成安全校验、动态装配并高效执行的。

一、 系统整体架构蓝图 (System Architecture)

PhD-Agent 采用的是 基于共享状态的可插拔多智能体架构。系统不设硬编码的工作流，所有业务能力均被封装为独立的智能体（Agent）插件，通过“中转路由”进行调度。

在整个架构中，三大核心组件协同工作：

智能体注册表 (Agent Registry)：统一存放所有可用插件的元数据与执行体。

全局状态中心 (Global Graph State)：唯一的“数据源”，所有数据流转、数据消费均在此处进行。

中转路由器 (Central Router)：根据用户定制的执行链，动态分配下一阶段的控制权。

二、 数据枢纽：松紧结合的“全局状态” (Flexible State & Sandbox)

在多智能体系统中，最棘手的问题是 数据污染 —— 生物学 Agent 写入的数据如果破坏了计算机类 Agent 的输入，系统就会崩溃。

为此，我们设计了 “松紧结合” 的状态模型：

紧耦合（标准化核心字段）：存放所有 Agent 通用的高频数据（如 user_background，email_draft）。

松耦合（动态隔离沙盒 dynamic_storage）：各插拔 Agent 独有的非标准化数据，统统放入此沙盒，互不干扰。

数据流向示意

当执行 pubmed_scout 插件时：

从 GlobalState 读取标准字段 user_background。

调用 PubMed API 获取医学文献。

将文献摘要以 {"pubmed_papers": [...]} 形式写入 dynamic_storage 沙盒中，保持全局状态干净。

三、 第一道安全防线：契约化依赖校验 (Contract Validation)

当用户在前端 WebUI 自定义拖拽了一条工作流时，后端不会盲目执行，而是首先启动 静态契约校验算法。

3.1 核心数学原理

每个 Agent 必须声明其 输入契约（$Required$） 和 输出契约（$Output$）。
设 $ProvidedFields_{t}$ 为在第 $t$ 步时系统已提供的数据字段集。

状态迭代递推公式：


$$ProvidedFields_{t} = ProvidedFields_{t-1} \cup OutputFields_{t-1}$$

安全边界约束条件（关键）：
对于管道中的第 $t$ 个智能体，其输入契约 $Required_t$ 必须满足：


$$Required_t \subseteq ProvidedFields_{t}$$

如果该约束条件在任意一步 $t$ 不成立，系统将拒绝执行，并向前端抛出数据缺失警告。

3.2 校验流决策树

3.3 校验场景模拟

假设用户组装了这条流水线：jargon_polisher (黑话润色) $\rightarrow$ csc_matcher (CSC奖学金匹配)。

初始状态：provided_fields = {"user_id", "user_background"}。

第 1 步校验 (jargon_polisher)：

该插件需要：email_draft (输入契约)。

当前提供：provided_fields 并不包含 email_draft。

结果：$Required \not\subseteq Provided$，校验失败！前端立刻在“黑话润色”卡片前显示红色断线，并提示：“无法运行，因为您没有先放置套磁信撰写器！”

四、 核心控制中枢：动态中转路由 (Central Router & Loop)

一旦校验通过，系统将编译 DAG。为了避免静态路由的死板，我们采用 中转路由循环调度机制。

4.1 自动推进包装器 (Agent Wrapper)

具体的 Agent 业务代码不需要关心执行步骤。在动态加载时，系统会自动为其套上统一的 Wrapper。

Wrapper 伪代码工作流：

[ 激活 Wrapped Agent ]
          │
          ▼
   [ 执行业务逻辑 ] (如: 检索文献、生成文书)
          │
          ▼
   [ 更新 State ] (写入 dynamic_storage 或覆盖 email_draft)
          │
          ▼
[ 自动执行: current_step += 1 ] 
          │
          ▼
 [ 无条件回流至 Central Router ]


4.2 路由分发器工作逻辑 (Central Router Logic)

中转路由器就像机场的控制塔，每一次 Agent 执行完毕后，控制权都会收回到控制塔，由它指引下一架飞机：

If state.current_step >= Length(state.active_pipeline) Then
    Return "END" (全链路顺利结束，将控制权和文书推给前端)
Else
    Next_Agent_Id = state.active_pipeline[state.current_step]
    Return Next_Agent_Id (指引执行流，空降到下一个插拔 Agent 节点)


五、 前后端协同：拖拽画布与动态看板 (UI-Backend Co-Design)

这一套底层的可插拔逻辑，在前端 WebUI 被封装为极具科技感和人性化的两项设计：

5.1 连线依赖智能提醒 (Intelligent Connection)

由于后端会在拖拽过程中实时运行 validate_pipeline 算法，前端可以实现“实时红绿连线”：

绿线：表示数据链路完全闭合，处于 Ready 状态。

红线/断线：表示因前后节点配置不当，缺少数据依赖。用户可以点击红色警示图标，查看具体的字段缺失情况。

5.2 动态看板挂载 (Dynamic Widget Mounting)

系统在编译 DAG 时，会向前端发送当前工作流激活的插件列表（如 ["pubmed_scout"]）。前端渲染引擎根据这一列表，在右侧工作区动态挂载对应的可视化看板组件。

激活了生信插件 $\rightarrow$ 挂载“生信专属 PubMed 看板”。

激活了文书插件 $\rightarrow$ 挂载“文书高亮 Diff 对比看板”。
真正做到“因学科而变，随人定制”。