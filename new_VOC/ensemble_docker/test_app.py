import json
import numpy as np
from fastapi.testclient import TestClient

# 引入app以启动测试客户端
from app import app, predictor

client = TestClient(app)

def generate_sequence():
    """生成合法的 96 步测试序列"""
    return {
        "data_sequence": [
            {
                "timestamp": "2026-04-05T00:00:00",
                "feature_values": [1.0, 2.0]
            }
            for _ in range(96)
        ]
    }

def run_tests():
    # 保存原始的 predict 方法，以便做切片代理
    original_predict = predictor.predict
    
    print("="*70)
    print("▶ 场景 1: 正常情况测试 (RTO预测出口浓度在安全区间 35-50)")
    print("="*70)
    
    # 构造拦截器（Wrapper）来强制返回正常的预测值
    def normal_predict(seq):
        preds, attr = original_predict(seq)
        # 生成正常范围的预测值 (均在 80.0 以下)
        normal_preds = np.random.uniform(35.0, 50.0, size=len(preds))
        # 修正 attr 中的 target 和 increment 以保持闭环逻辑自洽
        attr['target'] = float(np.mean(normal_preds))
        attr['total_increment'] = attr['target'] - attr['baseline']
        return normal_preds, attr

    predictor.predict = normal_predict
    response = client.post("/predict", json=generate_sequence())
    data = response.json()
    
    print(f"[API 状态码]: {response.status_code}")
    print(f"[是否触发预警 (is_exceed_warning)]: {data['is_exceed_warning']}")
    print(f"[当前警报数量]: {len(data['alerts'])} 个")
    print(f"[前三步预测情况]: {data['predictions'][:3]}")
    
    
    print("\n" + "="*70)
    print("▶ 场景 2: 异常超标情况测试 (预测浓度出现大突刺 > 80.0)")
    print("="*70)
    
    def abnormal_predict(seq):
        preds, attr = original_predict(seq)
        # 生成有突刺的高危预测值
        abnormal_preds = np.random.uniform(40.0, 60.0, size=len(preds))
        abnormal_preds[11] = 85.5  # t+12 步超标
        abnormal_preds[15] = 92.3  # t+16 步超标
        
        attr['target'] = float(np.mean(abnormal_preds))
        attr['total_increment'] = attr['target'] - attr['baseline']
        
        # 模拟真实的归因：由于发生了超标，我们将绝大部份的增量锅甩给 "车间废气源"
        attr['waterfall_groups'][0]['contribution'] = float(attr['total_increment'] * 0.82)
        attr['waterfall_groups'][1]['contribution'] = float(attr['total_increment'] * 0.13)
        attr['waterfall_groups'][2]['contribution'] = float(attr['total_increment'] * 0.05)
        return abnormal_preds, attr

    predictor.predict = abnormal_predict
    response = client.post("/predict", json=generate_sequence())
    data = response.json()
    
    print(f"[API 状态码]: {response.status_code}")
    print(f"[是否触发预警 (is_exceed_warning)]: {data['is_exceed_warning']}")
    print(f"[警报详情]: \n{json.dumps(data['alerts'], indent=2, ensure_ascii=False)}")
    
    print(f"\n--- [增量瀑布图：异常原因智能追溯] ---")
    incr_attr = data['incremental_attribution']
    print(f"基准浓度: {incr_attr['baseline']:.2f}")
    print(f"本次平均目标浓度: {incr_attr['target']:.2f}")
    print(f"总污染增量: +{incr_attr['total_increment']:.2f}")
    print("污染增量定责拆解 (溯源结论):")
    for group in incr_attr['waterfall_groups']:
        print(f" ➤ {group['group']}: {group['contribution']:.2f}")

    # 测试结束还原
    predictor.predict = original_predict

if __name__ == '__main__':
    run_tests()