<script setup lang="ts">
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import type {
  EmitterConcentrations,
  EmitterIndicator,
  FactoryNode,
} from "@/types/dashboard";
import EmitterHistoryPopup from "./EmitterHistoryPopup.vue";
import { EMITTER_DEFINITIONS } from "./scene/EmitterConfig";
import { HeatShellSet } from "./scene/HeatShell";

const props = defineProps<{
  nodes: FactoryNode[];
  currentVocs: number;
  systemPhase: string;
  isExceedWarning?: boolean;
  emitterConcentrations?: EmitterConcentrations;
}>();

const sceneRef = ref<HTMLDivElement | null>(null);
const hoveredNodeId = ref<string | null>(null);
// 监测点位 / 关键设备 / 1号排口 三个文字标签已按需求移除，
// 3D 场景仍保留状态高亮标记（颜色区分正常/预警/告警），
// 下方图例仍需对应这三种状态色。
const projectedBuildingLabels = ref<
  Array<{ id: string; name: string; left: string; top: string; visible: boolean }>
>([]);

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let campusGroup: THREE.Group | null = null;
let controls: OrbitControls | null = null;
// 热力外壳集合：每个工艺单元一个发光 mesh，颜色由浓度 ratio 驱动
let heatShells: HeatShellSet | null = null;
// 后处理 pipeline：RenderPass → UnrealBloomPass → OutputPass
let composer: EffectComposer | null = null;
let bloomPass: UnrealBloomPass | null = null;
let frameId = 0;
const clock = new THREE.Clock();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const markerMeshes = new Map<string, THREE.Mesh>();
const pulseMeshes = new Map<string, THREE.Mesh>();
const interactiveMeshes = new Map<string, THREE.Object3D>();
const smokeMeshes: THREE.Mesh[] = [];
const buildingAnchorPoints = new Map<string, THREE.Object3D>();

/** 构建标签要渲染的多指标行 —— 每个 label 最多展示 3 条 indicator。 */
const indicatorsByEmitterId = computed<Record<string, EmitterIndicator[]>>(() => {
  const out: Record<string, EmitterIndicator[]> = {};
  const concs = props.emitterConcentrations;
  if (!concs) return out;
  for (const id of Object.keys(concs)) {
    out[id] = concs[id].indicators?.slice(0, 3) ?? [];
  }
  return out;
});

/** 格式化 indicator 值：大数字去掉小数；百分比等小数保留 1 位。 */
const formatIndicatorValue = (value: number): string => {
  if (!Number.isFinite(value)) return "--";
  const abs = Math.abs(value);
  if (abs >= 1000) return value.toFixed(0);
  if (abs >= 100) return value.toFixed(1);
  return value.toFixed(2);
};

// id 与 EMITTER_DEFINITIONS / 后端 EMITTER_CONFIGS 对齐，保证点击标签时能直接用
// 同一 id 向 /api/dashboard/emitter-history/{id} 拉取历史。
const buildingLabels = [
  { id: "coating", name: "喷涂生产厂房", anchor: new THREE.Vector3(-3.6, 1.7, 2.55) },
  { id: "rotor", name: "转轮吸附厂房", anchor: new THREE.Vector3(-1.05, 1.85, 1.85) },
  { id: "rto_in", name: "RTO 主处理厂房", anchor: new THREE.Vector3(1.95, 2.15, 1.95) },
  { id: "utility", name: "公辅燃烧区", anchor: new THREE.Vector3(5.15, 1.45, 2.55) },
  { id: "stack", name: "排口烟囱区", anchor: new THREE.Vector3(-5.45, 4.95, -0.55) },
  { id: "public", name: "监测附属区", anchor: new THREE.Vector3(5.4, 1.1, 4.0) },
];

/** 当前弹窗指向的 emitter id，空字符串代表没有弹窗。 */
const selectedEmitterId = ref<string>("");
/** 弹窗参考 anchor 的屏幕像素坐标（相对 sceneRef 容器）。 */
const popupAnchor = ref<{ left: number; top: number }>({ left: 0, top: 0 });
/** 弹窗计算尺寸使用的 host 宽高，跟随场景 resize。 */
const hostSize = ref<{ width: number; height: number }>({ width: 0, height: 0 });

const syncHostSize = () => {
  if (!sceneRef.value) return;
  hostSize.value = {
    width: sceneRef.value.clientWidth,
    height: sceneRef.value.clientHeight,
  };
};

const handleLabelClick = (event: MouseEvent, id: string) => {
  event.stopPropagation();
  if (!sceneRef.value) return;
  // 没有对应 emitter 配置就不弹（防止未来新增 label 忘了同步）
  if (!EMITTER_DEFINITIONS.some((def) => def.id === id)) return;

  const rect = sceneRef.value.getBoundingClientRect();
  popupAnchor.value = {
    left: event.clientX - rect.left,
    top: event.clientY - rect.top,
  };
  syncHostSize();
  selectedEmitterId.value = id;
};

const closePopup = () => {
  selectedEmitterId.value = "";
};

const statusColor = (status: string) => {
  if (status === "critical") {
    return "#ff5b61";
  }
  if (status === "warning") {
    return "#ffb347";
  }
  return "#53d1ff";
};

const statusHex = (status: string) => new THREE.Color(statusColor(status));

const createStandardMaterial = (
  color: string,
  metalness = 0.18,
  roughness = 0.82,
) =>
  new THREE.MeshStandardMaterial({
    color,
    metalness,
    roughness,
  });

