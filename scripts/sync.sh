#!/usr/bin/env bash
set -euo pipefail

# Project root directory resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Load .env if present
if [ -f "${PROJECT_ROOT}/.env" ]; then
  # export variables from .env
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
fi

VAULT_DIR="${VAULT_DIR:-${PROJECT_ROOT}/../KnowledgeVault}"
# Expand tilde if present
VAULT_DIR="${VAULT_DIR/#\~/$HOME}"

DB_DIR="${PROJECT_ROOT}/.evernote"
DB_FILE="${DB_DIR}/data.db"
ENEX_DIR="${DB_DIR}/enex"
RUNTIME_CONFIG="${DB_DIR}/yarle-runtime.json"

echo "==> [1/5] 检查同步先决条件与数据仓库..."
echo "  - 代码工程根目录: ${PROJECT_ROOT}"
echo "  - 数据仓库目标路径: ${VAULT_DIR}"

if [ ! -d "${VAULT_DIR}" ]; then
  echo "⚠️ 目标数据仓库目录不存在，正在自动初始化: ${VAULT_DIR}"
  mkdir -p "${VAULT_DIR}"
fi

mkdir -p "${DB_DIR}" "${ENEX_DIR}"
mkdir -p "${VAULT_DIR}/00_Inbox"
mkdir -p "${VAULT_DIR}/10_Core"
mkdir -p "${VAULT_DIR}/20_Evernote/Active"
mkdir -p "${VAULT_DIR}/20_Evernote/Archives"
mkdir -p "${VAULT_DIR}/assets"

if [ ! -f "${DB_FILE}" ]; then
  echo "❌ 错误: 未检测到本地授权数据库 (.evernote/data.db)"
  echo "请先运行一次授权命令完成印象笔记国内版登录绑定："
  echo "  make init-auth"
  echo "  或者: uvx evernote-backup init-db --backend china --database .evernote/data.db"
  exit 1
fi

echo "==> [2/5] 从印象笔记云端增量拉取笔记 (evernote-backup sync)..."
uvx evernote-backup sync --database "${DB_FILE}"

echo "==> [3/5] 导出本地 ENEX 文件 (evernote-backup export)..."
uvx evernote-backup export --database "${DB_FILE}" "${ENEX_DIR}"

echo "==> [4/5] 动态生成 Yarle 转换配置..."
cat <<EOF > "${RUNTIME_CONFIG}"
{
  "enexSources": [
    "${ENEX_DIR}"
  ],
  "templateFile": "",
  "currentTemplate": "",
  "outputDir": "${VAULT_DIR}/20_Evernote/Active",
  "keepOriginalHtml": false,
  "isMetadataNeeded": true,
  "isTagsNeeded": true,
  "isZettelkastenNeeded": false,
  "plainTextNotesOnly": false,
  "skipImages": false,
  "skipWebClips": false,
  "useHashTags": false,
  "outputFormat": "ObsidianMD",
  "skipEnexFileNameFromImagePath": true,
  "nestedTags": {
    "separatorInEN": "_",
    "replaceSeparatorWith": "/"
  },
  "resourcesDir": "../../assets",
  "turndown": {
    "headingStyle": "atx",
    "hr": "---",
    "bulletListMarker": "-",
    "codeBlockStyle": "fenced"
  },
  "keepOriginalDate": true,
  "addExtension": false,
  "generateNLink": false
}
EOF

echo "==> [5/5] 转换为 Obsidian 高保真 Markdown 与资源迁移 (yarle)..."
npx --yes @yarle/yarle --configFile "${RUNTIME_CONFIG}"

echo ""
echo "✅ 同步完成！"
echo "  - Markdown 输出路径: ${VAULT_DIR}/20_Evernote/Active"
echo "  - 媒体附件输出路径: ${VAULT_DIR}/assets"
echo "  - 提示: 历史/低频网页剪藏可手动移至 ${VAULT_DIR}/20_Evernote/Archives 以免影响 RAG 检索。"
