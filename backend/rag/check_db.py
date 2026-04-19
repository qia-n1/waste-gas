from simple_vector_db import SimpleVectorDB

# 加载你建好的向量库
db = SimpleVectorDB("./vector_db/rto_spec.pkl")

# 打印总条数
print(f"\n✅ 向量库总文本块数量：{len(db.chunks)}")
print("=" * 60)

# 打印前 5 条内容（看看是不是你PDF里的标准）
print("\n【前 5 条内容预览】\n")
for i, chunk in enumerate(db.chunks[:5]):
    print(f"[{i+1}] {chunk[:150]}...")
    print("-" * 50)

# 做一次查询，看看能不能搜到
print("\n【测试查询：RTO 燃烧室温度】\n")
results = db.query("RTO 燃烧室温度要求", top_k=2)

for i, r in enumerate(results):
    print(f"结果 {i+1} | 相似度：{r['score']:.4f}")
    print(r["text"])
    print("-" * 50)