.PHONY: help init-auth sync clean

help:
	@echo "KnowledgeBase 常用操作指令:"
	@echo "  make init-auth  - 首次运行：登录并授权印象笔记（国内版）"
	@echo "  make sync       - 增量拉取印象笔记并转为 Obsidian Markdown"
	@echo "  make clean      - 清理本地临时 ENEX 文件缓存"

init-auth:
	@./scripts/init-auth.sh

sync:
	@./scripts/sync.sh

clean:
	@rm -rf .evernote/enex/*
	@echo "✅ 临时 ENEX 文件已清理"
