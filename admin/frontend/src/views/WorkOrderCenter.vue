<script setup lang="ts">
import dayjs from "dayjs";
import { computed, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import VChart from "vue-echarts";

import HeaderBar from "@/components/layout/HeaderBar.vue";
import { useAuthStore } from "@/stores/auth";
import { useWorkOrderStore } from "@/stores/workOrder";

const authStore = useAuthStore();
const router = useRouter();
const store = useWorkOrderStore();

const metrics = reactive({
  currentVocs: 0,
  peakForecast: 0,
  alertLevel: "normal",
  onlineDevices: 0,
  totalDevices: 0,
  todayAlerts: 0,
  systemPhase: "代维工单全流程管理",
  uptime: "--",
  confidence: 0,
  dataCompleteness: 0,
  latencyMs: 0,
  predictionType: "manual",
});

const handleLogout = async () => {
  authStore.logout();
  await router.push("/login");
};

onMounted(async () => {
  try {
    await store.fetchAll();
    metrics.onlineDevices = store.overview.totalThisMonth;
    metrics.totalDevices = store.overview.totalThisMonth + store.overview.pendingCount;
    metrics.todayAlerts = store.overview.pendingCount;
  } catch (error) {
    console.error(error);
    ElMessage.warning("工单数据加载失败，请检查后端服务。");
  }
});

// —————— chart options ——————

const trendOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    borderColor: "rgba(95, 122, 191, 0.28)",
    textStyle: { color: "#e9f2ff" },
    formatter: (params: Array<{ axisValue: string; data: number }>) =>
      `${dayjs(params[0]?.axisValue).format("MM-DD")}<br/>工单数：${params[0]?.data}`,
  },
  grid: { top: 16, left: 8, right: 12, bottom: 28, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: store.trend.points.map((p) => p.date),
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisTick: { show: false },
    axisLabel: {
      color: "#8ea3c9",
      fontSize: 10,
      interval: Math.max(0, Math.floor(store.trend.points.length / 6) - 1),
      formatter: (v: string) => dayjs(v).format("M/D"),
    },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLabel: { color: "#8ea3c9", fontSize: 10 },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      type: "line",
      smooth: 0.35,
      showSymbol: false,
      lineStyle: { width: 2.4, color: "#53d1ff" },
      areaStyle: {
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(83, 209, 255, 0.28)" },
            { offset: 1, color: "rgba(83, 209, 255, 0.02)" },
          ],
        },
      },
      data: store.trend.points.map((p) => p.count),
    },
  ],
}));

const typeOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: { trigger: "item", backgroundColor: "rgba(8, 16, 33, 0.92)", textStyle: { color: "#e9f2ff" } },
  legend: {
    bottom: 0,
    textStyle: { color: "#8ea3c9", fontSize: 10 },
    itemWidth: 10,
    itemHeight: 8,
  },
  series: [
    {
      type: "pie",
      radius: ["42%", "66%"],
      center: ["50%", "44%"],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: "rgba(8, 16, 33, 0.9)", borderWidth: 2 },
      label: { color: "#cfd9ee", fontSize: 10, formatter: "{b}\n{d}%" },
      labelLine: { lineStyle: { color: "rgba(160,180,220,0.4)" } },
      data: store.typeDistribution.items.map((i) => ({
        name: i.name,
        value: i.value,
        itemStyle: { color: i.color },
      })),
    },
  ],
}));

const firstFixOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    textStyle: { color: "#e9f2ff" },
    formatter: (params: Array<{ name: string; data: number }>) =>
      `${params[0]?.name}<br/>一次性修复率：${(params[0]?.data * 100).toFixed(1)}%`,
  },
  grid: { top: 12, left: 8, right: 28, bottom: 8, containLabel: true },
  xAxis: {
    type: "value",
    max: 1,
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLabel: { color: "#8ea3c9", fontSize: 10, formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  yAxis: {
    type: "category",
    inverse: true,
    data: store.firstFixRate.items.map((i) => i.category),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: "#cfd9ee", fontSize: 11 },
  },
  series: [
    {
      type: "bar",
      barWidth: 14,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: (params: { dataIndex: number }) =>
          store.firstFixRate.items[params.dataIndex]?.color ?? "#53d1ff",
      },
      label: {
        show: true,
        position: "right",
        color: "#cfd9ee",
        fontSize: 10,
        formatter: (p: { data: number }) => `${(p.data * 100).toFixed(0)}%`,
      },
      data: store.firstFixRate.items.map((i) => i.rate),
    },
  ],
}));

const durationOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    textStyle: { color: "#e9f2ff" },
    formatter: (params: Array<{ name: string; data: number }>) =>
      `${params[0]?.name}<br/>平均 ${params[0]?.data} 小时`,
  },
  grid: { top: 16, left: 8, right: 12, bottom: 28, containLabel: true },
  xAxis: {
    type: "category",
    data: store.durationStats.items.map((i) => i.month.slice(5)),
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisTick: { show: false },
    axisLabel: { color: "#8ea3c9", fontSize: 10 },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLabel: { color: "#8ea3c9", fontSize: 10, formatter: (v: number) => `${v}h` },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      type: "bar",
      barWidth: 18,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "#ffb347" },
            { offset: 1, color: "rgba(255, 179, 71, 0.15)" },
          ],
        },
      },
      data: store.durationStats.items.map((i) => i.avgHours),
    },
  ],
}));

const deviceAgeOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
    axisPointer: { type: "shadow" },
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    textStyle: { color: "#e9f2ff" },
  },
  grid: { top: 12, left: 8, right: 12, bottom: 28, containLabel: true },
  xAxis: {
    type: "category",
    data: store.deviceAge.buckets.map((b) => b.range),
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisTick: { show: false },
    axisLabel: { color: "#8ea3c9", fontSize: 10 },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "rgba(120, 146, 209, 0.1)" } },
    axisLabel: { color: "#8ea3c9", fontSize: 10 },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      type: "bar",
      barWidth: 22,
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "#a78bfa" },
            { offset: 1, color: "rgba(167, 139, 250, 0.2)" },
          ],
        },
      },
      data: store.deviceAge.buckets.map((b) => b.count),
    },
  ],
}));

const rootCauseOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: { trigger: "item", backgroundColor: "rgba(8, 16, 33, 0.92)", textStyle: { color: "#e9f2ff" } },
  series: [
    {
      type: "pie",
      roseType: "radius",
      radius: ["28%", "72%"],
      center: ["50%", "52%"],
      itemStyle: { borderColor: "rgba(8, 16, 33, 0.9)", borderWidth: 2 },
      label: { color: "#cfd9ee", fontSize: 10 },
      labelLine: { lineStyle: { color: "rgba(160,180,220,0.4)" } },
      data: store.rootCauses.items.map((i) => ({
        name: i.cause,
        value: i.count,
        itemStyle: { color: i.color },
      })),
    },
  ],
}));

const attachmentOption = computed(() => ({
  backgroundColor: "transparent",
  tooltip: {
    trigger: "axis",
    backgroundColor: "rgba(8, 16, 33, 0.92)",
    textStyle: { color: "#e9f2ff" },
    formatter: (params: Array<{ axisValue: string; data: number }>) =>
      `${dayjs(params[0]?.axisValue).format("MM-DD")}<br/>照片 ${params[0]?.data} 张`,
  },
  grid: { top: 10, left: 8, right: 8, bottom: 22, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: store.attachmentsTrend.points.map((p) => p.date),
    axisLine: { lineStyle: { color: "rgba(120, 146, 209, 0.18)" } },
    axisTick: { show: false },
    axisLabel: {
      color: "#8ea3c9",
      fontSize: 9,
      interval: Math.max(0, Math.floor(store.attachmentsTrend.points.length / 5) - 1),
      formatter: (v: string) => dayjs(v).format("M/D"),
    },
  },
  yAxis: { show: false, type: "value" },
  series: [
    {
      type: "line",
      smooth: 0.4,
      showSymbol: false,
      lineStyle: { width: 2, color: "#7dd3fc" },
      areaStyle: {
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(125, 211, 252, 0.3)" },
            { offset: 1, color: "rgba(125, 211, 252, 0.02)" },
          ],
        },
      },
      data: store.attachmentsTrend.points.map((p) => p.count),
    },
  ],
}));

