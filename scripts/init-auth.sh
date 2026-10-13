#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Load .env if present
if [ -f "${PROJECT_ROOT}/.env" ]; then
  set -a
  source "${PROJECT_ROOT}/.env"
  set +a
fi

DB_DIR="${PROJECT_ROOT}/.evernote"
DB_FILE="${DB_DIR}/data.db"

mkdir -p "${DB_DIR}"

echo "=========================================================="
echo "  印象笔记（中国区）首次授权向导"
echo "=========================================================="
echo "由于印象笔记国内版接口特性，需要通过账号密码进行初次凭证获取。"
echo "凭证将保存在本地安全的 .evernote/data.db 中（已被 gitignore）。"
echo ""

YX_USER="${EVERNOTE_USER:-}"
YX_PASS="${EVERNOTE_PASSWORD:-}"

if [ -z "${YX_USER}" ]; then
  read -r -p "请输入印象笔记账号 (注册邮箱或绑定的手机号): " YX_USER
fi

if [ -z "${YX_PASS}" ]; then
  read -r -s -p "请输入印象笔记密码: " YX_PASS
  echo ""
fi

if [ -z "${YX_USER}" ] || [ -z "${YX_PASS}" ]; then
  echo "❌ 账号或密码不能为空！"
  exit 1
fi

echo ""
echo "==> 正在连接印象笔记服务器获取授权 Token..."
uvx evernote-backup init-db --backend china --database "${DB_FILE}" --user "${YX_USER}" --password "${YX_PASS}"

echo ""
echo "✅ 授权信息已成功持久化至: ${DB_FILE}"
echo "后续无需再输入密码，直接执行 'make sync' 即可进行增量同步。"
