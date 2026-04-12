export interface SensorMetaItem {
  field: string;
  label: string;
  unit: string;
  group: string;
}

export const sensorMeta: SensorMetaItem[] = [
  { field: "ambient_temp", label: "环境温度", unit: "°C", group: "气象" },
  { field: "ambient_humidity", label: "环境湿度", unit: "%", group: "气象" },
  { field: "ambient_pressure", label: "环境压力", unit: "kPa", group: "气象" },
  { field: "coating_flow", label: "喷涂风量", unit: "m³/h", group: "喷涂段" },
  { field: "coating_conc", label: "喷涂浓度", unit: "mg/m³", group: "喷涂段" },
  { field: "coating_temp", label: "喷涂温度", unit: "°C", group: "喷涂段" },
  { field: "coating_pressure", label: "喷涂压力", unit: "kPa", group: "喷涂段" },
  { field: "rotor_speed", label: "转轮转速", unit: "rpm", group: "转轮段" },
  { field: "adsorption_fan_power", label: "吸附风机功率", unit: "kW", group: "转轮段" },
  { field: "desorption_fan_power", label: "脱附风机功率", unit: "kW", group: "转轮段" },
  { field: "rotor_inlet_temp", label: "转轮入口温度", unit: "°C", group: "转轮段" },
  { field: "rotor_inlet_humid", label: "转轮入口湿度", unit: "%", group: "转轮段" },
  { field: "desorption_temp", label: "脱附温度", unit: "°C", group: "脱附段" },
  { field: "concentrated_flow", label: "浓缩风量", unit: "m³/h", group: "浓缩段" },
  { field: "concentrated_conc", label: "浓缩浓度", unit: "mg/m³", group: "浓缩段" },
  { field: "concentrated_temp", label: "浓缩温度", unit: "°C", group: "浓缩段" },
  { field: "concentrated_pressure", label: "浓缩压力", unit: "kPa", group: "浓缩段" },
  { field: "rto_in_flow", label: "RTO入口流量", unit: "m³/h", group: "RTO" },
  { field: "rto_in_conc", label: "RTO入口浓度", unit: "mg/m³", group: "RTO" },
  { field: "rto_in_temp", label: "RTO入口温度", unit: "°C", group: "RTO" },
  { field: "rto_in_pressure", label: "RTO入口压力", unit: "kPa", group: "RTO" },
  { field: "burner_gas_flow", label: "燃烧器气体流量", unit: "Nm³/h", group: "焚烧" },
  { field: "combustion_temp", label: "燃烧温度", unit: "°C", group: "焚烧" },
  { field: "rto_out_conc", label: "RTO出口浓度", unit: "mg/m³", group: "排口" },
  { field: "rto_out_temp", label: "RTO出口温度", unit: "°C", group: "排口" },
];

export const highlightedSensorFields = [
  "rto_out_conc",
  "rto_in_conc",
  "combustion_temp",
  "burner_gas_flow",
  "coating_conc",
  "ambient_temp",
];
