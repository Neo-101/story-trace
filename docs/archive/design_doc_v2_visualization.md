# StoryTrace 可视化系统设计文档 (v2.0)

## 1. 概述 (Overview)

为了实现“点击总结跳转原文”且不打断心流的深度阅读体验，本项目将从纯命令行工具升级为 **B/S 架构 (Browser/Server)** 的本地应用。

### 核心目标
*   **双向溯源 (Bidirectional Tracing)**: 点击总结高亮原文，滚动原文联动总结。
*   **沉浸式体验 (Immersive Experience)**: 左右分栏布局，避免弹窗打断。
*   **未来扩展性 (Future Proofing)**: 为后续的“世界观图谱”和“实体关系图”预留前端渲染能力。

## 2. 交互设计 (Interaction Design)

### 2.1 界面布局 (Layout)
*   **左侧 (30% - 40%, 可拖拽)**：**智能总结区 (Intelligence Layer)**
    *   展示结构化总结卡片。
    *   交互：点击句子触发右侧滚动和高亮。
*   **右侧 (60% - 70%)**：**原文阅读区 (Source Layer)**
    *   展示完整章节内容。
    *   交互：平滑滚动，支持关键词高亮。

### 2.2 交互流程
1.  用户点击左侧总结句。
2.  前端获取该句的 `source_spans` (start_index, end_index)。
3.  右侧原文视图自动滚动至目标位置 (ScrollTo)。
4.  目标文本背景色渐变高亮 (Highlight)。

## 3. 技术架构 (Technical Architecture)

### 3.1 模块划分
新增 `web_ui` 顶层模块，与 `core` 并列。

```text
story-trace/
├── core/               # 核心业务逻辑
│   ├── summarizer/     # [重点] 需升级溯源算法
│   └── ...
├── web_ui/             # [NEW] 可视化子系统
│   ├── server.py       # FastAPI 后端
│   ├── static/         # 前端静态资源
│   └── templates/      # HTML 模板
├── app/
│   └── main.py         # CLI 入口 (新增 `serve` 命令)
└── output/             # 数据存储 (JSON/TXT)
```

### 3.2 技术栈 (Tech Stack)
*   **后端**: **FastAPI** (高性能，异步，易于扩展)。
*   **前端**: **Vue 3** + **Tailwind CSS** (响应式联动，快速开发)。
*   **数据层**: 复用现有的 `output` 目录结构 (JSON 文件作为简易数据库)。

## 4. 关键算法升级：原文溯源 (Source Mapping)

目前的 `_find_source_spans` 是占位符，必须重构以支持精准定位。

### 4.1 算法选型：加权模糊匹配 (Weighted Fuzzy Matching)
鉴于 LLM 总结可能概括或改写原文，直接字符串匹配 (Exact Match) 成功率极低。
我们采用 **基于关键词密度的滑动窗口算法**：

1.  **预处理**: 对总结句进行分词，提取关键词 (去除停用词)。
2.  **滑动窗口**: 在原文上移动窗口 (窗口大小 ≈ 总结句长度 * 膨胀系数)。
3.  **打分**: 计算窗口内包含关键词的数量和权重。
4.  **定位**: 取分数最高的窗口作为 `source_span`。

*后期可升级为本地 Embedding 向量相似度匹配 (Semantic Similarity)。*

## 5. 开发路线图 (Roadmap)

### Phase 2.1: 数据层重构 (Data Layer Refactoring) [已完成]
- [x] 重写 `core/summarizer/generator.py` 中的 `_find_source_spans` 方法。
- [x] 实现基于关键词的模糊匹配算法。
- [x] 验证生成的 JSON 数据中包含正确的 `start_index` 和 `end_index`。

### Phase 2.2: 后端 API 开发 (Backend API) [已完成]
- [x] 引入 `FastAPI` 和 `uvicorn`。
- [x] 实现 `GET /api/books` (获取小说列表)。
- [x] 实现 `GET /api/books/{book_id}/chapters/{chapter_id}` (获取详情)。

### Phase 2.3: 前端开发 (Frontend) [已完成]
- [x] 搭建 Vue 3 基础页面。
- [x] 实现左右分栏和滚动联动逻辑。
