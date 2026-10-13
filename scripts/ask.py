#!/usr/bin/env python3
"""
KnowledgeBase 命令行本地 RAG 问答脚本
直连 LM Studio (OpenAI Compatible API)，基于知识库笔记检索增强生成回答。
零三方依赖，仅使用 Python 3 标准库。
"""

import os
import sys
import json
import math
import re
from pathlib import Path
import urllib.request
import urllib.error

# ---------------------------------------------------------
# 配置读取与环境变量解析
# ---------------------------------------------------------
def load_env(env_path: Path):
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_env(PROJECT_ROOT / ".env")

VAULT_DIR_RAW = os.getenv("VAULT_DIR", "~/Documents/KnowledgeVault")
VAULT_DIR = Path(os.path.expanduser(VAULT_DIR_RAW)).resolve()

LMSTUDIO_HOST = os.getenv("LMSTUDIO_HOST", "http://localhost:1234").rstrip("/")
LMSTUDIO_API_URL = f"{LMSTUDIO_HOST}/v1/chat/completions"
LMSTUDIO_MODELS_URL = f"{LMSTUDIO_HOST}/v1/models"
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "")

# 排除检索的低价值/噪音目录（相对于 VAULT_DIR）
EXCLUDED_DIRS = {
    "20_Evernote/Archives",
    ".obsidian",
    ".trash",
    ".git",
    "assets",
}

# ---------------------------------------------------------
# 文本切块与 BM25 检索算法 (零依赖纯 Python 实现)
# ---------------------------------------------------------
def tokenize(text: str):
    """
    中英文混合分词：
    英文按单词分词并小写化；中文按单字/双字切分以提高字符级召回。
    """
    text = text.lower()
    # 提取英文与数字
    en_tokens = re.findall(r"[a-z0-9_]+", text)
    # 提取中文字符
    cn_chars = re.findall(r"[\u4e00-\u9fa5]", text)
    cn_bigrams = [cn_chars[i] + cn_chars[i+1] for i in range(len(cn_chars)-1)]
    return en_tokens + cn_chars + cn_bigrams

class SimpleBM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avg_dl = sum(self.doc_lengths) / (len(corpus) or 1)
        self.doc_count = len(corpus)
        
        # 统计词频与倒排
        self.df = {}
        self.doc_freqs = []
        for doc in corpus:
            freq = {}
            for token in doc:
                freq[token] = freq.get(token, 0) + 1
            self.doc_freqs.append(freq)
            for token in freq:
                self.df[token] = self.df.get(token, 0) + 1
        
        # 计算 IDF
        self.idf = {}
        for token, freq in self.df.items():
            self.idf[token] = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1)

    def get_scores(self, query_tokens):
        scores = [0.0] * self.doc_count
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf = self.idf[token]
            for i, freq_map in enumerate(self.doc_freqs):
                tf = freq_map.get(token, 0)
                if tf == 0:
                    continue
                num = tf * (self.k1 + 1)
                denom = tf + self.k1 * (1 - self.b + self.b * (self.doc_lengths[i] / (self.avg_dl or 1)))
                scores[i] += idf * (num / denom)
        return scores

# ---------------------------------------------------------
# 知识库索引与分块
# ---------------------------------------------------------
class KnowledgeChunk:
    def __init__(self, file_path: Path, rel_path: str, chunk_index: int, content: str):
        self.file_path = file_path
        self.rel_path = rel_path
        self.chunk_index = chunk_index
        self.content = content
        self.tokens = tokenize(content)

def load_vault_chunks(vault_dir: Path, chunk_size=800, overlap=100):
    chunks = []
    if not vault_dir.exists():
        return chunks

    for root, dirs, files in os.walk(vault_dir):
        rel_root = os.path.relpath(root, vault_dir)
        # 排除指定目录
        if any(rel_root == ex or rel_root.startswith(ex + os.sep) for ex in EXCLUDED_DIRS):
            continue

        for file in files:
            if not file.endswith(".md"):
                continue
            file_path = Path(root) / file
            rel_file = os.path.relpath(file_path, vault_dir)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read().strip()
                if not text:
                    continue

                # 按段落与长度切块
                paras = text.split("\n\n")
                curr = []
                curr_len = 0
                idx = 0

                for para in paras:
                    p = para.strip()
                    if not p:
                        continue
                    if curr_len + len(p) > chunk_size and curr:
                        chunk_text = "\n\n".join(curr)
                        chunks.append(KnowledgeChunk(file_path, rel_file, idx, chunk_text))
                        idx += 1
                        # 保留部分重叠段落
                        curr = [curr[-1]] if len(curr) > 1 else []
                        curr_len = sum(len(x) for x in curr)
                    curr.append(p)
                    curr_len += len(p)

                if curr:
                    chunk_text = "\n\n".join(curr)
                    chunks.append(KnowledgeChunk(file_path, rel_file, idx, chunk_text))

            except Exception:
                continue

    return chunks