const setShadow = (mesh: THREE.Mesh) => {
  mesh.castShadow = true;
  mesh.receiveShadow = true;
};

const addBox = (
  parent: THREE.Group,
  size: [number, number, number],
  position: [number, number, number],
  color: string,
  metalness = 0.15,
  roughness = 0.84,
) => {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(size[0], size[1], size[2]),
    createStandardMaterial(color, metalness, roughness),
  );
  mesh.position.set(position[0], position[1], position[2]);
  setShadow(mesh);
  parent.add(mesh);
  return mesh;
};

const addCylinder = (
  parent: THREE.Group,
  radiusTop: number,
  radiusBottom: number,
  height: number,
  radialSegments: number,
  position: [number, number, number],
  color: string,
  metalness = 0.16,
  roughness = 0.78,
) => {
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments),
    createStandardMaterial(color, metalness, roughness),
  );
  mesh.position.set(position[0], position[1], position[2]);
  setShadow(mesh);
  parent.add(mesh);
  return mesh;
};

const addRoad = (
  parent: THREE.Group,
  size: [number, number, number],
  position: [number, number, number],
  rotationY = 0,
) => {
  const road = addBox(parent, size, position, "#2a3347", 0.08, 0.96);
  road.rotation.y = rotationY;
  return road;
};

const buildGround = (parent: THREE.Group) => {
  const base = addBox(parent, [18.5, 0.3, 12.8], [0, -0.18, 0], "#4d5c74", 0.08, 0.96);
  base.receiveShadow = true;

  const grass = new THREE.Mesh(
    new THREE.BoxGeometry(16.8, 0.08, 11.1),
    createStandardMaterial("#90a069", 0.04, 0.98),
  );
  grass.position.set(0.15, 0.02, -0.1);
  grass.receiveShadow = true;
  parent.add(grass);

  const roadGroup = new THREE.Group();
  parent.add(roadGroup);

  addRoad(roadGroup, [15.6, 0.06, 0.72], [0.2, 0.08, 4.75]);
  addRoad(roadGroup, [14.9, 0.06, 0.72], [-0.1, 0.08, -4.55]);
  addRoad(roadGroup, [0.72, 0.06, 10.1], [-7.1, 0.08, 0.1]);
  addRoad(roadGroup, [0.72, 0.06, 10.2], [7.2, 0.08, 0.1]);
  addRoad(roadGroup, [0.66, 0.06, 6.5], [2.3, 0.08, 1.4]);
  addRoad(roadGroup, [0.66, 0.06, 4.9], [-2.8, 0.08, -0.8]);
  addRoad(roadGroup, [4.8, 0.06, 0.62], [3.7, 0.08, -1.25], Math.PI / 7);
  addRoad(roadGroup, [2.8, 0.06, 0.58], [-4.8, 0.08, 2.1], -Math.PI / 8);

  const markings = new THREE.Group();
  parent.add(markings);
  for (let index = 0; index < 11; index += 1) {
    addBox(markings, [0.4, 0.02, 0.06], [-4.8 + index * 1.05, 0.12, 4.75], "#d7d9df", 0.02, 0.94);
  }
};

const buildCoolingTower = (
  parent: THREE.Group,
  position: [number, number, number],
) => {
  const profile = [
    new THREE.Vector2(0.72, -1.55),
    new THREE.Vector2(0.66, -1.15),
    new THREE.Vector2(0.56, -0.45),
    new THREE.Vector2(0.48, 0.2),
    new THREE.Vector2(0.54, 0.82),
    new THREE.Vector2(0.68, 1.28),
    new THREE.Vector2(0.82, 1.55),
  ];

  const tower = new THREE.Mesh(
    new THREE.LatheGeometry(profile, 48),
    createStandardMaterial("#ece7e2", 0.08, 0.86),
  );
  tower.position.set(position[0], position[1], position[2]);
  setShadow(tower);
  parent.add(tower);

  const innerWall = new THREE.Mesh(
    new THREE.LatheGeometry(
      profile.map((point, index) =>
        new THREE.Vector2(
          Math.max(point.x - (index >= profile.length - 2 ? 0.08 : 0.06), 0.22),
          point.y,
        ),
      ),
      48,
    ),
    createStandardMaterial("#d8dce2", 0.08, 0.92),
  );
  innerWall.scale.y = 0.92;
  innerWall.position.set(position[0], position[1] + 0.08, position[2]);
  setShadow(innerWall);
  parent.add(innerWall);

  const topLip = addCylinder(
    parent,
    0.84,
    0.84,
    0.08,
    40,
    [position[0], position[1] + 1.56, position[2]],
    "#f8f4f0",
    0.12,
    0.62,
  );
  topLip.castShadow = false;

  const baseRing = addCylinder(
    parent,
    0.74,
    0.78,
    0.1,
    40,
    [position[0], position[1] - 1.52, position[2]],
    "#cfd5de",
    0.1,
    0.86,
  );
  baseRing.castShadow = false;

  return tower;
};

const buildSolarField = (parent: THREE.Group) => {
  const group = new THREE.Group();
  parent.add(group);
  for (let row = 0; row < 2; row += 1) {
    for (let col = 0; col < 4; col += 1) {
      const panel = addBox(
        group,
        [0.82, 0.05, 0.52],
        [3.45 + col * 0.98, 0.34, -0.8 - row * 0.78],
        "#24476d",
        0.26,
        0.42,
      );
      panel.rotation.x = -0.42;
      const stand = addBox(
        group,
        [0.78, 0.14, 0.48],
        [3.45 + col * 0.98, 0.18, -0.8 - row * 0.78],
        "#7f8d9f",
        0.08,
        0.92,
      );
      stand.castShadow = false;
    }
  }
};

