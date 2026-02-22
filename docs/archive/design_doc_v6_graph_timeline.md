# StoryTrace Phase 6: Dynamic Graph & Timeline Visualization

## 1. 核心目标 (Core Objectives)
构建一个**低 Token 消耗**、**高扩展性**的动态可视化系统，通过**图谱 (Graph)** 和 **时间轴 (Timeline)** 两个维度，展示小说中的实体关系演变。

### 关键约束
*   **Token 效率**: 必须采用“局部提取 (Local Extraction)”策略，避免将整书上下文一次性输入 LLM。
*   **长篇支持**: 架构必须支持 1000+ 章节的增量构建，避免内存溢出或计算瓶颈。
*   **非 LLM 渲染**: 视图渲染完全依赖前端算法 (如 D3.js/Vis.js)，不依赖 LLM 生成图像。

## 2. 架构设计 (Architecture)

### 2.1 数据流 (Data Flow)
1.  **Extraction (LLM)**: 逐章提取实体 (Entities) 和 **显式关系 (Relationships)**。
2.  **Storage (JSONL)**: 增量存储为 `summaries.jsonl`，每行包含单章的实体和关系数据。
3.  **Aggregation (Python)**: 
    *   **Node Merging**: 归一化实体 (SameAs)。
    *   **Edge Merging**: 将不同章节的关系叠加为**带时间戳的边** (Time-stamped Edges)。
4.  **Visualization (Frontend)**:
    *   **Timeline**: 渲染章节/时间点序列。
    *   **Graph**: 根据当前选中的时间点，动态过滤并渲染对应的节点和边。

## 3. 数据模型设计 (Data Models)

### 3.1 关系模型 (Relationship)
在 `data_protocol/models.py` 中新增：

```python
class Relationship(BaseModel):
    source: str = Field(..., description="主体 (Subject)，如 '孙杰克'")
    target: str = Field(..., description="客体 (Object)，如 '塔派'")
    relation: str = Field(..., description="关系类型/谓语，如 '朋友', '敌人', '攻击', '遇见'")
    description: str = Field(..., description="关系描述，如 '在垃圾场捡到的机器人'")
    confidence: float = Field(default=1.0)
```

### 3.2 章节扩展
`ChapterSummary` 增加 `relationships` 字段：

```python
class ChapterSummary(BaseModel):
    # ... existing fields
    relationships: List[Relationship] = Field(default_factory=list, description="本章内发生的实体互动关系")
```

### 3.3 全局聚合模型 (Global Graph)
`AggregatedEntity` 保持不变，新增 `AggregatedRelationship`：

```python
class AggregatedRelationship(BaseModel):
    source: str
    target: str
    timeline: List[Dict[str, Any]] = Field(..., description="关系演变历史: [{'chapter_id': 'ch1', 'relation': 'stranger'}, {'chapter_id': 'ch50', 'relation': 'friend'}]")
```

## 4. 开发计划 (Implementation Plan)

### Phase 6.1: 关系提取 (Relationship Extraction) [Current]
*   **Backend**: 更新 `models.py` 定义 `Relationship`。
*   **Prompt**: 修改 `core/summarizer/prompts.py`，增加关系提取指令。
*   **Generator**: 更新 `generator.py` 解析逻辑。
*   **Testing**: 单元测试验证提取效果。

### Phase 6.2: 关系聚合 (Relationship Aggregation) [Next]
*   **Backend**: 升级 `core/world_builder/aggregator.py`。
*   **Logic**: 实现边的合并逻辑 (Merge Edges by Source/Target)。
*   **API**: 更新 `/api/novels/.../graph` 接口，返回图谱数据 (Nodes + Edges)。

### Phase 6.3: 前端可视化 (Frontend Visualization) [已完成]
*   ✅ **Lib**: 引入 `vis-network`。
*   ✅ **UI**: 实现时间轴滑块 (Slider)。
*   ✅ **Interaction**: 滑动时间轴 -> 过滤 Edges -> 更新 Graph。

## 6. 开发日志与问题排查 (Development Log & Troubleshooting)
### 6.1 前端白屏与布局错乱问题 (2026-02-19)
**问题现象**:
1.  页面初始白屏，显示原始 `{{ }}` 模板语法。
2.  修复 JS 错误后，出现 `setEntityScope is not defined` 报错。
3.  修复报错后，页面布局错乱（左右分栏失效，变为上下堆叠）。

