# 常用命令指南 (Cheat Sheet)

本文档整理了 StoryTrace 项目重构后（V2 架构）的最常用命令。

## 1. 🚀 启动可视化服务 (Web UI)

StoryTrace 采用前后端分离架构。你需要分别启动后端 API 服务和前端开发服务器。

### 1.1 启动后端 API (Backend)
后端基于 FastAPI，提供数据分析和图谱接口。

```powershell
# 方式 A: 通过主程序入口 (推荐)
# 在项目根目录下运行:
$env:PYTHONPATH = "."; python app/main.py serve

# 方式 B: 直接运行模块
$env:PYTHONPATH = "."; python -m backend.server
```
*   **API 文档**: http://localhost:8000/docs
*   **服务地址**: http://localhost:8000

### 1.2 启动前端界面 (Frontend)
前端基于 Vue 3 + Vite，提供交互式图谱和阅读器。

```powershell
# 新开一个终端窗口
cd frontend

# 首次运行需要安装依赖
npm install

# 启动开发服务器
npm run dev
```
*   **访问地址**: http://localhost:5173

---

## 2. 🛠️ 项目管理与运维 (Management Script)

使用 `manage.py` 脚本进行环境检查、缓存清理和数据库重置。

```powershell
# 环境自检 (检查依赖、路径和 API Key)
python manage.py check

# 清理 LLM 缓存 (删除 output/.cache)
# 注意：下次运行总结时会重新消耗 Token
python manage.py clean-cache

# 重置数据库 (删除 storytrace.db 并重建表)
# 注意：会清空 Web 端显示的所有数据，但不会删除已生成的 output 文件
# 重置后需重新运行迁移脚本或处理流程
python manage.py reset-db

# 清理所有输出 (删除 output/ 下所有文件，慎用！)
python manage.py clean-all
```

### 上下文管理 (Context Tools)

用于辅助 LLM 开发的工具集，包括代码打包和行数统计。

```powershell
# 启动实时监控 (Watch Mode)
# 自动检测代码变动，更新 docs/project_stats/ 下的统计文件
python manage.py context watch

# 执行代码打包 (Pack Mode)
# 将核心架构代码打包成 docs/project_stats/project_context_packed.txt
python manage.py context pack

# 生成统计报告 (Stats Mode)
# 生成一次性的行数和 Token 统计报告
python manage.py context stats
```

---

## 3. 📂 核心处理工具 (CLI)

用于处理小说文件（分割章节、调用 LLM 生成摘要和提取实体）。

### 交互式模式 (Interactive Mode)
按提示输入文件路径和配置。
```powershell
$env:PYTHONPATH = "."; python app/main.py
```

### 命令行模式 (Command Line Mode)
适用于自动化脚本。

```powershell
# 仅分割 (默认按章)
$env:PYTHONPATH = "."; python app/main.py -i inputs/novel.txt -m chapter

# 分割并开启 AI 总结 (使用 OpenRouter)
$env:PYTHONPATH = "."; python app/main.py -i inputs/novel.txt -m chapter --summarize --provider openrouter

# 分割并开启 AI 总结 (使用本地 Ollama)
$env:PYTHONPATH = "."; python app/main.py -i inputs/novel.txt -m chapter --summarize --provider local --model qwen2.5:14b
```

### 数据迁移 (Migration)
将处理生成的 JSON 数据导入 SQLite 数据库以供前端展示。
```powershell
# 自动扫描 output 目录并导入所有小说数据
$env:PYTHONPATH = "."; python scripts/migrate_json_to_sqlite.py
```

---

## 4. 📂 项目结构说明

*   **`frontend/`**: 现代前端项目 (Vue 3 + Vite + TypeScript)。
    *   `src/components/GraphView.vue`: 核心图谱组件。
    *   `src/stores/novel.ts`: 状态管理。
*   **`backend/`**: 后端 API 服务。
    *   `server.py`: FastAPI 入口。
    *   `routers/`: API 路由定义。
    *   `schemas.py`: Pydantic 数据模型定义。
*   **`app/`**: 应用程序入口。
    *   `main.py`: CLI 和 Server 的统一入口。
*   **`core/`**: 核心业务逻辑。
    *   `config.py`: 全局配置管理 (Pydantic Settings)。
    *   `identifiers.py`: 统一 ID 生成逻辑。
    *   `paths.py`: 统一路径管理逻辑。
    *   `splitter/`: 小说分割逻辑。
    *   `summarizer/`: LLM 摘要生成。
    *   `world_builder/`: 实体聚合与图谱构建。
*   **`manage.py`**: 项目管理脚本。

---

## 5. ⚙️ 配置与调试

### 统一配置 (Configuration)
项目现在支持通过 `.env` 文件或环境变量进行统一配置。
请在根目录下创建 `.env` 文件：

```ini
# .env 示例
DATABASE_URL=sqlite:///storytrace.db
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.0-flash-001
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=qwen2.5:14b
```

### 别名配置 (Alias Mapping)
解决实体同名异指问题（如“哈利”和“波特”）。
*   文件路径: `config/aliases.json` (如果不存在可手动创建)
*   **生效方式**: 修改后需**重启后端服务**。

### 常见问题
*   **ModuleNotFoundError: No module named 'core'**:
    *   请确保在项目根目录下运行，并设置 `PYTHONPATH`。
    *   PowerShell: `$env:PYTHONPATH = "."; python ...`
    *   CMD: `set PYTHONPATH=. && python ...`