const buildPipe = (
  parent: THREE.Group,
  length: number,
  position: [number, number, number],
  rotationY: number,
) => {
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08, 0.08, length, 18),
    createStandardMaterial("#2381d7", 0.28, 0.52),
  );
  mesh.rotation.z = Math.PI / 2;
  mesh.rotation.y = rotationY;
  mesh.position.set(position[0], position[1], position[2]);
  setShadow(mesh);
  parent.add(mesh);
  return mesh;
};

const buildCampus = () => {
  if (!scene) {
    return;
  }

  const group = new THREE.Group();
  group.position.set(0.1, 0, -0.3);
  scene.add(group);
  campusGroup = group;

  buildGround(group);

  const coatingHall = new THREE.Group();
  coatingHall.name = "coating";
  group.add(coatingHall);
  const coatingMain = addBox(coatingHall, [3.2, 1.15, 1.9], [-3.6, 0.6, 2.55], "#e6e7ea", 0.08, 0.9);
  coatingMain.name = "coating-hall";
  addBox(coatingHall, [3.26, 0.14, 1.98], [-3.6, 1.25, 2.55], "#2b84d3", 0.18, 0.44);
  addBox(coatingHall, [0.85, 0.66, 0.5], [-2.2, 0.35, 2.65], "#d5d9e0", 0.08, 0.86);
  addBox(coatingHall, [0.6, 0.42, 0.42], [-4.95, 0.23, 2.35], "#dfe2e7", 0.08, 0.9);

  const rotorHall = new THREE.Group();
  rotorHall.name = "rotor";
  group.add(rotorHall);
  const rotorMain = addBox(rotorHall, [2.75, 1.28, 1.65], [-1.05, 0.67, 1.85], "#e2e5ea", 0.08, 0.88);
  rotorMain.name = "monitor";
  addBox(rotorHall, [2.82, 0.16, 1.72], [-1.05, 1.39, 1.85], "#277dd1", 0.18, 0.46);
  addCylinder(rotorHall, 0.46, 0.46, 1.05, 28, [-1.9, 0.55, 1.1], "#d5dae3", 0.1, 0.8);
  addCylinder(rotorHall, 0.4, 0.4, 0.85, 28, [-0.35, 0.47, 1.1], "#d5dae3", 0.1, 0.8);
  addBox(rotorHall, [0.16, 0.8, 1.45], [-1.1, 0.44, 1.15], "#8798ae", 0.16, 0.66);

  const rtoHall = new THREE.Group();
  rtoHall.name = "rto";
  group.add(rtoHall);
  const rtoMain = addBox(rtoHall, [3.95, 1.52, 2.75], [1.95, 0.82, 1.95], "#e4e5e8", 0.08, 0.88);
  rtoMain.name = "device";
  addBox(rtoHall, [4.02, 0.16, 2.82], [1.95, 1.66, 1.95], "#2387d9", 0.18, 0.42);
  addBox(rtoHall, [1.1, 2.35, 1.18], [0.55, 1.18, 0.2], "#cfd5de", 0.12, 0.78);
  addBox(rtoHall, [1.18, 0.12, 1.24], [0.55, 2.42, 0.2], "#2e8fdd", 0.18, 0.46);
  addBox(rtoHall, [0.9, 2.15, 1.04], [2.15, 1.07, 0.05], "#c9d1dd", 0.12, 0.8);
  addBox(rtoHall, [0.98, 0.12, 1.1], [2.15, 2.2, 0.05], "#3293e2", 0.18, 0.46);
  for (let column = 0; column < 4; column += 1) {
    addBox(rtoHall, [0.08, 1.92, 0.08], [0.8 + column * 0.54, 0.96, 0.55], "#92a0b1", 0.2, 0.58);
  }

  const utilityHall = new THREE.Group();
  utilityHall.name = "utility";
  group.add(utilityHall);
  addBox(utilityHall, [2.5, 0.92, 1.35], [5.15, 0.48, 2.55], "#ececec", 0.05, 0.92);
  addBox(utilityHall, [2.56, 0.12, 1.42], [5.15, 1, 2.55], "#2f82c8", 0.16, 0.5);
  addBox(utilityHall, [1.15, 0.58, 0.82], [6.15, 0.31, 0.85], "#efefef", 0.05, 0.92);
  addBox(utilityHall, [0.86, 0.46, 0.72], [4.2, 0.24, 0.75], "#efefef", 0.05, 0.92);
  for (let index = 0; index < 4; index += 1) {
    addCylinder(
      utilityHall,
      0.28,
      0.3,
      0.72,
      22,
      [4 + index * 0.52, 0.4, 1.35],
      "#d9dde4",
      0.1,
      0.82,
    );
  }

  const chimneyZone = new THREE.Group();
  chimneyZone.name = "stack-zone";
  group.add(chimneyZone);
  const chimney = addCylinder(chimneyZone, 0.25, 0.36, 4.65, 28, [-5.45, 2.35, -0.55], "#f2f4f6", 0.12, 0.74);
  chimney.name = "stack";
  for (let index = 0; index < 3; index += 1) {
    addCylinder(
      chimneyZone,
      0.275,
      0.275,
      0.3,
      28,
      [-5.45, 0.85 + index * 1.3, -0.55],
      index % 2 === 0 ? "#2375c3" : "#eff4fa",
      0.18,
      0.66,
    );
  }
  addBox(chimneyZone, [1.15, 0.24, 1.05], [-5.48, 0.12, -0.48], "#d8dde4", 0.08, 0.9);

  const publicZone = new THREE.Group();
  publicZone.name = "public";
  group.add(publicZone);
  addBox(publicZone, [1.75, 0.44, 0.92], [1.85, 0.25, 4.05], "#ddd8d1", 0.05, 0.96);
  for (let index = 0; index < 3; index += 1) {
    addBox(publicZone, [0.22, 0.74, 0.22], [1.25 + index * 0.54, 0.56, 3.62], "#c0c7d4", 0.12, 0.74);
  }
  for (let row = 0; row < 2; row += 1) {
    for (let col = 0; col < 3; col += 1) {
      addBox(
        publicZone,
        [0.86, 0.38 + row * 0.1, 0.5],
        [4.7 + col * 1.05, 0.22 + row * 0.05, 4.05 - row * 0.9],
        "#f2f2f4",
        0.04,
        0.94,
      );
    }
  }

  buildSolarField(group);

  const pipeGroup = new THREE.Group();
  group.add(pipeGroup);
  buildPipe(pipeGroup, 2.45, [-2.2, 1, 2.1], 0.04);
  buildPipe(pipeGroup, 2.7, [0.1, 1.06, 1.82], 0.05);
  buildPipe(pipeGroup, 2.5, [2.8, 1.08, 1.15], -0.42);
  buildPipe(pipeGroup, 1.8, [4.05, 1.05, 1.1], -0.68);
  buildPipe(pipeGroup, 1.35, [5.55, 0.98, 1.95], 0.2);

  buildCoolingTower(group, [0.95, 1.55, -1.75]);
  buildCoolingTower(group, [2.9, 1.55, -1.25]);

  const fence = new THREE.Group();
  group.add(fence);
  for (let index = 0; index < 12; index += 1) {
    addBox(fence, [0.05, 0.26, 0.05], [-7.95 + index * 1.42, 0.14, 5.7], "#f5f7fa", 0.08, 0.94);
    addBox(fence, [0.05, 0.26, 0.05], [-7.95 + index * 1.42, 0.14, -5.65], "#f5f7fa", 0.08, 0.94);
  }

  const walkway = addBox(group, [4.2, 0.04, 0.78], [-3.8, 0.11, -2.75], "#d8cbbb", 0.02, 0.96);
  walkway.castShadow = false;

  buildingLabels.forEach((label) => {
    const anchor = new THREE.Object3D();
    anchor.position.copy(label.anchor);
    anchor.name = `${label.id}-anchor`;
    group.add(anchor);
    buildingAnchorPoints.set(label.id, anchor);
  });
};

