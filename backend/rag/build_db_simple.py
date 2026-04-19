"""
RAG 向量库构建工具 - 强制切块版（解决无换行只切1块问题）
带注释 + 打印日志
"""
import os
import re
import pickle
import numpy as np
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ====================== 配置 ======================
DEFAULT_FILE_DIR = "./ziliao"
DEFAULT_OUTPUT_DIR = "./vector_db"
MODEL_PATH = "../models/bge-large-zh"
VECTOR_DB_NAME = "rto_spec"

# ======================================================

def read_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        print(f"   └── 成功提取文本长度：{len(text)}")
        return text
    except:
        return ""

def read_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except:
        return ""

def read_docx(docx_path):
    try:
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except:
        return ""

def load_all_files(dir_path):
    print("\n========================================")
    print("📂 读取资料文件夹：", dir_path)
    print("========================================")
    all_text = ""
    files = os.listdir(dir_path)
    count = 0
    for f in files:
        path = os.path.join(dir_path, f)
        if f.lower().endswith(".pdf"):
            print(f"\n→ 读取PDF：{f}")
            all_text += read_pdf(path) + "\n\n"
            count +=1
        elif f.lower().endswith(".txt"):
            print(f"\n→ 读取TXT：{f}")
            all_text += read_txt(path) + "\n\n"
            count +=1
        elif f.lower().endswith(".docx"):
            print(f"\n→ 读取DOCX：{f}")
            all_text += read_docx(path) + "\n\n"
            count +=1
    print(f"\n✅ 共读取 {count} 个文件")
    print(f"📝 总文本长度：{len(all_text)}")
    return all_text

def clean_text(text):
    print("\n🧹 清理文本")
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r' +', ' ', text)  # 这里修复了！
    return text.strip()

# ======================
# 【修复】强制切块，不依赖换行！
# ======================
def split_fixed_chunks(text, chunk_size=500, overlap=100):
    print(f"\n✂️ 强制切块（大小：{chunk_size}，重叠：{overlap}）")
    chunks = []
    i = 0
    total = len(text)
    while i < total:
        chunk = text[i:i+chunk_size]
        if len(chunk) >= 100:
            chunks.append(chunk.strip())
        i += (chunk_size - overlap)
    print(f"✅ 切块完成：{len(chunks)} 块")
    return chunks

def deduplicate(chunks):
    print("\n🔍 去重中...")
    seen = set()
    res = []
    for c in chunks:
        key = c.strip()
        if key not in seen:
            seen.add(key)
            res.append(c)
    print(f"✅ 去重前：{len(chunks)} → 去重后：{len(res)}")
    return res

def save_db(chunks, embeddings, out_dir, name):
    print("\n💾 保存向量库...")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.pkl")
    data = {"chunks": chunks, "embeddings": embeddings}
    with open(path, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ 保存到：{path}")

def test_query(chunks, embeddings, model):
    print("\n========================================")
    print("🧪 测试查询")
    print("========================================")
    qs = [
        "RTO燃烧室温度要求",
        "VOCs浓度超标怎么办",
        "蓄热体堵塞怎么处理",
        "RTO运行参数标准"
    ]
    for q in qs:
        print(f"\n🔍 {q}")
        q_emb = model.encode([q])[0]
        scores = []
        for emb in embeddings:
            score = np.dot(q_emb, emb) / (np.linalg.norm(q_emb) * np.linalg.norm(emb))
            scores.append(score)
        top2 = np.argsort(scores)[-2:][::-1]
        for i, idx in enumerate(top2):
            print(f"  {i+1}. {chunks[idx][:180]}...")

def main():
    print("="*50)
    print("🚀 RAG 向量库构建工具（强制切块修复版）")
    print("="*50)

    # 1. 读取文件
    raw = load_all_files(DEFAULT_FILE_DIR)
    if len(raw) < 100:
        print("❌ 文本太短，读取失败")
        return

    # 2. 清理
    cleaned = clean_text(raw)

    # 3. 强制切块（关键修复）
    chunks = split_fixed_chunks(cleaned, chunk_size=500, overlap=100)
    if len(chunks) == 0:
        print("❌ 无有效文本块")
        return

    # 4. 去重
    chunks = deduplicate(chunks)

    # 5. 生成向量
    print("\n🤖 生成向量中...")
    model = SentenceTransformer(MODEL_PATH)
    embeddings = model.encode(chunks, show_progress_bar=True, convert_to_numpy=True)

    # 6. 保存
    save_db(chunks, embeddings, DEFAULT_OUTPUT_DIR, VECTOR_DB_NAME)

    # 7. 查询测试
    test_query(chunks, embeddings, model)

    print("\n" + "="*50)
    print("🎉 全部完成！正常切块 → 可以正常搜索！")
    print("="*50)

if __name__ == "__main__":
    main()