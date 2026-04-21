export interface TrendPoint {
  timestamp: string;
  value: number;
}

export interface DashboardMetrics {
  currentVocs: number;
  peakForecast: number;
  alertLevel: string;
  onlineDevices: number;
  totalDevices: number;
  todayAlerts: number;
  systemPhase: string;
  uptime: string;
  confidence: number;
  dataCompleteness: number;
  latencyMs: number;
  predictionType: string;
}

export interface DashboardTrend {
  actualSeries: TrendPoint[];
  forecastSeries: TrendPoint[];
  warningThreshold: number;
  criticalThreshold: number;
  confidence: number;
}

export interface StatusBanner {
  severity: string;
  text: string;
}

export interface KeyParameter {
  field: string;
  label: string;
  value: number;
  unit: string;
}

export interface DecisionContent {
  summary: string;
  suggestions: string[];
}

export interface ContinuousAlert {
  id: string;
  level: string;
  message: string;
  location: string;
  elapsed_seconds: number;
}

export interface FactoryNode {
  id: string;
  label: string;
  status: string;
  x: number;
  y: number;
}

export interface TopContributorSeries {
  feature: string;
  label: string;
  unit: string;
  group: string;
  ratio: number;
  contribution: number;
  currentValue: number;
  meanValue: number;
  maxValue: number;
  minValue: number;
  series: TrendPoint[];
}

export interface EmitterIndicator {
  field: string;
  label: string;
  value: number;
  unit: string;
  warning: number;
  critical: number;
  /** 0~1.15，按 _indicator_ratio 分段归一。1.0 = critical，>1 = 超标。 */
  ratio: number;
  level: "normal" | "warning" | "critical";
}

export interface EmitterConcentration {
  label: string;
  anchor: [number, number, number];
  /** 2~3 个工艺指标，indicators[0] = 主指标（决定 emitter-history 弹窗曲线）。 */
  indicators: EmitterIndicator[];
  /** 所有指标中的最大 ratio，用于热力外壳的颜色强度。 */
  maxRatio: number;
  /** 整体告警等级（indicators 里最坏的那个）。 */
  level: "normal" | "warning" | "critical";
  // 以下字段是主指标的直通副本，保留给只读取顶层 value/field/unit/... 的调用点
  field: string;
  value: number;
  unit: string;
  warning: number;
  critical: number;
}

export type EmitterConcentrations = Record<string, EmitterConcentration>;

export interface WindField {
  direction: [number, number, number];
  speed: number;
}

export interface EmitterHistoryResponse {
  id: string;
  label: string;
  field: string;
  unit: string;
  warning: number;
  critical: number;
  currentValue: number;
  minValue: number;
  maxValue: number;
  avgValue: number;
  level: "normal" | "warning" | "critical";
  points: TrendPoint[];
}

export interface DashboardOverview {
  timestamp: string;
  metrics: DashboardMetrics;
  trend: DashboardTrend;
  statusBanner: StatusBanner;
  keyParameters: KeyParameter[];
  decision: DecisionContent;
  continuousAlerts: ContinuousAlert[];
  factoryNodes: FactoryNode[];
  attribution?: Attribution;
  topContributorSeries?: TopContributorSeries[];
  emitterConcentrations?: EmitterConcentrations;
  windField?: WindField;
}

export interface EquipmentStatusItem {
  name: string;
  value: number;
  color: string;
}

export interface EquipmentStatusResponse {
  total: number;
  online: number;
  items: EquipmentStatusItem[];
}

export interface FeatureContribution {
  feature: string;
  group: string;
  ratio: number;
  contribution: number;
}

export interface GroupContribution {
  group: string;
  contribution: number;
}

export interface Attribution {
  baseline: number;
  target: number;
  total_increment: number;
  feature_contributions: FeatureContribution[];
  group_contributions: GroupContribution[];
  heatmap?: {
    time_steps: string[];
    feature_groups: string[];
    contribution_matrix: number[][];
  };
}

export interface HeatmapResponse {
  dates: string[];
  hours: number[];
  values: number[][];
}

export interface AlertItem {
  alert_id: string;
  timestamp: string;
  level: string;
  message: string;
  value: number;
  threshold: number;
  acknowledged: boolean;
  location: string;
  status: string;
}

export interface AlertsResponse {
  items: AlertItem[];
  total: number;
  byLevel: Record<string, number>;
}

export interface DiagnosisContributor {
  label: string;
  group?: string;
  weight: number;
  contribution?: number;
}

export interface RagCard {
  title: string;
  suggestionShort: string;
  sopSteps: string[];
  safetyRedline: string;
  standard: string;
  level: string;
  reason?: string;
  version?: number | null;
  generatedAt?: string | null;
  fromCache?: boolean;
}

export interface DiagnosisResponse {
  alertId: string;
  summary: string;
  recommendations: string[];
  contributors: DiagnosisContributor[];
  groupContributions?: GroupContribution[];
  baseline?: number | null;
  target?: number | null;
  totalIncrement?: number | null;
  ragCard?: RagCard | null;
}

export interface SensorPayload {
  timestamp: string;
  ambient_temp: number;
  ambient_humidity: number;
  ambient_pressure: number;
  coating_flow: number;
  coating_conc: number;
  coating_temp: number;
  coating_pressure: number;
  rotor_speed: number;
  adsorption_fan_power: number;
  desorption_fan_power: number;
  rotor_inlet_temp: number;
  rotor_inlet_humid: number;
  desorption_temp: number;
  concentrated_flow: number;
  concentrated_conc: number;
  concentrated_temp: number;
  concentrated_pressure: number;
  rto_in_flow: number;
  rto_in_conc: number;
  rto_in_temp: number;
  rto_in_pressure: number;
  burner_gas_flow: number;
  combustion_temp: number;
  rto_out_conc: number;
  rto_out_temp: number;
}

export interface PredictionPayload {
  timestamp: string;
  prediction_horizon: number;
  predicted_values: number[];
  confidence: number;
  alert_triggered: boolean;
  alert_message: string;
  prediction_type: string;
}
