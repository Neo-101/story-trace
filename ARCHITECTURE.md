# ARCHITECTURE.md

## 1. 目录字典 (Directory Map)
```text
📦 StoryTrace
 ┣ 📂 app/                 # CLI 交互大门，负责接收用户终端指令并启动处理流程。
 ┣ 📂 backend/             # 后端 API 大门，接收前端 HTTP 请求并返回分析数据。
 ┃ ┣ 📂 routers/           # 具体接口路由（如返回小说列表、组装图谱和时间轴数据）。
 ┣ 📂 core/                # 核心业务大脑，处理所有重度计算与分析逻辑。
 ┃ ┣ 📂 db/                # 数据库定义，存放 SQLModel 表结构和 SQLite 连接。
 ┃ ┣ 📂 splitter/          # 文本切片机，用正则把整本 TXT 拆解为带编号的卷和章。
 ┃ ┣ 📂 summarizer/        # LLM 通信枢纽，发 Prompt 并解析 JSON（摘要/实体/关系）。
 ┃ ┗ 📂 world_builder/     # 数据融合器，将各章零散的实体和互动聚合成全局“世界网”。
 ┣ 📂 data_protocol/       # 跨模块数据契约，用 Pydantic 规范长什么样（防字段拼写错）。
 ┣ 📂 frontend/            # 前端展示大门，Vue3 项目，负责图谱渲染和沉浸式交互。
 ┗ 📜 storytrace.db        # 核心物理状态，存放所有已分析结构化数据的 SQLite 数据库。
```

## 2. 核心数据流转链 (Data Flow Chains)

**[🔥 核心 1：文档解析与大模型结构化 (CLI 批处理)]**
本地小说.txt -> `app/main.py` (分配任务) -> `core/splitter` (切成单章) -> `core/summarizer` (并发请求大模型抽取实体/关系，中途写 `.cache` 避免重复花费 Token) -> 保存为本地 JSON/JSONL 并入库 `storytrace.db`

**[🕸️ 核心 2：全局关系图谱生成 (Global Graph View)]**
前端 Graph 组件 -> API `GET /api/novels/.../graph` -> `backend/routers/analysis.py` -> 查 DB 获取所有合并章节 (`get_merged_chapters`) -> `core/world_builder/aggregator.py` (聚合去重，计算权重排序) -> 返回 `GraphData` JSON -> 前端交给 Vis.js 渲染节点与连线

**[⏳ 核心 3：实体/关系时间轴漫游 (Timeline Focus)]**
前端选中某个节点 -> API `GET /api/.../entity/{name}/timeline` -> `backend/routers/analysis.py` -> 检索该实体在各章的 `SummarySentence` 或 `Relationship` -> 计算章节跨度 Gap -> 返回 `TimelineEvent` 数组 -> 前端沿时间轴渲染动态交互卡片

**[🧠 核心 4：渐进式世界观分析 (Concept Evolution)]**
前端点击"深度分析" -> API `POST /api/novels/.../analyze/concept` -> `backend/routers/analysis.py` -> `ContextManager` 读取实体编年史 (Entity Chronicle) -> `ConceptAnalyzer` 组装 Prompt 调用 LLM -> 识别 Rumor/Fact/Truth 阶段 -> 更新 DB -> 前端刷新展示

## 3. 状态与依赖契约 (State & Dependency)

*   **唯一真实数据源 (Single Source of Truth):** 
    后端一律以 `storytrace.db` (SQLite) 为权威状态。所有复杂查询依赖 `core.db.models` 定义的关系表（`Novel`, `Chapter`, `Entity`, `StoryRelationship`）。
*   **多轮运行防冲突 (Best-Effort Merge 机制):** 
    同一本小说如果多次分析，状态不会覆盖。`backend.routers.analysis` 会动态拉取属于同一 `file_hash` 的所有 Runs，用最新生成的数据**按章节索引**覆盖旧数据，拼出一个完整版发给前端。
*   **大模型通信契约 (LLM I/O Contract):** 
    大模型必须返回并只返回 JSON。格式由 `core/summarizer/prompts.py` 强制约束，必须包含 `headline`、`summary_sentences`、`entities` (带类型) 和 `relationships` (源/动作/目标 三元组)。
*   **前端状态共享契约 (Vue/Pinia State):** 
    全局阅读进度、选中的书目信息 (`file_hash`, `timestamp`) 及当前聚焦的实体/节点，由 Pinia Store (如 `novelStore`) 统一保管。图谱组件 (Vis.js) 与右侧边栏组件只负责订阅 Store 变化并渲染，不直接跨组件传参。