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

export interface DashboardOverview {
  timestamp: string;
  metrics: DashboardMetrics;
  trend: DashboardTrend;
  statusBanner: StatusBanner;
  keyParameters: KeyParameter[];
  decision: DecisionContent;
  continuousAlerts: ContinuousAlert[];
  factoryNodes: FactoryNode[];
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
  weight: number;
}

export interface DiagnosisResponse {
  alertId: string;
  summary: string;
  recommendations: string[];
  contributors: DiagnosisContributor[];
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
