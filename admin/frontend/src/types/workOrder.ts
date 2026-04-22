export interface WorkOrderOverview {
  month: string;
  totalThisMonth: number;
  totalLastMonth: number;
  momChangePct: number;
  firstFixRate: number;
  avgResponseHours: number;
  avgResolutionHours: number;
  pendingCount: number;
  overdueCount: number;
  photoCount: number;
  updatedAt: string;
  kpiNotes: string[];
  reportFeatures: string[];
}

export interface TrendPoint {
  date: string;
  count: number;
}

export interface WorkOrderTrend {
  points: TrendPoint[];
}

export interface TypeDistributionItem {
  name: string;
  value: number;
  color: string;
}

export interface TypeDistributionResponse {
  items: TypeDistributionItem[];
  total: number;
}

export interface FirstFixRateItem {
  category: string;
  rate: number;
  total: number;
  color: string;
}

export interface FirstFixRateResponse {
  items: FirstFixRateItem[];
  overall: number;
}

export interface RepeatedSiteItem {
  site: string;
  count: number;
  lastAt: string;
}

export interface RepeatedSitesResponse {
  items: RepeatedSiteItem[];
}

export interface DurationStatsItem {
  month: string;
  avgHours: number;
}

export interface DurationStatsResponse {
  items: DurationStatsItem[];
  currentAvg: number;
}

export interface DeviceAgeBucket {
  range: string;
  count: number;
}

export interface DeviceAgeResponse {
  buckets: DeviceAgeBucket[];
}

export interface RepairHeatmapCell {
  date: string;
  value: number;
}

export interface RepairHeatmapResponse {
  cells: RepairHeatmapCell[];
  start: string;
  end: string;
}

export interface RootCauseItem {
  cause: string;
  count: number;
  color: string;
}

export interface RootCauseResponse {
  items: RootCauseItem[];
  total: number;
}

export interface AttachmentTrendPoint {
  date: string;
  count: number;
}

export interface AttachmentsTrendResponse {
  points: AttachmentTrendPoint[];
  total: number;
}
