<script setup lang="ts">
/**
 * 点击 FactoryScene 里的建筑标签时弹出的小型历史图表。
 *
 * 设计原则：
 *  - 体积紧凑（默认 320 × 220），不遮挡主视觉
 *  - 视觉风格与 VocsTrendChart 对齐（同一套青色线性渐变 + 琥珀/红 阈值标线）
 *  - 组件每次打开都会自行 fetch 一次；关闭即销毁，不常驻网络
 */
import dayjs from "dayjs";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import VChart from "vue-echarts";

import client from "@/api/client";
import type { EmitterHistoryResponse } from "@/types/dashboard";

const props = defineProps<{
  emitterId: string;
  /** 弹窗相对父级的像素坐标（anchor 点） */
  anchorLeft: number;
  anchorTop: number;
  /** 父级宽高，用于 popup 位置边界检测 */
  hostWidth: number;
  hostHeight: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const POPUP_WIDTH = 320;
const POPUP_HEIGHT = 232;
const GAP = 12;

const loading = ref(false);
const error = ref<string | null>(null);
const data = ref<EmitterHistoryResponse | null>(null);

const levelClass = computed(() => {
  const level = data.value?.level;
  if (level === "critical") return "is-critical";
  if (level === "warning") return "is-warning";
  return "is-normal";
});

const displayCurrent = computed(() => {
  const value = data.value?.currentValue ?? 0;
  if (data.value?.unit === "norm") return (value * 100).toFixed(0);
  return value.toFixed(1);
});

const displayUnit = computed(() => {
  if (!data.value) return "";
  return data.value.unit === "norm" ? "%" : data.value.unit;
});

const formattedAvg = computed(() => {
  const value = data.value?.avgValue ?? 0;
  return data.value?.unit === "norm" ? (value * 100).toFixed(0) : value.toFixed(1);
});

const formattedMin = computed(() => {
  const value = data.value?.minValue ?? 0;
  return data.value?.unit === "norm" ? (value * 100).toFixed(0) : value.toFixed(1);
});

const formattedMax = computed(() => {
  const value = data.value?.maxValue ?? 0;
  return data.value?.unit === "norm" ? (value * 100).toFixed(0) : value.toFixed(1);
});

/** 位置计算：优先显示在 anchor 右侧；若溢出则翻转到左侧。顶边同理，避免裁切。 */
const popupStyle = computed(() => {
  let left = props.anchorLeft + GAP;
  if (left + POPUP_WIDTH > props.hostWidth - 8) {
    left = props.anchorLeft - POPUP_WIDTH - GAP;
  }
  left = Math.max(8, Math.min(left, props.hostWidth - POPUP_WIDTH - 8));

  let top = props.anchorTop - POPUP_HEIGHT / 2;
  top = Math.max(8, Math.min(top, props.hostHeight - POPUP_HEIGHT - 8));
  return {
    left: `${left}px`,
    top: `${top}px`,
    width: `${POPUP_WIDTH}px`,
    height: `${POPUP_HEIGHT}px`,
  };
});

const chartPoints = computed(() => data.value?.points ?? []);

const option = computed(() => {
  if (!data.value) {
    return {};
  }
  const xs = chartPoints.value.map((item) => item.timestamp);
  const ys = chartPoints.value.map((item) => item.value);
  const isNorm = data.value.unit === "norm";
  const scale = isNorm ? 100 : 1;
  const unit = isNorm ? "%" : data.value.unit;

  return {
    backgroundColor: "transparent",
    animationDuration: 350,
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(8, 16, 33, 0.94)",
      borderColor: "rgba(95, 122, 191, 0.28)",
      textStyle: { color: "#e9f2ff", fontSize: 11 },
      formatter: (
        params: Array<{ axisValue: string; data: number | null }>,
      ) => {
        const time = dayjs(params[0]?.axisValue).format("MM-DD HH:mm");
        const v = params[0]?.data;
        if (v === null || v === undefined) return time;
        return `${time}<br/>${(Number(v) * scale).toFixed(isNorm ? 0 : 1)} ${unit}`;
      },
    },
    grid: {
      top: 10,
      left: 4,
      right: 8,
      bottom: 20,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: xs,
      axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#7f94b9",
        fontSize: 9,
        interval: Math.max(Math.ceil(xs.length / 4) - 1, 0),
        formatter: (value: string) => dayjs(value).format("HH:mm"),
      },
    },
    yAxis: {
      type: "value",
      splitNumber: 3,
      min: 0,
      splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: "#7f94b9",
        fontSize: 9,
        formatter: (v: number) => (isNorm ? `${(v * 100).toFixed(0)}` : `${v.toFixed(0)}`),
      },
    },
    series: [
      {
        type: "line",
        smooth: 0.35,
        showSymbol: false,
        sampling: "lttb",
        lineStyle: {
          width: 2,
          color: "#53d1ff",
          cap: "round",
          join: "round",
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(83, 209, 255, 0.32)" },
              { offset: 1, color: "rgba(83, 209, 255, 0.01)" },
            ],
          },
        },
        markLine: {
          silent: true,
          symbol: "none",
          label: {
            color: "#8ea3c9",
            fontSize: 9,
            position: "insideEndTop",
          },
          data: [
            {
              yAxis: data.value.warning,
              lineStyle: { color: "#ffb347", type: "dashed", opacity: 0.85 },
              label: { formatter: "警戒" },
            },
            {
              yAxis: data.value.critical,
              lineStyle: { color: "#ff5b61", type: "dashed", opacity: 0.9 },
              label: { formatter: "红线" },
            },
          ],
        },
        data: ys,
      },
    ],
  };
});

