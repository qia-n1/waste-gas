import * as THREE from "three";

import type { EmitterConcentration } from "@/types/dashboard";
import type { EmitterDefinition, HeatHotspotConfig } from "./EmitterConfig";

const MAX_SPOTS = 3;

interface ShellEntry {
  id: string;
  mesh: THREE.Mesh;
  material: THREE.ShaderMaterial;
  targetRatio: number;
  currentRatio: number;
  targetLevel: number;
  currentLevel: number;
  targetSpotStrengths: number[];
  currentSpotStrengths: number[];
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

const FRAGMENT_SHADER = /* glsl */ `
  uniform float uBaseRatio;
  uniform float uPulse;
  uniform float uLevel;
  uniform vec3 uHalfSize;
  uniform vec3 uSpotPos[3];
  uniform float uSpotStrength[3];
  uniform float uSpotRadius[3];

  varying vec3 vLocalPos;
  varying vec3 vNormal;

  vec3 heatmapColor(float t) {
    vec3 c0 = vec3(0.36, 0.82, 0.95);
    vec3 c1 = vec3(0.40, 0.92, 0.70);
    vec3 c2 = vec3(1.00, 0.82, 0.30);
    vec3 c3 = vec3(1.00, 0.50, 0.20);
    vec3 c4 = vec3(1.00, 0.22, 0.22);

    float x = clamp(t, 0.0, 1.15);
    if (x < 0.25) return mix(c0, c1, x / 0.25);
    if (x < 0.55) return mix(c1, c2, (x - 0.25) / 0.30);
    if (x < 0.85) return mix(c2, c3, (x - 0.55) / 0.30);
    return mix(c3, c4, clamp((x - 0.85) / 0.30, 0.0, 1.0));
  }

  float hotspotField(vec3 point) {
    float field = 0.0;
    for (int index = 0; index < 3; index += 1) {
      float strength = uSpotStrength[index];
      if (strength <= 0.0001) {
        continue;
      }

      vec3 delta = point - uSpotPos[index];
      delta.y *= 0.78;
      float distanceSquared = dot(delta, delta);
      float radius = max(uSpotRadius[index], 0.08);
      float visibleStrength = 0.18 + strength * 0.92;
      float core = exp(-distanceSquared / (radius * radius * 1.10));
      float haloRadius = radius * 2.25;
      float halo = exp(-distanceSquared / (haloRadius * haloRadius));
      float bridgeRadius = radius * 3.30;
      float bridge = exp(-distanceSquared / (bridgeRadius * bridgeRadius));
      field += visibleStrength * (0.95 * core + 0.68 * halo + 0.34 * bridge);
    }
    return field;
  }

  void main() {
    vec3 normalizedPos = vLocalPos / uHalfSize;
    float yN = clamp((normalizedPos.y + 1.0) * 0.5, 0.0, 1.0);
    float verticalLift = mix(0.92, 1.18, smoothstep(0.02, 0.94, yN));
    float edgeGlow = pow(1.0 - clamp(abs(vNormal.z), 0.0, 1.0), 1.8) * 0.22;

    float field = hotspotField(normalizedPos);
    float baseWash = uBaseRatio * (0.34 + 0.20 * verticalLift);
    float blendedRatio = clamp(baseWash + field * (0.80 + 0.20 * verticalLift), 0.0, 1.15);

    float pulseAmplitude = 0.03 + uLevel * 0.05;
    float pulse = 1.0 - pulseAmplitude + pulseAmplitude * sin(uPulse);

    float baseCoverage = smoothstep(0.02, 0.24, baseWash) * 0.42;
    float hotspotCoverage = smoothstep(0.04, 0.62, field) * 0.72;
    float coverage = clamp(baseCoverage + hotspotCoverage, 0.0, 1.0);
    float hotspotGlow = smoothstep(0.36, 1.05, field) * 0.24;
    float alpha = (0.02 + 0.62 * coverage + hotspotGlow + edgeGlow) * pulse;
    alpha *= mix(0.96, 1.08, smoothstep(0.08, 0.88, yN));
    alpha = clamp(alpha, 0.0, 0.82);

    vec3 color = heatmapColor(blendedRatio);
    float colorLift = 0.92 + 0.42 * clamp(blendedRatio, 0.0, 1.0) + coverage * 0.22;
    gl_FragColor = vec4(color * colorLift, alpha);
  }
`;

const levelToNumber = (level: string): number => {
  if (level === "critical") return 2;
  if (level === "warning") return 1;
  return 0;
};

const padHotspots = (hotspots: HeatHotspotConfig[]) => {
  const positions: THREE.Vector3[] = [];
  const radii: number[] = [];

  for (let index = 0; index < MAX_SPOTS; index += 1) {
    const hotspot = hotspots[index];
    if (hotspot) {
      positions.push(
        new THREE.Vector3(
          hotspot.position[0],
          hotspot.position[1],
          hotspot.position[2],
        ),
      );
      radii.push(hotspot.spread * 1.18);
    } else {
      positions.push(new THREE.Vector3(0, 0, 0));
      radii.push(0.55);
    }
  }

  return { positions, radii };
};

export class HeatShellSet {
  private readonly parent: THREE.Object3D;
  private readonly shells = new Map<string, ShellEntry>();

