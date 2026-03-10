# 动态时间轴导航设计 (Dynamic Timeline Navigation)

## 1. 核心目标 (Goals)
将侧边栏简单的“章节列表”升级为**可视化的剧情强度热力图**。该时间轴不仅用于导航，还能直观反映小说的节奏起伏，并与主视图的筛选器实时联动。

## 2. 数据结构增强 (Data Structure)

### 2.1 章节强度评分 (Intensity Score)
- **公式**: `score = entity_count * 1.5 + relationship_count * 3.0`
- **归一化**: 将所有章节的分数映射到 0-1 区间，用于颜色插值。
- **颜色映射**:
    - Low (0.0 - 0.33): `bg-gray-200` (平静/铺垫)
    - Medium (0.33 - 0.66): `bg-indigo-300` (推进/发展)
    - High (0.66 - 1.0): `bg-rose-500` (高潮/冲突)

### 2.2 时间轴节点 (Timeline Node)
侧边栏不再只是卷名列表，而是**“卷 + 迷你章节条”**的组合结构。
```typescript
interface TimelineVolume {
  title: string;
  chapters: TimelineChapter[];
}

interface TimelineChapter {
  id: string;
  index: number;
  intensityScore: number; // 0-1
  isFilteredOut: boolean; // 是否被当前筛选器隐藏
}
```

## 3. UI/UX 设计

### 3.1 视觉呈现 (Visualization)
- **位置**: 左侧侧边栏 (`<aside>`)。
- **样式**:
    - **卷标题**: 保持置顶，点击可折叠该卷的时间轴。
    - **章节条**: 在卷标题下方，展示为一排细长的色块（类似 DNA 条带或 GitHub 贡献图的纵向版）。
    - **节点状态**:
        - **默认**: 显示强度颜色。
        - **筛选后**: 如果该章节被筛选掉 (isFilteredOut=true)，则显示为极淡的灰色或透明，保留占位但弱化视觉。
        - **Hover**: 悬停显示章节标题和强度数值。
        - **Click**: 滚动主视图到该章节。

### 3.2 交互联动 (Interaction)
1.  **双向同步**:
    - **筛选 -> 时间轴**: 当用户在顶部 Filter Bar 选择 "High Intensity" 或 "POV: 孙杰克" 时，侧边栏时间轴上**不符合条件**的节点会自动变灰/变细，符合条件的节点高亮显示。
    - **滚动 -> 时间轴**: 主视图滚动时，侧边栏对应章节的节点应自动高亮（Active State），指示当前阅读进度。

2.  **点击导航**: 点击时间轴上的任意色块，主视图平滑滚动到对应卡片。

## 4. 实现步骤 (Implementation Plan)

### Phase 1: 强度计算逻辑
1.  在 `OverviewGrid.vue` 中添加 `intensityMap` 计算属性，计算全局最大值并为每章打分。
2.  为 `groupedChapters` 的逻辑添加副作用，或者单独创建一个 `filteredChapterIds` Set，用于标记哪些章节是可见的。

### Phase 2: 重构侧边栏
1.  废弃仅显示卷名的旧列表。
2.  实现 `<div v-for="vol in volumeKeys">` 循环。
3.  在卷标题下嵌套渲染章节微型条形图。
    - 使用 Flex 布局或 Grid 布局。
    - 动态 Class: `:class="getIntensityColor(chap)"`。
    - 动态样式: `opacity: isVisible ? 1 : 0.2`。

### Phase 3: 滚动监听增强
1.  利用 `IntersectionObserver` 监听主视图中的章节卡片。
2.  实时更新 `currentActiveChapterId`。
3.  在时间轴上同步高亮当前章节节点（例如添加一个白色边框或放大效果）。

## 5. 预期效果
用户一眼就能通过左侧的“热力条”看出哪一卷是全书的高潮（红色密集），哪一卷是过渡期（灰色为主）。当筛选“孙杰克”时，时间轴上只有他出场的章节亮起，形成通过人物视角观察的独特“剧情指纹”。
