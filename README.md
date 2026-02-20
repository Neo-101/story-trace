# 📚 StoryTrace

**基于 LLM 的智能小说分析与可视化系统**

StoryTrace (原 split-novel-txt) 将纯文本小说转化为结构化、可探索的知识库。它不仅是一个强大的文本分割工具，更深度集成 LLM (如 DeepSeek) 生成章节摘要、提取人物关系，并通过现代化的 Web 界面提供交互式知识图谱和沉浸式阅读体验。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.x-green.svg)

## ✨ 核心特性

*   **📖 智能结构化**：自动识别并分割卷/章，支持复杂的中文数字与格式解析（借助 `cn2an`）。
*   **🧠 AI 深度分析**：集成 LLM 生成剧情摘要，智能提取人物、地点、组织等实体。
*   **🕸️ 交互式图谱**：
    *   **全局概览 (Global Mode)**：宏观展示人物关系网络，支持按权重过滤。
    *   **聚焦模式 (Focus Mode)**：查看特定章节内的实体互动细节。
*   **⚡ 现代化界面**：
    *   基于 **Vue 3 + TypeScript + Vite** 构建的响应式 Web UI。
    *   提供虚拟滚动列表、自动定位阅读、实体高亮等“Vibe Coding”体验。
*   **🚀 高性能架构**：支持异步并行处理、SQLite 缓存以及断点续传 (Best-effort Merge)。

## 🛠️ 技术栈

*   **Backend**: Python, FastAPI, SQLModel (SQLite), AsyncIO
*   **Frontend**: Vue 3, TypeScript, Vite, Pinia, Tailwind CSS v4
*   **Visualization**: Vis.js (Network Graph)
*   **AI/LLM**: OpenAI API 兼容接口 (支持 DeepSeek, ChatGPT 等)

## 🚀 快速开始

### 1. 环境准备

*   Python 3.10+
*   Node.js 18+ (用于前端开发)

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 LLM

在项目根目录创建 `.env` 文件或直接在界面配置 API Key。

### 4. 运行项目

本项目包含前后端两部分。

#### 启动后端 API 服务

```bash
python -m web_ui.server
```
服务默认运行在 `http://localhost:8000`。

#### 启动前端界面 (开发模式)

进入 `web_ui_v2` 目录：

```bash
cd web_ui_v2
npm install
npm run dev
```
访问终端输出的本地地址 (如 `http://localhost:5173`) 即可开始使用。

## 📂 项目结构

*   `app/`: CLI 入口与流程控制
*   `core/`: 核心业务逻辑 (Splitter, Summarizer, Graph)
*   `web_ui/`: FastAPI 后端服务
*   `web_ui_v2/`: Vue 3 前端工程
*   `data_protocol/`: 数据模型定义
*   `storytrace.db`: SQLite 数据存储 (自动生成)

## 📝 命令行工具 (CLI)

除了 Web 界面，你仍然可以使用命令行工具进行基础的文本分割：

```bash
python main.py -i input.txt -m volume -o output
```

## 📄 License

MIT License
