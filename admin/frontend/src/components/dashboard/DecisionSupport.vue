<script setup lang="ts">
import { computed, ref } from "vue";
import dayjs from "dayjs";

import type {
  DashboardMetrics,
  KeyParameter,
  RagCard,
  TrendPoint,
} from "@/types/dashboard";

const props = defineProps<{
  metrics: DashboardMetrics;
  keyParameters: KeyParameter[];
  summary: string;
  suggestions: string[];
  forecastSeries: TrendPoint[];
  ragCard?: RagCard | null;
}>();

const emit = defineEmits<{
  acknowledge: [];
  export: [];
}>();

const drawerVisible = ref(false);

const forecastPreview = computed(() =>
  props.forecastSeries.slice(0, 6).map((item) => ({
    ...item,
    label: dayjs(item.timestamp).format("MM/DD HH:mm"),
  })),
);

/** HTML escape —— 避免建议文字里的 < > & 把报告结构破坏。 */
const esc = (text: string): string =>
  String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const alertLevelText = (level: string): string => {
  if (level === "critical") return "红色预警";
  if (level === "warning") return "橙色预警";
  return "稳定";
};

/**
 * 生成一份自包含 HTML 报告并触发浏览器下载。
 * 设计要点：
 *   - 所有样式 inline（<style> 块），下载后双击可直接用浏览器打开；
 *   - 内容全部来自当前 props 的快照，不依赖后端接口（即使断网也能出报告）；
 *   - 文件名带时间戳，方便多次生成不互相覆盖。
 */
