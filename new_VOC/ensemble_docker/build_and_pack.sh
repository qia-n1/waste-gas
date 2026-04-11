#!/bin/bash
set -e

echo "==============================================="
echo "  VOCs 集成预测微服务 - Docker一键打包构建工具"
echo "==============================================="

cd "$(dirname "$0")"

echo "[1/4] 清理旧的环境及缓存产物..."
rm -rf api_src models data
mkdir -p api_src models data

echo "[2/4] 提取主项目核心源代码到部署环境..."
cp ../src/config.py api_src/
cp ../src/features.py api_src/
cp ../src/model.py api_src/
cp ../src/vendor.py api_src/
cp ../src/schemas.py api_src/
cp ../src/ensemble_predictor.py api_src/
touch api_src/__init__.py
sed -i 's/from \.config/from api_src.config/g' api_src/*.py 2>/dev/null || true
sed -i 's/from \.features/from api_src.features/g' api_src/*.py 2>/dev/null || true
sed -i 's/from \.model/from api_src.model/g' api_src/*.py 2>/dev/null || true
sed -i 's/from \.vendor/from api_src.vendor/g' api_src/*.py 2>/dev/null || true
sed -i 's/from \.schemas/from api_src.schemas/g' api_src/*.py 2>/dev/null || true
sed -i 's/from \.ensemble_predictor/from api_src.ensemble_predictor/g' api_src/*.py 2>/dev/null || true

echo "[3/4] 准备初始化基准数据集与真实模型权重..."
cp ../artifacts_pca_ensemble/pca_dlinear_large.pt models/
cp -r ../../VOCS/src/data/vocs_dataset.csv data/ || true

echo "[4/4] 调整 app 逻辑直接调用真实推演引擎代码..."
sed -i 's/from src.ensemble_predictor/from api_src.ensemble_predictor/g' app.py 2>/dev/null || true

echo "==============================================="
echo " 环境抽离完成！可以随时运行以下命令打包服务："
echo "   cd $(pwd) && docker compose up --build -d"
echo "==============================================="