const markerAnchors: Record<string, [number, number, number]> = {
  monitor: [-1.05, 2.2, 1.85],
  device: [1.95, 3, 1.65],
  stack: [-5.45, 4.9, -0.55],
};

const buildMarkers = () => {
  const group = campusGroup;
  if (!group) {
    return;
  }

  props.nodes.forEach((node, index) => {
    const anchor = markerAnchors[node.id] ?? [1 + index * 1.4, 2.2, 0];

    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(0.16, 24, 24),
      new THREE.MeshStandardMaterial({
        color: statusColor(node.status),
        emissive: statusColor(node.status),
        emissiveIntensity: 0.55,
        metalness: 0.14,
        roughness: 0.36,
      }),
    );
    glow.position.set(anchor[0], anchor[1], anchor[2]);
    glow.userData.nodeId = node.id;
    setShadow(glow);
    markerMeshes.set(node.id, glow);
    interactiveMeshes.set(node.id, glow);
    group.add(glow);

    const pulse = new THREE.Mesh(
      new THREE.RingGeometry(0.22, 0.42, 36),
      new THREE.MeshBasicMaterial({
        color: statusColor(node.status),
        transparent: true,
        opacity: 0.55,
        side: THREE.DoubleSide,
      }),
    );
    pulse.rotation.x = -Math.PI / 2;
    pulse.position.set(anchor[0], 0.16, anchor[2]);
    pulse.userData.nodeId = node.id;
    pulseMeshes.set(node.id, pulse);
    group.add(pulse);

    const stem = addCylinder(
      group,
      0.03,
      0.03,
      Math.max(anchor[1] - 0.35, 0.6),
      12,
      [anchor[0], (anchor[1] - 0.35) / 2 + 0.18, anchor[2]],
      "#7ed8ff",
      0.24,
      0.34,
    );
    stem.castShadow = false;
    stem.receiveShadow = false;
  });
};

const buildSmoke = () => {
  const group = campusGroup;
  if (!group) {
    return;
  }
  for (let index = 0; index < 6; index += 1) {
    const smoke = new THREE.Mesh(
      new THREE.SphereGeometry(0.18 + index * 0.03, 18, 18),
      new THREE.MeshBasicMaterial({
        color: "#dbe4ef",
        transparent: true,
        opacity: 0.12 + index * 0.015,
        depthWrite: false,
      }),
    );
    smoke.position.set(-5.45 + index * 0.02, 4.95 + index * 0.34, -0.55 + index * 0.03);
    smoke.userData.offset = index * 0.6;
    smokeMeshes.push(smoke);
    group.add(smoke);
  }
};

