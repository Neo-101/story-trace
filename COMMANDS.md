# 常用命令指南 (Cheat Sheet)

本文档整理了 StoryTrace 项目开发和运行中最常用的命令。

## 1. 核心功能

### 启动新版 Web 可视化前端 (Web UI V2 - Recommended)
这是重构后的现代化前端，提供更流畅的交互体验（自动滚动、响应式布局）。
```bash
# 1. 确保后端服务已运行 (Backend)
python -m web_ui.server

# 2. 新开一个终端窗口，启动前端开发服务器 (Frontend)
cd web_ui_v2
npm run dev
```
*   前端访问地址: http://localhost:5173 (如果端口被占用，可能会自动切换到 5174)
*   后端 API 地址: http://localhost:8000

### 启动旧版 Web 可视化服务 (Legacy Backend Server)
这是查看图谱、阅读小说和调试的最常用方式。
```bash
python -m web_ui.server
```
*   服务地址: http://localhost:8000
*   Swagger API 文档: http://localhost:8000/docs
*   **注意**: 如果修改了后端代码 (`core/`, `web_ui/`)，必须重启此服务才能生效。

### 运行主程序 (CLI Mode)
用于处理小说文件（分割、AI 总结）。
```bash
python main.py
```
*   运行后会进入交互式向导，按提示输入文件路径、选择模式等。
*   如果配置了 `config.json`，会提示是否直接加载配置。

### 带参数运行主程序
适用于自动化脚本或不想交互的情况。
```bash
# 仅分割 (默认按章)
python main.py -i inputs/novel.txt -m chapter

# 分割并开启 AI 总结
python main.py -i inputs/novel.txt -m chapter --summarize --provider openrouter
```

## 2. 调试与测试

### 运行测试脚本
用于验证特定模块的功能。
```bash
# 测试实体聚合逻辑 (包含别名测试)
python tests/test_aggregator.py

# 复现图谱生成逻辑
python tests/repro_graph_logic.py
```

## 3. 配置文件

### 别名配置 (Alias Mapping)
当遇到同一实体的不同称呼（如“机器人”和“塔派”）未合并时，修改此文件。
*   文件路径: `config/aliases.json`
*   格式:
    ```json
    {
        "机器人": "塔派",
        "宋6": "宋6PUS"
    }
    ```
*   **修改后操作**: 无需重新运行 `main.py`，只需**重启 Web 服务**并刷新页面即可看到合并效果。

## 4. 常见问题排查

*   **图谱显示空白**:
    *   检查浏览器控制台 (F12) 是否有报错。
    *   检查后端服务是否正在运行。
    *   检查“单章专注”模式下是否因全局过滤器（如最少互动次数）设置过高导致（已修复，但需留意）。
*   **实体未合并**:
    *   检查 `config/aliases.json` 是否正确配置。
    *   **重启 Web 服务**以加载新的别名配置。

## 5. 项目结构速查
*   `web_ui_v2/`: **新版前端 (Vue 3 + Vite)**。
*   `main.py`: CLI 入口。
*   `web_ui/server.py`: 后端 API 服务入口。
*   `web_ui/static/js/`: 旧版前端逻辑 (已废弃，仅供参考)。
*   `core/world_builder/aggregator.py`: 实体/关系聚合逻辑 (含别名处理)。
*   `output/`: 处理结果输出目录。
