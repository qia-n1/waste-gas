import * as THREE from "three";

import type { EmitterDefinition } from "./EmitterConfig";
import {
  mapConcentrationToVisual,
  type ConcentrationVisual,
} from "./ConcentrationColor";

/**
 * 基于 Three.js Points 的粒子系统，用于在 FactoryScene 3D 场景里可视化 VOCs 浓度分布。
 *
 * 架构：
 * - 单一 Points 对象 + BufferGeometry（MAX_PARTICLES 预分配），只有 1 次 draw call
 * - 每帧 CPU 遍历粒子更新 position/velocity/life；粒子属性用 typed array 直接写
 * - 发射器按 emitRate 累加器投放新粒子，随风场扩散，寿命到即回收（环形指针）
 * - ShaderMaterial 做 additive blending + 圆形柔边，多粒子叠加自然形成云雾
 *
 * 用法：
 *   const heatmap = new ParticleHeatmap(scene, definitions)
 *   heatmap.updateEmitter("stack", 95.3, "warning")
 *   heatmap.updateWind([-1, 0.3, 0.2], 0.8)
 *   // 在 requestAnimationFrame 循环里：
 *   heatmap.tick(deltaSeconds)
 *   // 退出时：
 *   heatmap.dispose()
 */

export type AlertLevel = "normal" | "warning" | "critical";

interface EmitterRuntime {
  def: EmitterDefinition;
  visual: ConcentrationVisual;
  level: AlertLevel;
  accumulator: number; // 粒子投放累加器（秒 × emitRate）
  pulsePhase: number; // critical 状态下的闪烁相位
}

const MAX_PARTICLES = 3000;
const BASE_MAX_LIFE = 2.6; // 基础寿命（秒）
const PARTICLE_BASE_SIZE = 28; // shader 里的基础尺寸（像素）

const VERT_SHADER = /* glsl */ `
  attribute float aLife;
  attribute float aSize;
  attribute vec3 aColor;

  varying float vLife;
  varying vec3 vColor;

  void main() {
    vLife = aLife;
    vColor = aColor;

    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    // 尺寸按寿命和相机距离衰减：寿命末期缩小，远处按透视缩小
    float lifeFade = smoothstep(0.0, 0.25, aLife) * smoothstep(1.0, 0.6, aLife);
    gl_PointSize = aSize * (300.0 / -mv.z) * (0.4 + 0.8 * lifeFade);
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAG_SHADER = /* glsl */ `
  precision mediump float;

  varying float vLife;
  varying vec3 vColor;

  void main() {
    if (vLife <= 0.0) discard;
    vec2 uv = gl_PointCoord - vec2(0.5);
    float d = length(uv);
    if (d > 0.5) discard;
    // 柔边：中心强外圈弱，additive 叠加后就是云雾
    float alpha = smoothstep(0.5, 0.0, d) * (0.35 + 0.65 * vLife);
    gl_FragColor = vec4(vColor * (0.7 + 0.3 * vLife), alpha);
  }