const updateMarkers = () => {
  props.nodes.forEach((node) => {
    const glow = markerMeshes.get(node.id);
    if (glow) {
      const material = glow.material as THREE.MeshStandardMaterial;
      material.color.copy(statusHex(node.status));
      material.emissive.copy(statusHex(node.status));
    }

    const pulse = pulseMeshes.get(node.id);
    if (pulse) {
      const material = pulse.material as THREE.MeshBasicMaterial;
      material.color.copy(statusHex(node.status));
    }
  });
};

const resizeScene = () => {
  if (!sceneRef.value || !renderer || !camera) {
    return;
  }
  const { clientWidth, clientHeight } = sceneRef.value;
  renderer.setSize(clientWidth, clientHeight);
  camera.aspect = clientWidth / clientHeight;
  camera.updateProjectionMatrix();
  if (composer) {
    composer.setSize(clientWidth, clientHeight);
  }
  hostSize.value = { width: clientWidth, height: clientHeight };
};

const updatePointer = (event: PointerEvent) => {
  if (!sceneRef.value || !camera || !scene) {
    return;
  }

  const rect = sceneRef.value.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const candidates = [...interactiveMeshes.values()];
  const intersects = raycaster.intersectObjects(candidates, false);
  hoveredNodeId.value =
    intersects[0]?.object.userData.nodeId || intersects[0]?.object.parent?.userData.nodeId || null;
};

const clearHover = () => {
  hoveredNodeId.value = null;
};

const updateBuildingLabels = () => {
  const container = sceneRef.value;
  const activeCamera = camera;
  if (!container || !activeCamera || !campusGroup) {
    return;
  }

  const width = container.clientWidth;
  const height = container.clientHeight;
  const results = buildingLabels.map((label) => {
    const anchor = buildingAnchorPoints.get(label.id);
    if (!anchor) {
      return {
        id: label.id,
        name: label.name,
        left: "0%",
        top: "0%",
        visible: false,
      };
    }

    const worldPosition = new THREE.Vector3();
    anchor.getWorldPosition(worldPosition);
    const projected = worldPosition.project(activeCamera);
    const isVisible = projected.z < 1 && projected.z > -1;
    const left = ((projected.x + 1) / 2) * width;
    const top = ((-projected.y + 1) / 2) * height;

    return {
      id: label.id,
      name: label.name,
      left: `${left}px`,
      top: `${top}px`,
      visible:
        isVisible &&
        left >= -120 &&
        left <= width + 120 &&
        top >= -80 &&
        top <= height + 80,
    };
  });

  projectedBuildingLabels.value = results;
};

/** 把 store 里的最新浓度推给热力外壳（smoothed tick 在 animate 里做）。 */
const pushConcentrationsToShells = () => {
  if (!heatShells) return;
  const concs = props.emitterConcentrations;
  if (concs) heatShells.updateFromConcentrations(concs);
};

const animate = () => {
  if (!renderer || !scene || !camera || !campusGroup) {
    return;
  }

  const dt = clock.getDelta();
  const elapsed = clock.elapsedTime;
  campusGroup.rotation.y = -0.46 + Math.sin(elapsed * 0.18) * 0.035;
  campusGroup.position.y = Math.sin(elapsed * 0.55) * 0.04;
  if (controls) {
    controls.update();
  } else {
    camera.position.x = 8.8 + Math.sin(elapsed * 0.16) * 0.18;
    camera.position.z = 10.4 + Math.cos(elapsed * 0.14) * 0.16;
    camera.lookAt(0.4, 1.55, 0.45);
  }

  props.nodes.forEach((node, index) => {
    const marker = markerMeshes.get(node.id);
    if (marker) {
      const material = marker.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity =
        (hoveredNodeId.value === node.id ? 0.95 : 0.5) +
        Math.sin(elapsed * 2.2 + index) * 0.12;
    }

    const pulse = pulseMeshes.get(node.id);
    if (pulse) {
      const scale = 1 + ((elapsed * 0.65 + index * 0.35) % 1.2) * 0.55;
      pulse.scale.setScalar(scale);
      const material = pulse.material as THREE.MeshBasicMaterial;
      material.opacity = hoveredNodeId.value === node.id ? 0.82 : 0.45;
    }
  });

  smokeMeshes.forEach((smoke, index) => {
    const drift = elapsed * 0.28 + Number(smoke.userData.offset ?? 0);
    smoke.position.x = -5.45 + Math.sin(drift * 0.85) * 0.18;
    smoke.position.z = -0.55 + Math.cos(drift * 0.7) * 0.16;
    smoke.position.y = 4.95 + ((drift + index * 0.12) % 2.4);
    smoke.scale.setScalar(1 + ((drift % 1.4) * 0.45));
  });

  updateBuildingLabels();

  // 热力外壳：每帧 smoothing 到目标 ratio + pulse 相位
  if (heatShells) {
    heatShells.tick(dt, elapsed);
  }

  // 后处理 pipeline（Render → Bloom → Output），composer 内部会自己调 renderer
  if (composer) {
    composer.render();
  } else {
    renderer.render(scene, camera);
  }

  frameId = requestAnimationFrame(animate);
};

const disposeScene = () => {
  if (!scene) {
    return;
  }

  scene.traverse((object) => {
    if (object instanceof THREE.Mesh) {
      object.geometry.dispose();
      const material = object.material;
      if (Array.isArray(material)) {
        material.forEach((entry) => entry.dispose());
      } else {
        material.dispose();
      }
    }
  });
};

