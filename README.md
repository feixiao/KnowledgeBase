# KnowledgeBase (个人知识库)

基于 **Markdown + Git + 印象笔记双向联动 + Obsidian / VS Code 双核 + 本地 RAG** 构建的个人工程技术知识库。

---

## 📁 目录拓扑与规范

```text
KnowledgeBase/
├── 00_Inbox/                # [速记] 本地随时记录的零散想法与草稿
├── 10_Core/                 # [核心] 架构方案、Dev Wiki、技术踩坑 (RAG 核心索引区)
├── 20_Evernote/             # [印象笔记镜像]
│   ├── Active/              # 从印象笔记同步过来的活跃笔记 (进入 RAG 索引)
│   └── Archives/            # 历史纯网页剪藏、陈旧资料 (RAG 排除该目录以隔离噪音)
├── assets/                  # 全局附件与图片资源库
├── scripts/                 # 自动化同步与运维脚本
│   ├── init-auth.sh         # 印象笔记首次授权引导
│   └── sync.sh              # 增量拉取 + 转 Markdown + 整理附件流水线
├── Makefile                 # 极简终端操作入口
└── yarle-config.json        # Evernote ENEX -> Obsidian Markdown 高保真转换规则
```

---

## 🚀 快速上手与日常流

### 1. 先决条件
- **uv** (已具备): 用于零安装运行 `evernote-backup`
- **Node.js** (已具备): 用于运行 `yarle` 格式转换器
- **Obsidian**: 作为主阅读与 RAG 交互界面
- **VS Code**: 作为批量工程重构与代码编辑工具

### 2. 首次初始化 (仅需一次)
在终端运行授权命令，绑定你的印象笔记（中国区后端）：
```bash
make init-auth
```
> 会提示输入账号密码或通过浏览器完成 OAuth 授权，授权凭证保存在本地 `.evernote/data.db`（已被 Git 忽略，绝对安全）。

### 3. 日常一键增量同步
当在手机端或网页用印象笔记记录了新内容后，终端执行：
```bash
make sync
```
脚本会自动：
1. 增量抓取印象笔记变动至本地数据库
2. 导出为 ENEX 中间格式
3. 通过 Yarle 转换为 Obsidian 规范的 Markdown，自动提取图片到 `assets/`，保存到 `20_Evernote/Active/`

---

## 🧠 Obsidian 与 Smart Connections (RAG) 配置推荐

1. **打开知识库**：
   - 打开 Obsidian -> `Open folder as vault` -> 选择当前 `KnowledgeBase` 文件夹。

2. **安装并配置 Smart Connections 插件**：
   - 在 Obsidian 设置 -> **Community plugins** -> 搜索并安装 **Smart Connections**。
   - **Embedding 设置 (向量模型)**：
     - 选择 **Built-in / Local**（内置轻量模型，在 Mac 本地极速计算，无需消耗 API）。
   - **Chat 设置 (对话与智能问答)**：
     - 选择 **Custom OpenAI Compatible**。
     - 填入你的自定义 API 网关 URL 与 API Key（如接入 DeepSeek / 硅基流动等）。
   - **文件过滤与排除 (极其关键)**：
     - 在 Smart Connections 的 **Exclusions**（排除路径）中添加：
       ```text
       20_Evernote/Archives
       ```
     - 这样大体积的历史网页剪藏不会污染技术问答上下文。

3. **在 Obsidian 里加一个“一键同步”按钮 (可选)**：
   - 安装 Community plugin: **Shell Commands**。
   - 新建一条命令：`bash /Users/frank/wk/github/KnowledgeBase/scripts/sync.sh`。
   - 绑定到侧边栏图标或快捷键（如 `Cmd + Shift + S`）。

---

## 🔒 Git 版本控制原则

- **追踪**：所有 Markdown 笔记、目录结构规范、以及中小型图片资源。
- **忽略**：`.evernote/` 数据库、临时 `*.enex` 导出品、Obsidian 本地工作区状态与向量缓存索引（`.smart-connections/`）。
