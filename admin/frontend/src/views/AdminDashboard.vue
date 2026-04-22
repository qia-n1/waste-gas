<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElNotification } from "element-plus";

import { createAdminSseConnection } from "@/api/adminSse";
import { createVocsSseConnection } from "@/api/sse";
import AlarmCenter from "@/components/dashboard/AlarmCenter.vue";
import AnomalyHeatmap from "@/components/dashboard/AnomalyHeatmap.vue";
import ContinuousAlerts from "@/components/dashboard/ContinuousAlerts.vue";
import DecisionSupport from "@/components/dashboard/DecisionSupport.vue";
import EquipmentStatusChart from "@/components/dashboard/EquipmentStatusChart.vue";
import FactoryScene from "@/components/dashboard/FactoryScene.vue";
import TopContributorCharts from "@/components/dashboard/TopContributorCharts.vue";
import VocsTrendChart from "@/components/dashboard/VocsTrendChart.vue";
import DashboardLayout from "@/layouts/DashboardLayout.vue";
import { useAlertsStore } from "@/stores/alerts";
import { useAuthStore } from "@/stores/auth";
import { useDashboardStore } from "@/stores/dashboard";
import { useSensorsStore } from "@/stores/sensors";

const authStore = useAuthStore();
const dashboardStore = useDashboardStore();
const alertsStore = useAlertsStore();
const sensorsStore = useSensorsStore();
const router = useRouter();

const selectedAlertId = ref("");
let refreshTimer: number | null = null;

const sse = createVocsSseConnection({
  onSensorData(data) {
    sensorsStore.updateLatest(data);
    dashboardStore.updateFromSensorData(data);
  },
  onPrediction(data) {
    dashboardStore.updateFromPrediction(data, sensorsStore.latestSensorData);
    if (data.alert_triggered) {
      void alertsStore.fetchAlerts();
    }
  },
  onStatusChange(connected) {
    dashboardStore.setConnected(connected);
  },
});

// Admin-side SSE for watchdog (90s 设备掉线) alerts. Pushes straight into the
// AlarmCenter and pops a toast so operators are notified immediately.
const adminSse = createAdminSseConnection({
  onDeviceAlert(alert) {
    alertsStore.pushAlert(alert);
    const isRecovery = alert.level === "info" || alert.status === "已恢复";
    ElNotification({
      title: isRecovery ? "设备通信已恢复" : "设备数据采集中断",
      message: alert.message,
      type: isRecovery ? "success" : "error",
      duration: isRecovery ? 4000 : 0, // critical stays until dismissed
      position: "top-right",
    });
  },
});

const decisionSummary = computed(
  () => alertsStore.diagnosis?.summary ?? dashboardStore.overview.decision.summary,
);
const decisionSuggestions = computed(
  () => alertsStore.diagnosis?.recommendations ?? dashboardStore.overview.decision.suggestions,
);
const decisionRagCard = computed(() => alertsStore.diagnosis?.ragCard ?? null);

const loadData = async () => {
  try {
    await Promise.all([dashboardStore.initializeDashboard(), alertsStore.fetchAlerts()]);
  } catch (error) {
    console.error(error);
    ElMessage.warning("部分实时服务未连接，当前显示本地回放数据。");
  }
};

const handleSearch = async (value: string) => {
  alertsStore.searchQuery = value;
  await alertsStore.fetchAlerts({ search: value });
};

const handleSelectAlert = async (alertId: string) => {
  selectedAlertId.value = alertId;
  try {
    await alertsStore.loadDiagnosis(alertId);
  } catch (error) {
    console.error(error);
  }
};

const handleAcknowledge = async (alertId?: string) => {
  const targetId =
    alertId ||
    selectedAlertId.value ||
    alertsStore.alerts.find((item) => !item.acknowledged)?.alert_id;

  if (!targetId) {
    ElMessage.info("当前没有待处置告警");
    return;
  }

  try {
    await alertsStore.acknowledgeAlert(targetId);
    await alertsStore.fetchAlerts();
    ElMessage.success("已完成告警确认");
  } catch (error) {
    console.error(error);
    ElMessage.error("告警确认失败");
  }
};

const handleExport = () => {
  // DecisionSupport 已经在本地把 HTML 报告下载下来了，这里只负责反馈
  ElMessage.success("报告已生成并下载");
};

const handleLogout = async () => {
  authStore.logout();
  await router.push("/login");
};

onMounted(async () => {
  await loadData();
  sse.connect();
  adminSse.connect();
  refreshTimer = window.setInterval(() => {
    void loadData();
  }, 30000);
});

onBeforeUnmount(() => {
  sse.disconnect();
  adminSse.disconnect();
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer);
  }
});
</script>

<template>
  <DashboardLayout
    :metrics="dashboardStore.overview.metrics"
    :connected="dashboardStore.connected"
    :user-name="authStore.user?.name ?? '管理员'"
    @logout="handleLogout"
  >
    <template #left>
      <VocsTrendChart :trend="dashboardStore.overview.trend" />
      <EquipmentStatusChart :data="dashboardStore.equipmentStatus" :attribution="dashboardStore.attribution" />
      <TopContributorCharts :items="dashboardStore.topContributorSeries" />
      <AnomalyHeatmap :data="dashboardStore.heatmap" />
    </template>

    <template #center>
      <FactoryScene
        :nodes="dashboardStore.overview.factoryNodes"
        :current-vocs="dashboardStore.overview.metrics.currentVocs"
        :system-phase="dashboardStore.overview.metrics.systemPhase"
        :is-exceed-warning="dashboardStore.isExceedWarning"
        :emitter-concentrations="dashboardStore.emitterConcentrations"
      />
    </template>

    <template #right>
      <AlarmCenter
        :alerts="alertsStore.alerts"
        :loading="alertsStore.loading"
        :search="alertsStore.searchQuery"
        @search="handleSearch"
        @select="handleSelectAlert"
        @acknowledge="handleAcknowledge"
      />
      <ContinuousAlerts :items="dashboardStore.overview.continuousAlerts" />
      <DecisionSupport
        :metrics="dashboardStore.overview.metrics"
        :key-parameters="dashboardStore.overview.keyParameters"
        :summary="decisionSummary"
        :suggestions="decisionSuggestions"
        :forecast-series="dashboardStore.overview.trend.forecastSeries"
        :rag-card="decisionRagCard"
        @acknowledge="handleAcknowledge"
        @export="handleExport"
      />
    </template>
  </DashboardLayout>
</template>
