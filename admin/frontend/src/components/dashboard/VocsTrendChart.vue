<script setup lang="ts">
import dayjs from "dayjs";
import { computed, ref } from "vue";
import VChart from "vue-echarts";

import type { DashboardTrend } from "@/types/dashboard";

const props = defineProps<{
  trend: DashboardTrend;
}>();

const range = ref<[Date, Date]>([
  dayjs().subtract(1, "day").toDate(),
  dayjs().add(1, "day").toDate(),
]);
const showForecast = ref(true);

const filteredActual = computed(() =>
  props.trend.actualSeries.filter((item) => {
    const time = dayjs(item.timestamp);
    return time.isAfter(dayjs(range.value[0]).startOf("day")) &&
      time.isBefore(dayjs(range.value[1]).endOf("day"));
  }),
);

const option = computed(() => ({
  backgroundColor: "transparent",
  tooltip: { trigger: "axis" },
  legend: {
    top: 8,
    right: 0,
    textStyle: { color: "#8ea3c9" },
  },
  grid: { top: 44, left: 18, right: 18, bottom: 24, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: filteredActual.value.map((item) => dayjs(item.timestamp).format("MM/DD HH:mm")),
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisLabel: { color: "#8ea3c9", fontSize: 11 },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLabel: { color: "#8ea3c9" },
  },
  series: [
    {
      name: "实测值",
      type: "line",
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 3, color: "#53d1ff" },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(83, 209, 255, 0.38)" },
            { offset: 1, color: "rgba(83, 209, 255, 0.02)" },
          ],
        },
      },
      markLine: {
        silent: true,
        symbol: "none",
        data: [
          {
            yAxis: props.trend.warningThreshold,
            lineStyle: { color: "#ffb347", type: "dashed" },
            label: { formatter: "80 预警线" },
          },
          {
            yAxis: props.trend.criticalThreshold,
            lineStyle: { color: "#ff5b61", type: "dashed" },
            label: { formatter: "100 红线" },
          },
        ],
      },
      data: filteredActual.value.map((item) => item.value),
    },
    {
      name: "预测值",
      type: "line",
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2, type: "dashed", color: "#ffb347" },
      areaStyle: {
        color: "rgba(255, 179, 71, 0.08)",
      },
      data: showForecast.value ? props.trend.forecastSeries.map((item) => item.value) : [],
    },
  ],
}));
</script>

<template>
  <section class="panel-card trend-card">
    <div class="panel-title">VOCs 浓度趋势</div>
    <div class="toolbar">
      <el-date-picker
        v-model="range"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
      />
      <el-switch v-model="showForecast" inline-prompt active-text="预告" inactive-text="隐藏" />
    </div>
    <div class="trend-meta">
      <span>预测置信度 {{ Math.round(trend.confidence * 100) }}%</span>
      <span>当前阈值 {{ trend.warningThreshold }}/{{ trend.criticalThreshold }} mg/m³</span>
    </div>
    <VChart class="chart-host" :option="option" autoresize />
  </section>
</template>

<style scoped>
.trend-card {
  min-height: 0;
}

.toolbar,
.trend-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.toolbar {
  margin-bottom: 10px;
}

.trend-meta {
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
