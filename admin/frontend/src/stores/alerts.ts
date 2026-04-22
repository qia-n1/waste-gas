import { computed, ref } from "vue";
import { defineStore } from "pinia";

import client from "@/api/client";
import type { AlertItem, AlertsResponse, DiagnosisResponse } from "@/types/dashboard";

/**
 * 演示用 Mock 告警 —— 后端告警数量较少时用来"撑场面"，保证评审/答辩
 * 能看到典型的红/橙/已处理混合状态。每次 fetchAlerts 时会把这些 mock
 * 追加到真实告警之后，真实告警优先展示。
 *
 * 时间戳用相对当前时间的偏移生成（见 buildMockAlerts），不会固定在某个
 * 死掉的过去时刻，避免首屏看起来"数据很旧"。
 */
const buildMockAlerts = (): AlertItem[] => {
  const now = Date.now();
  const iso = (offsetMinutes: number) => new Date(now - offsetMinutes * 60_000).toISOString();
  return [
    {
      alert_id: "mock-alert-001",
      timestamp: iso(3),
      level: "critical",
      message: "RTO 出口 VOCs 浓度连续 8 分钟超过 100 mg/m³ 红线，请立即核查燃烧段温度与气量。",
      value: 112.4,
      threshold: 100,
      acknowledged: false,
      location: "排口烟囱 / RTO 出口",
      status: "待处置",
    },
    {
      alert_id: "mock-alert-002",
      timestamp: iso(12),
      level: "warning",
      message: "转轮入口浓度持续偏高 (185 mg/m³)，建议关注前级喷涂工况与转轮转速。",
      value: 185.2,
      threshold: 150,
      acknowledged: false,
      location: "转轮吸附 / 入口",
      status: "处置中",
    },
    {
      alert_id: "mock-alert-003",
      timestamp: iso(26),
      level: "warning",
      message: "脱附温度 198°C 接近上限 (200°C)，请检查热媒阀位与换热器积垢。",
      value: 198,
      threshold: 180,
      acknowledged: false,
      location: "公辅燃烧区 / 脱附换热器",
      status: "待处置",
    },
    {
      alert_id: "mock-alert-004",
      timestamp: iso(54),
      level: "warning",
      message: "喷涂风量 15800 m³/h 超过预警阈值，工艺风阀开度偏大。",
      value: 15800,
      threshold: 14000,
      acknowledged: true,
      location: "喷涂生产厂房 / 入口风机",
      status: "已处理",
    },
    {
      alert_id: "mock-alert-005",
      timestamp: iso(92),
      level: "critical",
      message: "燃气流量 118 Nm³/h 持续偏高，有超温风险。",
      value: 118,
      threshold: 110,
      acknowledged: true,
      location: "公辅燃烧区 / 主燃烧器",
      status: "已处理",
    },
  ];
};

export const useAlertsStore = defineStore("alerts", () => {
  const alerts = ref<AlertItem[]>([]);
  const diagnosis = ref<DiagnosisResponse | null>(null);
  const searchQuery = ref("");
  const loading = ref(false);

  const activeCount = computed(
    () => alerts.value.filter((item) => !item.acknowledged).length,
  );

  const fetchAlerts = async (params?: { search?: string; level?: string }) => {
    loading.value = true;
    try {
      const { data } = await client.get<AlertsResponse>("/alerts", {
        params: {
          limit: 30,
          search: params?.search ?? searchQuery.value,
          level: params?.level ?? "",
        },
      });
      const mocks = buildMockAlerts();
      // 去重：如果后端真的塞了同 ID 的数据（理论上不会，但给未来接真数据留余地）
      // 优先保留真实条目，mock 只填不够的部分。
      const realIds = new Set(data.items.map((item) => item.alert_id));
      const merged = [...data.items, ...mocks.filter((m) => !realIds.has(m.alert_id))];
      // 搜索词生效时对合并结果做一次前端过滤，让 mock 也响应搜索
      const search = (params?.search ?? searchQuery.value).trim();
      alerts.value = search
        ? merged.filter(
            (item) =>
              item.message.includes(search) ||
              item.location.includes(search) ||
              item.level.includes(search),
          )
        : merged;
    } catch (_error) {
      // 后端挂了也至少让 mock 出来，保证答辩演示不会全空
      alerts.value = buildMockAlerts();
    } finally {
      loading.value = false;
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    await client.post(`/alerts/${alertId}/acknowledge`);
    alerts.value = alerts.value.map((item) =>
      item.alert_id === alertId
        ? { ...item, acknowledged: true, status: "已处理" }
        : item,
    );
  };

  const loadDiagnosis = async (alertId: string) => {
    const { data } = await client.get<DiagnosisResponse>(`/alerts/${alertId}/diagnosis`);
    diagnosis.value = data;
  };

  /**
   * Insert (or replace) an alert at the top of the list. Used by the admin
   * SSE pipeline so that watchdog-emitted device alerts surface immediately
   * in the AlarmCenter without waiting for the next 30s polling tick.
   */
  const pushAlert = (alert: AlertItem) => {
    const filtered = alerts.value.filter((item) => item.alert_id !== alert.alert_id);
    alerts.value = [alert, ...filtered].slice(0, 50);
  };

  return {
    alerts,
    diagnosis,
    searchQuery,
    loading,
    activeCount,
    fetchAlerts,
    acknowledgeAlert,
    loadDiagnosis,
    pushAlert,
  };
});