// —————— heatmap: simple grid by weeks × 7 days ——————
const heatmapMatrix = computed(() => {
  const cells = store.repairHeatmap.cells;
  if (cells.length === 0) return [] as Array<Array<{ date: string; value: number }>>;
  const startDate = dayjs(cells[0].date);
  const startDow = startDate.day(); // 0=Sun..6=Sat
  const buffered = [
    ...Array(startDow).fill(null).map(() => ({ date: "", value: -1 })),
    ...cells,
  ];
  const weeks: Array<Array<{ date: string; value: number }>> = [];
  for (let i = 0; i < buffered.length; i += 7) {
    weeks.push(buffered.slice(i, i + 7));
  }
  return weeks;
});

const heatmapColor = (v: number) => {
  if (v < 0) return "transparent";
  if (v === 0) return "rgba(120, 146, 209, 0.08)";
  if (v === 1) return "rgba(83, 209, 255, 0.28)";
  if (v === 2) return "rgba(83, 209, 255, 0.55)";
  if (v === 3) return "rgba(83, 209, 255, 0.75)";
  return "rgba(83, 209, 255, 0.95)";
};
</script>

<template>
  <div class="workorder-page">
    <HeaderBar
      :metrics="metrics"
      :connected="!store.error"
      :user-name="authStore.user?.name ?? '管理员'"
      @logout="handleLogout"
    />

    <main class="wo-content">
      <!-- 标题带 -->
      <section class="wo-hero">
        <div class="wo-hero__title">
          <span class="wo-hero__badge">运维工单</span>
          <h2>运维工单全流程管理</h2>
        </div>
        <div class="wo-hero__kpis">
          <div class="kpi-chip">
            <span>当月工单</span>
            <strong>{{ store.overview.totalThisMonth }}</strong>
            <em :class="store.overview.momChangePct >= 0 ? 'up' : 'down'">
              {{ store.overview.momChangePct >= 0 ? "+" : "" }}{{ store.overview.momChangePct }}%
            </em>
          </div>
          <div class="kpi-chip">
            <span>一次性修复率</span>
            <strong class="highlight-cyan">{{ (store.overview.firstFixRate * 100).toFixed(1) }}%</strong>
          </div>
          <div class="kpi-chip">
            <span>平均处理</span>
            <strong class="highlight-amber">{{ store.overview.avgResolutionHours }}h</strong>
          </div>
          <div class="kpi-chip">
            <span>待处理 / 超时</span>
            <strong>
              {{ store.overview.pendingCount }}
              <em class="down">/ {{ store.overview.overdueCount }}</em>
            </strong>
          </div>
        </div>
      </section>

      <!-- 九宫格主体 -->
      <section class="wo-grid">
        <!-- Row 1 -->
        <article class="panel-card card--span2">
          <div class="card-header">
            <span class="card-title">工单处理数量（近 30 天）</span>
            <span class="card-sub">月度分析报告</span>
          </div>
          <VChart class="chart-host" :option="trendOption" autoresize />
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">工单类型分布</span>
            <span class="card-sub">More quantity</span>
          </div>
          <VChart class="chart-host" :option="typeOption" autoresize />
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">月度分析报告</span>
            <span class="card-sub">实现的功能</span>
          </div>
          <ul class="feature-list">
            <li v-for="(feat, idx) in store.overview.reportFeatures" :key="feat">
              <span class="feature-idx">{{ idx + 1 }}.</span>{{ feat }}
            </li>
          </ul>
        </article>

        <!-- Row 2 -->
        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">平均维修时长</span>
            <span class="card-sub">Average duration</span>
          </div>
          <div class="big-metric">
            <strong>{{ store.durationStats.currentAvg }}</strong>
            <span>小时</span>
          </div>
          <VChart class="chart-host chart-small" :option="durationOption" autoresize />
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">一次性修复率</span>
            <span class="card-sub">按故障类型</span>
          </div>
          <VChart class="chart-host" :option="firstFixOption" autoresize />
          <div class="overall-bar">
            <span>整体</span>
            <strong class="highlight-cyan">{{ (store.firstFixRate.overall * 100).toFixed(1) }}%</strong>
          </div>
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">反复报修厂区 Top</span>
            <span class="card-sub">多发地区汇总</span>
          </div>
          <ul class="site-list">
            <li v-for="site in store.repeatedSites.items" :key="site.site">
              <div class="site-info">
                <span class="site-name">{{ site.site }}</span>
                <span class="site-time">最近：{{ site.lastAt }}</span>
              </div>
              <span class="site-count">{{ site.count }} 次</span>
            </li>
          </ul>
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">维修日历热力图</span>
            <span class="card-sub">Less ▢▢▢▢ More</span>
          </div>
          <div class="heatmap">
            <div v-for="(week, wi) in heatmapMatrix" :key="wi" class="heatmap-col">
              <div
                v-for="(cell, ci) in week"
                :key="ci"
                class="heatmap-cell"
                :style="{ background: heatmapColor(cell.value) }"
                :title="cell.date ? `${cell.date}：${cell.value} 单` : ''"
              />
            </div>
          </div>
          <div class="heatmap-legend">
            <span>少</span>
            <span class="legend-dot" :style="{ background: heatmapColor(0) }" />
            <span class="legend-dot" :style="{ background: heatmapColor(1) }" />
            <span class="legend-dot" :style="{ background: heatmapColor(2) }" />
            <span class="legend-dot" :style="{ background: heatmapColor(3) }" />
            <span class="legend-dot" :style="{ background: heatmapColor(4) }" />
            <span>多</span>
          </div>
        </article>

        <!-- Row 3 -->
        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">设备服役年限</span>
            <span class="card-sub">年限分布</span>
          </div>
          <VChart class="chart-host" :option="deviceAgeOption" autoresize />
        </article>

        <article class="panel-card">
          <div class="card-header">
            <span class="card-title">故障根因 Top</span>
            <span class="card-sub">原因汇总 73%</span>
          </div>
          <VChart class="chart-host" :option="rootCauseOption" autoresize />
        </article>

        <article class="panel-card card--span2">
          <div class="card-header">
            <span class="card-title">现场照片收集数量</span>
            <span class="card-sub">附件增长 · 共 {{ store.attachmentsTrend.total }} 张</span>
          </div>
          <div class="photo-metric">
            <strong>{{ store.overview.photoCount }}</strong>
            <span>累计图片</span>
          </div>
          <VChart class="chart-host chart-small" :option="attachmentOption" autoresize />
        </article>
      </section>

      <!-- 底部说明带 -->
      <section class="wo-footer-note">
        该页面对工单的地点、时间、类别、故障类型、处理时长等因素均进行了统计分析，参考上月或去年同时期的维修记录统计，
        横向分析周围设备是否会出现聚集故障的情况，纵向分析最近一段时间是否会再次出现同类隐患。
      </section>
    </main>
  </div>
