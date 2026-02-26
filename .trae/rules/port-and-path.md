## 🛡️ Configuration & Environment Rules

1.  **单一事实来源 (Single Source of Truth)**
    *   所有配置（端口 `API_PORT`、地址 `API_HOST`、密钥）**必须且只能** 从根目录的 `.env` 读取。
    *   **严禁**在代码中硬编码具体数值（如 `8000`, `localhost`），即使作为默认值也应优先读取环境变量。

2.  **Monorepo 路径感知 (Path Awareness)**
    *   前端在 `frontend/` 子目录下运行，但配置文件在根目录。
    *   在编写前端构建脚本（如 `vite.config.ts`）时，**必须**显式指定读取上级目录 (`../.env`) 的配置，防止读取失败回退到默认值。

3.  **配置同步验证 (Sync Verification)**
    *   修改配置逻辑后，必须确保后端启动日志（Server）和前端代理日志（Proxy）显示的端口/地址完全一致。
    *   任何端口变更只需修改 `.env` 一处即可生效，无需改动代码。