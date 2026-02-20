# StoryTrace 缓存与增量构建设计 (v3.0)

## 1. 背景 (Background)
为了避免重复调用 LLM 造成的资金浪费和时间损耗，系统需要引入智能缓存机制。当**数据源**、**提示词**和**模型配置**均未发生变化时，系统应直接复用历史结果。

## 2. 运行指纹 (Run Fingerprint)
系统通过计算“运行指纹”来判定任务是否重复。指纹由以下部分组成：

1.  **Data Hash**: 输入文本文件的 MD5 哈希（已实现）。
2.  **Prompt Hash**: `core.summarizer.prompts` 模块中 System Prompt 和 User Prompt 模板内容的哈希值。
3.  **Config Hash**: 
    *   LLM Provider & Model Name
    *   Split Mode (按卷/按章) & Parameters

## 3. 工作流 (Workflow)

1.  **初始化**: 用户启动任务。
2.  **计算指纹**: 系统计算当前任务的 `target_fingerprint`。
3.  **扫描历史**: 遍历 `output/{novel}/{hash}/` 下的所有 `run_metadata.json`。
4.  **匹配**:
    *   如果发现某个历史记录的 `fingerprint` 与当前完全一致：
        *   **Skip Generation**: 跳过 LLM 调用。
        *   **Create Symlink**: 在新时间戳目录下创建 `ref_link.json`，指向历史目录。
        *   **Log**: 提示用户“命中缓存，复用 [Timestamp] 的结果”。
    *   如果没有匹配：
        *   **Execute**: 执行正常的分割和总结流程。
        *   **Record**: 将 `target_fingerprint` 写入新的 `run_metadata.json`。

## 4. 数据结构变更 (Schema Changes)

### 4.1 run_metadata.json
新增 `fingerprint` 字段。

```json
{
  "timestamp": "...",
  "fingerprint": {
    "prompt_checksum": "sha256_of_prompts",
    "model": "gpt-4",
    "provider": "openrouter",
    "splitter_mode": "chapter"
  },
  "stats": { ... }
}
```

### 4.2 ref_link.json (新文件)
当命中缓存时，新目录下仅包含此文件。

```json
{
  "link_type": "cache_hit",
  "target_timestamp": "20260219_173728",
  "reason": "Fingerprint match"
}
```

## 5. UI 适配
Visualization Server 需要识别 `ref_link.json`。如果读取到该文件，自动重定向读取 `target_timestamp` 目录下的 `summaries.json` 和文本文件。
