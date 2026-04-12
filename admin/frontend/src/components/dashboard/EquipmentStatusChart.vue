<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";

import type { EquipmentStatusResponse } from "@/types/dashboard";

const props = defineProps<{
  data: EquipmentStatusResponse;
}>();

const option = computed(() => ({
  tooltip: { trigger: "item" },
  legend: {
    orient: "vertical",
    right: 0,
    top: "center",
    textStyle: { color: "#c8d7f6" },
  },
  series: [
    {
      type: "pie",
      radius: ["56%", "76%"],
      center: ["36%", "52%"],
      itemStyle: { borderColor: "#08111f", borderWidth: 4 },
      label: { show: false },
      data: props.data.items.map((item) => ({
        ...item,
        itemStyle: { color: item.color },
      })),
    },
  ],
}));
</script>

<template>
  <section class="panel-card chart-card">
    <div class="panel-title">设备状态分布</div>
    <div class="ring-wrap">
      <VChart class="chart-host" :option="option" autoresize />
      <div class="ring-center">
        <strong>{{ data.online }}</strong>
        <span>在线设备</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.chart-card {
  min-height: 280px;
}

.ring-wrap {
  position: relative;
  flex: 1;
  min-height: 220px;
}

.ring-center {
  position: absolute;
  top: 50%;
  left: 36%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.ring-center strong {
  font-size: 30px;
}

.ring-center span {
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
