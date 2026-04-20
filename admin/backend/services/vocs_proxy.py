from __future__ import annotations

import asyncio
import csv
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Union

import httpx

from config import settings


# ---------------------------------------------------------------------------
# RAG 惰性导入：失败也不影响服务，诊断接口会回退到原有启发式建议
# 日志走 ASCII，避免 Windows GBK 控制台打印 emoji 崩溃。
# ---------------------------------------------------------------------------
try:
    from rag import get_warning_diagnose as _rag_get_warning_diagnose  # type: ignore

    RAG_AVAILABLE = True
    print("[RAG] module loaded, diagnosis endpoint will attach SOP card")
except Exception as _rag_exc:  # pragma: no cover - 依赖缺失时走兜底
    _rag_get_warning_diagnose = None  # type: ignore
    RAG_AVAILABLE = False
    print(f"[RAG] module unavailable ({_rag_exc}); diagnosis will use built-in suggestions only")


WARNING_THRESHOLD = 80.0
CRITICAL_THRESHOLD = 100.0
SENSOR_INTERVAL_MINUTES = 15
SENSOR_FIELDS = [
    "ambient_temp",
    "ambient_humidity",
    "ambient_pressure",
    "coating_flow",
    "coating_conc",
    "coating_temp",
    "coating_pressure",
    "rotor_speed",
    "adsorption_fan_power",
    "desorption_fan_power",
    "rotor_inlet_temp",
    "rotor_inlet_humid",
    "desorption_temp",
    "concentrated_flow",
    "concentrated_conc",
    "concentrated_temp",
    "concentrated_pressure",
    "rto_in_flow",
    "rto_in_conc",
    "rto_in_temp",
    "rto_in_pressure",
    "burner_gas_flow",
    "combustion_temp",
    "rto_out_conc",
    "rto_out_temp",
]

# Mirrors admin/frontend/src/utils/sensorMeta.ts
SENSOR_LABEL_META: Dict[str, Dict[str, str]] = {
    "ambient_temp": {"label": "环境温度", "unit": "°C"},
    "ambient_humidity": {"label": "环境湿度", "unit": "%"},
    "ambient_pressure": {"label": "环境压力", "unit": "kPa"},
    "coating_flow": {"label": "喷涂风量", "unit": "m³/h"},
    "coating_conc": {"label": "喷涂浓度", "unit": "mg/m³"},
    "coating_temp": {"label": "喷涂温度", "unit": "°C"},
    "coating_pressure": {"label": "喷涂压力", "unit": "kPa"},
    "rotor_speed": {"label": "转轮转速", "unit": "rpm"},
    "adsorption_fan_power": {"label": "吸附风机功率", "unit": "kW"},
    "desorption_fan_power": {"label": "脱附风机功率", "unit": "kW"},
    "rotor_inlet_temp": {"label": "转轮入口温度", "unit": "°C"},
    "rotor_inlet_humid": {"label": "转轮入口湿度", "unit": "%"},
    "desorption_temp": {"label": "脱附温度", "unit": "°C"},
    "concentrated_flow": {"label": "浓缩风量", "unit": "m³/h"},
    "concentrated_conc": {"label": "浓缩浓度", "unit": "mg/m³"},
    "concentrated_temp": {"label": "浓缩温度", "unit": "°C"},
    "concentrated_pressure": {"label": "浓缩压力", "unit": "kPa"},
    "rto_in_flow": {"label": "RTO入口流量", "unit": "m³/h"},
    "rto_in_conc": {"label": "RTO入口浓度", "unit": "mg/m³"},
    "rto_in_temp": {"label": "RTO入口温度", "unit": "°C"},
    "rto_in_pressure": {"label": "RTO入口压力", "unit": "kPa"},
    "burner_gas_flow": {"label": "燃烧器气体流量", "unit": "Nm³/h"},
    "combustion_temp": {"label": "燃烧温度", "unit": "°C"},
    "rto_out_conc": {"label": "RTO出口浓度", "unit": "mg/m³"},
    "rto_out_temp": {"label": "RTO出口温度", "unit": "°C"},
}


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_round(value: Any, digits: int = 2) -> float:
    return round(_as_float(value), digits)


