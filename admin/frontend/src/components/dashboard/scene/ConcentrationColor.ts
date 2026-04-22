import * as THREE from "three";

/**
 * 浓度 → 视觉属性映射。
 *
 * 低浓度：青色、稀疏、小粒径、快速飘散
 * 预警：琥珀色、中等密度、拖尾变长
 * 超标：饱和红、密集、大粒径、强脉冲
 *
 * 归一比 ratio = value / critical，裁剪到 [0, 1.2]（给超标一点 overshoot）。
 */
export interface ConcentrationVisual {
  color: THREE.Color;
  emitRate: number; // 每秒发射粒子数
  sizeScale: number; // 粒径系数
  lifeScale: number; // 寿命系数
}

const HUE_COLD = 190 / 360; // 青
const HUE_WARM = 10 / 360; // 红

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

const cachedColor = new THREE.Color();

export const mapConcentrationToVisual = (
  value: number,
  warning: number,
  critical: number,
): ConcentrationVisual => {
  const ratio = clamp(value / Math.max(critical, 1e-6), 0, 1.2);
  const hue = HUE_COLD + (HUE_WARM - HUE_COLD) * clamp(ratio, 0, 1);
  const sat = 0.55 + 0.35 * clamp(ratio, 0, 1);
  const light = 0.5 + 0.1 * clamp(ratio, 0, 1);
  cachedColor.setHSL(hue, sat, light);

  // 预警/超标超过阈值后显著抬升发射速率，让视觉强度可被立刻感知
  const warnRatio = value / Math.max(warning, 1e-6);
  const emitRate = 6 + 20 * clamp(warnRatio, 0, 1) + 30 * Math.max(0, ratio - 0.8);

  return {
    color: cachedColor.clone(),
    emitRate: Math.min(emitRate, 80),
    sizeScale: 1 + 1.5 * clamp(ratio, 0, 1),
    lifeScale: 1 + 0.8 * clamp(ratio, 0, 1),
  };
};
