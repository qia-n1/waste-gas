<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";

import type { HeatmapResponse } from "@/types/dashboard";

const props = defineProps<{
  data: HeatmapResponse;
}>();

const option = computed(() => ({
  tooltip: { position: "top" },
  grid: { top: 24, left: 18, right: 18, bottom: 18, containLabel: true },
  xAxis: {
    type: "category",
    data: props.data.dates,
    splitArea: { show: false },
    axisLabel: { color: "#8ea3c9" },
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.16)" } },
  },
  yAxis: {
    type: "category",
    data: props.data.hours.map((hour) => `${hour}`),
    splitArea: { show: false },
    axisLabel: { color: "#8ea3c9" },
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.16)" } },
  },
  visualMap: {
    min: 0,
    max: 6,
    calculable: false,
    orient: "horizontal",
    right: 0,
    top: 0,
    textStyle: { color: "#8ea3c9" },
    inRange: {
      color: ["#10213f", "#2157b8", "#53d1ff", "#ffb347", "#ff5b61"],
    },
  },
  series: [
    {
      type: "heatmap",
      data: props.data.values,
      emphasis: {
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 1,
        },
      },
    },
  ],
}));
</script>

<template>
  <section class="panel-card heatmap-card">
    <div class="panel-title">异常时段热力图</div>
    <VChart class="chart-host" :option="option" autoresize />
  </section>
</template>

<style scoped>
.heatmap-card {
  min-height: 260px;
}
</style>
