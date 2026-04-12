<script setup lang="ts">
import dayjs from "dayjs";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import type { DashboardMetrics } from "@/types/dashboard";

const props = defineProps<{
  metrics: DashboardMetrics;
  connected: boolean;
  userName: string;
}>();

defineEmits<{
  logout: [];
}>();

const now = ref(dayjs());
let timer: number | null = null;

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = dayjs();
  }, 1000);
});

onBeforeUnmount(() => {
  if (timer !== null) {
    window.clearInterval(timer);
  }
});

const connectionText = computed(() => (props.connected ? "实时连接" : "离线回放"));
</script>

<template>
  <header class="header-bar panel-card">
    <div class="header-left">
      <button class="back-button" type="button">回园</button>
      <div class="title-block">
        <p class="sub-title">Smart VOCs Control Center</p>
        <h1>智洁园区 - 废气综合管理平台</h1>
      </div>
    </div>

    <div class="header-center">
      <div class="status-chip" :class="{ 'status-chip--online': connected }">
        {{ connectionText }}
      </div>
      <div class="clock">{{ now.format("YYYY-MM-DD HH:mm:ss") }}</div>
    </div>

    <div class="header-right">
      <div class="metric-card">
        <span class="metric-label">在线设备</span>
        <strong>{{ metrics.onlineDevices }}/{{ metrics.totalDevices }}</strong>
      </div>
      <div class="metric-card">
        <span class="metric-label">告警次数</span>
        <strong>{{ metrics.todayAlerts }} 次</strong>
      </div>
      <div class="user-chip">
        <span class="avatar">{{ userName.slice(0, 1) }}</span>
        <button class="logout" type="button" @click="$emit('logout')">退出</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header-bar {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  padding: 0 22px;
}

.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
}

.header-left {
  gap: 18px;
}

.back-button,
.logout {
  height: 38px;
  padding: 0 16px;
  border: 1px solid rgba(83, 209, 255, 0.3);
  border-radius: 999px;
  background: rgba(15, 28, 55, 0.82);
  color: var(--text-primary);
  cursor: pointer;
}

.title-block h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.sub-title {
  margin: 0 0 6px;
  color: var(--text-secondary);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.header-center {
  justify-content: center;
  gap: 14px;
}

.status-chip {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 179, 71, 0.14);
  border: 1px solid rgba(255, 179, 71, 0.24);
  color: #ffe4b8;
  font-size: 12px;
}

.status-chip--online {
  background: rgba(64, 223, 154, 0.16);
  border-color: rgba(64, 223, 154, 0.32);
  color: #dfffee;
}

.clock {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.header-right {
  gap: 12px;
}

.metric-card,
.user-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 0 16px;
  border-radius: 16px;
  background: rgba(11, 21, 41, 0.72);
  border: 1px solid rgba(95, 122, 191, 0.18);
}

.metric-card {
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}

.metric-label {
  color: var(--text-secondary);
  font-size: 12px;
}

.metric-card strong {
  font-size: 18px;
}

.avatar {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
  color: #03111f;
  font-weight: 800;
}

@media (max-width: 1280px) {
  .header-bar {
    grid-template-columns: 1fr;
    gap: 12px;
    height: auto;
    padding: 16px 18px;
  }

  .header-center {
    justify-content: flex-start;
  }

  .header-right {
    justify-content: space-between;
    flex-wrap: wrap;
  }
}
</style>
