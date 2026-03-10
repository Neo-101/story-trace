# POV 角色筛选功能设计文档

## 1. 功能概述 (Overview)
POV (Point of View) 角色筛选功能允许用户选择小说中的特定角色，从而在概览页面中仅显示该角色出场或作为核心视点的章节。这有助于用户快速梳理单个人物的剧情线。

## 2. 数据流设计 (Data Flow)

### 2.1 数据源 (Source of Truth)
- **后端接口**: `GET /api/novels/{novel_name}/{file_hash}/{timestamp}/entities`
    - 该接口返回聚合后的全局实体列表 (`List[GraphNode]`)。
    - 每个实体对象包含 `chapter_ids` 字段，记录了该实体出现的所有章节 ID。
    - `count` 字段记录了总出场次数，可用于排序。

### 2.2 前端状态管理 (State Management)
- **Store**: `useNovelStore` (`frontend/src/stores/novel.ts`)
    - **State**: 新增 `globalEntities: Entity[]` 状态（现有代码中已存在，需确认是否正确填充）。
    - **Action**: 新增/优化 `loadGlobalEntities()` 方法，调用上述 API 并缓存结果。

### 2.3 筛选逻辑 (Filter Logic)
- **输入**: 
    - `allChapters`: 完整的章节列表。
    - `selectedPovEntity`: 用户选中的实体对象（或 ID）。
- **处理**:
    - 如果 `selectedPovEntity` 为 "All"，返回 `allChapters`。
    - 否则，获取该实体的 `chapter_ids` 集合 `targetIds`。
    - 遍历 `allChapters`，保留 `id` 存在于 `targetIds` 中的章节。
- **输出**: `filteredChapters`，供 UI 渲染。

## 3. UI/UX 设计 (Interface Design)

### 3.1 筛选控件
- **位置**: `OverviewGrid.vue` 顶部的筛选栏 (Filter Bar)。
- **组件**: 下拉选择框 (`<select>` 或自定义 Dropdown)。
- **内容**:
    - 默认选项: "全部视角 (All Perspectives)"。
    - 选项列表: 动态加载出场率最高的 Top 20 角色。
    - 格式: `${RoleName} (${Count}章)`，例如 "孙杰克 (42章)"。

### 3.2 交互反馈
- **加载状态**: 在实体数据加载完成前，下拉框显示 "加载中..." 或禁用。
- **空状态**: 如果某卷（Volume）内的所有章节都被筛选掉了，该卷的标题栏应保持显示但内容为空，或者折叠，或者显示 "本卷无该角色出场" 的提示（建议后者以增强信息密度）。
- **实时性**: 选择变更后，下方网格应立即刷新（使用 Vue `computed` 属性实现）。

## 4. 实现步骤 (Implementation Plan)

### Phase 1: Store 增强
1.  在 `useNovelStore` 中实现 `loadGlobalEntities` action。
2.  确保在切换 Run 或 Novel 时清空 `globalEntities`。

### Phase 2: 组件逻辑
1.  在 `OverviewGrid.vue` 中引入 `loadGlobalEntities`。
2.  在 `onMounted` 或 `watch(currentRun)` 中触发加载。
3.  计算属性 `povOptions`: 
    - 过滤 `store.globalEntities`，只保留 `type === 'Person'`。
    - 按 `count` 降序排列。
    - 取 Top 20。
4.  更新 `groupedChapters` 计算属性，加入 POV 筛选逻辑。

### Phase 3: 视觉优化 (Optional)
1.  为筛选后的视图添加过渡动画。
2.  在空卷状态下添加友好的占位提示。

## 5. 边缘情况 (Edge Cases)
- **同名角色**: 后端已处理别名聚合，前端直接使用聚合后的 `name`。
- **数据未就绪**: 如果后端尚未完成实体分析，实体列表可能为空。此时下拉框应隐藏或提示“需先运行分析”。
- **ID 不匹配**: 确保后端返回的 `chapter_ids` 格式与前端章节列表的 `id` 严格一致（目前均为字符串格式）。
