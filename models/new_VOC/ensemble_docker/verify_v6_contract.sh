#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8001}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl not found"
  exit 1
fi

echo "[1/3] checking status endpoint"
STATUS_JSON="$(curl -fsS "${BASE_URL}/status")"
python - "$STATUS_JSON" <<'PY'
import json
import sys

status = json.loads(sys.argv[1])
required = ["module_ready", "model_family", "inference_contract_version", "model_path", "scaler_path"]
missing = [k for k in required if k not in status]
if missing:
    raise SystemExit(f"status missing keys: {missing}")
if not status.get("module_ready"):
    raise SystemExit(f"module_ready is false, reason={status.get('module_ready_reason')}")
if str(status.get("model_family", "")).lower() != "v6":
    raise SystemExit(f"model_family invalid: {status.get('model_family')}")
print("status check passed")
PY

echo "[2/3] checking predict parameter validation"
PREDICT_PAYLOAD='{"data_sequence":[]}'
HTTP_CODE="$(curl -s -o /tmp/v6_predict_err.json -w "%{http_code}" -H "Content-Type: application/json" -d "$PREDICT_PAYLOAD" "${BASE_URL}/predict")"
if [[ "$HTTP_CODE" != "400" ]]; then
  echo "expected 400 for invalid payload, got ${HTTP_CODE}"
  cat /tmp/v6_predict_err.json
  exit 1
fi
echo "predict validation check passed"

echo "[3/3] checking health endpoint"
HEALTH_JSON="$(curl -fsS "${BASE_URL}/health")"
python - "$HEALTH_JSON" <<'PY'
import json
import sys
health = json.loads(sys.argv[1])
if health.get("status") != "healthy":
    raise SystemExit(f"health status invalid: {health}")
print("health check passed")
PY

echo "all v6 protocol checks passed"
