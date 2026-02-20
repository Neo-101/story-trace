# StoryTrace Phase 7: 按需处理与交互优化 (Interactive & Incremental Processing)

## 1. 核心目标 (Core Objectives)
*   **按需处理 (On-Demand Processing)**: 允许用户指定处理的小说章节范围（如 "1-10", "50-100"），而非强制全量处理。
*   **增量缓存复用 (Incremental Caching)**: 利用现有的 `CacheManager` (Level 2)，确保已处理过的章节（无论是在哪次运行中）都能被自动复用，零 Token 消耗。
*   **交互优化 (UX Improvement)**: 在 CLI 启动时提供友好的章节预览和选择界面。

## 2. 交互设计 (Interaction Design)

### CLI 启动流程
1.  **输入文件**: 用户输入小说路径。
2.  **预扫描 (Pre-scan)**: 系统快速扫描文件，识别章节结构。
    *   *输出示例*: `检测到共 1250 章。范围: 第1章 - 第1250章。`
    *   *检查*: 自动检测章节号连续性，如有缺失或乱序则警告。
3.  **范围选择**: 提示用户输入。
    *   支持格式:
        *   `N` (默认): 处理前 N 章（如 `10` -> 1-10）。
        *   `start-end`: 处理区间（如 `50-100`）。
        *   `all`: 处理所有章节。
4.  **执行处理**:
    *   **Splitter**: 仅提取指定范围的文本。
    *   **Summarizer**:
        *   对于每个章节，先检查 `output/.cache`。
        *   **Hit**: 读取缓存，显示 "✅ [Cache] 第X章"。
        *   **Miss**: 调用 LLM，显示 "🔄 [LLM] 第X章"，并写入缓存。
5.  **结果生成**:
    *   生成本次运行的 `summaries.jsonl` (仅包含选定章节)。
    *   Web UI 可视化该次运行结果。

## 3. 技术方案 (Technical Implementation)

### 3.1 预扫描与分割 (Splitter Upgrade)
修改 `core/splitter/processor.py`:
*   新增 `scan_chapters(file_path)` 方法：
    *   只读不写，使用正则快速匹配所有章节标题。
    *   返回 `(total_count, chapter_list, is_continuous)`。
*   修改 `split(..., chapter_range=(start, end))` 方法：
    *   增加 `chapter_range` 参数。
    *   在生成 `Chapter` 对象列表时，过滤掉不在范围内的章节。

### 3.2 缓存策略 (Caching Strategy)
*   **Level 2 Cache (`core/cache_manager.py`)**: 
    *   保持现状。其基于 `Content_Hash + Prompt_Hash` 的机制天然支持跨运行复用。
    *   确保缓存目录是全局共享的 (`output/.cache`)，而非运行私有。

### 3.3 主程序逻辑 (Main Loop)
修改 `app/main.py`:
*   在 `get_user_input` 中集成 `scan_chapters`。
*   解析用户输入的范围字符串。
*   将范围传递给 `Splitter`。

## 4. 开发计划 (Development Plan)

*   **Phase 7.1 [Current]**: 实现 `scan_chapters` 和 CLI 交互逻辑。
*   **Phase 7.2**: 修改 `Splitter.split` 支持范围过滤。
*   **Phase 7.3**: 集成到 `main.py` 并测试增量缓存效果。

## 6. 开发日志与问题排查 (Development Log & Troubleshooting)

### 7.1 CLI 交互模式下的静默退出问题 (2026-02-19)
**问题现象**:
1.  用户运行 `python main.py` 进入交互模式。
2.  成功扫描到章节 (644章)，选择了范围 (1-10)。
3.  开启了 AI 总结，配置了 OpenRouter。
4.  程序在最后一步输入 `Y` 确认使用环境变量 Key 后，直接退出，没有任何输出，也没有生成 output 文件夹。

**排查分析**:
1.  **编码问题已排除**: 程序明确显示 "成功使用编码读取文件: gbk"，说明 `Splitter.read_file` 工作正常且编码已正确传递。
2.  **流程中断点**:
    *   根据日志，程序在 `get_user_input` 返回后，进入 `main` 函数。
    *   打印了 "开始处理..." 和 "模式: chapter"。
    *   打印了 "输出目录 (绝对路径): ..."。
    *   打印了 "正在读取文件..." 和 "正在分割章节..."。
    *   **关键点**: 没有打印 "成功分割出 X 章"。
    *   这意味着 `splitter.split_by_chapter` 返回了空列表 `[]`。