onMounted(() => {
  if (!sceneRef.value) {
    return;
  }

  scene = new THREE.Scene();
  scene.fog = new THREE.Fog("#0b1322", 17, 32);

  camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
  camera.position.set(8.8, 7.2, 10.4);
  camera.lookAt(0.4, 1.55, 0.45);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  sceneRef.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.target.set(0.4, 1.55, 0.45);
  controls.minDistance = 7.5;
  controls.maxDistance = 18;
  controls.minPolarAngle = Math.PI / 4.4;
  controls.maxPolarAngle = Math.PI / 2.15;
  controls.enablePan = false;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.45;

  const ambient = new THREE.AmbientLight("#d2e6ff", 1.45);
  const hemi = new THREE.HemisphereLight("#d8ecff", "#0a1020", 1.15);
  const sun = new THREE.DirectionalLight("#fff7ea", 2.5);
  sun.position.set(9, 11, 6);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -12;
  sun.shadow.camera.right = 12;
  sun.shadow.camera.top = 12;
  sun.shadow.camera.bottom = -12;
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 32;

  const rim = new THREE.PointLight("#57b6ff", 2.2, 50);
  rim.position.set(-7, 6, 6);

  scene.add(ambient, hemi, sun, rim);

  buildCampus();
  buildMarkers();
  buildSmoke();
  updateMarkers();

  // 热力外壳：每个工艺单元一个发光罩，颜色由浓度 ratio 驱动。
  // 加到 campusGroup 下而不是 scene 下，这样 breathing 动画会带着外壳一起动。
  if (campusGroup) {
    heatShells = new HeatShellSet(campusGroup, EMITTER_DEFINITIONS);
    pushConcentrationsToShells();
  }

  // 后处理：RenderPass → UnrealBloomPass（让外壳颜色有"溢出"泛光）→ OutputPass。
  // 参数调优历史：之前 threshold=0.25 + strength=0.55 会把浅灰建筑和 ambient 光
  // 一起拉进 bloom，整屏发白。现在 threshold=0.88 只吃热力外壳里最饱和的红/橙段，
  // strength=0.28、radius=0.45 让泛光保持轻量、不糊。
  {
    const { clientWidth, clientHeight } = sceneRef.value;
    composer = new EffectComposer(renderer);
    composer.setSize(clientWidth, clientHeight);
    composer.addPass(new RenderPass(scene, camera));
    bloomPass = new UnrealBloomPass(
      new THREE.Vector2(clientWidth, clientHeight),
      0.28, // strength
      0.45, // radius
      0.88, // threshold
    );
    composer.addPass(bloomPass);
    composer.addPass(new OutputPass());
  }

  resizeScene();
  syncHostSize();
  animate();

  sceneRef.value.addEventListener("pointermove", updatePointer);
  sceneRef.value.addEventListener("pointerleave", clearHover);
  window.addEventListener("resize", resizeScene);
});

watch(
  () => props.nodes,
  () => {
    updateMarkers();
  },
  { deep: true },
);

// SSE 更新浓度时把目标 ratio 推给 HeatShell。实际 uniform 刷新 + 平滑插值在
// animate() 的 tick() 里完成，保证颜色过渡柔和，不会跳变。
watch(
  () => props.emitterConcentrations,
  () => {
    pushConcentrationsToShells();
  },
  { deep: true },
);

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId);
  window.removeEventListener("resize", resizeScene);
  sceneRef.value?.removeEventListener("pointermove", updatePointer);
  sceneRef.value?.removeEventListener("pointerleave", clearHover);
  if (heatShells) {
    heatShells.dispose();
    heatShells = null;
  }
  if (composer) {
    composer.dispose();
    composer = null;
  }
  bloomPass = null;
  disposeScene();
  controls?.dispose();
  controls = null;
  renderer?.dispose();
  markerMeshes.clear();
  pulseMeshes.clear();
  interactiveMeshes.clear();
  buildingAnchorPoints.clear();
  smokeMeshes.length = 0;
  if (sceneRef.value && renderer?.domElement.parentElement === sceneRef.value) {
    sceneRef.value.removeChild(renderer.domElement);
  }
});
</script>

<template>
  <section class="panel-card factory-card" :class="{ 'exceed-warning': isExceedWarning }">
    <div class="panel-title">园区工艺场景</div>
    <div class="factory-meta">
      <span>系统阶段：{{ systemPhase }}</span>
      <strong>当前 VOCs {{ currentVocs.toFixed(1) }} mg/m³</strong>
    </div>
    <div class="scene-wrap" @click="closePopup">
      <div ref="sceneRef" class="scene-host"></div>
      <div class="scene-legend">
        <span><i class="dot dot-normal"></i>正常</span>
        <span><i class="dot dot-warning"></i>预警</span>
        <span><i class="dot dot-critical"></i>告警</span>
      </div>
      <!-- 右上角图例：仅保留"浓度热力图"标题 + 色系条（0~100+），
           原本罗列 6 个工艺单元数据的列表已下沉到建筑上方的 .building-tag，
           这里只作为 3D 场景颜色→数值的解读键。 -->
      <div class="heatmap-hud">
        <div class="heatmap-hud__title">浓度热力图</div>
        <div class="heatmap-hud__scale">
          <span class="heatmap-hud__scale-label">0</span>
          <div class="heatmap-hud__scale-bar"></div>
          <span class="heatmap-hud__scale-label">100+</span>
        </div>
      </div>
    </div>
    <div class="node-layer">
      <div
        v-for="label in projectedBuildingLabels"
        :key="label.id"
        class="building-tag"
        :class="[
          `building-tag--${emitterConcentrations?.[label.id]?.level ?? 'normal'}`,
          {
            'building-tag--hidden': !label.visible,
            'building-tag--active': selectedEmitterId === label.id,
          },
        ]"
        :style="{ left: label.left, top: label.top }"
        @click="handleLabelClick($event, label.id)"
      >
        <span class="building-tag__halo"></span>
        <span class="building-tag__line"></span>
        <span class="building-tag__text">
          <span class="building-tag__title">{{ label.name }}</span>
          <ul
            v-if="indicatorsByEmitterId[label.id]?.length"
            class="building-tag__indicators"
          >
            <li
              v-for="ind in indicatorsByEmitterId[label.id]"
              :key="ind.field"
              :class="['building-tag__row', `building-tag__row--${ind.level}`]"
            >
              <span class="building-tag__label">{{ ind.label }}</span>
              <span class="building-tag__value">
                {{ formatIndicatorValue(ind.value) }}
                <em>{{ ind.unit }}</em>
              </span>
            </li>
          </ul>
          <span v-else class="building-tag__subtitle">工艺单元 · 点击看历史</span>
        </span>
      </div>
      <EmitterHistoryPopup
        v-if="selectedEmitterId"
        :emitter-id="selectedEmitterId"
        :anchor-left="popupAnchor.left"
        :anchor-top="popupAnchor.top"
        :host-width="hostSize.width"
        :host-height="hostSize.height"
        @close="closePopup"
      />
    </div>
  </section>