**原因分析**:
1.  **JS 语法错误**: 在 `index.html` 的 `setup()` 函数中意外残留了多余的 `return` 语句块，导致 Vue 应用无法挂载。
2.  **函数丢失**: 在修复 JS 错误时，误删了 `setEntityScope` 函数定义。
3.  **布局错乱**: 疑似 Tailwind CSS 库未正确加载或执行。
    *   尝试更换了 CDN 源 (`unpkg.com` -> `cdn.staticfile.org`)。
    *   如果在无网络或 CDN 访问受限环境下，Tailwind 将无法解析类名，导致页面失去样式，回退到默认的块级元素堆叠布局。

**解决方案**:
1.  清理 `index.html` 中的冗余代码，确保 Vue `setup()` 结构正确。
2.  补全丢失的函数定义。
3.  增加全局错误捕获 (`window.onerror`) 以便快速定位白屏原因。
4.  (待验证) 检查 Tailwind CDN 的连通性，或考虑将 CSS 库本地化。

**当前状态**:
后端 API 与数据逻辑正常。前端 JS 逻辑已修复，但样式渲染存在环境依赖问题。

### 6.2 前端基础设施固化 (Frontend Hardening) [Next Step]
**目标**: 彻底解决白屏和布局错乱问题，不再依赖外部 CDN。

**行动计划**:
1.  **本地化依赖库**: 下载 `vue.global.prod.js`, `tailwindcss.js`, `vis-network.min.js` 到项目的 `web_ui/static/libs/` 目录。
2.  **后端配置**: 修改 `web_ui/server.py`，挂载 `/static` 路径以服务静态文件。
3.  **前端更新**: 将 `index.html` 中的 `<script src="https://cdn...">` 替换为本地相对路径 `/static/libs/...`。
4.  **验证**: 确保在离线或网络不佳环境下，页面布局依然稳固，功能可用。

### 6.3 数据增量更新 (Data Regeneration) [Pending]
**目标**: 生成缺失的“关系数据”。
*   由于 Prompt 模板已更新，重新运行 `main.py` 将自动触发 LLM 重新提取，填充 `relationships` 字段。

### 6.4 UI Refinement & Bug Fixes (UI 优化与问题修复) [Planned]
**用户反馈**:
1.  **Critical Bug**: 切换视图（百科 -> 图谱）后，图谱消失。
2.  **UX Issue**: 节点间距过大，布局松散。
3.  **UX Issue**: 节点缺乏形状区分（仅靠颜色）。
4.  **UX Issue**: 缺少图例 (Legend)。
5.  **UX Issue**: 缩放时字体过小，缺乏自适应。

**解决方案**:
1.  **修复图谱消失**: 
    *   修改 `fetchGraphData` 逻辑，移除过早的 return，确保每次进入 Graph 视图时都调用 `initGraph` 重新挂载 DOM。
2.  **优化布局 (Physics)**:
    *   调整 `barnesHut` 参数：增加 `gravitationalConstant`（引力），减小 `springLength`（弹簧长度），使图谱更紧凑。
3.  **形状区分 (Shapes)**:
    *   配置 `groups`：Person -> `dot` (圆形), Location -> `square` (方形), Organization -> `triangle` (三角形), Item -> `diamond` (菱形), Concept -> `star` (星形)。
4.  **增加图例 (Legend)**:
    *   在图谱左下角添加一个半透明的 HTML 覆盖层，展示颜色和形状的对应关系。
5.  **字体自适应 (Scaling)**:
### Phase 6.5: 专注模式 (Focus Mode) - 2026-02-19

*   **Status**: Implemented & Bug Fixed
*   **Feature**:
    *   Added "Focus Mode" toggle to switch between Cumulative (Global) and Focus (Chapter) views.
    *   **Auto-Fit**: Graph now automatically zooms to fit screen when:
        *   Physics stabilization finishes.
        *   User switches between Focus/Cumulative modes.
        *   User drags the timeline slider.
    *   **Manual Fit**: Added "⛶ 适配视图" button for manual re-centering.
    *   **Cumulative Mode**: Shows all relationships up to the current chapter. Nodes accumulate.
    *   **Focus Mode**: Shows ONLY relationships active in the current chapter. Nodes not involved are hidden.
    *   **Physics Tuning**:
        *   Focus Mode: Increased repulsion (-20000) and spring length (200) for better visibility of sparse graphs.
        *   Cumulative Mode: Tighter physics (-10000, 120) to handle dense clusters.
*   **Fixes**:
    *   Resolved "Focus Mode Toggle Bug": The toggle button was unresponsive because `setGraphFilterMode` and `graphFilterMode` were not exposed in Vue's `setup()` return object.
    *   Resolved "Graph Drifting": Added `network.fit()` calls on `stabilized` event and `updateGraphFilter` to keep graph centered.

