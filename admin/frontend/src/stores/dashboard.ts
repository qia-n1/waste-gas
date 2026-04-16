import { computed, ref } from "vue";
import { defineStore } from "pinia";

import client from "@/api/client";
import type {
  Attribution,
  DashboardOverview,
  EquipmentStatusResponse,
  FactoryNode,
  HeatmapResponse,
  KeyParameter,
  PredictionPayload,
  SensorPayload,
} from "@/types/dashboard";
import { highlightedSensorFields, sensorMeta } from "@/utils/sensorMeta";

const createOverview = (): DashboardOverview => ({
  timestamp: "",
  metrics: {
    currentVocs: 0,
    peakForecast: 0,
    alertLevel: "normal",
    onlineDevices: 0,
    totalDevices: 0,
    todayAlerts: 0,
    systemPhase: "初始化中",
    uptime: "--",
    confidence: 0,
    dataCompleteness: 0,
    latencyMs: 0,
    predictionType: "Fallback",
  },
  trend: {
    actualSeries: [],
    forecastSeries: [],
    warningThreshold: 80,
    criticalThreshold: 100,
    confidence: 0.5,
  },
  statusBanner: {
    severity: "normal",
    text: "等待数据接入",
  },
  keyParameters: [],
  decision: {
    summary: "正在等待 VOCs 监测数据。",
    suggestions: ["请先启动共享 VOCs 服务，或使用本地 CSV 回放数据。"],
  },
  continuousAlerts: [],
  factoryNodes: [],
});

const createEquipment = (): EquipmentStatusResponse => ({
  total: 0,
  online: 0,
  items: [],
});

const createHeatmap = (): HeatmapResponse => ({
  dates: [],
  hours: Array.from({ length: 24 }, (_, index) => index),
  values: [],
});

const roundNumber = (value: number, digits = 1) => Number(value.toFixed(digits));

const getStatusByValue = (value: number) => {
  if (value >= 100) {
    return "critical";
  }
  if (value >= 80) {
    return "warning";
  }
  return "normal";
};

const buildKeyParameters = (payload: SensorPayload): KeyParameter[] =>
  highlightedSensorFields
    .map((field) => {
      const meta = sensorMeta.find((item) => item.field === field);
      return meta
        ? {
            field,
            label: meta.label,
            value: roundNumber(payload[field as keyof SensorPayload] as number),
            unit: meta.unit,
          }
        : null;
    })
    .filter((item): item is KeyParameter => Boolean(item));

const buildFactoryNodes = (
  currentValue: number,
  combustionTemp: number,
  peakForecast: number,
): FactoryNode[] => [
  { id: "monitor", label: "监测点位", status: getStatusByValue(currentValue), x: 22, y: 28 },
  { id: "device", label: "关键设备", status: getStatusByValue(combustionTemp), x: 49, y: 22 },
  { id: "stack", label: "1号排口", status: getStatusByValue(peakForecast), x: 72, y: 45 },
];

const buildDecisionSummary = (payload: SensorPayload, peakForecast: number) =>
  `当前 RTO 出口浓度 ${roundNumber(payload.rto_out_conc)} mg/m³，入口浓度 ${roundNumber(
    payload.rto_in_conc,
  )} mg/m³，燃烧温度 ${roundNumber(payload.combustion_temp)} °C，未来 6 小时预测峰值约 ${roundNumber(
    peakForecast,
  )} mg/m³。`;

const buildDecisionSuggestions = (payload: SensorPayload, peakForecast: number) => {
  const suggestions: string[] = [];
  if (peakForecast >= 100) {
    suggestions.push("建议优先检查排口和焚烧段，必要时立即降低相关设备负荷。");
  } else if (peakForecast >= 80) {
    suggestions.push("建议提前安排巡检，关注入口浓度和燃烧温度波动。");
  } else {
    suggestions.push("系统整体处于平稳区间，继续保持常规巡检。");
  }
  if (payload.combustion_temp < 760) {
    suggestions.push("燃烧温度偏低，建议核查燃烧器供气和温控逻辑。");
  }
  if (payload.rotor_speed < 4.8) {
    suggestions.push("转轮转速偏低，建议检查转轮驱动状态。");
  }
  return suggestions.slice(0, 3);
};