</template>

<style scoped>
.workorder-page {
  width: 100%;
  height: 100%;
  padding: 18px;
  display: grid;
  grid-template-rows: 88px minmax(0, 1fr);
  gap: 14px;
}

.wo-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 10px;
  scrollbar-gutter: stable;
  /* Firefox */
  scrollbar-width: thin;
  scrollbar-color: rgba(117, 167, 255, 0.45) rgba(9, 18, 38, 0.4);
}

/* WebKit / Chromium custom scrollbar — visible draggable thumb */
.wo-content::-webkit-scrollbar {
  width: 10px;
}

.wo-content::-webkit-scrollbar-track {
  background: rgba(9, 18, 38, 0.4);
  border: 1px solid rgba(98, 128, 194, 0.16);
  border-radius: 8px;
  margin: 4px 0;
}

.wo-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(125, 211, 252, 0.55), rgba(117, 167, 255, 0.75));
  border: 1px solid rgba(185, 215, 255, 0.25);
  border-radius: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
}

.wo-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(125, 211, 252, 0.8), rgba(117, 167, 255, 0.95));
}

.wo-content::-webkit-scrollbar-thumb:active {
  background: linear-gradient(180deg, rgba(83, 209, 255, 0.95), rgba(97, 160, 255, 1));
}

/* —— hero —— */
.wo-hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 14px 20px;
  border: 1px solid rgba(117, 167, 255, 0.25);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(62, 80, 180, 0.55), rgba(22, 30, 78, 0.8));
  box-shadow: inset 0 1px 0 rgba(185, 215, 255, 0.14), 0 4px 24px rgba(4, 12, 34, 0.3);
}

