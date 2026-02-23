# 🛡️ Vibe Coding 防御策略：分层防御与组件化架构

> **Status**: Approved
> **Date**: 2026-02-23
> **Focus**: Regression Testing, Component Isolation, Integration Safety

本文档阐述了在 Vibe Coding 并行开发模式下，如何通过**分层防御 (Layered Defense)** 和 **组件化架构 (Component Architecture)** 来解决“集成地狱”和“UI 回归”问题。我们的核心原则是：**先打样，再复制 (Template First, Then Parallel)**。

---

## 1. 🛑 核心痛点与解决方案

| 痛点 | 表现 | 解决方案 |
| :--- | :--- | :--- |
| **数据冲突** | 多个 Agent 同时修改 `aggregator.py`，导致逻辑覆盖。 | **数据隔离**：每个模块拥有独立字段；严禁修改公共字段。 |
| **UI 崩坏** | 多个 Agent 同时修改 `EntityDetail.vue`，导致样式错乱。 | **组件插槽**：主组件只提供 Slot，Agent 只开发独立子组件。 |
| **功能退化** | 新功能上线导致旧功能（如概览）失效。 | **回归防线**：设立 `tests/regression/`，提交前必须通过。 |

---

## 2. 🏗️ 架构设计 (Architecture)

### A. 后端：逻辑隔离与回归测试
*   **独立 Aggregator**：每个模块必须有独立的聚合器（如 `ConceptAggregator`），严禁在 `EntityAggregator` 中直接写死逻辑。
*   **Golden Master Test**：
    *   建立基准数据集 (`tests/regression/data/golden_master.json`)。
    *   每次运行测试时，对比新生成的 Output 与基准数据的差异。
    *   **规则**：新增字段允许，原有字段修改/删除**必须报错**。

### B. 前端：组件插槽化 (Slot Architecture)
我们将重构 `EntityDetail.vue`，使其从一个“巨石组件”变为“容器组件”。

**Before (Monolithic):**
```vue
<template>
  <div>
    <h1>{{ entity.name }}</h1>
    <p>{{ entity.description }}</p>
    <!-- 所有的逻辑都写在这里，几百行代码 -->
    <div v-if="entity.concept_evolution">...</div>
    <div v-if="entity.clue_lifecycle">...</div>
  </div>
</template>
```

**After (Container + Slots):**
```vue
<template>
  <div class="entity-detail-container">
    <!-- 1. 公共头部 (Base Info) -->
    <EntityHeader :entity="entity" />

    <!-- 2. 动态插槽区域 (Dynamic Modules) -->
    <!-- 每个模块只开发自己的组件，互不干扰 -->
    <ConceptEvolutionCard v-if="entity.concept_evolution" :data="entity.concept_evolution" />
    <ClueTimelineCard v-if="entity.clue_lifecycle" :data="entity.clue_lifecycle" />
    <FactionHeatmapCard v-if="entity.faction" :data="entity.faction" />
  </div>
</template>
```

---

## 3. 🚀 执行路线 (Execution Path)

### Phase 1: 建立防线 (Current Step)
1.  **回归测试体系**: 创建 `tests/regression/`，编写基准测试脚本。
2.  **前端重构**: 将 `EntityDetail.vue` 重构为插槽架构，提取 `EntityHeader.vue`。

### Phase 2: 模块打样 (Template Module)
1.  **Module 2 (Concept)**: 在当前窗口完整实现后端聚合逻辑 + 前端 `ConceptEvolutionCard.vue`。
2.  **验证**: 确保通过回归测试，且不影响其他功能。

### Phase 3: 并行复制 (Parallel Replication)
1.  **分发**: 将 Module 2 的代码结构作为**样板**，分发给 Agent B (Clue) 和 Agent C (Faction)。
2.  **指令**: "请参照 `ConceptEvolutionCard.vue` 的写法，实现 `ClueTimelineCard.vue`，并注册到 `EntityDetail.vue` 中。"

---

## 4. ✅ 验收标准 (Definition of Done)
*   [ ] `tests/regression/test_core_features.py` 能够成功运行并拦截破坏性修改。
*   [ ] `EntityDetail.vue` 只有 < 50 行代码，且清晰地引入了子组件。
*   [ ] 新增模块代码不触碰 `core/world_builder/aggregator.py` 的核心逻辑。