</template>

<style scoped>
.factory-card {
  position: relative;
  min-height: 100%;
  padding-bottom: 24px;
  overflow: hidden;
}

.factory-meta {
  display: flex;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 13px;
}

.factory-meta strong {
  color: var(--text-primary);
}

.scene-wrap {
  position: relative;
  flex: 1;
  margin-top: 14px;
  border-radius: 20px;
  overflow: hidden;
  background:
    radial-gradient(circle at 35% 18%, rgba(122, 166, 255, 0.12), transparent 24%),
    linear-gradient(180deg, rgba(23, 35, 67, 0.9), rgba(8, 15, 31, 0.96));
}

.scene-host {
  min-height: 560px;
}

.scene-legend {
  position: absolute;
  left: 18px;
  bottom: 16px;
  display: inline-flex;
  gap: 14px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(7, 15, 31, 0.58);
  border: 1px solid rgba(95, 122, 191, 0.18);
  color: var(--text-secondary);
  font-size: 12px;
}

.scene-legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  box-shadow: 0 0 10px currentColor;
}

.dot-normal {
  background: var(--accent-cyan);
  color: var(--accent-cyan);
}

.dot-warning {
  background: var(--accent-amber);
  color: var(--accent-amber);
}

.dot-critical {
  background: var(--accent-red);
  color: var(--accent-red);
}

/* ---------- 粒子浓度热力图 HUD ---------- */
.heatmap-hud {
  position: absolute;
  right: 16px;
  top: 16px;
  min-width: 168px;
  padding: 10px 12px 11px;
  border-radius: 10px;
  background: rgba(7, 15, 31, 0.72);
  border: 1px solid rgba(95, 122, 191, 0.24);
  backdrop-filter: blur(6px);
  color: var(--text-secondary);
  font-size: 12px;
  pointer-events: none;
  z-index: 3;
}

.heatmap-hud__title {
  font-size: 11px;
  letter-spacing: 0.12em;
  color: var(--text-secondary);
  margin-bottom: 6px;
  opacity: 0.85;
}

.heatmap-hud__scale {
  display: flex;
  align-items: center;
  gap: 6px;
}

.heatmap-hud__scale-bar {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    hsl(190, 72%, 55%) 0%,
    hsl(100, 72%, 55%) 35%,
    hsl(40, 82%, 58%) 65%,
    hsl(10, 82%, 58%) 100%
  );
  box-shadow: 0 0 12px rgba(83, 209, 255, 0.25);
}

.heatmap-hud__scale-label {
  font-size: 10px;
  color: rgba(169, 196, 232, 0.7);
}

.node-layer {
  position: absolute;
  inset: 82px 18px 26px 18px;
  pointer-events: none;
}

.building-tag {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transform: translate(-18%, -110%);
  /* 父级 .node-layer 设了 pointer-events: none 以便鼠标事件穿透到 Three 画布，
     这里单独把标签打开，让点击仅命中标签本身。 */
  pointer-events: auto;
  cursor: pointer;
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    filter 180ms ease;
}

.building-tag:hover .building-tag__text {
  border-color: rgba(142, 230, 255, 0.62);
  box-shadow:
    inset 0 1px 0 rgba(180, 235, 255, 0.14),
    0 14px 30px rgba(5, 14, 28, 0.45),
    0 0 18px rgba(83, 209, 255, 0.28);
  transform: translateY(-1px);
}

.building-tag:hover .building-tag__halo {
  box-shadow:
    0 0 0 4px rgba(83, 209, 255, 0.14),
    0 0 24px rgba(83, 209, 255, 0.55);
}

.building-tag--active .building-tag__text {
  border-color: rgba(142, 230, 255, 0.75);
  box-shadow:
    inset 0 1px 0 rgba(180, 235, 255, 0.18),
    0 16px 32px rgba(5, 14, 28, 0.5),
    0 0 24px rgba(83, 209, 255, 0.42);
}

.building-tag--hidden {
  opacity: 0;
  pointer-events: none;
}