const fetchHistory = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await client.get<EmitterHistoryResponse>(
      `/dashboard/emitter-history/${props.emitterId}`,
      { params: { limit: 48 } },
    );
    data.value = response.data;
  } catch (err) {
    console.error(err);
    error.value = "历史数据加载失败";
    data.value = null;
  } finally {
    loading.value = false;
  }
};

const handleEsc = (event: KeyboardEvent) => {
  if (event.key === "Escape") {
    emit("close");
  }
};

onMounted(() => {
  void fetchHistory();
  window.addEventListener("keydown", handleEsc);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleEsc);
});

// 切换 emitterId（重新打开不同建筑）时重新请求
watch(
  () => props.emitterId,
  () => {
    void fetchHistory();
  },
);
</script>

<template>
  <div class="emitter-popup" :class="levelClass" :style="popupStyle" @click.stop>
    <header class="emitter-popup__header">
      <div class="emitter-popup__label-wrap">
        <span class="emitter-popup__dot"></span>
        <span class="emitter-popup__label">{{ data?.label ?? "加载中…" }}</span>
      </div>
      <button class="emitter-popup__close" aria-label="关闭" @click="emit('close')">
        ×
      </button>
    </header>

    <div v-if="data" class="emitter-popup__stats">
      <div class="emitter-popup__current">
        <span class="emitter-popup__current-value">{{ displayCurrent }}</span>
        <span class="emitter-popup__current-unit">{{ displayUnit }}</span>
      </div>
      <div class="emitter-popup__mini-stats">
        <div>
          <span class="mini-label">均</span>
          <span class="mini-value">{{ formattedAvg }}</span>
        </div>
        <div>
          <span class="mini-label">峰</span>
          <span class="mini-value">{{ formattedMax }}</span>
        </div>
        <div>
          <span class="mini-label">谷</span>
          <span class="mini-value">{{ formattedMin }}</span>
        </div>
      </div>
    </div>

    <div class="emitter-popup__chart-wrap">
      <VChart
        v-if="data && chartPoints.length > 0"
        class="emitter-popup__chart"
        :option="option"
        autoresize
      />
      <div v-else-if="loading" class="emitter-popup__placeholder">
        <span class="emitter-popup__spinner"></span>
        读取历史数据…
      </div>
      <div v-else-if="error" class="emitter-popup__placeholder emitter-popup__placeholder--error">
        {{ error }}
      </div>
      <div v-else class="emitter-popup__placeholder">暂无历史数据</div>
    </div>
  </div>
</template>

