from sentence_transformers import SentenceTransformer
import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from simple_vector_db import SimpleVectorDB

# ==============================
# 0. 加载环境配置
# ==============================
load_dotenv()
print("🔧 正在加载环境配置...")

API_KEY = os.getenv("LLM_API_KEY", "")
API_BASE = os.getenv("LLM_API_BASE", "https://api.deepseek.com")
MODEL_NAME = os.getenv("LLM_MODEL", "deepseek-chat")

VECTOR_DB_PATH = "./vector_db/rto_spec.pkl"

try:
    llm_client = OpenAI(api_key=API_KEY, base_url=API_BASE)
    print("✅ LLM客户端初始化完成")
except Exception as e:
    print(f"❌ LLM客户端初始化失败: {str(e)}")
    llm_client = None

# ==============================
# 1. 加载本地模型 & 向量库
# ==============================
print("\n🚀 正在加载本地BGE模型...")
try:
    model = SentenceTransformer("../models/bge-large-zh")
    print("✅ 本地模型加载完成")
except Exception as e:
    print(f"❌ 模型加载失败: {str(e)}")
    model = None

print("\n🔗 正在连接本地向量库...")
try:
    vector_db = SimpleVectorDB(VECTOR_DB_PATH)
    print("✅ 向量库连接成功")
except Exception as e:
    print(f"❌ 向量库连接失败: {str(e)}")
    vector_db = None

# ==============================
# 2. 核心检索函数
# ==============================
def retrieve_docs(question, top_k=2):
    if vector_db is None:
        return ""
    try:
        
        results = vector_db.query(question, top_k=top_k)
        return "\n".join([r["text"] for r in results])
    except Exception as e:
        print(f"⚠️ 检索出错: {e}")
        return ""

# ==============================
# 【优化】事实一致性检查
# ==============================
def clean_sop_steps(steps):
    cleaned = []
    forbidden = ["必须", "立即", "强行", "直接", "绝对", "禁止"]
    for step in steps:
        if not any(word in step for word in forbidden):
            cleaned.append(step)
    while len(cleaned) < 3:
        cleaned.append("持续监测VOCs浓度变化")
    return cleaned[:3]

# ==============================
# 🏆【最终版】预警诊断卡片生成器
# ==============================
def get_warning_diagnose(vocs, shap_reason, shap_score):
    print(f"\n📊 正在处理告警逻辑 | VOCs: {vocs} | 诱因: {shap_reason}")

    # 1. 语义检索
    query = f"VOCs浓度{vocs}超标，{shap_reason}的处理方案"
    context = retrieve_docs(query)

    
    print("=" * 80)
    print("🔍 RAG 检索到的知识库内容：")
    print(context if context else "⚠️ 未检索到内容，使用通用规范")
    print("=" * 80)

    # 2. 系统提示
    system_prompt = (
        "你是化工园区VOCs治理与RTO设备运维辅助顾问，仅提供**参考性处置建议**。"
        "回答严谨保守，不做绝对化判断、不编造数据、不超出行业通用规范。"
        "若无足够信息，基于通用规范给出保守建议。"
        "请严格输出标准JSON，**不输出任何多余文字**，遵守键值对规范。"
    )

    user_prompt = f"""
【实时工况】
- VOCs浓度：{vocs} mg/m³
- SHAP核心诱因：{shap_reason}（贡献度：{shap_score}）

【参考知识库】
{context if context else "参考GB 16297-1996及行业通用规范"}

请按以下格式输出JSON：
{{
  "title": "简短故障标题",
  "suggestion_short": "一句话核心处置建议",
  "sop_steps": ["步骤1", "步骤2", "步骤3"]
}}
"""

    fallback_data = {
        "level": "warning",
        "title": "VOCs浓度异常告警",
        "reason": shap_reason,
        "suggestion_short": "请立即核实传感器读数并检查相关设备",
        "sop_steps": ["检查设备运行状态", "观察浓度趋势", "手动监测浓度"],
        "standard": "GB 16297-1996",
        "safety_redline": "异常持续请执行紧急停机",
        "component_id": "system"
    }

    if not llm_client:
        return fallback_data

    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        result_json = json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"❌ AI生成失败，启动兜底逻辑: {e}")
        return fallback_data

    vocs_float = float(vocs)
    if vocs_float > 100:
        level = "danger"
        title = "VOCs浓度严重超标"
    else:
        level = "warning"
        title = "VOCs浓度异常偏高"

    result_json["sop_steps"] = clean_sop_steps(result_json.get("sop_steps", []))

    return {
        "level": level,
        "title": title,
        "reason": shap_reason,
        "suggestion_short": result_json.get("suggestion_short", "建议检查设备状态"),
        "sop_steps": result_json["sop_steps"],
        "standard": "GB 16297-1996",
        "safety_redline": "异常持续请执行紧急停机",
        "component_id": "system"
    }

# ==============================
# 测试运行
# ==============================
if __name__ == "__main__":
    print("="*60)
    print("🚀 RAG 预警卡片测试环境")
    print("="*60)

    test_result = get_warning_diagnose(
        vocs="92.5",
        shap_reason="引风机频率异常波动",
        shap_score="78%"
    )

    print("\n[AI 返回的标准化键值对结果]:")
    print(json.dumps(test_result, indent=2, ensure_ascii=False))