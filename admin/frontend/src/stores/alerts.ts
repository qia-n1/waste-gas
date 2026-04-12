import { computed, ref } from "vue";
import { defineStore } from "pinia";

import client from "@/api/client";
import type { AlertItem, AlertsResponse, DiagnosisResponse } from "@/types/dashboard";

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
      alerts.value = data.items;
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

  return {
    alerts,
    diagnosis,
    searchQuery,
    loading,
    activeCount,
    fetchAlerts,
    acknowledgeAlert,
    loadDiagnosis,
  };
});
