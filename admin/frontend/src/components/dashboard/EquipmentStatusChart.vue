<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";

import type { Attribution, EquipmentStatusResponse } from "@/types/dashboard";
import { sensorMeta } from "@/utils/sensorMeta";

const featureLabel = (feature: string) =>
  sensorMeta.find((item) => item.field === feature)?.label ?? feature;

const GROUP_COLORS: Record<string, string> = {
  "废气源与环境组": "#53d1ff",
  "转轮浓缩系统": "#ffb347",
  "RTO焚烧系统": "#ff5b61",
  "其它": "#5f6d95",
};

const FEATURE_COLORS = [
  "#53d1ff", "#3abfed", "#47e6b1", "#6dd5a0",
  "#ffb347", "#ffd166", "#ff8a5c", "#ff5b61",
  "#c084fc", "#9b8afb", "#60a5fa", "#a78bfa",
];

const props = defineProps<{
  data: EquipmentStatusResponse;
  attribution?: Attribution | null;
}>();

const hasAttribution = computed(
  () => props.attribution && props.attribution.feature_contributions.length > 0,
);

const title = computed(() =>
  hasAttribution.value ? "细分指标贡献度" : "设备状态分布",
);

const centerLabel = computed(() => {
  if (hasAttribution.value && props.attribution) {
    return {
      main: props.attribution.target.toFixed(1),
      sub: "预测均值",
    };
  }
  return {
    main: String(props.data.online),
    sub: "在线设备",
  };
});

const option = computed(() => {
  if (hasAttribution.value && props.attribution) {
    const contributions = props.attribution.feature_contributions.slice(0, 10);
    return {
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(8, 16, 33, 0.92)",
        borderColor: "rgba(95, 122, 191, 0.28)",
        textStyle: { color: "#e9f2ff", fontSize: 12 },
        formatter: (params: { name: string; value: number; data: { contribution: number; group: string } }) =>
          `<b>${params.name}</b><br/>占比：${(params.value * 100).toFixed(1)}%<br/>贡献值：${params.data.contribution.toFixed(2)}<br/>分组：${params.data.group}`,
      },
      legend: {
        type: "scroll",
        orient: "vertical",
        right: 0,
        top: 8,
        bottom: 8,
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 8,
        textStyle: { color: "#c8d7f6", fontSize: 11, width: 90, overflow: "truncate" },
        pageIconColor: "#53d1ff",
        pageIconInactiveColor: "#3a4a6b",
        pageTextStyle: { color: "#8ea3c9", fontSize: 10 },
        formatter: (name: string) => {
          const item = contributions.find((c) => featureLabel(c.feature) === name);
          return item ? `${name} ${(item.ratio * 100).toFixed(0)}%` : name;
        },
      },
      series: [
        {
          type: "pie",
          radius: ["52%", "72%"],
          center: ["30%", "52%"],
          itemStyle: { borderColor: "#08111f", borderWidth: 3 },
          label: { show: false },
          data: contributions.map((item, index) => ({
            name: featureLabel(item.feature),
            value: item.ratio,
            contribution: item.contribution,
            group: item.group,
            itemStyle: {
              color: GROUP_COLORS[item.group] ?? FEATURE_COLORS[index % FEATURE_COLORS.length],
            },
          })),
        },
      ],
    };
  }

  // Fallback: original equipment status chart
  return {
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
  };
});
</script>

<template>
  <section class="panel-card chart-card">
    <div class="panel-title">{{ title }}</div>
    <div class="ring-wrap">
      <VChart class="chart-host" :option="option" autoresize />
      <div class="ring-center">
        <strong>{{ centerLabel.main }}</strong>
        <span>{{ centerLabel.sub }}</span>
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
  top: 52%;
  left: 30%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
}

.ring-center strong {
  font-size: 26px;
}

.ring-center span {
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
