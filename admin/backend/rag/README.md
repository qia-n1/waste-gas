# RAG 模块使用说明

RAG (Retrieval-Augmented Generation) 模块用于 VOCs 告警智能诊断，结合向量检索和大模型生成处置建议。

## 目录结构

```
rag/
├── __init__.py              # 包初始化，导出主要函数
├── rag_service.py           # 主服务：智能诊断入口
├── simple_vector_db.py      # 向量数据库：轻量级向量检索
├── build_db_simple.py       # 构建脚本：从文档生成向量库
├── check_db.py              # 检查脚本：验证向量库状态
├── download-model.py        # 模型下载：下载BGE嵌入模型
├── models/                  # 存放BGE模型（需自行下载）
│   └── bge-large-zh/        # 中文语义嵌入模型
├── vector_db/               # 存放向量库文件
│   └── rto_spec.pkl         # RTO设备规范向量库
└── ziliao/                  # 原始文档资料
    └── (放PDF/Word/TXT文档)
```

## 文件说明

### 1. rag_service.py
**功能**：对外提供智能诊断服务  
**核心函数**：`get_warning_diagnose(vocs, shap_reason, shap_score)`

```python
from rag import get_warning_diagnose

result = get_warning_diagnose(
    vocs="95.5",                    # VOCs浓度值
    shap_reason="燃烧温度偏低",      # SHAP分析的核心诱因
    shap_score="65%"                # 贡献度分数
)
```

**返回结果**：
```json
{
  "level": "warning/danger",
  "title": "故障标题",
  "reason": "核心诱因",
  "suggestion_short": "一句话建议",
  "sop_steps": ["步骤1", "步骤2", "步骤3"],
  "standard": "GB 16297-1996",
  "safety_redline": "安全红线提示",
  "component_id": "system"
}
```

---

### 2. simple_vector_db.py
**功能**：轻量级向量数据库，替代Chroma  
**原理**：使用余弦相似度进行向量检索  
**存储格式**：pickle文件（.pkl）

---

### 3. build_db_simple.py
**功能**：从原始文档构建向量库  
**支持格式**：PDF、Word(docx)、TXT

---

### 4. check_db.py
**功能**：检查向量库状态  
**用途**：验证向量库是否正常加载

---

### 5. download-model.py
**功能**：下载BGE中文嵌入模型

## 首次使用步骤

### 第一步：下载BGE模型

```bash
cd admin/backend/rag
python download-model.py
```

或手动下载：
```bash
# 安装git-lfs后
git lfs install
git clone https://huggingface.co/BAAI/bge-large-zh models/bge-large-zh
```

**模型大小**：约1.2GB  
**下载时间**：取决于网络，约5-10分钟

---

### 第二步：准备原始文档

将RTO设备规范、操作手册等文档放入 `ziliao/` 目录：

```
ziliao/
├── RTO操作手册.pdf
├── 设备维护规范.docx
├── 应急处理流程.txt
└── ...
```

---

### 第三步：构建向量库

```bash
python build_db_simple.py
```

**构建过程**：
1. 读取 `ziliao/` 目录所有文档
2. 使用BGE模型将文本转为向量
3. 保存到 `vector_db/rto_spec.pkl`

**耗时**：取决于文档数量，通常1-5分钟

---

### 第四步：检查向量库

```bash
python check_db.py
```

正常输出示例：
```
[加载] 向量库: vector_db/rto_spec.pkl
  - 文本块数量: 156
  - 向量维度: 1024
[加载] 模型: models/bge-large-zh
✅ 向量库检查通过！
```

---

## 日常使用

### 方式一：直接运行测试

```bash
cd admin/backend/rag
python rag_service.py
```

这会运行文件底部的测试代码，输出生成的诊断卡片。

### 方式二：作为模块导入

```python
import sys
sys.path.insert(0, 'rag')
from rag_service import get_warning_diagnose

result = get_warning_diagnose("92.5", "引风机异常", "78%")
print(result)
```

### 方式三：后端API调用

管理端后端已集成到告警诊断API：
```
GET http://localhost:8003/api/alerts/{alert_id}/diagnosis
```

## 常见问题

### Q1: 模型加载报错 `DLL load failed`
**原因**：Windows缺少Visual C++运行库  
**解决**：安装 https://aka.ms/vs/17/release/vc_redist.x64.exe

### Q2: `向量库未加载` 错误
**原因**：vector_db/rto_spec.pkl 不存在  
**解决**：运行 `python build_db_simple.py` 构建向量库

### Q3: 诊断结果都是兜底方案
**原因**：LLM API Key未配置或失效  
**解决**：
1. 在 `admin/backend` 目录创建 `.env` 文件
2. 写入：`LLM_API_KEY=你的API密钥`
3. 重启后端服务

### Q4: 如何更新知识库？
1. 将新文档放入 `ziliao/` 目录
2. 重新运行 `python build_db_simple.py`
3. 向量库会自动覆盖更新

## 依赖安装

```bash
pip install sentence-transformers openai python-dotenv numpy
```

如需GPU加速（可选）：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
