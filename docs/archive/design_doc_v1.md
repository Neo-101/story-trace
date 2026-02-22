# StoryTrace 项目架构设计文档 (Version 1.1)

## 1. 项目愿景 (Vision)

StoryTrace 旨在构建一个智能化的长篇小说阅读与分析辅助系统。它不仅仅是一个文本处理工具，更是一个“故事理解引擎”。

核心价值主张：
1.  **结构化 (Structuring)**：将非结构化的长篇文本转化为结构化的章节、实体和事件数据。
2.  **增强阅读 (Augmented Reading)**：通过 AI 生成的章节总结，提供“总结-原文”的双向溯源能力，帮助用户快速回顾和定位。
3.  **知识图谱 (Knowledge Graph)**：未来将进一步提取世界观、人物关系和剧情脉络，形成可视化的故事地图。

## 2. 架构原则 (Architectural Principles)

本项目采用 **单体仓库 (Monorepo) + 模块化 (Modular)** 架构，遵循以下原则：

*   **数据驱动 (Data-Driven)**：模块之间通过定义良好的数据协议（Schema）进行通信，而非直接的函数调用。
*   **松耦合 (Loose Coupling)**：各个核心模块（Splitter, Summarizer, WorldBuilder）应具备独立运行的能力，通过配置进行组合。
*   **渐进式增强 (Progressive Enhancement)**：系统应允许在没有 LLM 的情况下运行基础功能（如分割），在有 LLM 资源时提供高级功能（如总结）。

## 3. 系统模块划分 (System Modules)

### 3.1 核心模块 (Core Modules)

| 模块名称 | 职责描述 | 输入 (Input) | 输出 (Output) | 关键技术 |
| :--- | :--- | :--- | :--- | :--- |
| **`core.splitter`** | **文本分割器**。负责清洗原始文本，识别卷/章结构，处理中文数字转换。 | 原始 txt 文件 | `ChapterList` (JSON) | Regex, cn2an |
| **`core.summarizer`** | **智能总结器**。负责调用 LLM 对章节内容进行摘要，并建立摘要句与原文的映射关系。支持本地 LLM (LM Studio) 和在线 API (OpenRouter)。 | `ChapterList` | `SummaryMap` (JSON) | LLM Client (OpenAI/Local/OpenRouter) |
| **`core.world_builder`** | **世界构建器** (规划中)。负责从文本和总结中提取实体（人物、地点）及关系。 | `ChapterList`, `SummaryMap` | `KnowledgeGraph` (GraphML/JSON) | NER, RE (Relation Extraction) |

### 3.2 支撑模块 (Support Modules)

*   **`data_protocol`**：定义所有模块共享的数据结构（Pydantic Models）。这是系统的“骨架”。
*   **`app`**：应用层。负责 CLI 交互、参数解析、流程编排（Pipeline Orchestration）。
*   **`utils`**：通用工具。如文件读写、日志记录、字符串处理。

## 4. 数据协议设计 (Data Protocol Design)

为了实现模块解耦，我们必须严格定义中间数据格式。以下是核心数据模型的设计草案（使用 Python Pydantic 风格描述）：

### 4.1 基础单元

```python
class TextSpan:
    """表示文本中的一个片段及其位置"""
    text: str           # 片段内容
    start_index: int    # 在原文中的起始字符偏移量
    end_index: int      # 在原文中的结束字符偏移量
```

### 4.2 分割模块输出 (Splitter Output)

```python
class Chapter:
    """章节数据模型"""
    id: str             # 唯一标识符 (如 "vol1_ch1")
    title: str          # 章节标题 (如 "第一章 序幕")
    volume_title: str   # 所属分卷标题 (可选)
    content: str        # 章节完整文本
    word_count: int     # 字数

class BookStructure:
    """整书结构模型"""
    book_name: str
    chapters: List[Chapter]
    metadata: Dict      # 额外元数据
```

