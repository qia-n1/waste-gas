/**
 * 监测字段中文名，与 admin/frontend/src/utils/sensorMeta.ts 的 label 保持一致。
 */

const SENSOR_FIELD_LABELS = {
  ambient_temp: '环境温度',
  ambient_humidity: '环境湿度',
  ambient_pressure: '环境压力',
  coating_flow: '喷涂风量',
  coating_conc: '喷涂浓度',
  coating_temp: '喷涂温度',
  coating_pressure: '喷涂压力',
  rotor_speed: '转轮转速',
  adsorption_fan_power: '吸附风机功率',
  desorption_fan_power: '脱附风机功率',
  rotor_inlet_temp: '转轮入口温度',
  rotor_inlet_humid: '转轮入口湿度',
  desorption_temp: '脱附温度',
  concentrated_flow: '浓缩风量',
  concentrated_conc: '浓缩浓度',
  concentrated_temp: '浓缩温度',
  concentrated_pressure: '浓缩压力',
  rto_in_flow: 'RTO入口流量',
  rto_in_conc: 'RTO入口浓度',
  rto_in_temp: 'RTO入口温度',
  rto_in_pressure: 'RTO入口压力',
  burner_gas_flow: '燃烧器气体流量',
  combustion_temp: '燃烧温度',
  rto_out_conc: 'RTO出口浓度',
  rto_out_temp: 'RTO出口温度',
};

/** 废气源/排口等中文点名（与 admin 建模图一致） */
const SOURCE_NAME_LABELS = {
  监测点位: '监测点位',
};

/**
 * @param {string} raw 后端 source_name 或传感器字段名
 * @returns {string} 管理员端一致的中文名；未知则原样返回
 */
export function displaySensorFieldLabel(raw) {
  const k = String(raw || '').trim();
  if (!k) return '';
  if (SOURCE_NAME_LABELS[k]) return SOURCE_NAME_LABELS[k];
  if (SENSOR_FIELD_LABELS[k]) return SENSOR_FIELD_LABELS[k];
  return k;
}