.wo-hero__title {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.wo-hero__badge {
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #e9f2ff;
  font-size: 12px;
  letter-spacing: 0.12em;
}

.wo-hero__title h2 {
  margin: 0;
  color: #f3f8ff;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.wo-hero__kpis {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.kpi-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-width: 110px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(9, 18, 38, 0.55);
  border: 1px solid rgba(117, 167, 255, 0.2);
}

.kpi-chip span {
  color: rgba(180, 200, 235, 0.7);
  font-size: 11px;
}

.kpi-chip strong {
  color: #e8f0ff;
  font-size: 18px;
  font-weight: 700;
}

.kpi-chip em {
  font-style: normal;
  font-size: 11px;
  margin-left: 4px;
}

.kpi-chip em.up { color: #ff8e98; }
.kpi-chip em.down { color: #7dd3fc; }

.highlight-cyan { color: #53d1ff !important; }
.highlight-amber { color: #ffb347 !important; }

/* —— grid —— */
.wo-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: 260px;
  gap: 14px;
}

.card--span2 {
  grid-column: span 2;
}

.panel-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  border: 1px solid rgba(98, 128, 194, 0.2);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(16, 28, 58, 0.82), rgba(10, 18, 40, 0.82));
  box-shadow: inset 0 1px 0 rgba(185, 215, 255, 0.08), 0 4px 20px rgba(4, 12, 34, 0.25);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 2px;
}

.card-title {
  font-size: 14px;
  font-weight: 700;
  color: #e8f0ff;
  letter-spacing: 0.04em;
}

.card-sub {
  font-size: 11px;
  color: rgba(180, 200, 235, 0.65);
}

.chart-host {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.chart-small {
  height: 120px;
  flex: none;
}

/* —— feature list —— */
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.feature-list li {
  font-size: 12px;
  color: #cfd9ee;
  padding: 4px 0;
  border-bottom: 1px dashed rgba(120, 146, 209, 0.15);
}

.feature-idx {
  color: #53d1ff;
  margin-right: 6px;
  font-weight: 700;
}

/* —— big metric / photo metric —— */
.big-metric, .photo-metric {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.big-metric strong, .photo-metric strong {
  color: #ffb347;
  font-size: 34px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.photo-metric strong { color: #7dd3fc; }

.big-metric span, .photo-metric span {
  color: rgba(180, 200, 235, 0.7);
  font-size: 12px;
}

/* —— overall bar under first-fix —— */
.overall-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-top: 1px dashed rgba(120, 146, 209, 0.15);
  font-size: 12px;
  color: rgba(180, 200, 235, 0.7);
}

.overall-bar strong {
  font-size: 16px;
  font-weight: 700;
}

/* —— site list —— */
.site-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.site-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(9, 18, 38, 0.4);
  border: 1px solid rgba(120, 146, 209, 0.1);
}

.site-info {
  display: flex;
  flex-direction: column;
}

.site-name {
  font-size: 12px;
  color: #e8f0ff;
  font-weight: 600;
}

.site-time {
  font-size: 10px;
  color: rgba(180, 200, 235, 0.55);
}

.site-count {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 91, 97, 0.16);
  color: #ff8e98;
  font-size: 11px;
  font-weight: 600;
}

/* —— heatmap —— */
.heatmap {
  display: flex;
  gap: 3px;
  flex: 1;
  min-height: 0;
  padding: 4px 0;
  align-items: flex-start;
}

.heatmap-col {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.heatmap-cell {
  aspect-ratio: 1;
  width: 100%;
  border-radius: 3px;
  border: 1px solid rgba(120, 146, 209, 0.1);
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  font-size: 10px;
  color: rgba(180, 200, 235, 0.65);
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  border: 1px solid rgba(120, 146, 209, 0.2);
}

/* —— footer —— */
.wo-footer-note {
  padding: 14px 20px;
  border: 1px solid rgba(117, 167, 255, 0.2);
  border-radius: 14px;
  background: rgba(15, 27, 56, 0.55);
  color: #cfd9ee;
  font-size: 13px;
  line-height: 1.8;
}

@media (max-width: 1440px) {
  .wo-grid {
    grid-auto-rows: 240px;
  }
}

@media (max-width: 1200px) {
  .wo-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .card--span2 { grid-column: span 2; }
}
</style>
