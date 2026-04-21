/**
 * 热力外壳 —— 把工艺单元的多指标浓度以"发光半透明罩"的形式贴在建筑上。
 *
 * 设计要点：
 *   1. 每个工艺单元用一个 mesh（box 或 cylinder）略大于建筑本体，
 *      材质是自定义 ShaderMaterial + AdditiveBlending，避免挡住原 mesh。
 *   2. 色彩：uRatio uniform 0~1.15 驱动 heatmapColor(cyan→yellow→orange→red)，
 *      再叠一层垂直方向的亮度梯度（底亮顶暗），呼应"热气从底部往上散"的感觉。
 *   3. uPulse 轻微脉动，critical 级 mesh 脉动幅度更大，作视觉高亮。
 *   4. uRatio 更新时用一阶低通插值到目标值，避免浓度跳变导致颜色闪烁。
 *
 * 对外 API：
 *   - new HeatShellSet(scene, EMITTER_DEFINITIONS)  创建并加入场景
 *   - updateFromConcentrations(concs)               传入 store 的最新浓度
 *   - tick(dt, elapsed)                              每帧调用，更新 uniform
 *   - dispose()
 */
import * as THREE from "three";

import type { EmitterConcentration } from "@/types/dashboard";
import type { EmitterDefinition } from "./EmitterConfig";

interface ShellEntry {
  id: string;
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
  targetRatio: number;
  currentRatio: number;
  /** 0 normal / 1 warning / 2 critical（shader 里拿来加脉动幅度） */
  targetLevel: number;
  currentLevel: number;
}

const VERTEX_SHADER = /* glsl */ `
  varying vec3 vLocalPos;
  varying vec3 vNormal;

  void main() {
    vLocalPos = position;
    vNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

/**
 * 颜色映射：与右侧 HUD 图例色条同源（浅青→青绿→黄→橙→红）。
 * 和 FactoryScene 的 .heatmap-hud__scale-bar linear-gradient 断点保持一致。
 */
const FRAGMENT_SHADER = /* glsl */ `
  uniform float uRatio;
  uniform float uPulse;
  uniform float uLevel;
  uniform vec3  uHalfSize;

  varying vec3 vLocalPos;
  varying vec3 vNormal;

  vec3 heatmapColor(float t) {
    // 与 .heatmap-hud__scale-bar 的色段一致，保证场景颜色和右侧图例读数能对应
    vec3 c0 = vec3(0.36, 0.82, 0.95);  // 浅青  #5DD2F2  (低浓度)
    vec3 c1 = vec3(0.40, 0.92, 0.70);  // 青绿
    vec3 c2 = vec3(1.00, 0.82, 0.30);  // 琥珀黄
    vec3 c3 = vec3(1.00, 0.50, 0.20);  // 橙
    vec3 c4 = vec3(1.00, 0.22, 0.22);  // 红    (超标)

    float x = clamp(t, 0.0, 1.15);
    if (x < 0.25) return mix(c0, c1, x / 0.25);
    if (x < 0.55) return mix(c1, c2, (x - 0.25) / 0.30);
    if (x < 0.85) return mix(c2, c3, (x - 0.55) / 0.30);
    return mix(c3, c4, clamp((x - 0.85) / 0.30, 0.0, 1.0));
  }

  void main() {
    // 局部 y 归一到 0 (底) ~ 1 (顶)
    float yN = clamp((vLocalPos.y / uHalfSize.y + 1.0) * 0.5, 0.0, 1.0);

    // 垂直梯度：底部稍亮，往顶部柔和衰减（保持"厚度感"但不会过浓）
    float verticalFalloff = mix(0.85, smoothstep(1.2, 0.1, yN), 0.55);

    // 菲涅耳：边缘稍亮做出"笼罩感"。abs(vNormal.z) 近似视线方向
    float edge = pow(1.0 - abs(vNormal.z), 2.4) * 0.22;

    // 脉动：normal 级基本不动，critical 级才有可见呼吸
    float pulseAmp = 0.04 + uLevel * 0.05;
    float pulse = 1.0 - pulseAmp + pulseAmp * sin(uPulse);

    vec3 col = heatmapColor(uRatio);

    // 最终 alpha 压得很低 —— additive blending 下 alpha 是颜色叠加强度，
    // 过大就会饱和成白。0.04~0.18 的区间让颜色"着色"而不"发光糊"
    float intensityBase = mix(0.04, 0.18, clamp(uRatio, 0.0, 1.0));
    float alpha = (intensityBase * verticalFalloff + edge * 0.12) * pulse;
    alpha = clamp(alpha, 0.0, 0.22);

    // 颜色本身稍微压暗 20%，避免 additive 把白色成分推得太亮
    gl_FragColor = vec4(col * 0.8, alpha);
  }
