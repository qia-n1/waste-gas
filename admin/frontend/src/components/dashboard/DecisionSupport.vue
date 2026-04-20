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

defineEmits<{
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
      <el-button type="success" @click="$emit('export')">生成指告</el-button>
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
