<script setup lang="ts">
import dayjs from "dayjs";
import { computed } from "vue";
import VChart from "vue-echarts";

import type { TopContributorSeries } from "@/types/dashboard";

const GROUP_COLORS: Record<string, string> = {
  "废气源与环境组": "#53d1ff",
  "转轮浓缩系统": "#ffb347",
  "RTO焚烧系统": "#ff5b61",
  "其它": "#5f6d95",
};

const FALLBACK_COLORS = [
  "#53d1ff",
  "#ffb347",
  "#ff5b61",
  "#9b8afb",
  "#47e6b1",
  "#60a5fa",
];

const props = defineProps<{
  items: TopContributorSeries[];
}>();

const colorFor = (item: TopContributorSeries, index: number) =>
  GROUP_COLORS[item.group] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length];

const buildOption = (item: TopContributorSeries, color: string) => {
  const values = item.series.map((point) => point.value);
  const timestamps = item.series.map((point) => point.timestamp);
  const numeric = values.filter((v) => Number.isFinite(v));
  const minVal = numeric.length ? Math.min(...numeric) : 0;
  const maxVal = numeric.length ? Math.max(...numeric) : 1;
  const span = maxVal - minVal;
  const yMin = span === 0 ? minVal - 1 : minVal - span * 0.1;
  const yMax = span === 0 ? maxVal + 1 : maxVal + span * 0.1;

  return {
    backgroundColor: "transparent",
    animationDuration: 300,
    grid: { top: 6, left: 4, right: 4, bottom: 4, containLabel: false },
    tooltip: {
      trigger: "axis",
      appendToBody: true,
      confine: false,
      backgroundColor: "rgba(8, 16, 33, 0.96)",
      borderColor: color,
      borderWidth: 1,
      padding: [8, 12],
      extraCssText: "z-index: 99999; box-shadow: 0 8px 24px rgba(0,0,0,0.45); pointer-events: none;",
      textStyle: { color: "#e9f2ff", fontSize: 12 },
      position: (
        point: [number, number],
        _params: unknown,
        _dom: HTMLElement,
        _rect: unknown,
        size: { viewSize: [number, number]; contentSize: [number, number] },
      ) => {
        // Place above the cursor; flip below if too close to top
        const [x, y] = point;
        const [tw, th] = size.contentSize;
        const left = Math.max(4, x - tw / 2);
        const top = y - th - 12;
        return [left, top < 4 ? y + 16 : top];
      },
      formatter: (params: Array<{ axisValue: string; data: number }>) => {
        const point = params[0];
        if (!point) return "";
        const ts = dayjs(point.axisValue);
        const dateStr = ts.isValid() ? ts.format("YYYY-MM-DD HH:mm") : String(point.axisValue);
        const val = Number(point.data);
        return (
          `<div style="font-weight:600;color:${color};margin-bottom:4px;">${item.label}</div>` +
          `<div style="color:#8ea3c9;font-size:11px;margin-bottom:2px;">🕒 ${dateStr}</div>` +
          `<div>数值：<b>${val.toFixed(2)}</b> ${item.unit}</div>` +
          `<div style="color:#8ea3c9;font-size:11px;margin-top:2px;">分组：${item.group}</div>`
        );
      },
    },
    xAxis: {
      type: "category",
      data: timestamps,
      show: false,
      boundaryGap: false,
    },
    yAxis: {
      type: "value",
      show: false,
      min: yMin,
      max: yMax,
    },
    series: [
      {
        type: "line",
        data: values,
        smooth: 0.35,
        smoothMonotone: "x",
        showSymbol: false,
        sampling: "lttb",
        lineStyle: { width: 1.6, color, cap: "round", join: "round" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${color}55` },
              { offset: 1, color: `${color}05` },
            ],
          },
        },
      },
    ],
  };
};

const cards = computed(() =>
  props.items.slice(0, 6).map((item, index) => {
    const color = colorFor(item, index);
    return {
      key: item.feature || `idx-${index}`,
      item,
      color,
      option: buildOption(item, color),
    };
  }),
);
</script>

<template>
  <section class="panel-card top-contributor-card">
    <div class="panel-title">贡献度 Top 6 指标趋势</div>
    <div v-if="cards.length === 0" class="empty">等待集成模型归因数据…</div>
    <div v-else class="grid">
      <div
        v-for="card in cards"
        :key="card.key"
        class="mini-card"
        :style="{ borderTopColor: card.color }"
      >
        <div class="mini-header">
          <span class="mini-label" :title="card.item.label">{{ card.item.label }}</span>
          <span class="mini-ratio" :style="{ color: card.color }">
            {{ (card.item.ratio * 100).toFixed(0) }}%
          </span>
        </div>
        <VChart class="mini-chart" :option="card.option" autoresize />
        <div class="mini-footer">
          <span class="mini-value">{{ card.item.currentValue.toFixed(2) }}</span>
          <span class="mini-unit">{{ card.item.unit }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.top-contributor-card {
  padding: 12px 14px 14px;
}

.panel-title {
  margin-bottom: 10px;
}

.empty {
  color: var(--text-secondary);
  font-size: 12px;
  padding: 18px 6px;
  text-align: center;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-template-rows: repeat(2, 1fr);
  gap: 8px;
}

.mini-card {
  display: flex;
  flex-direction: column;
  background: rgba(8, 16, 33, 0.55);
  border: 1px solid rgba(95, 122, 191, 0.18);
  border-top-width: 2px;
  border-radius: 8px;
  padding: 6px 8px 4px;
  min-height: 90px;
  overflow: hidden;
}

.mini-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  font-size: 11px;
  line-height: 1.2;
}

.mini-label {
  color: #c8d7f6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.mini-ratio {
  font-weight: 600;
  font-size: 11px;
  flex-shrink: 0;
}

.mini-chart {
  flex: 1;
  min-height: 36px;
  width: 100%;
}

.mini-footer {
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-size: 11px;
  line-height: 1.1;
}

.mini-value {
  color: #e9f2ff;
  font-weight: 600;
  font-size: 13px;
}

.mini-unit {
  color: var(--text-secondary);
  font-size: 10px;
}
</style>