# ---------------------------------------------------------
# LM Studio 请求与交互
# ---------------------------------------------------------
def get_lmstudio_model(default_model: str) -> str:
    """如果未显式配置模型名称，尝试从 LM Studio 接口拉取当前加载的模型"""
    if default_model:
        return default_model
    try:
        req = urllib.request.Request(LMSTUDIO_MODELS_URL, headers={"User-Agent": "KnowledgeBase-CLI"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]["id"]
    except Exception:
        pass
    return "local-model"

def stream_chat(prompt: str, context_chunks: list, model: str):
    """构建提示词并发起流式请求"""
    context_str = ""
    for i, c in enumerate(context_chunks, 1):
        context_str += f"\n--- [文档片段 {i}] (来源: {c.rel_path}) ---\n{c.content}\n"

    system_prompt = (
        "你是一个严谨的本地个人知识库助手。"
        "请根据下面提供的参考文档回答用户的问题。"
        "要求：\n"
        "1. 回答应紧扣提供的参考文档事实，不要编造未提及的内容；\n"
        "2. 若参考文档中信息不足以回答问题，请如实告知；\n"
        "3. 在回答时，若引用了片段，可以在文末注明来源文件相对路径。\n"
    )

    user_message = f"【参考文档】：\n{context_str}\n\n【用户问题】：\n{prompt}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3,
        "stream": True
    }

    req = urllib.request.Request(
        LMSTUDIO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data: "):
                    continue
                data_part = line[6:]
                if data_part == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_part)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        sys.stdout.write(content)
                        sys.stdout.flush()
                except Exception:
                    continue
            print()
    except urllib.error.URLError as e:
        print(f"\n❌ 连接 LM Studio 失败: {e.reason}")
        print(f"👉 请确保 LM Studio 已启动，并已在 Developer 界面开启 Local Server (地址: {LMSTUDIO_HOST})。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 请求出错: {e}")
        sys.exit(1)

# ---------------------------------------------------------
# 主入口
# ---------------------------------------------------------
def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("KnowledgeBase 本地 RAG 问答命令行工具")
        print("\n用法:")
        print("  python3 scripts/ask.py \"你的问题\"")
        print("  make ask Q=\"你的问题\"")
        print("  直接运行交互式提问: make ask")
        sys.exit(0)

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("💡 请输入要向知识库提问的问题: ").strip()
    if not query:
        print("问题不能为空。")
        sys.exit(0)

    if not VAULT_DIR.exists():
        print(f"⚠️ Vault 目录不存在: {VAULT_DIR}")
        print("请检查 .env 中的 VAULT_DIR 配置。")
        sys.exit(1)

    print(f"🔍 正在扫描知识库 ({VAULT_DIR})...", flush=True)
    chunks = load_vault_chunks(VAULT_DIR)
    if not chunks:
        print("⚠️ 知识库中未找到 Markdown 笔记，请先运行 make sync 同步数据。")
        sys.exit(0)

    corpus = [c.tokens for c in chunks]
    bm25 = SimpleBM25(corpus)
    q_tokens = tokenize(query)
    scores = bm25.get_scores(q_tokens)

    # 选取分数最高的 Top-5 片段
    scored_chunks = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    top_chunks = [c for c, score in scored_chunks[:5] if score > 0]

    model_name = get_lmstudio_model(LMSTUDIO_MODEL)

    print(f"🤖 目标模型: {model_name}")
    if top_chunks:
        print(f"📄 命中了 {len(top_chunks)} 个相关文档片段:")
        seen_files = set()
        for c in top_chunks:
            if c.rel_path not in seen_files:
                print(f"   • {c.rel_path}")
                seen_files.add(c.rel_path)
    else:
        print("ℹ️ 未找到强相关段落，将直接由模型根据通用知识或空上下文回答。")

    print("\n" + "="*50 + "\n")
    stream_chat(query, top_chunks, model_name)
    print("\n" + "="*50)

if __name__ == "__main__":
    main()
