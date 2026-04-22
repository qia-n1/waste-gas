import type {
  EmitterConcentration,
  EmitterIndicator,
  SensorPayload,
} from "@/types/dashboard";

export interface EmitterIndicatorConfig {
  field: keyof SensorPayload;
  label: string;
  unit: string;
  warning: number;
  critical: number;
}

export interface HeatHotspotConfig {
  /**
   * Normalized local-space position inside the shell mesh.
   * Range is roughly [-1, 1] on each axis after dividing by shell half-size.
   */
  position: [number, number, number];
  /**
   * Normalized spread radius. Larger values make hotspots connect into one
   * continuous heat layer instead of isolated blobs.
   */
  spread: number;
}

export interface EmitterDefinition {
  id: string;
  label: string;
  anchor: [number, number, number];
  /**
   * Primary indicator thresholds kept for legacy particle-heatmap code.
   */
  warning: number;
  critical: number;
  indicators: EmitterIndicatorConfig[];
  shell: {
    kind: "box" | "cylinder";
    size: [number, number, number];
    center: [number, number, number];
    hotspots: HeatHotspotConfig[];
  };
}

type EmitterDefinitionInput = Omit<EmitterDefinition, "warning" | "critical">;

const makeEmitter = (definition: EmitterDefinitionInput): EmitterDefinition => ({
  ...definition,
  warning: definition.indicators[0].warning,
  critical: definition.indicators[0].critical,
});

export const EMITTER_DEFINITIONS: EmitterDefinition[] = [
  makeEmitter({
    id: "coating",
    label: "喷涂生产厂房",
    anchor: [-3.6, 1.7, 2.55],
    indicators: [
      { field: "coating_conc", label: "喷涂", unit: "mg/m³", warning: 80, critical: 120 },
      { field: "coating_temp", label: "温度", unit: "°C", warning: 40, critical: 55 },
      { field: "coating_flow", label: "风量", unit: "m³/h", warning: 14000, critical: 18000 },
    ],
    shell: {
      kind: "box",
      size: [3.6, 1.6, 2.2],
      center: [-3.6, 0.75, 2.55],
      hotspots: [
        { position: [-0.58, -0.18, 0.22], spread: 0.94 },
        { position: [-0.02, 0.2, -0.1], spread: 0.82 },
        { position: [0.56, -0.08, -0.34], spread: 0.92 },
      ],
    },
  }),
  makeEmitter({
    id: "rotor",
    label: "转轮吸附厂房",
    anchor: [-1.05, 1.85, 1.85],
    indicators: [
      { field: "concentrated_conc", label: "转轮", unit: "mg/m³", warning: 150, critical: 250 },
      { field: "rotor_inlet_temp", label: "入口温度", unit: "°C", warning: 45, critical: 55 },
      { field: "rotor_speed", label: "转速", unit: "rpm", warning: 7, critical: 10 },
    ],
    shell: {
      kind: "box",
      size: [3.1, 1.75, 2.0],
      center: [-1.05, 0.83, 1.85],
      hotspots: [
        { position: [-0.52, -0.08, -0.16], spread: 0.9 },
        { position: [0.02, 0.3, 0.14], spread: 0.8 },
        { position: [0.54, -0.16, 0.28], spread: 0.88 },
      ],
    },
  }),
  makeEmitter({
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
      hotspots: [
        { position: [-0.56, 0.14, -0.2], spread: 0.98 },
        { position: [0.0, -0.06, 0.02], spread: 0.9 },
        { position: [0.56, 0.22, 0.2], spread: 0.98 },
      ],
    },
  }),
  makeEmitter({
    id: "utility",
    label: "公辅燃烧区",
    anchor: [5.15, 1.45, 2.55],
    indicators: [
      { field: "desorption_temp", label: "脱附", unit: "°C", warning: 180, critical: 220 },
      { field: "burner_gas_flow", label: "燃气", unit: "Nm³/h", warning: 80, critical: 110 },
      { field: "adsorption_fan_power", label: "风机", unit: "kW", warning: 40, critical: 50 },
    ],
    shell: {
      kind: "box",
      size: [2.9, 1.3, 1.65],
      center: [5.15, 0.65, 2.55],
      hotspots: [
        { position: [-0.44, 0.12, -0.08], spread: 0.9 },
        { position: [0.06, -0.02, 0.08], spread: 0.82 },
        { position: [0.56, -0.1, 0.22], spread: 0.88 },
      ],
    },
  }),
  makeEmitter({
    id: "stack",
    label: "排口烟囱区",
    anchor: [-5.45, 4.95, -0.55],
    indicators: [
      { field: "rto_out_conc", label: "排口", unit: "mg/m³", warning: 80, critical: 100 },
      { field: "rto_out_temp", label: "温度", unit: "°C", warning: 200, critical: 260 },
    ],
    shell: {
      kind: "cylinder",
      size: [0.55, 5.2, 0.6],
      center: [-5.45, 2.6, -0.55],
      hotspots: [
        { position: [0.12, -0.28, 0.44], spread: 1.02 },
        { position: [-0.18, 0.24, -0.22], spread: 0.94 },
      ],
    },
  }),
  makeEmitter({
    id: "public",
    label: "监测附属区",
    anchor: [5.4, 1.1, 4.0],
    indicators: [
      { field: "ambient_humidity", label: "湿度", unit: "%", warning: 85, critical: 95 },
      { field: "ambient_temp", label: "环境", unit: "°C", warning: 32, critical: 38 },
      { field: "ambient_pressure", label: "压力", unit: "kPa", warning: 101.8, critical: 102.5 },
    ],
    shell: {
      kind: "box",
      size: [2.1, 0.85, 1.2],
      center: [1.85, 0.45, 4.05],
      hotspots: [
        { position: [-0.56, 0.04, -0.16], spread: 0.9 },
        { position: [0.0, 0.22, 0.06], spread: 0.8 },
        { position: [0.56, -0.12, 0.18], spread: 0.88 },
      ],
    },
  }),
];