### 4.3 总结模块输出 (Summarizer Output)

```python
class SummarySentence:
    """单句总结及其溯源"""
    summary_text: str           # 总结的句子 (LLM 生成)
    source_spans: List[TextSpan]# 对应的原文片段 (用于点击跳转)
    confidence: float           # 置信度 (可选)

class ChapterSummary:
    """单章总结"""
    chapter_id: str             # 关联的章节 ID
    summary_sentences: List[SummarySentence]
    key_entities: List[str]     # 本章出现的关键实体 (可选)
```

## 5. 目录结构规划 (Directory Structure)

```text
StoryTrace/
├── data_protocol/          # [核心] 数据协议定义
│   ├── __init__.py
│   ├── models.py           # Pydantic 模型定义
│   └── serializers.py      # JSON 序列化/反序列化工具
├── core/                   # [核心] 业务逻辑
│   ├── splitter/           # 分割模块
│   │   ├── __init__.py
│   │   ├── regex_rules.py  # 正则规则库
│   │   └── processor.py    # 分割逻辑实现
│   ├── summarizer/         # 总结模块
│   │   ├── __init__.py
│   │   ├── llm_client.py   # LLM 客户端适配器 (LM Studio/OpenAI/OpenRouter)
│   │   ├── prompts.py      # Prompt 模板管理
│   │   └── generator.py    # 总结生成逻辑
│   └── world_builder/      # 世界构建模块 (预留)
├── app/                    # [应用] 交互与编排
│   ├── __init__.py
│   ├── main.py             # CLI 入口
│   ├── pipeline.py         # 流程控制器 (串联 Splitter -> Summarizer)
│   └── ui/                 # 简单的 Web UI (Streamlit/Gradio)
├── tests/                  # 测试用例
├── docs/                   # 项目文档
├── requirements.txt
└── README.md
```

## 6. 开发路线图 (Roadmap)

### Phase 1: 基础重构 (Refactoring) [已完成]
- [x] 创建 `data_protocol`，定义 `Chapter` 和 `BookStructure`。
- [x] 将现有的 `split_*.py` 脚本重构为 `core.splitter` 模块。
- [x] 确保 `core.splitter` 输出符合 `data_protocol` 标准的 JSON。
- [x] 更新 `app/main.py` 以适配新架构。
- [x] 增强 `Splitter` 正则表达式，支持繁体中文数字 (壹贰叁...) 和异体字 (卷/巻)。

### Phase 2: 智能总结 (AI Summarization) [已完成]
- [x] 实现 `core.summarizer` 模块基础框架。
- [x] 设计 LLM 交互接口，支持配置本地 LM Studio API 地址和 OpenRouter API。
- [x] 设计 Prompt，要求 LLM 输出总结的同时引用原文片段（难点：如何精准定位）。
- [x] 实现简单的 HTML 报告生成，展示“点击总结跳转原文”的效果。
- [x] **[NEW] 增量构建与缓存**: 实现基于指纹的缓存机制，避免重复 LLM 调用。
- [x] **[NEW] 可视化系统**: 开发基于 Vue 3 + FastAPI 的本地 Web 服务，提供沉浸式阅读体验。
- [ ] **[NEW] 全书概览模式 (Book Overview Mode)**: 提供侧边栏章节列表 + 一句话核心总结，支持快速浏览剧情脉络。

### Phase 3: 知识图谱 (World Building) [Next]
- [ ] 设计实体提取 (NER) 流程。
- [ ] 构建人物关系图。
- [ ] 开发可视化大屏。

## 7. 技术栈选型 (Tech Stack)

*   **语言**: Python 3.10+
*   **数据验证**: Pydantic (强类型数据定义)
*   **CLI**: Typer 或 Argparse
*   **LLM 交互**: OpenAI SDK (兼容 LM Studio/OpenRouter)
*   **Web UI**: Streamlit (快速构建数据可视化应用)