export const useDashboardStore = defineStore("dashboard", () => {
  const overview = ref<DashboardOverview>(createOverview());
  const equipmentStatus = ref<EquipmentStatusResponse>(createEquipment());
  const heatmap = ref<HeatmapResponse>(createHeatmap());
  const attribution = ref<Attribution | null>(null);
  const isExceedWarning = ref(false);
  const loading = ref(false);
  const connected = ref(false);

  const currentAlertLevel = computed(() => overview.value.metrics.alertLevel);

  const initializeDashboard = async () => {
    loading.value = true;
    try {
      const [overviewResponse, equipmentResponse, heatmapResponse] = await Promise.all([
        client.get<DashboardOverview>("/dashboard/overview"),
        client.get<EquipmentStatusResponse>("/dashboard/equipment-status"),
        client.get<HeatmapResponse>("/dashboard/anomaly-heatmap"),
      ]);
      overview.value = overviewResponse.data;
      equipmentStatus.value = equipmentResponse.data;
      heatmap.value = heatmapResponse.data;
      attribution.value = overviewResponse.data.attribution ?? null;
      isExceedWarning.value = overview.value.metrics.alertLevel !== "normal";
    } finally {
      loading.value = false;
    }
  };

  const setConnected = (status: boolean) => {
    connected.value = status;
  };

  const updateFromSensorData = (payload: SensorPayload) => {
    overview.value.timestamp = payload.timestamp;
    overview.value.metrics.currentVocs = roundNumber(payload.rto_out_conc);
    overview.value.metrics.alertLevel = getStatusByValue(
      Math.max(payload.rto_out_conc, overview.value.metrics.peakForecast),
    );
    overview.value.trend.actualSeries = [
      ...overview.value.trend.actualSeries.slice(-23),
      { timestamp: payload.timestamp, value: roundNumber(payload.rto_out_conc) },
    ];
    overview.value.keyParameters = buildKeyParameters(payload);
    overview.value.factoryNodes = buildFactoryNodes(
      payload.rto_out_conc,
      payload.combustion_temp,
      overview.value.metrics.peakForecast,
    );
  };

  const updateFromPrediction = (payload: PredictionPayload, latestSensor?: SensorPayload) => {
    const baseTimestamp = payload.timestamp || overview.value.timestamp || new Date().toISOString();
    const start = new Date(baseTimestamp);
    overview.value.metrics.peakForecast = roundNumber(
      Math.max(...(payload.predicted_values || [0])),
    );
    overview.value.metrics.confidence = roundNumber(payload.confidence * 100, 0);
    overview.value.metrics.predictionType = payload.prediction_type || "SSE";
    overview.value.metrics.alertLevel = getStatusByValue(
      Math.max(overview.value.metrics.currentVocs, overview.value.metrics.peakForecast),
    );
    overview.value.trend.confidence = payload.confidence;
    overview.value.trend.forecastSeries = (payload.predicted_values || []).map(
      (value, index) => ({
        timestamp: new Date(start.getTime() + (index + 1) * 15 * 60 * 1000).toISOString(),
        value: roundNumber(value),
      }),
    );

    if (latestSensor) {
      overview.value.decision.summary = buildDecisionSummary(
        latestSensor,
        overview.value.metrics.peakForecast,
      );
      overview.value.decision.suggestions = buildDecisionSuggestions(
        latestSensor,
        overview.value.metrics.peakForecast,
      );
      overview.value.factoryNodes = buildFactoryNodes(
        latestSensor.rto_out_conc,
        latestSensor.combustion_temp,
        overview.value.metrics.peakForecast,
      );
    }

    overview.value.statusBanner =
      overview.value.metrics.peakForecast >= overview.value.trend.criticalThreshold
        ? {
            severity: "critical",
            text: `预测峰值 ${overview.value.metrics.peakForecast} mg/m³，已超过红色预警阈值。`,
          }
        : overview.value.metrics.peakForecast >= overview.value.trend.warningThreshold
          ? {
              severity: "warning",
              text: `预测峰值 ${overview.value.metrics.peakForecast} mg/m³，建议提前处置。`,
            }
          : {
              severity: "normal",
              text: `预测峰值 ${overview.value.metrics.peakForecast} mg/m³，系统保持平稳。`,
            };
  };

  return {
    overview,
    equipmentStatus,
    heatmap,
    attribution,
    isExceedWarning,
    loading,
    connected,
    currentAlertLevel,
    initializeDashboard,
    setConnected,
    updateFromSensorData,
    updateFromPrediction,
  };
});