  constructor(parent: THREE.Object3D, definitions: EmitterDefinition[]) {
    this.parent = parent;
    for (const definition of definitions) {
      const entry = this.createShell(definition);
      this.shells.set(definition.id, entry);
      this.parent.add(entry.mesh);
    }
  }

  private createShell(definition: EmitterDefinition): ShellEntry {
    let geometry: THREE.BufferGeometry;
    let halfSize: THREE.Vector3;

    if (definition.shell.kind === "cylinder") {
      const [radiusTop, height, radiusBottom] = definition.shell.size;
      geometry = new THREE.CylinderGeometry(
        radiusTop,
        radiusBottom,
        height,
        40,
        8,
        true,
      );
      halfSize = new THREE.Vector3(
        Math.max(radiusTop, radiusBottom),
        height / 2,
        Math.max(radiusTop, radiusBottom),
      );
    } else {
      const [sizeX, sizeY, sizeZ] = definition.shell.size;
      geometry = new THREE.BoxGeometry(sizeX, sizeY, sizeZ, 10, 8, 10);
      halfSize = new THREE.Vector3(sizeX / 2, sizeY / 2, sizeZ / 2);
    }

    const padded = padHotspots(definition.shell.hotspots);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        uBaseRatio: { value: 0 },
        uPulse: { value: 0 },
        uLevel: { value: 0 },
        uHalfSize: { value: halfSize },
        uSpotPos: { value: padded.positions },
        uSpotStrength: { value: [0, 0, 0] },
        uSpotRadius: { value: padded.radii },
      },
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      blending: THREE.NormalBlending,
      side: THREE.FrontSide,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -2,
      toneMapped: false,
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(
      definition.shell.center[0],
      definition.shell.center[1],
      definition.shell.center[2],
    );
    if (definition.shell.kind === "cylinder") {
      mesh.scale.set(1.12, 1.03, 1.12);
    } else {
      mesh.scale.set(1.05, 1.06, 1.05);
    }
    mesh.renderOrder = 5;
    mesh.userData.emitterId = definition.id;
    mesh.castShadow = false;
    mesh.receiveShadow = false;

    return {
      id: definition.id,
      mesh,
      material,
      targetRatio: 0,
      currentRatio: 0,
      targetLevel: 0,
      currentLevel: 0,
      targetSpotStrengths: [0, 0, 0],
      currentSpotStrengths: [0, 0, 0],
    };
  }

  updateFromConcentrations(concentrations: Record<string, EmitterConcentration>): void {
    for (const [id, entry] of this.shells) {
      const concentration = concentrations[id];
      if (!concentration) {
        entry.targetRatio = 0;
        entry.targetLevel = 0;
        entry.targetSpotStrengths = [0, 0, 0];
        continue;
      }

      entry.targetRatio = concentration.maxRatio;
      entry.targetLevel = levelToNumber(concentration.level);
      entry.targetSpotStrengths = Array.from({ length: MAX_SPOTS }, (_, index) =>
        concentration.indicators[index]?.ratio ?? 0,
      );
    }
  }

  tick(dt: number, elapsed: number): void {
    const smooth = 1 - Math.exp(-dt / 0.42);

    for (const entry of this.shells.values()) {
      entry.currentRatio += (entry.targetRatio - entry.currentRatio) * smooth;
      entry.currentLevel += (entry.targetLevel - entry.currentLevel) * smooth;

      for (let index = 0; index < MAX_SPOTS; index += 1) {
        const target = entry.targetSpotStrengths[index] ?? 0;
        entry.currentSpotStrengths[index] +=
          (target - entry.currentSpotStrengths[index]) * smooth;
      }

      entry.material.uniforms.uBaseRatio.value = entry.currentRatio;
      entry.material.uniforms.uLevel.value = entry.currentLevel;
      entry.material.uniforms.uPulse.value = elapsed * 2.2 + entry.mesh.id * 0.37;
      entry.material.uniforms.uSpotStrength.value = [...entry.currentSpotStrengths];
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
