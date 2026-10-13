# KnowledgeBase (知识库运维与工具链代码仓库)

本仓库为**纯代码与工具链工程**，负责管理数据同步、格式转换与自动化运维流水线。
知识库的真实数据（Markdown、图片、Obsidian Vault）独立存放于专门的数据仓库中，实现**代码与数据物理隔离**。

---

## 🏗️ 架构拓扑 (双仓库解耦)

```text
/Users/frank/
├── wk/github/KnowledgeBase/           # [当前代码仓库] 纯工具链与流水线
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
在 `.env` 中确认 `VAULT_DIR`（默认已指向 `~/Documents/KnowledgeVault`）：
```env
VAULT_DIR=/Users/frank/Documents/KnowledgeVault
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

## 🧠 Obsidian 与 Smart Connections (RAG) 配置说明

1. **打开数据仓库**：
   - 打开 Obsidian -> `Open folder as vault` -> 选择目标目录（例如 `~/Documents/KnowledgeVault`）。

2. **安装并配置 Smart Connections 插件**：
   - 在 Obsidian 设置 -> **Community plugins** -> 安装 **Smart Connections**。
   - **Embedding 设置**：选择 **Built-in / Local**（内置轻量模型，在 Mac 本地极速计算，无需消耗 API）。
   - **Chat 设置**：选择 **Custom OpenAI Compatible**，填入你的 API Gateway URL 与 Key。
   - **文件过滤与排除 (降噪)**：
     - 在 Exclusions 排除项中添加：`20_Evernote/Archives`。

3. **在 Obsidian 里挂载一键同步按钮 (可选)**：
   - 安装插件 **Shell Commands**，添加命令：
     ```bash
     bash /Users/frank/wk/github/KnowledgeBase/scripts/sync.sh
     ```
   - 绑定快捷键或侧边栏按钮即可在 Obsidian 内部一键触发拉取。
