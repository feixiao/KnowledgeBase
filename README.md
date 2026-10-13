# KnowledgeBase (知识库运维与工具链代码仓库)

本仓库为**纯代码与工具链工程**，负责管理数据同步、格式转换与自动化运维流水线。
知识库的真实数据（Markdown、图片、Obsidian Vault）独立存放于专门的数据仓库中，实现**代码与数据物理隔离**。

---

## 🏗️ 架构拓扑 (双仓库解耦)

```text
~ (用户家目录)
├── path/to/KnowledgeBase/             # [当前代码仓库] 纯工具链与流水线
│   ├── .env                           # 本地私有配置 (指向目标 Vault 路径及凭证)
│   ├── scripts/                       # 同步与转换脚本
│   │   ├── init-auth.sh               # 印象笔记首次授权引导
│   │   └── sync.sh                    # 增量拉取 -> 转 Markdown -> 推送至 Vault
│   ├── Makefile                       # 极简终端操作指令
│   └── yarle-config.json              # 默认转换规则模板
│
└── Documents/KnowledgeVault/          # [独立数据仓库 / Obsidian Vault] 纯笔记内容
    ├── 00_Inbox/                      # [速记] 本地随时记录的零散草稿
    ├── 10_Core/                       # [核心] 架构方案、Dev Wiki (RAG 核心索引区)
    ├── 20_Evernote/                   # [印象笔记镜像]
    │   ├── Active/                    # 同步过来的有效笔记 (进入 RAG 索引)
    │   └── Archives/                  # 历史网页剪藏 (RAG 排除此目录以防噪音)
    └── assets/                        # 全局附件与图片资源
```

---

## 🚀 快速上手与日常流

### 1. 配置数据仓库路径
在本项目根目录下复制或编辑 `.env`：
```bash
cp .env.example .env
```
在 `.env` 中确认 `VAULT_DIR`（支持 `~` 相对用户家目录路径）：
```env
VAULT_DIR=~/Documents/KnowledgeVault
```

### 2. 首次初始化 (仅需一次)
在终端运行授权向导，绑定你的印象笔记（中国区后端）：
```bash
make init-auth
```
> 输入账号密码，授权凭证会自动保存在本地 `.evernote/data.db`（已被 Git 忽略，绝对安全）。

### 3. 日常一键增量同步
```bash
make sync
```
脚本会自动：
1. 增量抓取印象笔记变动至本地缓存；
2. 转换为 Obsidian 规范的 Markdown 与独立图片；
3. 输出至 `${VAULT_DIR}/20_Evernote/Active` 与 `${VAULT_DIR}/assets`。

---

## 🧠 本地 AI 与知识库问答配置 (LM Studio + Obsidian)

针对 Smart Connections 商业化及 Pro 限制问题，推荐使用**完全开源、无订阅墙**的方案与本地 LM Studio 对接：

### 方案一：Obsidian Copilot（首选，侧边栏 AI 助手 & Vault QA）

适合在 Obsidian 侧边栏与当前笔记或整个知识库对话。

1. **启动 LM Studio**：
   - 加载模型（如 `qwen2.5-7b-instruct`、`llama-3.1-8b-instruct`）。
   - 切换至 **Developer / Local Server** 标签页，开启服务（默认地址 `http://localhost:1234`）。

2. **配置 Obsidian Copilot**：
   - 在 Obsidian 设置 -> **Community plugins** -> 搜索并安装 **Copilot**。
   - 打开 Copilot 设置：
     - **Default Model Provider**：选择 `Custom (OpenAI Compatible)`
     - **API Key**：任意填写（例如 `lm-studio`）
     - **Base URL**：`http://localhost:1234/v1`
     - **Model Name**：输入 LM Studio 中加载的模型名称（如 `qwen2.5-7b-instruct`）
   - **知识库问答 (Vault QA)**：
     - 在侧边栏对话框中，可直接 `@笔记名称` 引用单篇或多篇笔记；
     - 切换到 **Vault QA** 模式可直接检索整个 Vault 进行问答。

---

### 方案二：Text Generator（笔记内联生成与 Prompt 模版）

适合在写笔记时按快捷键就地补全、总结、提取要点或批量执行 Prompt 模版。

1. **配置 Text Generator**：
   - 在 Obsidian 设置 -> **Community plugins** -> 安装 **Text Generator**。
   - 打开 Text Generator 设置：
     - **Provider**：选择 `Custom` (或 `OpenAI Compatible`)
     - **Endpoint**：`http://localhost:1234/v1/chat/completions` (或 `http://localhost:1234/v1`)
     - **API Key**：任意填写（例如 `lm-studio`）
     - **Model**：填写 LM Studio 中加载的模型名称
2. **使用方式**：
   - 选中文本或在光标处按下快捷键（默认 `Cmd/Ctrl + J`），即可调用本地模型自动补全或处理内容。
   - 支持在模板目录中创建自定义 Prompt，一键格式化印象笔记转过来的内容。

---

### 方案三：命令行直接向知识库提问（免安装 Obsidian 插件）

本仓库内置了轻量级本地 RAG 问答脚本（基于纯 Python 3 标准库，零三方依赖，自动分块、BM25 混合检索并直连 LM Studio 本地流式输出）：

1. **启动 LM Studio**：开启 Local Server（默认端口 `1234`）并加载模型。
2. **终端直接提问**：
   ```bash
   # 带参数直接提问
   make ask Q="知识库里有哪些关于架构设计的笔记？"

   # 或进入交互式输入
   make ask
   ```
3. **可选自定义配置**（在 `.env` 中）：
   ```env
   LMSTUDIO_HOST=http://localhost:1234
   LMSTUDIO_MODEL=qwen2.5-7b-instruct
   ```
   > 若不配置 `LMSTUDIO_MODEL`，脚本会自动检测并使用 LM Studio 当前激活的模型。
---

### 附：在 Obsidian 里挂载一键同步按钮 (可选)

配合 **Shell Commands** 插件或自定义命令：
1. 新建一条命令（使用脚本绝对路径或 `~` 路径）：
   ```bash
   bash ~/path/to/KnowledgeBase/scripts/sync.sh
   ```
2. 绑定快捷键或侧边栏按钮即可在 Obsidian 内部一键触发拉取印象笔记。
