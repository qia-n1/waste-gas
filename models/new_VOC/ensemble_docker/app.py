import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from api_src.ensemble_predictor import EnsemblePredictor

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(title="VOC 集成学习预测服务", version="1.0.0")

# 初始化预测器实例
predictor = EnsemblePredictor()

class SensorData(BaseModel):
    timestamp: str
    feature_values: List[float] # 按时间顺序和特征顺序的传入传感器及气象特征

class PredictionRequest(BaseModel):
    data_sequence: List[SensorData] # 需要传入过去96步(seq_len)

class PredictionResponse(BaseModel):
    status: str
    predictions: List[float] # 预测未来24步
    is_exceed_warning: bool  # 安全拦截：判断预测值中是否超过安全阈值(>80.0)
    alerts: List[Dict[str, Any]] # 特定警报的内容
    incremental_attribution: Dict[str, Any] # 新增：支持增量瀑布图和热力图的增量归因数据

@app.on_event("startup")
async def startup_event():
    """系统启动，加载并在显存中准备加权的预测集成"""
    logger.info("Initializing VOC Mamba Ensemble predictor...")
    try:
        predictor.load_models()
        logger.info("Ensemble successfully loaded.")
    except Exception as e:
        logger.error(f"Failed to load models at startup: {e}")

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    处理模型推理请求：给定序列返回预测，并给出安全阈值预警。
    """
    if len(request.data_sequence) != predictor.config.seq_len:
        raise HTTPException(
            status_code=400, 
            detail=f"数据长度不合法，预期 {predictor.config.seq_len} 步数据，收到 {len(request.data_sequence)} 步"
        )
    
    try:
        # TODO: 从 SensorData 对象转成 numpy
        
        # 将结果交由集成模型推理及增量归因分析
        preds, attribution_data = predictor.predict(request.data_sequence)
        
        # 执行安全巡检 (对应 evaluate_regression_safe 内部的判断逻辑)
        alerts = []
        is_exceed_warning = False
        exceed_threshold = 80.0
        
        for step, val in enumerate(preds):
            if val > exceed_threshold:
                is_exceed_warning = True
                alerts.append({"step": step + 1, "value": float(val), "warning": "污染物超标预警!"})
                
        return PredictionResponse(
            status="success",
            predictions=preds.tolist(),
            is_exceed_warning=is_exceed_warning,
            alerts=alerts,
            incremental_attribution=attribution_data
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": predictor.is_loaded()}
