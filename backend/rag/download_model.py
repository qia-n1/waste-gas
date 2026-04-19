from sentence_transformers import SentenceTransformer

# 下载模型
model = SentenceTransformer("BAAI/bge-large-zh")

# 保存到你项目的 models 文件夹
model.save("./models/bge-large-zh")