**根本原因 (怀疑)**:
*   `scan_chapters` 和 `split_by_chapter` 使用的正则表达式虽然相同，但上下文环境可能不同。
*   或者 `chapter_range_filter` 的逻辑导致过滤结果为空。用户输入 "10" -> `parse_range` 返回 `(1, 10)` -> `split_by_chapter` 转换索引 `start=0, end=10`。这应该是正确的。
*   **最可能的嫌疑**: `Splitter` 类的实例化方式。
    *   在 `main.py` 中：`splitter = Splitter(encoding=encoding)`。
    *   虽然 `encoding` 变量被更新为 'gbk'，但在 `split_by_chapter` 内部，正则表达式匹配是否受编码影响？(Python 字符串是 Unicode，不应受影响)。
    *   **文件读取的一致性**: `scan_chapters` 使用的是 `content` (已读取的字符串)。`split_by_chapter` 在 `main` 中也是接收 `content`。
    *   **正则表达式**: `fr'(?:^第[{cn_nums}\d]+[章回節节])|(?:^Chapter\s+\d+)'`。
    *   如果 `scan_chapters` 能匹配到 644 章，说明正则没问题。

**待验证假设**:
*   `main.py` 中的 `splitter.read_file(input_file)` 是否真的返回了正确的内容？虽然打印了 "成功使用编码: gbk"，但内容是否完整？
*   **BUG**: 在 `main.py` 中，`get_user_input` 返回的 `input_file` 路径字符串可能带有隐藏字符？(已处理 `strip`).
*   **CRITICAL**: `get_user_input` 返回字典，`main` 函数中解包。
    *   `encoding` 变量在 `main` 函数作用域中是否被正确更新？
    *   在 `get_user_input` 内部，`encoding` 变量被更新了。
    *   但是 `return { ..., 'encoding': encoding, ... }` 返回的是更新后的吗？是的，Python 闭包/作用域规则。
    *   在 `main` 中：`encoding = args_dict['encoding']`。
    *   然后 `splitter = Splitter(encoding=encoding)`。
    *   这看起来是正确的。

**下一步行动 (Next Actions)**:
1.  **增加调试日志**: 在 `split_by_chapter` 内部打印 `matches` 的数量，确认正则是否匹配到了内容。
2.  **检查范围过滤逻辑**: 打印 `start_idx` 和 `end_idx`，确认是否因索引计算错误导致切片为空。
3.  **持久化调试**: 如果控制台输出闪退，考虑将日志写入文件。

### 7.2 图谱数据空白问题 (2026-02-20)
**问题现象**:
*   Web UI 中，"概览"、"专注"、"百科" 等功能均正常，显示数据无误。
*   "全书关系图谱" (Graph) 页面显示正常框架，时间轴可拖动且章节名正确（如 "第10章雪"）。
*   **异常点**: 画布一片空白，左下角显示 "节点数量: 0, 关系数量: 0"。

**排查分析 (2026-02-20 Update)**:
1.  **后端正常**: 增加了调试日志，确认后端成功加载了 10 个章节，并聚合了 55 条关系。
2.  **前端数据接收正常**: 通过 Debug Overlay 确认前端接收到了 `Edges: 55` 和 `Chapters: 10`。
3.  **过滤器逻辑正常**: 模拟的过滤器逻辑显示 `Condition: 4 <= 9` 为真，说明数据应该被显示。
4.  **渲染异常**: 尽管数据和逻辑看似正常，Vis.js 仍然显示 0 节点/0 关系。
5.  **怀疑方向**: 
    *   Vis.js 初始化时机问题（容器高度为0？）。
    *   `graphNetwork` 实例状态问题。
    *   `activeNodeIds` 计算逻辑在实际运行环境中的细微差异。

**决策**: 暂时搁置具体的 Bug 修复，转向架构层面的优化，以提高项目的可维护性和 LLM 辅助开发的效率。

