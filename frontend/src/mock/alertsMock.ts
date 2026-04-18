export const alertsMockData = [
  {
    alert_id: "uuid-12345",
    trigger_time: "2026-04-08 10:30",
    level: "action",
    status: "pending",
    current_vocs: 82.3,
    peak_forecast: 94.1,
    first_exceed_at: "2026-04-08 11:00"
  }
];

export const alertDetailsMockData = {
  alert_id: "uuid-12345",
  trigger_time: "2026-04-08 10:30",
  level: "action",
  current_vocs: 82.3,
  peak_forecast: 94.1,
  diagnosis: "由于涂布流量突然增加 15%，RTO 装载炉出口浓度预计将会在 15 分钟后突破阈值。",
  feature_contributions: [
    { feature: "coating_flow", label: "涂布流量", delta: "+15%", weight: 0.42 },
    { feature: "combustion_temp", label: "燃烧温度", delta: "-3%", weight: 0.28 },
    { feature: "ambient_humidity", label: "环境湿度", delta: "+8%", weight: 0.12 }
  ],
  suggestions: [
    "手动调大燃烧机功率至 85%",
    "降低 A 设备涂布速率至 80%",
    "降温至 导风门开度"
  ],
  similar_cases: [
    { case_id: "CASE-2024-112", similarity: 0.87, summary: "去年 11 月涂布流量大幅变化出 90mg/m³" }
  ],
  confidence: 0.92
};