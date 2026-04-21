/**
 * 工艺单元 / 热力外壳配置。
 *
 * anchor 坐标与 FactoryScene.vue 的 buildingLabels 一一对齐。indicators 与后端
 * admin/backend/services/vocs_proxy.py::EMITTER_CONFIGS 同步（任何一边改阈值都
 * 必须同步，否则视觉会和后端 level 不一致）。
 *
 * shellSize 描述热力外壳 mesh 的大小（世界坐标半宽，单位和 Three.js 场景对齐）。
 * bottomY 是外壳底部的世界 y 坐标，让外壳紧贴地面 (~0) 而不是贴 anchor 高度。
 *
 * kind = "cylinder" 给 stack 烟囱用，其他都是 "box"。
 */
import type { EmitterConcentration, EmitterIndicator, SensorPayload } from "@/types/dashboard";

export interface EmitterIndicatorConfig {
  field: keyof SensorPayload;
  label: string;
  unit: string;
  warning: number;
  critical: number;
}

export interface EmitterDefinition {
  id: string;
  label: string;
  anchor: [number, number, number];
  indicators: EmitterIndicatorConfig[];
  /** 热力外壳的世界空间尺寸 & 形状。 */
  shell: {
    kind: "box" | "cylinder";
    /** box: [sizeX, sizeY, sizeZ]；cylinder: [radiusTop, height, radiusBottom] */
    size: [number, number, number];
    /** 外壳中心的世界坐标（通常就是建筑几何中心） */
    center: [number, number, number];
  };
}

export const EMITTER_DEFINITIONS: EmitterDefinition[] = [
  {
    id: "coating",
    label: "喷涂生产厂房",
    anchor: [-3.6, 1.7, 2.55],
    indicators: [
      { field: "coating_conc", label: "喷涂浓度", unit: "mg/m³", warning: 80, critical: 120 },
      { field: "coating_temp", label: "喷涂温度", unit: "°C", warning: 40, critical: 55 },
      { field: "coating_flow", label: "喷涂风量", unit: "m³/h", warning: 14000, critical: 18000 },
    ],
    shell: {
      kind: "box",
      size: [3.6, 1.6, 2.2],
      center: [-3.6, 0.75, 2.55],
    },
  },
  {
    id: "rotor",
    label: "转轮吸附厂房",
    anchor: [-1.05, 1.85, 1.85],
    indicators: [
      { field: "concentrated_conc", label: "浓缩浓度", unit: "mg/m³", warning: 150, critical: 250 },
      { field: "rotor_inlet_temp", label: "入口温度", unit: "°C", warning: 45, critical: 55 },
      { field: "rotor_speed", label: "转轮转速", unit: "rpm", warning: 7, critical: 10 },
    ],
    shell: {
      kind: "box",
      size: [3.1, 1.75, 2.0],
      center: [-1.05, 0.83, 1.85],
    },
  },
  {
    id: "rto_in",
    label: "RTO 主处理厂房",
    anchor: [1.95, 2.15, 1.95],
    indicators: [
      { field: "rto_in_conc", label: "RTO入口", unit: "mg/m³", warning: 180, critical: 280 },
      { field: "rto_in_flow", label: "入口流量", unit: "m³/h", warning: 25000, critical: 32000 },
      { field: "rto_in_temp", label: "入口温度", unit: "°C", warning: 45, critical: 60 },
    ],
    shell: {
      kind: "box",
      size: [4.3, 2.0, 3.1],
      center: [1.95, 1.0, 1.95],
    },
  },
  {
    id: "utility",
    label: "公辅燃烧区",
    anchor: [5.15, 1.45, 2.55],
    indicators: [
      { field: "desorption_temp", label: "脱附温度", unit: "°C", warning: 180, critical: 220 },
      { field: "burner_gas_flow", label: "燃气流量", unit: "Nm³/h", warning: 80, critical: 110 },
      { field: "adsorption_fan_power", label: "风机功率", unit: "kW", warning: 40, critical: 50 },
    ],
    shell: {
      kind: "box",
      size: [2.9, 1.3, 1.65],
      center: [5.15, 0.65, 2.55],
    },
  },
  {
    id: "stack",
    label: "排口烟囱区",
    anchor: [-5.45, 4.95, -0.55],
    indicators: [
      { field: "rto_out_conc", label: "RTO出口", unit: "mg/m³", warning: 80, critical: 100 },
      { field: "rto_out_temp", label: "出口温度", unit: "°C", warning: 200, critical: 260 },
    ],
    shell: {
      kind: "cylinder",
      size: [0.55, 5.2, 0.6], // radiusTop, height, radiusBottom
      center: [-5.45, 2.6, -0.55],
    },
  },
  {
    id: "public",
    label: "监测附属区",
    anchor: [5.4, 1.1, 4.0],
    indicators: [
      { field: "ambient_humidity", label: "环境湿度", unit: "%", warning: 85, critical: 95 },
      { field: "ambient_temp", label: "环境温度", unit: "°C", warning: 32, critical: 38 },
      { field: "ambient_pressure", label: "环境压力", unit: "kPa", warning: 101.8, critical: 102.5 },
    ],
    shell: {
      kind: "box",
      size: [2.1, 0.85, 1.2],
      center: [1.85, 0.45, 4.05],
    },
  },
];