def _normalize_sensor(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    data: dict[str, Any] = {"timestamp": ""}
    if not row:
        return data
    data["timestamp"] = str(row.get("timestamp", ""))
    for field in SENSOR_FIELDS:
        data[field] = _as_float(row.get(field))
    return data


def _load_csv_rows(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    csv_path = Path(settings.csv_path)
    if not csv_path.exists():
        return []

    rows: Union[Deque[Dict[str, Any]], List[Dict[str, Any]]]
    rows = deque(maxlen=limit) if limit else []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized = _normalize_sensor(row)
            if limit:
                rows.append(normalized)
            else:
                rows.append(normalized)

    return list(rows)


def _latest_local_sensor() -> Optional[Dict[str, Any]]:
    rows = _load_csv_rows(limit=1)
    return rows[-1] if rows else None


def _build_fallback_prediction(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        now = datetime.now()
        values = [0.0] * 24
        return {
            "timestamp": now.isoformat(),
            "prediction_horizon": 24,
            "predicted_values": values,
            "confidence": 0.5,
            "alert_triggered": False,
            "alert_message": "使用本地默认预测",
            "prediction_type": "Fallback",
        }

    recent = history[-12:]
    values = [item["rto_out_conc"] for item in recent]
    baseline = sum(values) / len(values)
    trend = 0.0 if len(values) < 2 else (values[-1] - values[0]) / max(1, len(values) - 1)
    forecast = [
        max(0.0, min(180.0, baseline + trend * (index + 1) * 0.75))
        for index in range(24)
    ]
    peak = max(forecast) if forecast else 0.0
    return {
        "timestamp": history[-1]["timestamp"],
        "prediction_horizon": 24,
        "predicted_values": forecast,
        "confidence": 0.68,
        "alert_triggered": peak >= WARNING_THRESHOLD,
        "alert_message": "使用本地 CSV 估算预测",
        "prediction_type": "Fallback",
    }


def _serialize_trend(
    history: List[Dict[str, Any]], prediction: Optional[Dict[str, Any]]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    actual_series = [
        {"timestamp": item["timestamp"], "value": _safe_round(item["rto_out_conc"])}
        for item in history[-24:]
    ]

    if not prediction:
        return actual_series, []

    prediction_timestamp = _parse_timestamp(str(prediction.get("timestamp", "")))
    if prediction_timestamp is None:
        last_ts = _parse_timestamp(actual_series[-1]["timestamp"]) if actual_series else None
        prediction_timestamp = last_ts or datetime.now()

    forecast_series = []
    for index, value in enumerate(prediction.get("predicted_values", [])[:24]):
        timestamp = prediction_timestamp + timedelta(minutes=SENSOR_INTERVAL_MINUTES * (index + 1))
        forecast_series.append(
            {"timestamp": timestamp.isoformat(), "value": _safe_round(value)}
        )

    return actual_series, forecast_series


def _alert_level(value: float) -> str:
    if value >= CRITICAL_THRESHOLD:
        return "critical"
    if value >= WARNING_THRESHOLD:
        return "warning"
    return "normal"


def _alert_banner(current_vocs: float, peak_forecast: float) -> Dict[str, str]:
    if peak_forecast >= CRITICAL_THRESHOLD:
        return {
            "severity": "critical",
            "text": f"VOCs 预测峰值 {peak_forecast:.1f} mg/m³，已超过红色预警阈值。",
        }
    if peak_forecast >= WARNING_THRESHOLD or current_vocs >= WARNING_THRESHOLD:
        return {
            "severity": "warning",
            "text": f"VOCs 当前 {current_vocs:.1f} mg/m³，接近橙色预警阈值，请重点关注排口状态。",
        }
    return {
        "severity": "normal",
        "text": f"当前 VOCs {current_vocs:.1f} mg/m³，系统运行平稳。",
    }


def _build_key_parameters(sensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {"field": "rto_out_conc", "label": "RTO出口浓度", "value": _safe_round(sensor.get("rto_out_conc")), "unit": "mg/m³"},
        {"field": "rto_in_conc", "label": "RTO入口浓度", "value": _safe_round(sensor.get("rto_in_conc")), "unit": "mg/m³"},
        {"field": "combustion_temp", "label": "燃烧温度", "value": _safe_round(sensor.get("combustion_temp")), "unit": "°C"},
        {"field": "burner_gas_flow", "label": "燃烧器气体流量", "value": _safe_round(sensor.get("burner_gas_flow")), "unit": "Nm³/h"},
        {"field": "coating_conc", "label": "喷涂废气浓度", "value": _safe_round(sensor.get("coating_conc")), "unit": "mg/m³"},
        {"field": "ambient_temp", "label": "环境温度", "value": _safe_round(sensor.get("ambient_temp")), "unit": "°C"},
    ]


def _build_suggestions(sensor: Dict[str, Any], prediction: Dict[str, Any]) -> List[str]:
    suggestions: list[str] = []
    peak = _as_float(max(prediction.get("predicted_values", [0]) or [0]))
    if peak >= CRITICAL_THRESHOLD:
        suggestions.append("立即检查 1 号排口与 RTO 焚烧段，优先确认燃烧温度和入口浓度是否异常抬升。")
        suggestions.append("建议降低对应设备负荷，核查喷涂段来气浓度和转轮转速。")
    elif peak >= WARNING_THRESHOLD:
        suggestions.append("建议提前安排巡检，关注 RTO 出口浓度与入口浓度差值变化。")
        suggestions.append("保持燃烧温度稳定，避免短时负荷冲击引发二次波动。")
    else:
        suggestions.append("当前系统运行稳定，保持巡检节奏并持续观察趋势预测。")

    if _as_float(sensor.get("combustion_temp")) < 760:
        suggestions.append("燃烧温度偏低，可优先核查燃烧器供气和焚烧段温控策略。")
    if _as_float(sensor.get("rotor_speed")) < 4.8:
        suggestions.append("转轮转速偏低，建议检查吸附转轮运行状态和驱动系统。")

    return suggestions[:3]


def _build_decision(sensor: Dict[str, Any], prediction: Dict[str, Any]) -> Dict[str, Any]:
    peak = _safe_round(max(prediction.get("predicted_values", [0]) or [0]), 1)
    current_vocs = _safe_round(sensor.get("rto_out_conc"), 1)
    summary = (
        f"当前 RTO 出口浓度为 {current_vocs} mg/m³，未来 6 小时预测峰值约 {peak} mg/m³。"
        " 建议结合燃烧温度、入口浓度和转轮工况进行联动研判。"
    )
    return {"summary": summary, "suggestions": _build_suggestions(sensor, prediction)}


def _build_continuous_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    active = [item for item in alerts if not item.get("acknowledged", False)]
    if not active:
        return []

    enriched = []
    for index, alert in enumerate(active[:4]):
        timestamp = _parse_timestamp(str(alert.get("timestamp", ""))) or datetime.now()
        elapsed = max(int((datetime.now() - timestamp).total_seconds()), 0)
        enriched.append(
            {
                "id": str(alert.get("alert_id", f"alert-{index}")),
                "level": alert.get("level", "warning"),
                "message": str(alert.get("message", "告警持续关注")),
                "location": "1号排口",
                "elapsed_seconds": elapsed,
            }
        )
    return enriched


def _build_factory_nodes(sensor: Dict[str, Any], prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
    output_level = _alert_level(_as_float(sensor.get("rto_out_conc")))
    forecast_level = _alert_level(max(prediction.get("predicted_values", [0]) or [0]))
    return [
        {"id": "monitor", "label": "监测点位", "status": output_level, "x": 22, "y": 28},
        {"id": "device", "label": "关键设备", "status": _alert_level(_as_float(sensor.get("combustion_temp"))), "x": 49, "y": 22},
        {"id": "stack", "label": "1号排口", "status": forecast_level, "x": 72, "y": 45},
    ]


def _build_equipment_summary(
    sensor: Dict[str, Any], prediction: Dict[str, Any], alerts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    warning_count = len([item for item in alerts if item.get("level") == "warning"])
    critical_count = len([item for item in alerts if item.get("level") == "critical"])
    offline = 0
    if not sensor.get("timestamp"):
        offline = 12

    abnormal = critical_count + (1 if _as_float(sensor.get("combustion_temp")) < 760 else 0)
    warning = warning_count + (1 if max(prediction.get("predicted_values", [0]) or [0]) >= WARNING_THRESHOLD else 0)
    normal = max(settings.total_equipment - abnormal - warning - offline, 0)

    return {
        "total": settings.total_equipment,
        "online": settings.total_equipment - offline,
        "items": [
            {"name": "正常", "value": normal, "color": "#46d1ff"},
            {"name": "预警", "value": warning, "color": "#ffb347"},
            {"name": "故障", "value": abnormal, "color": "#ff5b61"},
            {"name": "离线", "value": offline, "color": "#5f6d95"},
        ],
    }


def _build_heatmap_source(
    history: List[Dict[str, Any]], alerts: List[Dict[str, Any]], days: int
) -> Dict[str, Any]:
    today = datetime.now().date()
    dates = [
        (today - timedelta(days=offset)).strftime("%m/%d")
        for offset in range(days - 1, -1, -1)
    ]
    counter: dict[tuple[str, int], int] = defaultdict(int)

    for alert in alerts:
        ts = _parse_timestamp(str(alert.get("timestamp", "")))
        if ts is None:
            continue
        key = (ts.strftime("%m/%d"), ts.hour)
        if key[0] in dates:
            counter[key] += 1

    if not counter:
        for item in history:
            ts = _parse_timestamp(item.get("timestamp"))
            if ts is None:
                continue
            if (today - ts.date()).days >= days:
                continue
            weight = 0
            value = _as_float(item.get("rto_out_conc"))
            if value >= CRITICAL_THRESHOLD:
                weight = 3
            elif value >= WARNING_THRESHOLD:
                weight = 1
            if weight:
                counter[(ts.strftime("%m/%d"), ts.hour)] += weight

    values = []
    for date_index, date in enumerate(dates):
        for hour in range(24):
            values.append([date_index, hour, counter.get((date, hour), 0)])

    return {"dates": dates, "hours": list(range(24)), "values": values}


def _row_to_feature_values(row: Dict[str, Any]) -> List[float]:
    return [_as_float(row.get(field)) for field in SENSOR_FIELDS]


async def _fetch_json(
    path: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Any]:
    try:
        async with httpx.AsyncClient(
            base_url=settings.vocs_base_url, timeout=settings.request_timeout
        ) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return None


async def call_ensemble_predict(
    history: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    rows = history if history is not None else _load_csv_rows(limit=96)
    if len(rows) < 96:
        return None

    data_sequence = []
    for row in rows[-96:]:
        data_sequence.append({
            "timestamp": str(row.get("timestamp", "")),
            "feature_values": _row_to_feature_values(row),
        })

    try:
        async with httpx.AsyncClient(
            base_url=settings.ensemble_base_url,
            timeout=settings.ensemble_timeout,
        ) as client:
            response = await client.post("/predict", json={"data_sequence": data_sequence})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return None


async def fetch_status() -> Optional[Dict[str, Any]]:
    return await _fetch_json("/status")


async def fetch_latest_prediction() -> Optional[Dict[str, Any]]:
    data = await _fetch_json("/predictions/latest")
    return data if isinstance(data, dict) and data else None


async def fetch_latest_sensor() -> Optional[Dict[str, Any]]:
    data = await _fetch_json("/sensor-data/latest")
    if isinstance(data, dict) and data and "message" not in data:
        return _normalize_sensor(data)
    return None


async def fetch_alerts(limit: int = 30) -> list[dict[str, Any]]:
    data = await _fetch_json("/alerts", params={"limit": limit})
    if isinstance(data, list):
        return data
    return []


def _build_top_contributor_series(
    history: List[Dict[str, Any]],
    attribution: Optional[Dict[str, Any]],
    top_n: int = 6,
    window: int = 48,
) -> List[Dict[str, Any]]:
    if not attribution or not history:
        return []
    contributions = attribution.get("feature_contributions") or []
    if not contributions:
        return []

    sorted_contrib = sorted(
        contributions, key=lambda item: _as_float(item.get("ratio")), reverse=True
    )[:top_n]
    recent = history[-window:] if len(history) > window else history

    result: List[Dict[str, Any]] = []
    for item in sorted_contrib:
        feature = str(item.get("feature", ""))
        if not feature:
            continue
        meta = SENSOR_LABEL_META.get(feature, {"label": feature, "unit": ""})
        series = [
            {
                "timestamp": str(row.get("timestamp", "")),
                "value": _safe_round(row.get(feature), 2),
            }
            for row in recent
        ]
        values = [point["value"] for point in series]
        current_value = values[-1] if values else 0.0
        mean_value = sum(values) / len(values) if values else 0.0
        max_value = max(values) if values else 0.0
        min_value = min(values) if values else 0.0
        result.append(
            {
                "feature": feature,
                "label": meta["label"],
                "unit": meta["unit"],
                "group": str(item.get("group", "")),
                "ratio": _as_float(item.get("ratio")),
                "contribution": _as_float(item.get("contribution")),
                "currentValue": current_value,
                "meanValue": round(mean_value, 2),
                "maxValue": max_value,
                "minValue": min_value,
                "series": series,
            }
        )
    return result


async def get_dashboard_overview() -> dict[str, Any]:
    history = _load_csv_rows(limit=96)
    status, latest_prediction, latest_sensor, alerts, ensemble_result = await asyncio.gather(
        fetch_status(),
        fetch_latest_prediction(),
        fetch_latest_sensor(),
        fetch_alerts(limit=20),
        call_ensemble_predict(history),
    )

    sensor = latest_sensor or (history[-1] if history else _normalize_sensor(None))

    # Prefer ensemble predictions when available
    attribution: Optional[Dict[str, Any]] = None
    if ensemble_result and ensemble_result.get("status") == "success":
        ensemble_preds = ensemble_result.get("predictions", [])
        if ensemble_preds:
            prediction = {
                "timestamp": sensor.get("timestamp") or datetime.now().isoformat(),
                "prediction_horizon": len(ensemble_preds),
                "predicted_values": ensemble_preds,
                "confidence": 0.88,
                "alert_triggered": ensemble_result.get("is_exceed_warning", False),
                "alert_message": "集成模型预测",
                "prediction_type": "DLinear-PCA-Ensemble",
            }
            attribution = ensemble_result.get("incremental_attribution")
        else:
            prediction = latest_prediction or _build_fallback_prediction(history)
    else:
        prediction = latest_prediction or _build_fallback_prediction(history)

    actual_series, forecast_series = _serialize_trend(history, prediction)
    equipment = _build_equipment_summary(sensor, prediction, alerts)
    decision = _build_decision(sensor, prediction)
    peak_forecast = _safe_round(max(prediction.get("predicted_values", [0]) or [0]), 1)
    current_vocs = _safe_round(sensor.get("rto_out_conc"), 1)
    today = datetime.now().date()
    today_alerts = 0
    for alert in alerts:
        ts = _parse_timestamp(str(alert.get("timestamp", "")))
        if ts and ts.date() == today:
            today_alerts += 1

    result: dict[str, Any] = {
        "timestamp": sensor.get("timestamp") or datetime.now().isoformat(),
        "metrics": {
            "currentVocs": current_vocs,
            "peakForecast": peak_forecast,
            "alertLevel": _alert_level(max(current_vocs, peak_forecast)),
            "onlineDevices": equipment["online"],
            "totalDevices": equipment["total"],
            "todayAlerts": today_alerts,
            "systemPhase": (status or {}).get("system_phase", "CSV Fallback"),
            "uptime": (status or {}).get("uptime", "未连接"),
            "confidence": _safe_round(_as_float(prediction.get("confidence")) * 100, 0),
            "dataCompleteness": 100 if history else 0,
            "latencyMs": 280 if status else 0,
            "predictionType": prediction.get("prediction_type", "Fallback"),
        },
        "trend": {
            "actualSeries": actual_series,
            "forecastSeries": forecast_series,
            "warningThreshold": WARNING_THRESHOLD,
            "criticalThreshold": CRITICAL_THRESHOLD,
            "confidence": _as_float(prediction.get("confidence"), 0.5),
        },
        "statusBanner": _alert_banner(current_vocs, peak_forecast),
        "keyParameters": _build_key_parameters(sensor),
        "decision": decision,
        "continuousAlerts": _build_continuous_alerts(alerts),
        "factoryNodes": _build_factory_nodes(sensor, prediction),
    }

    if attribution:
        result["attribution"] = attribution
        top_series = _build_top_contributor_series(history, attribution)
        if top_series:
            result["topContributorSeries"] = top_series

    return result


async def get_equipment_status() -> dict[str, Any]:
    history = _load_csv_rows(limit=96)
    latest_prediction, latest_sensor, alerts = await asyncio.gather(
        fetch_latest_prediction(),
        fetch_latest_sensor(),
        fetch_alerts(limit=50),
    )
    sensor = latest_sensor or (history[-1] if history else _normalize_sensor(None))
    prediction = latest_prediction or _build_fallback_prediction(history)
    return _build_equipment_summary(sensor, prediction, alerts)


async def get_anomaly_heatmap(days: int = 7) -> dict[str, Any]:
    history = _load_csv_rows(limit=24 * days * 4)
    alerts = await fetch_alerts(limit=100)
    return _build_heatmap_source(history, alerts, days)


async def get_alerts(limit: int = 30, search: str = "", level: str = "") -> dict[str, Any]:
    # Lazy import to avoid circular import (watchdog imports vocs_proxy)
    from services.device_watchdog import watchdog

    raw_alerts = await fetch_alerts(limit=max(limit, 50))
    # Merge in admin-side watchdog alerts (device offline / recovered) so they
    # appear in the AlarmCenter alongside upstream VOCs alerts.
    watchdog_alerts = watchdog.list_alerts()
    if watchdog_alerts:
        raw_alerts = watchdog_alerts + list(raw_alerts)
    if not raw_alerts:
        history = _load_csv_rows(limit=48)
        prediction = _build_fallback_prediction(history)
        peak = max(prediction.get("predicted_values", [0]) or [0])
        latest = history[-1] if history else _normalize_sensor(None)
        if peak >= WARNING_THRESHOLD:
            raw_alerts = [
                {
                    "alert_id": "LOCAL-FALLBACK-001",
                    "timestamp": latest.get("timestamp") or datetime.now().isoformat(),
                    "level": _alert_level(peak),
                    "message": f"本地估算预测峰值 {peak:.1f} mg/m³，请核查 1 号排口。",
                    "value": peak,
                    "threshold": WARNING_THRESHOLD,
                    "acknowledged": False,
                }
            ]

    normalized = []
    search_lower = search.lower().strip()
    for alert in raw_alerts:
        item = {
            "alert_id": str(alert.get("alert_id", "")),
            "timestamp": str(alert.get("timestamp", "")),
            "level": str(alert.get("level", "warning")),
            "message": str(alert.get("message", "VOCs 告警")),
            "value": _safe_round(alert.get("value")),
            "threshold": _safe_round(alert.get("threshold", WARNING_THRESHOLD)),
            "acknowledged": bool(alert.get("acknowledged", False)),
            "location": "1号排口",
            "status": "已处理" if alert.get("acknowledged") else "处理中",
        }
        if level and item["level"] != level:
            continue
        if search_lower and search_lower not in (
            f'{item["message"]} {item["location"]} {item["level"]}'.lower()
        ):
            continue
        normalized.append(item)

    normalized.sort(key=lambda item: item["timestamp"], reverse=True)
    return {
        "items": normalized[:limit],
        "total": len(normalized),
        "byLevel": dict(Counter(item["level"] for item in normalized)),
    }


async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    # Watchdog-generated alerts live only in admin memory — handle locally.
    if alert_id.startswith("WATCHDOG-"):
        from services.device_watchdog import watchdog

        for alert in watchdog.list_alerts():
            if alert.get("alert_id") == alert_id:
                alert["acknowledged"] = True
                alert["status"] = "已处理"
                break
        return {"success": True, "message": "设备状态告警已确认", "alert_id": alert_id}

    try:
        async with httpx.AsyncClient(
            base_url=settings.vocs_base_url, timeout=settings.request_timeout
        ) as client:
            response = await client.post(f"/alerts/{alert_id}/acknowledge")
            response.raise_for_status()
            return {"success": True, "message": "告警已确认", "alert_id": alert_id}
    except httpx.HTTPError:
        return {
            "success": True,
            "message": "共享服务不可用，已在管理端初版中模拟确认成功",
            "alert_id": alert_id,
        }


def _invoke_rag_diagnosis(
    vocs: str, shap_reason: str, shap_score: str
) -> Optional[Dict[str, Any]]:
    """同步调用 RAG 诊断，异常时返回 None，由上层走兜底。"""
    if not RAG_AVAILABLE or _rag_get_warning_diagnose is None:
        return None
    try:
        return _rag_get_warning_diagnose(vocs, shap_reason, shap_score)
    except Exception as exc:  # pragma: no cover - 网络/模型异常兜底
        print(f"[RAG] diagnosis call failed: {exc}")
        return None


def _plan_row_to_card(plan: Dict[str, Any]) -> Dict[str, Any]:
    """把 wg_alert_rag_plans 行映射成前端 ragCard。"""
    generated_at = plan.get("generated_at")
    return {
        "title": plan.get("title", ""),
        "suggestionShort": plan.get("suggestion_short", ""),
        "sopSteps": plan.get("sop_steps") or [],
        "safetyRedline": plan.get("safety_redline") or "",
        "standard": plan.get("standard") or "",
        "level": plan.get("level", "warning"),
        "reason": plan.get("reason") or "",
        "version": plan.get("version"),
        "generatedAt": generated_at.isoformat() if generated_at else None,
        "fromCache": True,
    }


def _raw_to_card(raw: Dict[str, Any]) -> Dict[str, Any]:
    """rag_service 直接返回值（未落库时的临时回包）映射成 ragCard。"""
    return {
        "title": raw.get("title", ""),
        "suggestionShort": raw.get("suggestion_short", ""),
        "sopSteps": raw.get("sop_steps", []),
        "safetyRedline": raw.get("safety_redline", ""),
        "standard": raw.get("standard", ""),
        "level": raw.get("level", "warning"),
        "reason": raw.get("reason", ""),
        "version": None,
        "generatedAt": None,
        "fromCache": False,
    }


async def get_alert_diagnosis(alert_id: str) -> dict[str, Any]:
    """诊断接口：缓存优先（DB），未命中时实时跑 RAG 并落库。

    流程：
      1. 取大屏 overview（contributors / attribution）
      2. 把 alert_id 转成 wg_alerts.id；非数字（本地 fallback / watchdog 告警）跳过 DB
      3. 优先 SELECT wg_alert_rag_plans WHERE alert_id=? AND is_current
      4. 命中 → 直接返回缓存（毫秒级）
      5. 未命中且有 attribution → 调 RAG，写入 DB，再返回
      6. 任一环节异常 → ragCard=None，其它字段不受影响
    """
    # 惰性 import 避免 vocs_proxy 启动期就强依赖 db 模块
    from services.rag_plans import get_current_plan, parse_alert_id, upsert_plan

    overview = await get_dashboard_overview()
    attribution = overview.get("attribution")

    # ------------------ contributors 构建（保持原逻辑） ------------------
    if attribution and attribution.get("feature_contributions"):
        contributors = [
            {
                "label": item["feature"],
                "group": item["group"],
                "weight": item["ratio"],
                "contribution": item["contribution"],
            }
            for item in attribution["feature_contributions"][:6]
        ]
        group_contributions = attribution.get("group_contributions", [])
    else:
        key_parameters = overview["keyParameters"]
        top_parameter = max(key_parameters, key=lambda item: item["value"])
        contributors = [
            {"label": top_parameter["label"], "group": "", "weight": 0.34, "contribution": 0.0},
            {"label": "燃烧温度", "group": "RTO焚烧系统", "weight": 0.27, "contribution": 0.0},
            {"label": "喷涂废气浓度", "group": "废气源与环境组", "weight": 0.18, "contribution": 0.0},
            {"label": "环境温度", "group": "废气源与环境组", "weight": 0.11, "contribution": 0.0},
        ]
        group_contributions = []

    # ------------------ ragCard：缓存优先 ------------------
    rag_card: Optional[Dict[str, Any]] = None
    aid_int = parse_alert_id(alert_id)

    # 1) 先查 DB 缓存
    if aid_int is not None:
        try:
            cached = await asyncio.to_thread(get_current_plan, aid_int)
            if cached:
                rag_card = _plan_row_to_card(cached)
        except Exception as exc:  # pragma: no cover - DB 故障走兜底
            print(f"[RAG] cache lookup failed for alert {aid_int}: {exc}")

    # 2) 未命中 → 实时跑 RAG（前提是 RAG 可用且有 attribution）
    if (
        rag_card is None
        and RAG_AVAILABLE
        and attribution
        and attribution.get("feature_contributions")
    ):
        top = attribution["feature_contributions"][0]
        feature = str(top.get("feature", ""))
        meta = SENSOR_LABEL_META.get(feature, {"label": feature})
        shap_reason = f"{meta['label']}异常"
        shap_ratio = _as_float(top.get("ratio"))
        shap_score_pct = f"{shap_ratio * 100:.0f}%"
        current_vocs = _as_float(overview["metrics"].get("currentVocs", 0))
        vocs_value = f"{current_vocs:.1f}"

        raw = await asyncio.to_thread(
            _invoke_rag_diagnosis, vocs_value, shap_reason, shap_score_pct
        )

        if raw:
            # 3) 落库（仅 wg_alerts 真实 id 才落库）
            if aid_int is not None:
                try:
                    saved = await asyncio.to_thread(
                        upsert_plan,
                        aid_int,
                        raw,
                        {
                            "top_feature": feature,
                            "top_feature_label": meta.get("label", feature),
                            "shap_score": shap_ratio,
                            "current_vocs": current_vocs,
                            "model_name": "deepseek-chat",
                            "confidence": 0.85,
                        },
                    )
                    rag_card = _plan_row_to_card(saved)
                    rag_card["fromCache"] = False  # 本次新生成，标记一下
                except Exception as exc:  # pragma: no cover
                    print(f"[RAG] persist plan failed for alert {aid_int}: {exc}")
                    rag_card = _raw_to_card(raw)
            else:
                # 本地 fallback / watchdog 告警，不属于 wg_alerts，仅返回不落库
                rag_card = _raw_to_card(raw)

    return {
        "alertId": alert_id,
        "summary": overview["decision"]["summary"],
        "recommendations": overview["decision"]["suggestions"],
        "contributors": contributors,
        "groupContributions": group_contributions,
        "baseline": attribution.get("baseline") if attribution else None,
        "target": attribution.get("target") if attribution else None,
        "totalIncrement": attribution.get("total_increment") if attribution else None,
        "ragCard": rag_card,
    }