### 7.3 前端模块化重构 (2026-02-20)
**目标**: 解决 `index.html` 代码量过大 (1000+ 行) 导致的 LLM 上下文消耗过高和调试困难问题。
**执行**:
1.  **目录结构**: 创建 `web_ui/static/js/`。
2.  **拆分逻辑**:
    *   `api.js`: 封装所有 `fetch` 请求。
    *   `graph.js`: 封装 Vis.js 的图谱初始化、更新、过滤逻辑。
    *   `app.js`: Vue 3 的 Composition API 逻辑，作为主入口。
3.  **修改入口**: `index.html` 移除内联脚本，改为 `<script type="module" src="/static/js/app.js"></script>`。
4.  **状态**: 重构完成，服务已重启。待人工验证。

### 7.4 后端模块化重构 (2026-02-20)
**目标**: 将 `server.py` 拆分为 `routers`, `schemas`, `utils`，进一步降低单文件代码量。
**执行**:
1.  **目录结构**: 创建 `web_ui/routers/`。
2.  **文件拆分**:
    *   `web_ui/schemas.py`: Pydantic 数据模型。
    *   `web_ui/utils.py`: 路径计算和文件解析工具。
    *   `web_ui/routers/novels.py`: 小说/版本列表接口。
    *   `web_ui/routers/analysis.py`: 章节/图谱/实体分析接口。
3.  **修复**: 修正了 `utils.py` 中 `OUTPUT_DIR` 指向父目录的 Bug。
4.  **状态**: 服务运行正常。

### 7.5 Graph Blank Issue 排查 (2026-02-20)
**现象**: 图谱页面节点和边数量显示为 0，画布空白。
**排查过程**:
1.  **Test Harness**: 创建 `tests/repro_graph_logic.py`，模拟后端聚合逻辑。
    *   **结果**: 后端逻辑完全正常，生成 55 条边，且 ID (`ch_1`) 与 Summaries 中的 ID 一致。
    *   **结论**: 排除后端数据问题。
2.  **Frontend Debug**:
    *   在网页上运行 Debug Check，显示 Filter 逻辑计算结果为 True (`Condition: 4 <= 9 ?`)。
    *   这证明前端接收到了数据，且逻辑判断认为应该显示。
    *   **根本原因锁定**: `GraphController` 在将数据添加到 `vis.DataSet` 时失败，或者 `vis` 实例未正确初始化。
    *   *Fix Attempt 1*: 修复 `const vis = window.vis` 引用问题。 (未解决)

## 8. 架构优化建议 (Architecture Optimization for LLM-IDE)

为了解决“随着项目规模扩大，调试困难且 Context 消耗巨大”的问题，建议采取以下策略：

### 8.1 模块化拆分 (Modularization)
*   **前端**: 将 900+ 行的 `index.html` 拆分为独立的 Vue 组件或 JS 模块。
    *   `components/GraphView.js`: 专注图谱逻辑。
    *   `components/SummaryView.js`: 专注文本阅读。
    *   `utils/api.js`: 统一 API 调用。
*   **后端**: 
    *   将 `main.py` 拆分为 `cli_interface.py` (交互) 和 `core_logic.py` (业务)。
    *   将 `server.py` 的路由拆分为 `routers/novel.py`, `routers/graph.py`。

### 8.2 上下文友好的测试桩 (Context-Friendly Test Harness)
*   创建**独立的小型测试脚本** (如 `tests/repro_graph_logic.py`)，仅加载必要的模块（如 `EntityAggregator`），而不依赖整个 Web 框架。
*   这样 LLM 只需要读取 50 行的测试脚本和 100 行的核心逻辑代码，即可复现和修复 Bug，而无需读取整个项目文件。

### 8.3 接口契约文档 (Strict Interface Contracts)
*   维护一份轻量级的 `api_schema.md`，明确输入输出格式。
*   LLM 只需要知道“输入是 A，期望输出是 B”，而不需要知道具体的实现细节。

### 8.4 上下文锚点 (Context Anchors)
*   建立 `context_map.md`，记录每个功能模块涉及的关键文件路径。
*   在提问时，仅向 LLM 提供相关的锚点文件。

## 5. 预期效果
*   用户指定 "1-10" -> 消耗 10 章 Token。
*   用户再次指定 "1-15" -> **只消耗 5 章 Token** (11-15)，前 10 章秒级完成。
