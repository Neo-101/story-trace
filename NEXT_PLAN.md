# 下一步计划：图谱交互与布局优化 (Graph Interaction & Layout Optimization)

## ✅ 已完成 (Completed)
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
### 1. 概览页重构 (Overview Page Refactor)
*   **目标**: 从简单的章节平铺升级为高级交互式概览系统。
*   **关键特性**:
    *   **结构化视图**: 支持按卷/弧 (Arc) 折叠与展开。
    *   **动态时间轴**: 结合关键事件的时间轴导航。
    *   **多维筛选**: 支持按POV角色、情节强度筛选章节。
    *   **无缝阅读**: 点击卡片平滑过渡到 Reader 模式。

## 📅 待办 (Backlog)
*   **关系演变时间轴 (Relationship Evolution Timeline)**: 在底部时间轴上标记关键关系转折点。
*   **多节点对比模式 (Multi-Node Comparison)**: 优化两个节点选中时的对比视图布局。