### Known Issues (To Be Verified)

### 6.6 UI 细节优化 (UI Polish) [Implemented]
1.  **时间轴刻度优化**: 
    *   实现智能刻度标签逻辑：章节数 <= 5 时显示所有标题；> 5 时显示“始、中、末”三个关键点。
    *   解决了“第2章消失”和“第2章显示在第1章位置”的视觉歧义。
2.  **图谱视觉增强**:
    *   **形状区分**: Person=Dot, Location=Square, Org=Triangle, Item=Diamond, Concept=Star。
    *   **图例**: 左下角半透明图例。
    *   **物理布局**: 调整引力和弹簧长度，使图谱更紧凑。
    *   **字体缩放**: 节点字体随重要性自适应。

### Phase 6.7: 数据归一化 (Data Normalization) [Implemented] - 2026-02-19

*   **问题**: 源文本包含繁体中文，导致 LLM 提取的实体名存在繁简混杂（如“孫傑克”和“孙杰克”），在图谱中分裂为两个节点。
*   **解决方案**:
    *   引入 `zhconv` 库进行简繁转换。
    *   在 `EntityAggregator` 中增加 `_normalize_text` 方法。
    *   在聚合实体和关系之前，强制将所有 `name`, `source`, `target` 转换为**简体中文**。
*   **效果**:
    *   图谱中的“孫傑克”节点将自动合并到“孙杰克”。
    *   无需重新运行昂贵的 LLM 提取流程。

### Known Issues (To Be Verified)

1.  **Graph Jitter**: Switching modes might cause sudden jumps. Physics stabilization needs testing.
2.  **Data Quality**: Need to verify if `relationships` extracted in Phase 5 are distinct enough per chapter.

### Phase 6.8: 关系时序可视化 (Relationship Order) [Implemented] - 2026-02-19

*   **需求**: 用户希望在单章（时间点）内，看到实体互动的先后顺序（如 1->2->3）。
*   **方案**:
    *   **后端**: 在 `EntityAggregator` 中，利用 `summary.relationships` 的列表索引作为 `order` (1-based index)，并存储在 `timeline` 数据中。
    *   **前端**: 在连线标签上增加 `[1]`, `[2]` 前缀。
    *   **无需重跑 LLM**: 利用现有的提取顺序（LLM 通常按文本顺序提取），通过增量聚合逻辑实现。

### Phase 6.9: 图谱精简与全局模式优化 (Graph Optimization) [Design] - 2026-02-20

*   **问题**: 
    1.  **全局模式过于复杂**: 即使只有10章，节点和连线也过多，导致图谱难以阅读。
    2.  **标签混乱**: 全局模式下，边的标签保留了单章的序号（如 `[2] 攻击`），导致同一条边上出现多个重复的序号（因为每章都有序号为2的事件），信息冗余且令人困惑。
    3.  **缺乏重点**: 全局视图应提供宏观视角，而非细节堆砌。

*   **需求 (Requirements)**:
    1.  **简化全局模式 (Simplify Global Mode)**: 
        *   全局模式下**移除连线标签**（或仅保留权重信息），不再显示具体的互动描述和序号。
        *   细节信息（如 `[1] 遇见`）仅在**专注模式 (Focus Mode)** 或 **鼠标悬停 (Hover)** 时显示。
    2.  **边聚合 (Edge Aggregation)**:
        *   全局模式下，同一对实体之间的多次互动应合并为一条边，**粗细**代表互动频率（权重）。
    3.  **节点过滤 (Node Filtering)**:
        *   **按频率过滤**: 提供滑块或选项，隐藏只出现一次的孤立节点/边缘角色。
        *   **按类型过滤**: 允许用户开关特定类型的节点（如隐藏 Item/Concept，只看 Person/Org）。

*   **解决方案 (Solution Design)**:
    1.  **Visuals (GraphController)**:
        *   `updateFilter` 逻辑分支：
            *   **Focus Mode**: 保持现状，显示 `label: "[1] 关系"`, `width: fixed/small`.
            *   **Cumulative Mode**: 设置 `label: undefined` (隐藏文字)，`title: "X interactions..."` (Tooltip), `width: Math.log(weight) * scale`.
    2.  **UI Controls (App.vue)**:
        *   新增 "Min Interactions" 滑块 (默认 1，可调至 2-5)。
        *   新增 "Entity Type" 复选框组 (Person, Location, etc.)。

## 4. Next Steps

1.  **Refactor GraphController**: Implement the display logic separation for Global/Focus modes.
2.  **Add Filters**: Add UI controls for filtering nodes by weight and type.
