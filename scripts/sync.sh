#!/usr/bin/env bash
set -euo pipefail

# Project root directory resolution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

DB_DIR="${PROJECT_ROOT}/.evernote"
DB_FILE="${DB_DIR}/data.db"
ENEX_DIR="${DB_DIR}/enex"
CONFIG_FILE="${PROJECT_ROOT}/yarle-config.json"

echo "==> [1/4] 检查同步先决条件..."
mkdir -p "${DB_DIR}" "${ENEX_DIR}" "20_Evernote/Active" "20_Evernote/Archives" "assets"

if [ ! -f "${DB_FILE}" ]; then
  echo "❌ 错误: 未检测到本地授权数据库 (.evernote/data.db)"
  echo "请先运行一次授权命令完成印象笔记国内版登录绑定："
  echo "  make init-auth"
  或者: uvx evernote-backup init-db --backend china --database .evernote/data.db
  exit 1
fi

echo "==> [2/4] 从印象笔记云端增量拉取笔记 (evernote-backup sync)..."
uvx evernote-backup sync --database "${DB_FILE}"

echo "==> [3/4] 导出本地 ENEX 文件 (evernote-backup export)..."
uvx evernote-backup export --database "${DB_FILE}" "${ENEX_DIR}"

echo "==> [4/4] 转换为 Obsidian 高保真 Markdown 与资源迁移 (yarle)..."
npx --yes @yarle/yarle --configFile "${CONFIG_FILE}"

echo ""
echo "✅ 同步完成！"
echo "  - Markdown 输出路径: 20_Evernote/Active"
echo "  - 媒体附件输出路径: assets/"
echo "  - 提示: 历史/低频网页剪藏可手动移至 20_Evernote/Archives 以免影响 RAG 检索。"
