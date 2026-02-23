# 🗺️ Vibe Coding 架构演进路线图

> **Status**: Draft
> **Date**: 2026-02-23
> **Focus**: Protocol First, Model Unification, API Automation

本文档详细记录了将 StoryTrace 项目架构向 **Vibe Coding (AI 辅助开发)** 范式迁移的路线图。核心目标是通过**高内聚的协议层**和**自动化的接口契约**，实现“人类定义协议，AI 并行实现”的高效开发模式。

---

## 🔍 现状诊断 (Diagnosis)

目前项目存在 **"三套模型，手动同步"** 的痛点，导致开发效率低下且容易引入 Bug。

| 层级 | 模型定义位置 | 职责 | 痛点 |
| :--- | :--- | :--- | :--- |
| **Protocol** | `data_protocol/models.py` | 核心业务交换格式 (Pydantic) | 被 Core 和 Summarizer 使用，但与 DB/API 模型割裂。 |
| **Storage** | `core/db/models.py` | 数据库持久化 (SQLModel) | 字段与 Protocol 高度重复，但独立定义。需手动维护 `db_chapter_to_summary` 等转换函数。 |
| **API** | `backend/schemas.py` | 前后端交互契约 (Pydantic) | 第三套定义。与 Protocol 相似但独立，导致修改字段需改三处。 |

**结论**: `data_protocol` 未能真正成为 **Single Source of Truth (SSOT)**。

---

## 🚀 演进路线 (Roadmap)

### Phase 1: 统一模型 (Model Unification) ✅ 当前阶段
**目标**: 确立 `data_protocol` 为唯一真理，消除冗余定义。

1.  **Refactor Protocol**:
    *   将 `data_protocol/models.py` 中的模型拆分为 `BaseModel` (纯字段定义) 和 `ProtocolModel` (含业务逻辑)。
    *   确保所有字段定义（如 `Entity.name`, `Entity.type`）只出现一次。

2.  **Inheritance Strategy (继承策略)**:
    *   **DB Models**: 让 `core.db.models` 直接继承 `data_protocol` 的 Base 类。
    *   **API Schemas**: 让 `backend.schemas` 直接继承或复用 `data_protocol` 的定义。
    *   **Result**: 修改 `data_protocol` 中的字段，DB 和 API 自动同步更新。

3.  **Mapper Simplification**:
    *   重构 `backend/routers/analysis.py`，移除手写的字段映射代码，使用 `.model_validate()` 或构造函数直接转换。

### Phase 2: 接口自动化 (API Automation) 📅 下一步
**目标**: 前端开发不再依赖后端代码实现，而是依赖自动生成的契约。

1.  **OpenAPI Enhancement**:
    *   在 FastAPI 中配置 `generate_unique_id_function`，确保生成的 Operation ID 语义化。
    *   确保所有 Router 的 `response_model` 都严格指向 `data_protocol` 或其衍生类。

2.  **Frontend Codegen**:
    *   引入 `openapi-typescript` 或类似工具。
    *   配置 npm 脚本 `gen:api`：自动拉取 `openapi.json` -> 生成 `src/types/schema.d.ts` 和 API Client。
    *   **Vibe Effect**: 后端改模型 -> 运行脚本 -> 前端报错 -> AI 修复前端组件。

### Phase 3: 测试驱动 (Spec-First) 📅 未来规划
**目标**: 用测试用例替代自然语言需求。

1.  **Feature Specs**:
    *   在 `tests/features/` 下编写 BDD 风格的测试脚本。
    *   定义输入（TextSpan）和期望输出（Entity Graph）。

2.  **Agent Loop**:
    *   建立 "Red-Green-Refactor" 的 AI 工作流。

---

## 🛠️ 执行计划 (Action Plan)

1.  **[Task 1]** 重构 `data_protocol/models.py`，提取基础字段定义 (Base Classes)。
2.  **[Task 2]** 修改 `core/db/models.py`，使其继承自 Protocol Base。
3.  **[Task 3]** 修改 `backend/schemas.py`，复用 Protocol 定义。
4.  **[Task 4]** 清理 `backend/routers/` 中的手动转换逻辑。
5.  **[Task 5]** 运行测试，确保重构未破坏现有功能。
