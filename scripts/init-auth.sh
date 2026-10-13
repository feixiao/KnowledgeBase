#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

DB_DIR="${PROJECT_ROOT}/.evernote"
DB_FILE="${DB_DIR}/data.db"

mkdir -p "${DB_DIR}"

echo "=========================================================="
echo "  印象笔记（中国区）首次授权向导"
echo "=========================================================="
echo "即将调用 evernote-backup 与国内印象笔记后端交互。"
echo "请按终端提示在浏览器完成登录与授权。"
echo ""

uvx evernote-backup init --backend china --database "${DB_FILE}"

echo ""
echo "✅ 授权信息已成功持久化至: ${DB_FILE}"
echo "后续可直接执行 'make sync' 进行增量同步。"