<style scoped>
.emitter-popup {
  position: absolute;
  z-index: 12;
  display: flex;
  flex-direction: column;
  padding: 10px 12px 8px;
  border-radius: 12px;
  background: linear-gradient(
    180deg,
    rgba(13, 30, 58, 0.96),
    rgba(7, 17, 35, 0.94)
  );
  border: 1px solid rgba(83, 209, 255, 0.28);
  color: #eaf6ff;
  box-shadow:
    inset 0 1px 0 rgba(180, 235, 255, 0.08),
    0 16px 40px rgba(5, 14, 28, 0.55);
  pointer-events: auto;
  backdrop-filter: blur(6px);
  animation: emitter-popup-in 160ms ease-out;
}

.emitter-popup.is-warning {
  border-color: rgba(255, 179, 71, 0.55);
  box-shadow:
    inset 0 1px 0 rgba(255, 221, 151, 0.1),
    0 16px 40px rgba(5, 14, 28, 0.55),
    0 0 22px rgba(255, 179, 71, 0.18);
}

.emitter-popup.is-critical {
  border-color: rgba(255, 91, 97, 0.62);
  box-shadow:
    inset 0 1px 0 rgba(255, 170, 175, 0.1),
    0 16px 40px rgba(5, 14, 28, 0.55),
    0 0 26px rgba(255, 91, 97, 0.24);
}

.emitter-popup__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.emitter-popup__label-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.emitter-popup__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent-cyan, #53d1ff);
  box-shadow: 0 0 8px currentColor;
  color: var(--accent-cyan, #53d1ff);
}

.emitter-popup.is-warning .emitter-popup__dot {
  background: var(--accent-amber, #ffb347);
  color: var(--accent-amber, #ffb347);
}

.emitter-popup.is-critical .emitter-popup__dot {
  background: var(--accent-red, #ff5b61);
  color: var(--accent-red, #ff5b61);
  animation: emitter-pulse 900ms ease-in-out infinite;
}

.emitter-popup__label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.emitter-popup__close {
  border: none;
  background: transparent;
  color: rgba(169, 196, 232, 0.82);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
  transition:
    background-color 120ms ease,
    color 120ms ease;
}

.emitter-popup__close:hover {
  background: rgba(83, 209, 255, 0.16);
  color: #eaf6ff;
}

.emitter-popup__stats {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 2px;
}

.emitter-popup__current {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  color: var(--accent-cyan, #53d1ff);
}

.emitter-popup.is-warning .emitter-popup__current {
  color: var(--accent-amber, #ffb347);
}

.emitter-popup.is-critical .emitter-popup__current {
  color: var(--accent-red, #ff5b61);
}

.emitter-popup__current-value {
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.01em;
  text-shadow: 0 0 12px currentColor;
}

.emitter-popup__current-unit {
  font-size: 11px;
  color: rgba(169, 196, 232, 0.82);
  font-weight: 400;
}

.emitter-popup__mini-stats {
  display: inline-flex;
  gap: 10px;
  padding-bottom: 2px;
  color: rgba(169, 196, 232, 0.88);
  font-size: 11px;
  line-height: 1.1;
}

.emitter-popup__mini-stats > div {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
}

.mini-label {
  color: rgba(169, 196, 232, 0.6);
  font-size: 10px;
}

.mini-value {
  font-variant-numeric: tabular-nums;
  color: #eaf6ff;
}

.emitter-popup__chart-wrap {
  flex: 1;
  min-height: 0;
  margin-top: 4px;
  position: relative;
}

.emitter-popup__chart {
  width: 100%;
  height: 100%;
}

.emitter-popup__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(169, 196, 232, 0.68);
  font-size: 11px;
  gap: 6px;
}

.emitter-popup__placeholder--error {
  color: var(--accent-red, #ff5b61);
}

.emitter-popup__spinner {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  border: 2px solid rgba(83, 209, 255, 0.2);
  border-top-color: #53d1ff;
  animation: emitter-spin 720ms linear infinite;
}

@keyframes emitter-popup-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes emitter-pulse {
  0%,
  100% {
    box-shadow: 0 0 8px currentColor;
    transform: scale(1);
  }
  50% {
    box-shadow:
      0 0 14px currentColor,
      0 0 22px currentColor;
    transform: scale(1.2);
  }
}

@keyframes emitter-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