const handleGenerateReport = () => {
  const now = dayjs();
  const generatedAt = now.format("YYYY-MM-DD HH:mm:ss");
  const filename = `vocs-report-${now.format("YYYYMMDD-HHmm")}.html`;

  const m = props.metrics;
  const paramRows = props.keyParameters
    .map(
      (p) =>
        `<tr><td>${esc(p.label)}</td><td class="num">${p.value.toFixed(2)} ${esc(p.unit)}</td></tr>`,
    )
    .join("");

  const suggestionItems = props.suggestions.length
    ? props.suggestions.map((s) => `<li>${esc(s)}</li>`).join("")
    : "<li>暂无建议</li>";

  const forecastRows = forecastPreview.value
    .map(
      (f) =>
        `<tr><td>${esc(f.label)}</td><td class="num">${f.value.toFixed(2)} mg/m³</td></tr>`,
    )
    .join("");

  const rag = props.ragCard;
  const ragBlock = rag
    ? `
    <section>
      <h2>RAG 辅助诊断</h2>
      <p><strong>${esc(rag.title || "辅助诊断")}</strong>${rag.standard ? ` · 参考：${esc(rag.standard)}` : ""}</p>
      ${rag.suggestionShort ? `<p class="tip">💡 ${esc(rag.suggestionShort)}</p>` : ""}
      ${
        rag.sopSteps && rag.sopSteps.length
          ? `<p><strong>标准作业步骤（SOP）：</strong></p><ol>${rag.sopSteps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>`
          : ""
      }
      ${rag.safetyRedline ? `<p class="redline">⚠ 安全红线：${esc(rag.safetyRedline)}</p>` : ""}
    </section>`
    : "";

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>VOCs 实时监测报告 · ${esc(generatedAt)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; margin: 0; padding: 32px 48px; color: #1a2233; background: #f5f7fb; }
  .wrap { max-width: 880px; margin: 0 auto; background: #fff; padding: 36px 44px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
  h1 { margin: 0 0 4px; font-size: 24px; color: #0a2744; }
  .meta { color: #6b7a90; font-size: 13px; margin-bottom: 24px; }
  section { margin-top: 28px; }
  h2 { font-size: 16px; color: #0a2744; border-left: 4px solid #2387d9; padding-left: 10px; margin: 0 0 12px; }
  .hero { display: flex; align-items: baseline; gap: 16px; padding: 18px 22px; border-radius: 10px; background: linear-gradient(135deg, #eef4ff 0%, #f8fbff 100%); border: 1px solid #dfe7f4; }
  .hero .big { font-size: 40px; font-weight: 700; color: #0a2744; }
  .hero .unit { color: #6b7a90; }
  .badge { margin-left: auto; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; }
  .badge-normal { background: #e1f3ea; color: #1f8a5a; }
  .badge-warning { background: #fff1d6; color: #b37200; }
  .badge-critical { background: #fde3e3; color: #c53131; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e6ecf5; }
  th { color: #6b7a90; font-weight: 500; background: #f5f7fb; }
  td.num { font-variant-numeric: tabular-nums; text-align: right; color: #0a2744; font-weight: 600; }
  ul, ol { margin: 8px 0; padding-left: 22px; line-height: 1.8; }
  p { line-height: 1.7; margin: 8px 0; }
  .tip { padding: 10px 14px; background: #fff8e1; border-left: 4px solid #ffaa00; border-radius: 6px; }
  .redline { padding: 10px 14px; background: #fde3e3; border-left: 4px solid #c53131; border-radius: 6px; color: #8a1f1f; }
  .footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e6ecf5; color: #9aa7bd; font-size: 12px; text-align: center; }
</style>
</head>
<body>
<div class="wrap">
  <h1>废气综合管理平台 · 实时监测报告</h1>
  <div class="meta">生成时间：${esc(generatedAt)} · 系统阶段：${esc(m.systemPhase)}</div>

  <section>
    <h2>总体态势</h2>
    <div class="hero">
      <div>
        <div style="color:#6b7a90;font-size:13px;">当前 VOCs 浓度</div>
        <span class="big">${m.currentVocs.toFixed(1)}</span>
        <span class="unit">mg/m³</span>
      </div>
      <span class="badge badge-${esc(m.alertLevel)}">${esc(alertLevelText(m.alertLevel))}</span>
    </div>
    <table style="margin-top:14px;">
      <tr><th>6 小时峰值预测</th><td class="num">${m.peakForecast.toFixed(2)} mg/m³</td></tr>
      <tr><th>在线设备</th><td class="num">${m.onlineDevices} / ${m.totalDevices}</td></tr>
      <tr><th>今日告警</th><td class="num">${m.todayAlerts}</td></tr>
      <tr><th>模型置信度</th><td class="num">${(m.confidence * 100).toFixed(1)}%</td></tr>
      <tr><th>数据完整率</th><td class="num">${(m.dataCompleteness * 100).toFixed(1)}%</td></tr>
      <tr><th>推理延迟</th><td class="num">${m.latencyMs} ms</td></tr>
    </table>
  </section>

  <section>
    <h2>关键工艺参数</h2>
    <table><thead><tr><th>参数</th><th style="text-align:right;">数值</th></tr></thead><tbody>${paramRows || "<tr><td colspan='2' style='color:#9aa7bd;'>暂无数据</td></tr>"}</tbody></table>
  </section>

  <section>
    <h2>AI 智能诊断</h2>
    <p>${esc(props.summary || "暂无诊断信息")}</p>
    <p><strong>处置建议：</strong></p>
    <ul>${suggestionItems}</ul>
  </section>
${ragBlock}
  <section>
    <h2>未来 6 小时预测片段</h2>
    <table><thead><tr><th>时间</th><th style="text-align:right;">预测浓度</th></tr></thead><tbody>${forecastRows || "<tr><td colspan='2' style='color:#9aa7bd;'>暂无预测数据</td></tr>"}</tbody></table>
  </section>

  <div class="footer">智洁园区 · 废气综合管理平台 — 本报告由系统自动生成</div>
</div>
</body>
</html>`;

  // Blob + 临时 <a download> 触发下载；URL.revokeObjectURL 释放内存。
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  // 通知父组件：用于弹 toast "报告已导出" 等反馈。
  emit("export");
};
</script>

<template>
  <section class="panel-card decision-card">
    <div class="panel-title">决策支持与详情</div>

    <div class="decision-body">
      <div class="hero-metric">
        <div>
          <span>VOCs 实时详情</span>
          <strong>{{ metrics.currentVocs.toFixed(1) }}</strong>
          <small>mg/m³</small>
        </div>
        <span class="badge" :class="`badge-${metrics.alertLevel}`">
          {{ metrics.alertLevel === "critical" ? "红色预警" : metrics.alertLevel === "warning" ? "橙色预警" : "稳定" }}
        </span>
      </div>

      <div class="parameter-list">
        <div v-for="item in keyParameters" :key="item.field" class="parameter-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value.toFixed(1) }} {{ item.unit }}</strong>
        </div>
      </div>

      <div class="summary-box">
        <h3>AI 智能建议</h3>
        <p>{{ summary }}</p>
        <ul>
          <li v-for="suggestion in suggestions" :key="suggestion">{{ suggestion }}</li>
        </ul>
      </div>

      <div v-if="ragCard" class="rag-card">
        <div class="rag-head">
          <el-tag
            :type="ragCard.level === 'danger' ? 'danger' : 'warning'"
            effect="dark"
            size="small"
          >
            {{ ragCard.title || "RAG 辅助诊断" }}
          </el-tag>
          <span v-if="ragCard.standard" class="standard">参考：{{ ragCard.standard }}</span>
        </div>

        <p v-if="ragCard.suggestionShort" class="rag-short">
          💡 {{ ragCard.suggestionShort }}
        </p>

        <div v-if="ragCard.sopSteps && ragCard.sopSteps.length" class="sop-list">
          <div class="sop-head">标准作业步骤 (SOP)</div>
          <ol>
            <li v-for="(step, idx) in ragCard.sopSteps" :key="idx">{{ step }}</li>
          </ol>
        </div>

        <div v-if="ragCard.safetyRedline" class="redline">
          ⚠️ 安全红线：{{ ragCard.safetyRedline }}
        </div>
      </div>
    </div>

    <div class="actions">
      <el-button @click="drawerVisible = true">影响预测</el-button>
      <el-button type="primary" @click="$emit('acknowledge')">一键处置</el-button>
      <el-button type="success" @click="handleGenerateReport">生成报告</el-button>
    </div>

    <el-drawer v-model="drawerVisible" title="未来 6 小时预测片段" size="420px">
      <div class="drawer-list">
        <div v-for="item in forecastPreview" :key="item.timestamp" class="drawer-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value.toFixed(1) }} mg/m³</strong>
        </div>
      </div>
    </el-drawer>
  </section>
</template>

<style scoped>
.decision-card {
  min-height: 0;
  flex: 1 1 0;
  overflow: hidden;
}

.decision-body {
  min-height: 0;
  flex: 1 1 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

.hero-metric {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.hero-metric span {
  color: var(--text-secondary);
  font-size: 13px;
}

.hero-metric strong {
  display: block;
  margin: 6px 0;
  font-size: 44px;
  line-height: 1;
}

.hero-metric small {
  color: var(--text-secondary);
}

.parameter-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.parameter-item {
  padding: 12px;
  border-radius: 14px;
  background: rgba(7, 15, 31, 0.42);
  border: 1px solid rgba(95, 122, 191, 0.16);
}

.parameter-item span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.parameter-item strong {
  display: block;
  margin-top: 6px;
  font-size: 15px;
}

.summary-box {
  padding: 14px;
  border-radius: 16px;
  background: rgba(8, 16, 33, 0.72);
  border: 1px solid rgba(95, 122, 191, 0.16);
}

.summary-box h3 {
  margin: 0 0 10px;
}

.summary-box p {
  margin: 0 0 10px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.summary-box ul {
  margin: 0;
  padding-left: 18px;
  color: var(--text-primary);
}

.summary-box li + li {
  margin-top: 6px;
}

.rag-card {
  margin-top: 14px;
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(
    135deg,
    rgba(255, 170, 0, 0.08) 0%,
    rgba(0, 212, 255, 0.06) 100%
  );
  border: 1px solid rgba(255, 170, 0, 0.25);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.25);
}

.rag-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.rag-head .standard {
  color: var(--text-secondary);
  font-size: 12px;
}

.rag-short {
  margin: 0 0 10px;
  color: var(--text-primary);
  font-weight: 600;
  line-height: 1.6;
}

.sop-list {
  margin-top: 8px;
}

.sop-head {
  margin-bottom: 6px;
  color: var(--accent-cyan);
  font-size: 13px;
  font-weight: 600;
}

.sop-list ol {
  margin: 0;
  padding-left: 20px;
  color: var(--text-primary);
}

.sop-list li + li {
  margin-top: 6px;
}

.redline {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 68, 68, 0.12);
  border: 1px solid rgba(255, 68, 68, 0.35);
  color: #ff9a9a;
  font-size: 13px;
  line-height: 1.6;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.drawer-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.drawer-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  border-radius: 12px;
  background: rgba(8, 16, 33, 0.72);
}
</style>
