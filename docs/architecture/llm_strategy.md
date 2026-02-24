# LLM Cost Efficiency & Architecture Strategy

## 1. 核心挑战：多维视角的重复开销
目前的架构是：
*   视角 A（关系）：读取 Ch1-Ch100 -> LLM -> 关系报告
*   视角 B（概念）：读取 Ch1-Ch100 -> LLM -> 演变报告
*   视角 C（伏笔）：读取 Ch1-Ch100 -> LLM -> 线索报告

**痛点**：Input Token（原文上下文）占据了 90% 的成本，而 Output Token（分析结果）只占 10%。重复读取相同的原文是巨大的浪费。

## 2. 优化策略 A：任务合并 (Multi-Task Prompting)
**原理**：利用 Context Window 的复用性。如果多个分析任务都需要读取相同的全书片段，应将其合并为一次 LLM 调用。

*   **推荐方案：分组并行（Grouped Parallelism）**
    *   **轻量组**：实体提取 + 简单描述更新（Ingestion 阶段）。
    *   **深度组**：当用户请求“概念演变”时，Prompt 可以顺便询问相关的**伏笔（Clue）**或**势力（Faction）**变动。
    *   **收益**：用 1.1 倍的 Output 消耗，省去了 1.0 倍的 Input 重复消耗。

## 3. 优化策略 B：缓存作为上下文 (Cache as Context)
**原理**：上一次分析的 Output，应成为下一次分析的 Input。

*   **Step 1（基础）**：Ingestion 阶段生成 `Entity Chronicle`（实体编年史）。这是**一级缓存**。
*   **Step 2（进阶）**：做“关系分析”时，**直接把 `Entity Chronicle` 发给 LLM**，而非原文。
    *   收益：Token 消耗从“百万级（原文）”降低到“万级（摘要）”，成本降低 99%。
*   **Step 3（协同）**：做“概念演变”时，如果已有“关系报告”，将其作为**辅助背景**喂给 LLM。
    *   收益：LLM 分析更精准，站在“巨人的肩膀”上。

## 4. 优化策略 C：按需触发 (On-Demand Triggering)
**原理**：并非所有实体都需要深度分析。仅在用户关注时触发高成本分析。

*   **架构实现**：
    *   **Backend API**: `POST /analyze/concept` (接收 `entity_name`)。
    *   **Context Manager**: 负责组装最小化上下文 (Entity Chronicle)。
    *   **Frontend**: 仅展示基础信息，提供 "Deep Analyze" 按钮。
*   **收益**：
    *   将 LLM 成本与用户活跃度挂钩，避免为无人问津的实体浪费 Token。
    *   支持用户交互式探索，提升参与感。

## 5. 开发原则 (Development Principles)

### 原则 1：Input 最小化原则 (Minimize Input Context)
*   **Rule**: 永远不要直接发送 Raw Text 进行高级分析，除非那是第一次提取。
*   **Action**: 必须先查询 `Entity Chronicle` 或 `Summary` 缓存。只有当缓存缺失时，才回退到 Raw Text。

### 原则 2：上下文继承原则 (Context Inheritance)
*   **Rule**: 高级任务（如 Worldview）应继承低级任务（如 Relationship）的成果。
*   **Action**: 在构建 Prompt 时，检查 `StateStore` 中是否已有相关实体的分析报告。如果有，将其摘要放入 `Background Context` 字段。

### 原则 3：原子化与组合 (Atomicity & Composition)
*   **Rule**: 单个 LLM 调用应保持原子性（只做一件事），但在用户体验层提供“组合拳”。
*   **Action**: 允许用户在 UI 上勾选“同时分析关系与概念”。后端调度器（Scheduler）负责判断是合并 Prompt 发送，还是分开发送但共享 Context 缓存。
