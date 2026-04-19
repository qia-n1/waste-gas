<script setup lang="ts">
import dayjs from "dayjs";
import { computed, ref } from "vue";
import VChart from "vue-echarts";

import type { DashboardTrend } from "@/types/dashboard";

interface AxisSeriesPoint {
  timestamp: string;
  actual: number | null;
  forecast: number | null;
}

const props = defineProps<{
  trend: DashboardTrend;
}>();

const initialRange = () => {
  const actual = props.trend.actualSeries;
  const first = actual[0]?.timestamp;
  const lastForecast = props.trend.forecastSeries[props.trend.forecastSeries.length - 1];
  const lastActual = actual[actual.length - 1];
  const last =
    lastForecast?.timestamp ??
    lastActual?.timestamp ??
    new Date().toISOString();

  return [
    first ? dayjs(first).toDate() : dayjs().subtract(1, "day").toDate(),
    last ? dayjs(last).toDate() : dayjs().add(1, "day").toDate(),
  ] as [Date, Date];
};

const range = ref<[Date, Date]>(initialRange());
const showForecast = ref(true);

const mergedSeries = computed<AxisSeriesPoint[]>(() => {
  const actualMap = new Map(
    props.trend.actualSeries.map((item) => [item.timestamp, item.value]),
  );
  const forecastMap = new Map(
    props.trend.forecastSeries.map((item) => [item.timestamp, item.value]),
  );

  const timestampSet = new Set<string>([
    ...props.trend.actualSeries.map((item) => item.timestamp),
    ...props.trend.forecastSeries.map((item) => item.timestamp),
  ]);

  return [...timestampSet]
    .sort((left, right) => dayjs(left).valueOf() - dayjs(right).valueOf())
    .filter((timestamp) => {
      const time = dayjs(timestamp);
      return (
        time.isAfter(dayjs(range.value[0]).startOf("day")) &&
        time.isBefore(dayjs(range.value[1]).endOf("day"))
      );
    })
    .map((timestamp) => ({
      timestamp,
      actual: actualMap.get(timestamp) ?? null,
      forecast: forecastMap.get(timestamp) ?? null,
    }));
});

const xAxisData = computed(() => mergedSeries.value.map((item) => item.timestamp));

const labelInterval = computed(() => {
  const total = xAxisData.value.length;
  if (total <= 8) {
    return 0;
  }
  return Math.max(Math.ceil(total / 8) - 1, 0);
});

const option = computed(() => ({
  backgroundColor: "transparent",
  animationDuration: 450,
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    borderColor: "rgba(95, 122, 191, 0.28)",
    textStyle: { color: "#e9f2ff" },
    formatter: (params: Array<{ axisValue: string; seriesName: string; data: number | null }>) => {
      const lines = [`${dayjs(params[0]?.axisValue).format("YYYY-MM-DD HH:mm")}`];
      params.forEach((item) => {
        if (item.data !== null && item.data !== undefined) {
          lines.push(`${item.seriesName}：${Number(item.data).toFixed(1)} mg/m³`);
        }
      });
      return lines.join("<br/>");
    },
  },
  legend: {
    top: 0,
    right: 0,
    itemWidth: 14,
    itemHeight: 8,
    textStyle: { color: "#8ea3c9", fontSize: 11 },
  },
  grid: {
    top: 18,
    left: 8,
    right: 8,
    bottom: 34,
    containLabel: true,
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: xAxisData.value,
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisTick: { show: false },
    axisLabel: {
      color: "#8ea3c9",
      fontSize: 10,
      lineHeight: 13,
      margin: 10,
      interval: labelInterval.value,
      formatter: (value: string) => {
        const time = dayjs(value);
        return `${time.format("HH:mm")}\n${time.format("M月D日")}`;
      },
    },
  },
  yAxis: {
    type: "value",
    splitNumber: 3,
    minInterval: 20,
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: {
      color: "#8ea3c9",
      fontSize: 10,
    },
  },
  series: [
    {
      name: "实测值",
      type: "line",
      smooth: 0.35,
      smoothMonotone: "x",
      connectNulls: false,
      showSymbol: false,
      sampling: "lttb",
      lineStyle: {
        width: 2.5,
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
            { offset: 0, color: "rgba(83, 209, 255, 0.28)" },
            { offset: 1, color: "rgba(83, 209, 255, 0.01)" },
          ],
        },
      },
      markLine: {
        silent: true,
        symbol: "none",
        label: {
          color: "#8ea3c9",
          fontSize: 10,
        },
        data: [
          {
            yAxis: props.trend.warningThreshold,
            lineStyle: { color: "#ffb347", type: "dashed", opacity: 0.85 },
            label: { formatter: "80 预警线" },
          },
          {
            yAxis: props.trend.criticalThreshold,
            lineStyle: { color: "#ff5b61", type: "dashed", opacity: 0.88 },
            label: { formatter: "100 红线" },
          },
        ],
      },
      data: mergedSeries.value.map((item) => item.actual),
    },
    {
      name: "预测值",
      type: "line",
      smooth: 0.35,
      smoothMonotone: "x",
      connectNulls: false,
      showSymbol: false,
      sampling: "lttb",
      lineStyle: {
        width: 2,
        type: "dashed",
        dashOffset: 2,
        color: "#ffb347",
        cap: "round",
        join: "round",
      },
      areaStyle: {
        color: "rgba(255, 179, 71, 0.06)",
      },
      data: showForecast.value ? mergedSeries.value.map((item) => item.forecast) : [],
    },
  ],
}));
</script>

<template>
  <section class="panel-card trend-card">
    <div class="panel-title">VOCs 浓度趋势</div>

    <div class="toolbar toolbar-primary">
      <el-date-picker
        v-model="range"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        size="small"
      />
      <div class="toolbar-actions">
        <span class="meta-chip">置信度 {{ Math.round(trend.confidence * 100) }}%</span>
        <el-switch
          v-model="showForecast"
          inline-prompt
          active-text="预告"
          inactive-text="隐藏"
        />
      </div>
    </div>

    <div class="toolbar toolbar-secondary">
      <span>阈值 {{ trend.warningThreshold }}/{{ trend.criticalThreshold }} mg/m³</span>
      <span>时间粒度 15 分钟</span>
    </div>

    <VChart class="chart-host trend-chart" :option="option" autoresize />
  </section>
</template>

<style scoped>
.trend-card {
  height: 208px;
  min-height: 208px;
  max-height: 208px;
  flex: 0 0 208px;
  padding: 14px 16px 12px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.toolbar-primary {
  margin-bottom: 4px;
}

.toolbar-secondary {
  margin-bottom: 4px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 1.1;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.meta-chip {
  color: var(--text-secondary);
  font-size: 11px;
  white-space: nowrap;
}

.trend-chart {
  min-height: 0;
  height: 118px;
}
</style>