const levelFor = (value: number, warning: number, critical: number) => {
  if (value >= critical) return "critical" as const;
  if (value >= warning) return "warning" as const;
  return "normal" as const;
};

const indicatorRatio = (value: number, warning: number, critical: number): number => {
  if (critical <= 0 || value <= 0) return 0;
  if (value <= warning) return 0.6 * (value / Math.max(warning, 1e-6));
  if (value <= critical) {
    const span = Math.max(critical - warning, 1e-6);
    return 0.6 + 0.4 * ((value - warning) / span);
  }
  return Math.min(1.15, 1.0 + 0.15 * ((value - critical) / Math.max(critical, 1e-6)));
};

export const buildEmitterConcentrations = (
  sensor: SensorPayload,
): Record<string, EmitterConcentration> => {
  const output: Record<string, EmitterConcentration> = {};

  for (const definition of EMITTER_DEFINITIONS) {
    const indicators: EmitterIndicator[] = [];
    let maxRatio = 0;
    let worstLevel: "normal" | "warning" | "critical" = "normal";

    for (const indicatorConfig of definition.indicators) {
      const rawValue = Number(sensor[indicatorConfig.field] ?? 0);
      const ratio = indicatorRatio(
        rawValue,
        indicatorConfig.warning,
        indicatorConfig.critical,
      );
      const level = levelFor(
        rawValue,
        indicatorConfig.warning,
        indicatorConfig.critical,
      );

      if (ratio > maxRatio) maxRatio = ratio;
      if (level === "critical" || (level === "warning" && worstLevel === "normal")) {
        worstLevel = level;
      }

      indicators.push({
        field: indicatorConfig.field,
        label: indicatorConfig.label,
        value: Number(rawValue.toFixed(2)),
        unit: indicatorConfig.unit,
        warning: indicatorConfig.warning,
        critical: indicatorConfig.critical,
        ratio: Number(ratio.toFixed(3)),
        level,
      });
    }

    const primaryIndicator = indicators[0];
    output[definition.id] = {
      label: definition.label,
      anchor: definition.anchor,
      indicators,
      maxRatio: Number(maxRatio.toFixed(3)),
      level: worstLevel,
      field: primaryIndicator.field,
      value: primaryIndicator.value,
      unit: primaryIndicator.unit,
      warning: primaryIndicator.warning,
      critical: primaryIndicator.critical,
    };
  }

  return output;
};

export const buildWindField = (sensor: SensorPayload) => {
  const fanPower = Number(sensor.adsorption_fan_power ?? 0);
  const speed = Math.max(0.25, Math.min(1, fanPower / 45));
  return {
    direction: [-1, 0.35, 0.2] as [number, number, number],
    speed: Number(speed.toFixed(3)),
  };
};
