# StoryTrace 全书概览模式设计 (v4.0)

## 1. 背景与目标 (Background & Goals)
目前系统仅支持“单章专注模式”，侧边栏展示的是单章内的多条详细总结。用户缺乏一个宏观视角来快速浏览整本书的剧情脉络。
本阶段目标是引入 **全书概览模式 (Book Overview Mode)**，允许用户在侧边栏查看所有章节的“一句话总结”，并支持点击快速切换章节。

## 2. 交互设计 (Interaction Design)

### 2.1 视图切换 (View Switcher)
在 Web UI 顶部导航栏增加视图切换控件（Toggle/Tab）：
*   **📖 专注模式 (Focus Mode)**: 现有模式。侧边栏显示当前章节的 *多条* 详细总结。
*   **📚 概览模式 (Overview Mode)**: 新模式。侧边栏显示章节列表及每章的 *一条* 核心总结。

### 2.2 概览模式详情
*   **侧边栏 (Sidebar)**:
    *   展示当前卷（或全书）的所有章节卡片。
    *   **卡片内容**:
        *   章节标题 (e.g., "第1章 孙杰克")
        *   **核心总结 (Headline)**: 一句概括本章主旨的话 (e.g., "孙杰克在太空站醒来，发现自己失去了记忆。")
    *   **交互**:
        *   点击卡片：右侧原文区域立即加载该章节内容。
        *   侧边栏保持在“概览模式”，方便用户继续点击下一章。
        *   卡片上提供一个“进入精读”按钮，点击后切换回“专注模式”。

*   **主视图 (Main View)**:
    *   展示选中章节的原文（与专注模式一致，支持滚动）。

## 3. 数据层改造 (Data Layer Changes)

为了支持“一句话总结”，我们需要修改数据结构和 Prompt。

### 3.1 数据模型 (Models)
修改 `data_protocol/models.py` 中的 `ChapterSummary`：

```python
class ChapterSummary(BaseModel):
    chapter_id: str
    chapter_title: Optional[str]
    headline: str = Field(..., description="一句话核心总结")  # [NEW] 新增字段
    summary_sentences: List[SummarySentence]
    key_entities: List[str]
```

### 3.2 Prompt 工程 (Prompt Engineering)
修改 `core/summarizer/prompts.py`，要求 LLM 返回更复杂的 JSON 结构：

**Before:**
```json
["句子1", "句子2"]
```

**After:**
```json
{
    "headline": "本章的一句话核心总结...",
    "details": ["句子1", "句子2", ...]
}
```

### 3.3 兼容性策略 (Backward Compatibility)
对于旧的历史数据（没有 `headline` 字段）：
*   **方案 A**: 在 API 层动态提取 `summary_sentences` 的第一句作为 fallback。
*   **方案 B**: 前端 UI 处理，如果 `headline` 为空，显示第一句详细总结。

## 4. API 接口调整 (API Changes)

### 4.1 列表接口增强
修改 `GET /api/novels/{...}/chapters`：
*   不仅返回 ID 和 Title，还需要返回 `headline`。
*   这样前端在加载概览列表时，无需请求每个章节的详情接口。

## 5. 开发计划 (Implementation Plan)

1.  **后端 (Backend)** [已完成]:
    *   ✅ 更新 `ChapterSummary` 模型。
    *   ✅ 更新 `Prompts` 和 `SummaryGenerator` 以支持新的 JSON 结构解析。
2.  **API 接口 (API)** [已完成]:
    *   ✅ 更新 API `list_chapters` 返回 `headline`。
    *   ✅ 更新 API `get_chapter_detail` 返回 `headline`。
3.  **前端 (Frontend)** [已完成]:
    *   ✅ 添加 Store 状态管理（当前视图模式 `viewMode`）。
    *   ✅ 实现侧边栏组件的条件渲染（概览模式显示章节列表+Headline，专注模式显示详细总结）。
    *   ✅ 适配旧数据展示（无 Headline 时显示提示）。