`;

const levelToNumber = (level: string): number => {
  if (level === "critical") return 2;
  if (level === "warning") return 1;
  return 0;
};

export class HeatShellSet {
  private readonly parent: THREE.Object3D;
  private readonly shells: Map<string, ShellEntry> = new Map();

  constructor(parent: THREE.Object3D, defs: EmitterDefinition[]) {
    this.parent = parent;
    for (const def of defs) {
      const entry = this.createShell(def);
      this.shells.set(def.id, entry);
      parent.add(entry.mesh);
    }
  }

  private createShell(def: EmitterDefinition): ShellEntry {
    let geometry: THREE.BufferGeometry;
    let halfSize: THREE.Vector3;

    if (def.shell.kind === "cylinder") {
      const [radiusTop, height, radiusBottom] = def.shell.size;
      // 用 open-ended 圆柱（openEnded=true）避免上下盖在相机某些角度挡视线
      geometry = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, 28, 1, true);
      halfSize = new THREE.Vector3(
        Math.max(radiusTop, radiusBottom),
        height / 2,
        Math.max(radiusTop, radiusBottom),
      );
    } else {
      const [sx, sy, sz] = def.shell.size;
      geometry = new THREE.BoxGeometry(sx, sy, sz, 3, 3, 3);
      halfSize = new THREE.Vector3(sx / 2, sy / 2, sz / 2);
    }

    const material = new THREE.ShaderMaterial({
      uniforms: {
        uRatio: { value: 0 },
        uPulse: { value: 0 },
        uLevel: { value: 0 },
        uHalfSize: { value: halfSize },
      },
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(def.shell.center[0], def.shell.center[1], def.shell.center[2]);
    mesh.renderOrder = 5; // 在其他 mesh 之后渲染，保证 additive 叠加正确
    mesh.userData.emitterId = def.id;
    mesh.castShadow = false;
    mesh.receiveShadow = false;

    return {
      id: def.id,
      mesh,
      material,
      targetRatio: 0,
      currentRatio: 0,
      targetLevel: 0,
      currentLevel: 0,
    };
  }

  /**
   * 用后端 / SSE 生成的 emitterConcentrations 刷新各外壳的目标 ratio。
   * 实际 uniform 的更新在 tick() 里做一阶低通平滑，避免跳变。
   */
  updateFromConcentrations(concs: Record<string, EmitterConcentration>): void {
    for (const [id, entry] of this.shells) {
      const data = concs[id];
      if (!data) {
        entry.targetRatio = 0;
        entry.targetLevel = 0;
        continue;
      }
      entry.targetRatio = data.maxRatio;
      entry.targetLevel = levelToNumber(data.level);
    }
  }

  /**
   * 每帧调用：smoothing + pulse 相位推进。
   * - dt: 自上一帧秒数
   * - elapsed: 场景 elapsed 秒（给 critical 脉动一个统一的时钟）
   */
  tick(dt: number, elapsed: number): void {
    // 一阶低通系数：k 越小越"粘"。0.08 / 16ms ≈ 5Hz 响应，视觉上顺滑但不迟钝
    const smooth = 1 - Math.exp(-dt / 0.45);
    for (const entry of this.shells.values()) {
      entry.currentRatio += (entry.targetRatio - entry.currentRatio) * smooth;
      entry.currentLevel += (entry.targetLevel - entry.currentLevel) * smooth;
      entry.material.uniforms.uRatio.value = entry.currentRatio;
      entry.material.uniforms.uLevel.value = entry.currentLevel;
      entry.material.uniforms.uPulse.value = elapsed * 2.2 + entry.mesh.id * 0.37;
    }
  }

  dispose(): void {
    for (const entry of this.shells.values()) {
      entry.mesh.geometry.dispose();
      entry.material.dispose();
      this.parent.remove(entry.mesh);
    }
    this.shells.clear();
  }
}