`;

export class ParticleHeatmap {
  // 挂载父节点，可以是 Scene 根或者 Group（场景里 campusGroup 会整体旋转/浮动，
  // 把粒子挂在 campusGroup 下，粒子云会跟着园区一起动，视觉保持相对静止）
  private readonly parent: THREE.Object3D;
  private readonly geometry: THREE.BufferGeometry;
  private readonly material: THREE.ShaderMaterial;
  private readonly points: THREE.Points;

  private readonly positions: Float32Array;
  private readonly velocities: Float32Array;
  private readonly colors: Float32Array;
  private readonly sizes: Float32Array;
  private readonly lives: Float32Array;
  // 每个粒子所属发射器索引，回收时不需要，调试用
  private readonly owners: Int16Array;

  private readonly emitters = new Map<string, EmitterRuntime>();
  private writeCursor = 0;

  private windDir = new THREE.Vector3(-1, 0.35, 0.2).normalize();
  private windSpeed = 0.6;

  private readonly tmpV = new THREE.Vector3();

  constructor(parent: THREE.Object3D, defs: EmitterDefinition[]) {
    this.parent = parent;

    this.positions = new Float32Array(MAX_PARTICLES * 3);
    this.velocities = new Float32Array(MAX_PARTICLES * 3);
    this.colors = new Float32Array(MAX_PARTICLES * 3);
    this.sizes = new Float32Array(MAX_PARTICLES);
    this.lives = new Float32Array(MAX_PARTICLES);
    this.owners = new Int16Array(MAX_PARTICLES);

    // 寿命全部初始 0 → 空槽
    this.lives.fill(0);

    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute(
      "position",
      new THREE.BufferAttribute(this.positions, 3).setUsage(THREE.DynamicDrawUsage),
    );
    this.geometry.setAttribute(
      "aColor",
      new THREE.BufferAttribute(this.colors, 3).setUsage(THREE.DynamicDrawUsage),
    );
    this.geometry.setAttribute(
      "aSize",
      new THREE.BufferAttribute(this.sizes, 1).setUsage(THREE.DynamicDrawUsage),
    );
    this.geometry.setAttribute(
      "aLife",
      new THREE.BufferAttribute(this.lives, 1).setUsage(THREE.DynamicDrawUsage),
    );

    this.material = new THREE.ShaderMaterial({
      vertexShader: VERT_SHADER,
      fragmentShader: FRAG_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.points = new THREE.Points(this.geometry, this.material);
    this.points.frustumCulled = false; // 粒子常超出原点 AABB，关掉剔除更稳
    this.points.renderOrder = 5;
    parent.add(this.points);

    for (const def of defs) {
      this.emitters.set(def.id, {
        def,
        visual: mapConcentrationToVisual(0, def.warning, def.critical),
        level: "normal",
        accumulator: 0,
        pulsePhase: 0,
      });
    }
  }

  updateEmitter(id: string, value: number, level: AlertLevel): void {
    const rt = this.emitters.get(id);
    if (!rt) return;
    rt.visual = mapConcentrationToVisual(value, rt.def.warning, rt.def.critical);
    rt.level = level;
  }

  updateWind(direction: [number, number, number], speed: number): void {
    this.tmpV.set(direction[0], direction[1], direction[2]);
    if (this.tmpV.lengthSq() > 1e-6) {
      this.windDir.copy(this.tmpV).normalize();
    }
    this.windSpeed = Math.max(0, speed);
  }

  /** 每帧调用（deltaSeconds = 上一帧耗时秒数）。 */
  tick(dt: number): void {
    const safeDt = Math.min(dt, 0.1); // 卡顿时兜底

    // 1) 各发射器按 emitRate 投放新粒子
    for (const rt of this.emitters.values()) {
      let rate = rt.visual.emitRate;
      // critical 状态下闪烁：60% 基础 + 40% sin(6Hz)
      if (rt.level === "critical") {
        rt.pulsePhase += safeDt * 6;
        rate *= 0.6 + 0.8 * Math.abs(Math.sin(rt.pulsePhase));
      }
      rt.accumulator += safeDt * rate;
      while (rt.accumulator >= 1) {
        rt.accumulator -= 1;
        this.spawnParticle(rt);
      }
    }

    // 2) 遍历所有粒子推进物理
    for (let i = 0; i < MAX_PARTICLES; i++) {
      if (this.lives[i] <= 0) continue;
      const base = i * 3;

      // life 归一递减（寿命到 → 下次循环跳过，对应的 draw 被 shader discard）
      this.lives[i] -= safeDt / BASE_MAX_LIFE;
      if (this.lives[i] <= 0) {
        this.lives[i] = 0;
        continue;
      }

      // velocity += wind * dt + buoyancy
      this.velocities[base] += this.windDir.x * this.windSpeed * 0.25 * safeDt;
      this.velocities[base + 1] += (0.3 + this.windDir.y * this.windSpeed) * 0.5 * safeDt;
      this.velocities[base + 2] += this.windDir.z * this.windSpeed * 0.25 * safeDt;

      // position += velocity * dt
      this.positions[base] += this.velocities[base] * safeDt;
      this.positions[base + 1] += this.velocities[base + 1] * safeDt;
      this.positions[base + 2] += this.velocities[base + 2] * safeDt;
    }

    this.geometry.attributes.position.needsUpdate = true;
    this.geometry.attributes.aLife.needsUpdate = true;
    this.geometry.attributes.aColor.needsUpdate = true;
    this.geometry.attributes.aSize.needsUpdate = true;
  }

  dispose(): void {
    this.parent.remove(this.points);
    this.geometry.dispose();
    this.material.dispose();
    this.emitters.clear();
  }

  // -------------------------------------------------------------------------
  // private helpers
  // -------------------------------------------------------------------------

  private spawnParticle(rt: EmitterRuntime): void {
    const idx = this.findSlot();
    if (idx < 0) return;
    const base = idx * 3;
    const [ax, ay, az] = rt.def.anchor;

    // anchor 小范围 jitter，让发射不像单点
    const jx = (Math.random() - 0.5) * 0.6;
    const jy = (Math.random() - 0.2) * 0.4; // 略微偏上，模拟烟气初始位置在排放口上方
    const jz = (Math.random() - 0.5) * 0.6;
    this.positions[base] = ax + jx;
    this.positions[base + 1] = ay + jy + 0.4;
    this.positions[base + 2] = az + jz;

    // 初速度：向上 + 风向 + 一点随机（让粒子有膨胀感）
    const spread = 0.35;
    this.velocities[base] =
      this.windDir.x * this.windSpeed * 0.5 + (Math.random() - 0.5) * spread;
    this.velocities[base + 1] = 0.5 + Math.random() * 0.35; // 始终有上升趋势
    this.velocities[base + 2] =
      this.windDir.z * this.windSpeed * 0.5 + (Math.random() - 0.5) * spread;

    // 颜色 / 尺寸 / 寿命
    const c = rt.visual.color;
    this.colors[base] = c.r;
    this.colors[base + 1] = c.g;
    this.colors[base + 2] = c.b;
    this.sizes[idx] = PARTICLE_BASE_SIZE * rt.visual.sizeScale;
    this.lives[idx] = Math.min(1, rt.visual.lifeScale); // 归一寿命 [0,1]
    this.owners[idx] = this.emitterIndex(rt.def.id);
  }

  /** 环形指针找空槽；若全占用（极端高密度）覆盖最老位置。 */
  private findSlot(): number {
    for (let tries = 0; tries < MAX_PARTICLES; tries++) {
      const i = this.writeCursor;
      this.writeCursor = (this.writeCursor + 1) % MAX_PARTICLES;
      if (this.lives[i] <= 0) return i;
    }
    // 全占用：返回当前 cursor，等于覆盖最老粒子（罕见）
    return this.writeCursor;
  }

  private emitterIndex(id: string): number {
    let i = 0;
    for (const key of this.emitters.keys()) {
      if (key === id) return i;
      i++;
    }
    return -1;
  }
}
