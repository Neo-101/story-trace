# StoryTrace 世界观构建设计 (v5.0)

## 1. 背景与目标 (Background & Goals)
目前 StoryTrace 已经具备了章节分割、智能总结、原文溯源和概览模式。
下一步的核心目标是 **"World Building" (世界观构建)**，即从小说中自动提取和整理核心实体（人物、地点、物品、组织等）及其相互关系，帮助读者建立起对小说世界的立体认知。

## 2. 核心功能 (Core Features)

### 2.1 实体提取 (Entity Extraction)
在现有的章节总结过程中，同步提取本章出现的关键实体。
*   **实体类型**:
    *   **Person (人物)**: 姓名、别名、身份。
    *   **Location (地点)**: 地名、环境特征。
    *   **Organization (组织)**: 门派、帮会、公司、国家。
    *   **Item (物品)**: 武器、法宝、关键道具。
    *   **Concept (概念)**: 功法、境界、特殊设定。

### 2.2 实体档案 (Entity Profile)
随着章节推进，动态更新实体的档案。
*   **首次出现**: 记录登场章节。
*   **属性更新**: 例如人物境界提升、获得新道具、地点变更。
*   **关系网络**: 记录实体之间的关系（如：师徒、敌对、情侣）。

### 2.3 可视化展示 (Visualization)
*   **实体列表**: 在 Web UI 中增加“百科”或“设定集”页面。
*   **关系图谱**: 使用 ECharts 或 D3.js 展示人物关系网。

## 3. 数据层设计 (Data Layer Design)

### 3.1 扩展 `ChapterSummary`
在 `data_protocol/models.py` 中，扩展 `ChapterSummary` 模型，增加 `entities` 字段。

```python
class Entity(BaseModel):
    name: str
    type: str  # Person, Location, etc.
    description: str  # 本章中的相关描述
    confidence: float

class ChapterSummary(BaseModel):
    # ... existing fields ...
    entities: List[Entity] = []
```

### 3.2 提示词工程 (Prompt Engineering)
修改 `core/summarizer/prompts.py`，要求 LLM 在返回 JSON 时包含 `entities` 列表。

**Example Output:**
```json
{
    "headline": "...",
    "summary_sentences": [...],
    "entities": [
        {"name": "孙杰克", "type": "Person", "description": "主角，失忆，身处太空站"},
        {"name": "塔派", "type": "Person", "description": "原本是清洁机器人，被孙杰克激活并改名，拥有迭代进化的AI"}
    ]
}
```

## 4. 开发计划 (Implementation Plan)

### Phase 5.1: 实体提取 (Entity Extraction) [已完成]
1.  ✅ **后端**: 更新 `models.py` 和 `prompts.py` (支持小说三要素提取)。
2.  ✅ **后端**: 更新 `generator.py` 解析逻辑 (支持 `entities` 字段)。
3.  ✅ **API**: 更新 `web_ui/server.py` 返回实体数据。
4.  ✅ **测试**: 完成单元测试并手动验证提取效果。

### Phase 5.2: 实体聚合 (Entity Aggregation) [进行中]
1.  ✅ **逻辑**: 编写一个新的处理模块 `core/world_builder/aggregator.py`，用于遍历所有章节的 `entities`，去重并合并生成全局的实体档案。
2.  ✅ **API**: 提供 `/api/novels/{...}/entities` 接口。

### Phase 5.3: 前端展示 (Frontend Display) [已完成]
1.  ✅ **UI**: 在 Web UI 增加“百科” (Encyclopedia) 视图模式。
2.  ✅ **组件**: 实现侧边栏实体分组列表 (按 Person, Location 等分类)。
3.  ✅ **全局视图**: 实现“本章/全书”切换，展示聚合后的实体列表及出现频次。

## 5. 架构优化 (Infrastructure Updates)
### 5.1 缓存机制升级 (Caching Strategy v4.0)
为了支持大规模章节处理（1000+章），系统已从“全量运行指纹缓存”升级为**章节级缓存 (Chapter-Level Caching)**。
*   **缓存粒度**: 单章。
*   **缓存键**: `MD5(Content + Prompt + ModelConfig)`。
*   **存储位置**: `output/.../run_timestamp/.cache/`。
*   **断点续传**: 支持在程序中断后，重新运行自动跳过已生成的章节。
*   **增量保存**: 引入 `summaries.jsonl` (JSON Lines) 实现实时追加写入，防止程序崩溃导致数据丢失。
