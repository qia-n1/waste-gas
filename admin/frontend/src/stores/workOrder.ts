import { ref } from "vue";
import { defineStore } from "pinia";

import {
  fetchAttachmentsTrend,
  fetchDeviceAge,
  fetchDurationStats,
  fetchFirstFixRate,
  fetchRepairHeatmap,
  fetchRepeatedSites,
  fetchRootCauses,
  fetchTypeDistribution,
  fetchWorkOrderOverview,
  fetchWorkOrderTrend,
} from "@/api/workOrder";
import type {
  AttachmentsTrendResponse,
  DeviceAgeResponse,
  DurationStatsResponse,
  FirstFixRateResponse,
  RepairHeatmapResponse,
  RepeatedSitesResponse,
  RootCauseResponse,
  TypeDistributionResponse,
  WorkOrderOverview,
  WorkOrderTrend,
} from "@/types/workOrder";

const createOverview = (): WorkOrderOverview => ({
  month: "--",
  totalThisMonth: 0,
  totalLastMonth: 0,
  momChangePct: 0,
  firstFixRate: 0,
  avgResponseHours: 0,
  avgResolutionHours: 0,
  pendingCount: 0,
  overdueCount: 0,
  photoCount: 0,
  updatedAt: "",
  kpiNotes: [],
  reportFeatures: [],
});

export const useWorkOrderStore = defineStore("workOrder", () => {
  const overview = ref<WorkOrderOverview>(createOverview());
  const trend = ref<WorkOrderTrend>({ points: [] });
  const typeDistribution = ref<TypeDistributionResponse>({ items: [], total: 0 });
  const firstFixRate = ref<FirstFixRateResponse>({ items: [], overall: 0 });
  const repeatedSites = ref<RepeatedSitesResponse>({ items: [] });
  const durationStats = ref<DurationStatsResponse>({ items: [], currentAvg: 0 });
  const deviceAge = ref<DeviceAgeResponse>({ buckets: [] });
  const repairHeatmap = ref<RepairHeatmapResponse>({ cells: [], start: "", end: "" });
  const rootCauses = ref<RootCauseResponse>({ items: [], total: 0 });
  const attachmentsTrend = ref<AttachmentsTrendResponse>({ points: [], total: 0 });

  const loading = ref(false);
  const error = ref("");

  const fetchAll = async () => {
    loading.value = true;
    error.value = "";
    try {
      const [
        overviewData,
        trendData,
        typeData,
        firstFixData,
        sitesData,
        durationData,
        ageData,
        heatmapData,
        rootCauseData,
        attachData,
      ] = await Promise.all([
        fetchWorkOrderOverview(),
        fetchWorkOrderTrend(30),
        fetchTypeDistribution(),
        fetchFirstFixRate(),
        fetchRepeatedSites(8),
        fetchDurationStats(),
        fetchDeviceAge(),
        fetchRepairHeatmap(14),
        fetchRootCauses(),
        fetchAttachmentsTrend(30),
      ]);

      overview.value = overviewData;
      trend.value = trendData;
      typeDistribution.value = typeData;
      firstFixRate.value = firstFixData;
      repeatedSites.value = sitesData;
      durationStats.value = durationData;
      deviceAge.value = ageData;
      repairHeatmap.value = heatmapData;
      rootCauses.value = rootCauseData;
      attachmentsTrend.value = attachData;
    } catch (err) {
      console.error("[workOrder] fetchAll failed", err);
      error.value = err instanceof Error ? err.message : String(err);
    } finally {
      loading.value = false;
    }
  };

  return {
    overview,
    trend,
    typeDistribution,
    firstFixRate,
    repeatedSites,
    durationStats,
    deviceAge,
    repairHeatmap,
    rootCauses,
    attachmentsTrend,
    loading,
    error,
    fetchAll,
  };
});
