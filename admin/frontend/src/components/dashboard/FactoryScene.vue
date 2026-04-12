<script setup lang="ts">
import * as THREE from "three";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { FactoryNode } from "@/types/dashboard";

const props = defineProps<{
  nodes: FactoryNode[];
  currentVocs: number;
  systemPhase: string;
}>();

const sceneRef = ref<HTMLDivElement | null>(null);

let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.PerspectiveCamera | null = null;
let factoryGroup: THREE.Group | null = null;
let frameId = 0;
const markerMeshes = new Map<string, THREE.Mesh>();

const statusColor = (status: string) => {
  if (status === "critical") {
    return "#ff5b61";
  }
  if (status === "warning") {
    return "#ffb347";
  }
  return "#53d1ff";
};

const updateMarkers = () => {
  props.nodes.forEach((node) => {
    const marker = markerMeshes.get(node.id);
    if (marker) {
      (marker.material as THREE.MeshStandardMaterial).color.set(statusColor(node.status));
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
};

const animate = () => {
  if (!renderer || !scene || !camera || !factoryGroup) {
    return;
  }
  factoryGroup.rotation.y += 0.0025;
  renderer.render(scene, camera);
  frameId = requestAnimationFrame(animate);
};

onMounted(() => {
  if (!sceneRef.value) {
    return;
  }

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(7, 5, 10);
  camera.lookAt(0, 1.4, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  sceneRef.value.appendChild(renderer.domElement);

  const ambient = new THREE.AmbientLight("#d6e6ff", 1.3);
  const point = new THREE.PointLight("#8dc8ff", 2.2, 100);
  point.position.set(5, 8, 6);
  scene.add(ambient, point);

  const floor = new THREE.Mesh(
    new THREE.BoxGeometry(9, 0.4, 7),
    new THREE.MeshStandardMaterial({ color: "#d4d9e7", metalness: 0.2, roughness: 0.9 }),
  );
  floor.position.y = -0.2;
  scene.add(floor);

  factoryGroup = new THREE.Group();
  const group = factoryGroup;
  scene.add(group);

  const baseMaterial = new THREE.MeshStandardMaterial({
    color: "#eef1f8",
    metalness: 0.1,
    roughness: 0.78,
  });

  const buildings = [
    { size: [2.2, 1.6, 1.8], position: [-2.2, 0.8, 0.2] },
    { size: [2, 2.2, 1.6], position: [0, 1.1, -0.7] },
    { size: [2.8, 1.2, 1.8], position: [1.8, 0.6, 1.2] },
  ];

  buildings.forEach((item) => {
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(item.size[0], item.size[1], item.size[2]),
      baseMaterial,
    );
    mesh.position.set(item.position[0], item.position[1], item.position[2]);
    group.add(mesh);
  });

  const stackMaterial = new THREE.MeshStandardMaterial({
    color: "#f2f4f8",
    metalness: 0.15,
    roughness: 0.75,
  });
  const stack = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.34, 3.6, 24), stackMaterial);
  stack.position.set(2.5, 1.8, -1.2);
  group.add(stack);

  props.nodes.forEach((node, index) => {
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.18, 24, 24),
      new THREE.MeshStandardMaterial({
        color: statusColor(node.status),
        emissive: statusColor(node.status),
        emissiveIntensity: 0.22,
      }),
    );
    const positions = [
      [-2.8, 2.2, -0.4],
      [0, 2.7, -0.8],
      [2.5, 3.8, -1.2],
    ];
    const pos = positions[index] ?? [0, 2, 0];
    marker.position.set(pos[0], pos[1], pos[2]);
    markerMeshes.set(node.id, marker);
    group.add(marker);
  });

  resizeScene();
  animate();
  window.addEventListener("resize", resizeScene);
});

watch(() => props.nodes, updateMarkers, { deep: true });

onBeforeUnmount(() => {
  cancelAnimationFrame(frameId);
  window.removeEventListener("resize", resizeScene);
  renderer?.dispose();
  markerMeshes.clear();
  if (sceneRef.value && renderer?.domElement.parentElement === sceneRef.value) {
    sceneRef.value.removeChild(renderer.domElement);
  }
});
</script>

<template>
  <section class="panel-card factory-card">
    <div class="panel-title">园区工艺场景</div>
    <div class="factory-meta">
      <span>系统阶段：{{ systemPhase }}</span>
      <strong>当前 VOCs {{ currentVocs.toFixed(1) }} mg/m³</strong>
    </div>
    <div ref="sceneRef" class="scene-host"></div>
    <div class="node-layer">
      <div
        v-for="node in nodes"
        :key="node.id"
        class="node-tag"
        :style="{ left: `${node.x}%`, top: `${node.y}%` }"
      >
        <span class="node-pin" :style="{ background: statusColor(node.status) }"></span>
        <span>{{ node.label }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.factory-card {
  position: relative;
  min-height: 100%;
  padding-bottom: 24px;
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

.scene-host {
  flex: 1;
  min-height: 520px;
}

.node-layer {
  position: absolute;
  inset: 70px 18px 24px 18px;
  pointer-events: none;
}

.node-tag {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(7, 15, 31, 0.68);
  border: 1px solid rgba(95, 122, 191, 0.2);
  font-size: 12px;
}

.node-pin {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 12px currentColor;
}
</style>
