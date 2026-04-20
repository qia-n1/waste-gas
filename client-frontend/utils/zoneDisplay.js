/**
 * 将后端区域名转为界面展示用中文车间/厂房名称。
 * 业务关系：涂装车间布置在喷涂厂房（喷涂生产厂房）内。
 * 命名与 admin 端厂区节点（如 FactoryScene）及区域表一致。
 */

import { displaySensorFieldLabel } from './sensorDisplay';

/** 后端历史别名：zsq 种子曾用「涂装车间」作区域名，与喷涂生产厂房为同一工艺单元 */
function canonicalAreaName(area) {
  const a = String(area || '').trim();
  if (a === '涂装车间') return '喷涂生产厂房';
  return a;
}

const ZONE_DISPLAY = {
  喷涂生产厂房: '喷涂生产厂房',
  排口烟囱区: '排口烟囱区',
  转轮吸附厂房: '转轮吸附厂房',
  'RTO 主处理厂房': 'RTO 主处理厂房',
  公辅燃烧区: '公辅燃烧区',
  监测附属区: '监测附属区',
  'A区处理车间': '甲区处理车间',
  'B区吸附站': '乙区吸附站',
};

export function displayZoneTitle(name) {
  const n = String(name || '').trim();
  if (!n) return '';
  const key = canonicalAreaName(n);
  return ZONE_DISPLAY[key] || ZONE_DISPLAY[n] || key;
}

/**
 * 地图缩放后标点：与 admin 三维图一致——主标题为点位/指标名，次行「区域名 + 工艺单元」。
 */
function mapPointPrimaryTitle(rawName) {
  const r = String(rawName || '').trim();
  if (!r) return '';
  // 后端英文指标键：用 sensorMeta 中文名（喷涂风量、RTO入口浓度等）
  const sensorLabel = displaySensorFieldLabel(r);
  if (sensorLabel !== r) return sensorLabel;
  // 与建模图一致的固定中文点名
  const fixed = {
    监测点位: '监测点位',
    关键设备: '关键设备',
    '1号排口': '1号排口',
    烟囱监测点: '烟囱监测点',
    转轮出口: '转轮出口',
    公辅监测点: '公辅监测点',
  };
  if (fixed[r]) return fixed[r];
  return r;
}

export function formatPointMapLabel(point) {
  const rawName = String(point?.name || '');
  const area = canonicalAreaName(point?.areaName);
  const zone = displayZoneTitle(area) || '厂区';
  const primary = mapPointPrimaryTitle(rawName);
  // 与建模图建筑标签一致：主标题 + 副标题「区域名 · 工艺单元」
  const sub = `${zone} · 工艺单元`;
  return primary ? `${primary}\n${sub}` : sub;
}

/**
 * 地图默认缩放下的短标签：优先与厂区示意图点位命名一致，确保“点位文字”和“标记点”一一对应。
 */
export function formatPointMarkerLabel(point) {
  const area = canonicalAreaName(point?.areaName);
  const byArea = {
    喷涂生产厂房: '监测点位',
    排口烟囱区: '烟囱监测点',
    转轮吸附厂房: '转轮出口',
    'RTO 主处理厂房': '关键设备',
    公辅燃烧区: '公辅监测点',
    监测附属区: '1号排口',
  };
  return byArea[area] || mapPointPrimaryTitle(point?.name || '');
}
