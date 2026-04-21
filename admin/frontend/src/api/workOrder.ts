import client from "@/api/client";
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

export const fetchWorkOrderOverview = async (): Promise<WorkOrderOverview> => {
  const { data } = await client.get<WorkOrderOverview>("/work-orders/overview");
  return data;
};

export const fetchWorkOrderTrend = async (days = 30): Promise<WorkOrderTrend> => {
  const { data } = await client.get<WorkOrderTrend>("/work-orders/trend", { params: { days } });
  return data;
};

export const fetchTypeDistribution = async (): Promise<TypeDistributionResponse> => {
  const { data } = await client.get<TypeDistributionResponse>("/work-orders/type-distribution");
  return data;
};

export const fetchFirstFixRate = async (): Promise<FirstFixRateResponse> => {
  const { data } = await client.get<FirstFixRateResponse>("/work-orders/first-fix-rate");
  return data;
};

export const fetchRepeatedSites = async (limit = 8): Promise<RepeatedSitesResponse> => {
  const { data } = await client.get<RepeatedSitesResponse>("/work-orders/repeated-sites", {
    params: { limit },
  });
  return data;
};

export const fetchDurationStats = async (): Promise<DurationStatsResponse> => {
  const { data } = await client.get<DurationStatsResponse>("/work-orders/duration-stats");
  return data;
};

export const fetchDeviceAge = async (): Promise<DeviceAgeResponse> => {
  const { data } = await client.get<DeviceAgeResponse>("/work-orders/device-age");
  return data;
};

export const fetchRepairHeatmap = async (weeks = 14): Promise<RepairHeatmapResponse> => {
  const { data } = await client.get<RepairHeatmapResponse>("/work-orders/repair-heatmap", {
    params: { weeks },
  });
  return data;
};

export const fetchRootCauses = async (): Promise<RootCauseResponse> => {
  const { data } = await client.get<RootCauseResponse>("/work-orders/root-causes");
  return data;
};

export const fetchAttachmentsTrend = async (days = 30): Promise<AttachmentsTrendResponse> => {
  const { data } = await client.get<AttachmentsTrendResponse>("/work-orders/attachments-trend", {
    params: { days },
  });
  return data;
};