.building-tag__halo {
  position: absolute;
  left: -6px;
  top: calc(100% + 10px);
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(142, 230, 255, 0.95), rgba(83, 209, 255, 0.2));
  box-shadow:
    0 0 0 4px rgba(83, 209, 255, 0.08),
    0 0 18px rgba(83, 209, 255, 0.35);
}

.building-tag__line {
  position: relative;
  width: 34px;
  height: 2px;
  background: linear-gradient(90deg, rgba(83, 209, 255, 0.95), rgba(83, 209, 255, 0.15));
  box-shadow: 0 0 14px rgba(83, 209, 255, 0.26);
}

.building-tag__line::after {
  content: "";
  position: absolute;
  left: 0;
  top: -30px;
  width: 2px;
  height: 32px;
  background: linear-gradient(180deg, rgba(83, 209, 255, 0.08), rgba(83, 209, 255, 0.72));
}

.building-tag__text {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  min-height: 42px;
  padding: 9px 13px 10px;
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(13, 30, 58, 0.94), rgba(7, 17, 35, 0.9));
  border: 1px solid rgba(83, 209, 255, 0.28);
  color: #eaf6ff;
  font-size: 12px;
  line-height: 1.1;
  white-space: nowrap;
  box-shadow:
    inset 0 1px 0 rgba(180, 235, 255, 0.08),
    0 12px 26px rgba(5, 14, 28, 0.34);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    transform 160ms ease;
}

.building-tag__title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #eaf6ff;
}

.building-tag__subtitle {
  color: rgba(169, 196, 232, 0.9);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* 多指标列表：名称左对齐、数值右对齐，每行按 level 变色 */
.building-tag__indicators {
  list-style: none;
  padding: 2px 0 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 144px;
}

.building-tag__row {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: baseline;
  gap: 10px;
  padding: 1px 0;
  font-size: 11px;
  color: rgba(205, 222, 247, 0.92);
  line-height: 1.2;
}

.building-tag__label {
  color: rgba(169, 196, 232, 0.82);
  font-size: 11px;
}

.building-tag__value {
  justify-self: end;
  font-variant-numeric: tabular-nums;
  font-size: 12px;
  font-weight: 600;
  color: #eaf6ff;
}

.building-tag__value em {
  margin-left: 2px;
  font-style: normal;
  font-size: 10px;
  font-weight: 400;
  color: rgba(169, 196, 232, 0.7);
}

.building-tag__row--warning .building-tag__value {
  color: #ffcf80;
  text-shadow: 0 0 8px rgba(255, 179, 71, 0.35);
}

.building-tag__row--critical .building-tag__value {
  color: #ff9f9f;
  text-shadow: 0 0 10px rgba(255, 91, 97, 0.45);
}

/* 根据整体 level 给标签边框染色 */
.building-tag--warning .building-tag__text {
  border-color: rgba(255, 179, 71, 0.55);
  box-shadow:
    inset 0 1px 0 rgba(255, 221, 151, 0.12),
    0 12px 26px rgba(5, 14, 28, 0.34),
    0 0 18px rgba(255, 179, 71, 0.22);
}

.building-tag--warning .building-tag__halo {
  background: radial-gradient(circle, rgba(255, 221, 151, 0.95), rgba(255, 179, 71, 0.2));
  box-shadow:
    0 0 0 4px rgba(255, 179, 71, 0.1),
    0 0 18px rgba(255, 179, 71, 0.45);
}

.building-tag--warning .building-tag__line {
  background: linear-gradient(90deg, rgba(255, 179, 71, 0.95), rgba(255, 179, 71, 0.15));
}

.building-tag--critical .building-tag__text {
  border-color: rgba(255, 91, 97, 0.65);
  box-shadow:
    inset 0 1px 0 rgba(255, 170, 175, 0.14),
    0 12px 26px rgba(5, 14, 28, 0.34),
    0 0 22px rgba(255, 91, 97, 0.32);
}

.building-tag--critical .building-tag__halo {
  background: radial-gradient(circle, rgba(255, 170, 175, 0.95), rgba(255, 91, 97, 0.2));
  box-shadow:
    0 0 0 4px rgba(255, 91, 97, 0.12),
    0 0 22px rgba(255, 91, 97, 0.55);
  animation: tag-critical-pulse 1.1s ease-in-out infinite;
}

.building-tag--critical .building-tag__line {
  background: linear-gradient(90deg, rgba(255, 91, 97, 0.95), rgba(255, 91, 97, 0.15));
}

@keyframes tag-critical-pulse {
  0%, 100% {
    box-shadow:
      0 0 0 4px rgba(255, 91, 97, 0.12),
      0 0 18px rgba(255, 91, 97, 0.45);
  }
  50% {
    box-shadow:
      0 0 0 6px rgba(255, 91, 97, 0.2),
      0 0 28px rgba(255, 91, 97, 0.75);
  }
}

.exceed-warning {
  animation: warning-pulse 2s ease-in-out infinite;
  border: 1.5px solid rgba(255, 60, 60, 0.6);
}

@keyframes warning-pulse {
  0%,
  100% {
    box-shadow:
      inset 0 0 18px rgba(255, 60, 60, 0.08),
      0 0 12px rgba(255, 60, 60, 0.15),
      0 0 32px rgba(255, 60, 60, 0.08);
    border-color: rgba(255, 60, 60, 0.35);
  }
  50% {
    box-shadow:
      inset 0 0 28px rgba(255, 60, 60, 0.18),
      0 0 24px rgba(255, 60, 60, 0.45),
      0 0 64px rgba(255, 60, 60, 0.2);
    border-color: rgba(255, 60, 60, 0.85);
  }
}
</style>
