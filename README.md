# 📚 StoryTrace

**基于 LLM 的智能小说分析与可视化系统**

StoryTrace (原 split-novel-txt) 将纯文本小说转化为结构化、可探索的知识库。它不仅是一个强大的文本分割工具，更深度集成 LLM (如 DeepSeek, Gemini, Qwen) 生成章节摘要、提取人物关系，并通过现代化的 Web 界面提供交互式知识图谱和沉浸式阅读体验。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Vue](https://img.shields.io/badge/vue-3.x-green.svg)

## ✨ 核心特性

*   **📖 智能结构化**：自动识别并分割卷/章，支持复杂的中文数字与格式解析。
*   **🧠 AI 深度分析**：集成 LLM 生成剧情摘要，智能提取人物、地点、组织等实体。
*   **🕸️ 交互式图谱**：
    *   **全局概览 (Global Mode)**：宏观展示人物关系网络，支持按权重过滤。
    *   **聚焦模式 (Focus Mode)**：查看特定章节内的实体互动细节。
    *   **时间轴漫游**：拖动时间轴，动态回放故事发展过程中的关系演变。
*   **⚡ 现代化界面**：
    *   基于 **Vue 3 + TypeScript + Vite** 构建的响应式 Web UI。
    *   提供虚拟滚动列表、自动定位阅读、实体高亮等“Vibe Coding”体验。
*   **🚀 高性能架构**：
    *   **Vibe Coding 友好**：内置自动化运维脚本 (`manage.py`) 和上下文打包工具。
    *   **缓存机制**：智能缓存 LLM 响应，节省 Token 并加速二次处理。
    *   **断点续传**：支持 Best-effort Merge，多次运行结果自动合并。

## 🛠️ 技术栈

*   **Backend**: Python, FastAPI, SQLModel (SQLite), AsyncIO
*   **Frontend**: Vue 3, TypeScript, Vite, Pinia, Tailwind CSS v4
*   **Visualization**: Vis.js (Network Graph)
*   **AI/LLM**: OpenAI API 兼容接口 (支持 DeepSeek, ChatGPT, Gemini, Local Ollama 等)

## 🚀 快速开始

### 1. 环境准备

*   Python 3.10+
*   Node.js 18+ (用于前端开发)

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 LLM

在项目根目录创建 `.env` 文件（参考 `core/config.py`）：

```ini
# 数据库配置
DATABASE_URL=sqlite:///storytrace.db

# API 服务配置
API_HOST=127.0.0.1
API_PORT=8000

# LLM 配置 (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.0-flash-001

# LLM 配置 (Local Ollama)
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:14b
```

### 4. 运行项目

本项目包含前后端两部分。

#### 启动后端 API 服务

```bash
# 推荐方式
python app/main.py serve
```
服务默认运行在 `http://127.0.0.1:8000`（端口可配置）。API 文档位于 `/docs`。

#### 启动前端界面 (开发模式)

进入 `frontend` 目录：

```bash
cd frontend
npm install
npm run dev
```
访问终端输出的本地地址 (如 `http://localhost:5173`) 即可开始使用。

## 🛠️ 常用运维命令

使用 `manage.py` 进行一站式运维：

### 基础管理
```bash
# 环境自检
python manage.py check

# 清理 LLM 缓存
python manage.py clean-cache

# 重置数据库 (开发调试用)
python manage.py reset-db
```

### 👩‍💻 上下文工具 (Context Tools)
专为 **Vibe Coding** (LLM 辅助开发) 设计，帮助快速生成项目上下文。

```bash
# 1. 启动实时监控 (Watch Mode)
# 自动检测代码变动，更新 docs/project_stats/ 下的统计文件 (含 Token 计数)
python manage.py context watch

# 2. 执行代码打包 (Pack Mode)
# 将核心架构代码 (排除 tests/scripts) 打包成 docs/project_stats/project_context_packed.txt
# 适合直接发送给 LLM 作为 Context
python manage.py context pack

# 3. 生成统计报告 (Stats Mode)
# 生成一次性的行数和 Token 统计报告
python manage.py context stats
```

> **提示**: 上下文工具会读取 `scripts/context_tools/.contextignore` 文件来过滤非核心代码（如 `tests`, `scripts`, `cache`），确保生成的上下文精简且聚焦于业务逻辑。

更多详细命令请参考 [COMMANDS.md](COMMANDS.md)。

## 📂 项目结构

*   `app/`: CLI 入口与流程控制
*   `backend/`: FastAPI 后端服务
*   `core/`: 核心业务逻辑 (Splitter, Summarizer, Graph)
*   `frontend/`: Vue 3 前端工程
*   `data_protocol/`: 数据模型定义
*   `scripts/`: 运维与辅助脚本 (Context Tools)
*   `docs/`: 项目文档与统计数据

## 📄 License

MIT License
