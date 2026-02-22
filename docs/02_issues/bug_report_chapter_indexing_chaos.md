# Bug Report: 章节索引与 ID 映射混乱 (Chapter Indexing Chaos)

## 问题描述 (Problem Description)
在进行小说章节处理和数据库迁移时，观察到章节编号（Chapter Index）与数据库 ID（Database ID）及实际章节标题严重不匹配。
*   **现象**：
    *   第1章的 ID 显示为 93（或其他大数），而非预期的 1。
    *   章节列表在 UI 中乱序显示（虽然尝试了排序，但源数据的 index 可能本身就是乱的）。
    *   时间轴（Timeline）的最大值异常偏大（例如只有34章，时间轴却到了99）。
*   **影响**：图谱演变顺序错误，阅读体验跳跃，数据合并逻辑（Best Effort Merge）可能因索引错误而覆盖错误的数据。

## 根本原因分析 (Root Cause Analysis)
1.  **ID 来源不统一**：
    *   **Splitter**: 生成基于文件顺序的 ID（如 `ch_1`, `ch_2`）。
    *   **Database**: 使用 SQLite 自增 ID（如 1, 2, ..., 93）。
    *   **UI**: 混用了 Database ID 和 Chapter Index。
2.  **迁移脚本逻辑缺陷 (`migrate_json_to_sqlite.py`)**：
    *   `extract_chapter_index` 函数尝试从 Title、ID、Loop Index 多种来源推断 `chapter_index`。
    *   在增量更新或多次运行（Run）的情况下，数据库 ID 会不断增加（因为是自增主键），而如果逻辑错误地回退到了使用 Database ID 或错误的 Regex 匹配作为 Index，会导致 Index 爆炸或乱序。
    *   即使尝试修复了优先级（ID > Title），但在 `ch_XX` 格式与数据库自增 ID 混淆时，仍可能出错。
3.  **数据污染**：多次运行生成的 JSONL 文件可能包含了历史错误的 ID/Index 数据，迁移脚本盲目信任了这些脏数据。

## 尝试过的修复 (Attempted Fixes)
1.  **修改解析优先级**：在迁移脚本中将 `id` 解析（`ch_XX`）优先级提至最高。
2.  **重建数据库**：删除 `.db` 文件并重新运行迁移。
    *   **结果**：失败。问题依旧存在，说明源数据（JSONL）本身可能已经污染，或者解析逻辑仍有漏洞。

## 建议解决方案 (Proposed Solution)
1.  **唯一标识符重构**：
    *   废弃使用数据库自增 ID 作为业务逻辑 ID。
    *   在 `Splitter` 阶段生成确定性的 UUID 或基于内容的 Hash ID。
    *   或者严格强制 `chapter_index` 等于 `file_order`，并在数据库层面强制约束。
2.  **清洗源数据**：需要编写脚本清洗 `output/` 目录下的 `summaries.jsonl`，强制重置其中的 `id` 和 `chapter_index`。
3.  **前端解耦**：前端不应依赖 ID 进行排序，而应严格依赖 `chapter_index`，并确保后端返回的数据是严格清洗过的。
