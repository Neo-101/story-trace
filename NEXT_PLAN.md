# 下一步计划：图谱交互与布局优化 (Graph Interaction & Layout Optimization)

## ✅ 已完成 (Completed)
- [x] **概览页重构 (Overview Page Refactor)**
    - [x] **结构化视图**: 废弃扁平网格，实现按“卷”折叠的手风琴式布局 (Accordion Layout)。
    - [x] **动态时间轴**: 实现左侧剧情热力图 (Heatmap Timeline)，可视化展示章节强度与筛选状态。
    - [x] **多维筛选**: 集成 Top 20 POV 角色筛选与红/黄/绿 (High/Med/Low) 剧情强度筛选。
    - [x] **无缝阅读**: 优化卡片点击转场，支持从概览平滑进入 Reader 模式。
- [x] **图谱动态关系标签 (Dynamic Relationship Labels)**
    - [x] 基于 LLM 分析结果 (Arc Stages) 显示高优先级标签。
    - [x] 基于 互动词库 (Lexicon) + 时间衰减算法 计算动态标签。
    - [x] 实现图谱点击交互：高亮选中节点及其邻居，淡化无关节点。
    - [x] 优化图谱渲染性能：增量更新 (Diffing) 与 物理防抖 (Physics Stabilization)。
- [x] **布局聚类与防遮挡 (Layout Clustering & Anti-Overlap)**
    - [x] **空间聚类 (Spatial Clustering)**: 当选中核心节点时，在同类关系的邻居节点之间动态添加隐形弹簧 (Invisible Springs)，利用物理引擎自然形成簇。
    - [x] **防重叠 (Anti-Overlap)**: 优化物理参数 (avoidOverlap)，增强节点间的排斥力，避免节点与标签互相遮挡。
- [x] **核心关系算法修正 (Relationship Scoring Fixes)**
    - [x] **词库补全 (Lexicon Expansion)**: 补充“营救”、“出卖”等关键动词，解决第108章等关键剧情漏判问题。
    - [x] **权重重构 (Score Rebalancing)**: 大幅提升 `Lifebound` (3.0->10.0) 等正向权重，对抗“平庸之恶”的负面累积。
    - [x] **时间衰减平缓化 (Slower Decay)**: 调整 `DECAY_FACTOR` (0.2 -> 0.05)，延长关键历史事件的影响力。
- [x] **修复多选交互 (Fix Multiselect Interaction)**
    - [x] 优化 `network.on("click")` 逻辑，优先检测多选意图 (Shift/Ctrl+Click)，解决单选状态下无法触发对比面板的问题。

## 🚀 进行中 (In Progress)
### 1. 自适应剧情分段 (Adaptive Plot Segmentation)
*   **目标**: 突破传统的“卷-章”物理结构，利用 NLP 和聚类算法实现“剧情弧 (Story Arc)”层面的语义分段。
*   **核心逻辑**:
    *   **语义聚合**: 综合考虑章节的一句话总结 (Headline)、剧情强度 (Intensity Score) 和实体共现率，自动将连续章节聚类为“剧情段落 (Plot Segment)”。
    *   **智能摘要**: 为每个生成的剧情段落自动提炼一个高层级的“段落核心梗概 (Segment Synopsis)”。
    *   **UI 可视化**: 在概览页的卷视图内部，进一步用视觉容器（如卡片组、时间轴标记）区分这些逻辑段落，增强叙事节奏感。

## 📅 待办 (Backlog)
*   **关系演变时间轴 (Relationship Evolution Timeline)**: 在底部时间轴上标记关键关系转折点。
*   **多节点对比模式 (Multi-Node Comparison)**: 优化两个节点选中时的对比视图布局。
