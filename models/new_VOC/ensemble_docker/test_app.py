import json
import numpy as np
from fastapi.testclient import TestClient

# 引入app以启动测试客户端
from app import app, predictor

client = TestClient(app)


def _rebuild_groups_from_features(feature_rows):
    group_sum = {}
    for item in feature_rows:
        group = item.get('group', '其它')
        group_sum[group] = group_sum.get(group, 0.0) + float(item.get('contribution', 0.0))
    return [{"group": k, "contribution": float(v)} for k, v in group_sum.items()]

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
        
        # 优先改写细分指标贡献度，再由细分指标反聚合得到分组贡献度。
        feature_rows = attr.get('feature_contributions', [])
        if len(feature_rows) > 0:
            # 让前两项细分特征承担主要增量，模拟强异常来源。
            main_ratios = [0.32, 0.22, 0.16, 0.10, 0.08, 0.06, 0.04, 0.02]
            for idx, item in enumerate(feature_rows):
                ratio = main_ratios[idx] if idx < len(main_ratios) else 0.0
                item['ratio'] = float(ratio)
                item['contribution'] = float(attr['total_increment'] * ratio)
            attr['group_contributions'] = _rebuild_groups_from_features(feature_rows)
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
    if 'feature_contributions' in incr_attr:
        print("污染增量定责拆解-细分指标 Top 8:")
        for item in incr_attr['feature_contributions'][:8]:
            print(f" ➤ {item['feature']} ({item['group']}): {item['contribution']:.2f}")
    print("分组聚合(兼容旧前端):")
    for group in incr_attr.get('group_contributions', []):
        print(f" ➤ {group['group']}: {group['contribution']:.2f}")

    # 测试结束还原
    predictor.predict = original_predict

if __name__ == '__main__':
    run_tests()