const levelFor = (value: number, warning: number, critical: number) => {
  if (value >= critical) return "critical" as const;
  if (value >= warning) return "warning" as const;
  return "normal" as const;
};

/**
 * 前端版 _indicator_ratio —— 必须与 backend 保持一致。
 */
const indicatorRatio = (value: number, warning: number, critical: number): number => {
  if (critical <= 0 || value <= 0) return 0;
  if (value <= warning) return 0.6 * (value / Math.max(warning, 1e-6));
  if (value <= critical) {
    const span = Math.max(critical - warning, 1e-6);
    return 0.6 + 0.4 * ((value - warning) / span);
  }
  return Math.min(1.15, 1.0 + 0.15 * ((value - critical) / Math.max(critical, 1e-6)));
};

/**
 * 从 SensorPayload 直接计算 6 个工艺单元的多指标状态；SSE sensor_data 事件走这里，
 * 保证热力外壳与标签的 reactive 更新比 REST overview 轮询快一个数量级。
 */
export const buildEmitterConcentrations = (
  sensor: SensorPayload,
): Record<string, EmitterConcentration> => {
  const out: Record<string, EmitterConcentration> = {};
  for (const cfg of EMITTER_DEFINITIONS) {
    const indicators: EmitterIndicator[] = [];
    let maxRatio = 0;
    let worst: "normal" | "warning" | "critical" = "normal";

    for (const ind of cfg.indicators) {
      const raw = Number(sensor[ind.field] ?? 0);
      const ratio = indicatorRatio(raw, ind.warning, ind.critical);
      const level = levelFor(raw, ind.warning, ind.critical);
      if (ratio > maxRatio) maxRatio = ratio;
      if (level === "critical" || (level === "warning" && worst === "normal")) {
        worst = level;
      }
      indicators.push({
        field: ind.field,
        label: ind.label,
        value: Number(raw.toFixed(2)),
        unit: ind.unit,
        warning: ind.warning,
        critical: ind.critical,
        ratio: Number(ratio.toFixed(3)),
        level,
      });
    }

    const primary = indicators[0];
    out[cfg.id] = {
      label: cfg.label,
      anchor: cfg.anchor,
      indicators,
      maxRatio: Number(maxRatio.toFixed(3)),
      level: worst,
      // 主指标直通副本
      field: primary.field,
      value: primary.value,
      unit: primary.unit,
      warning: primary.warning,
      critical: primary.critical,
    };
  }
  return out;
};

/**
 * 风场派生仍然保留，虽然 heat shell 方案不直接用，但 WindField 类型仍在 store 里
 * 保留；将来若恢复粒子风场可以直接复用。
 */
export const buildWindField = (sensor: SensorPayload) => {
  const fan = Number(sensor.adsorption_fan_power ?? 0);
  const speed = Math.max(0.25, Math.min(1, fan / 45));
  return {
    direction: [-1, 0.35, 0.2] as [number, number, number],
    speed: Number(speed.toFixed(3)),
  };
};
