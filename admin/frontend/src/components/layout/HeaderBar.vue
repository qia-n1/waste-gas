<script setup lang="ts">
import dayjs from "dayjs";
import { onBeforeUnmount, onMounted, ref } from "vue";

import type { DashboardMetrics } from "@/types/dashboard";

defineProps<{
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
</script>

<template>
  <header class="header-bar">
    <!-- Main content band -->
    <div class="header-shell">
      <!-- Left: Logo -->
      <div class="header-left">
        <div class="logo-wrapper">
          <svg class="logo-icon" viewBox="0 0 40 40" fill="none">
            <circle cx="20" cy="20" r="18" stroke="url(#logo-grad)" stroke-width="2" fill="rgba(16,28,66,0.6)" />
            <path d="M14 26 C14 18, 20 14, 20 14 C20 14, 26 18, 26 26" stroke="url(#logo-grad)" stroke-width="2.5" stroke-linecap="round" fill="none" />
            <path d="M11 28 C11 18, 20 11, 20 11 C20 11, 29 18, 29 28" stroke="url(#logo-grad)" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.5" />
            <defs>
              <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40">
                <stop offset="0%" stop-color="#71c6ff" />
                <stop offset="100%" stop-color="#5084ff" />
              </linearGradient>
            </defs>
          </svg>
          <span class="logo-label">回队</span>
        </div>
      </div>

      <!-- Center: Title (sits in the V center) -->
      <div class="header-center">
        <h1 class="platform-title">智洁园区 - 废气综合管理平台</h1>
      </div>

      <!-- Right: Metrics -->
      <div class="header-right">
        <div class="info-block">
          <span class="info-label">时间</span>
          <strong>{{ now.format("YYYY-MM-DD HH:mm") }}</strong>
        </div>
        <div class="info-block">
          <span class="info-label">在线设备</span>
          <strong class="highlight-cyan">{{ metrics.onlineDevices }}/{{ metrics.totalDevices }}</strong>
        </div>
        <div class="info-block">
          <span class="info-label">告警次数...</span>
          <strong class="highlight-alert">{{ metrics.todayAlerts }}次（今日）</strong>
        </div>
        <button
          class="logout-btn"
          type="button"
          title="退出登录"
          @click="$emit('logout')"
        >
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <path d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3M13 14l4-4m0 0l-4-4m4 4H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

  </header>
</template>

<style scoped>
/*
 * V-Chevron Header
 *
 * .header-bar                    full wrapper, overflow visible
 *   .header-shell                top rectangular content band
 *   svg.header-chevron           V-shaped SVG below (fill + edge lines + tip glow)
 */

/* ---- Wrapper ---- */
.header-bar {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: visible;
  z-index: 10;
}

/* ---- Top band ---- */
.header-shell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 32px;
  border: 1px solid rgba(89, 122, 233, 0.25);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(22, 40, 92, 0.95), rgba(16, 30, 70, 0.93));
  box-shadow:
    inset 0 1px 0 rgba(185, 215, 255, 0.14),
    0 4px 24px rgba(4, 12, 34, 0.3);
  z-index: 2;
}

/* Top highlight line */
.header-shell::before {
  content: "";
  position: absolute;
  top: 0;
  left: 8%;
  right: 8%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(160, 195, 255, 0.4), transparent);
}

/* ---- Logo (left) ---- */
.header-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  z-index: 1;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  filter: drop-shadow(0 0 10px rgba(83, 209, 255, 0.3));
}

.logo-label {
  font-size: 16px;
  font-weight: 700;
  color: rgba(200, 220, 255, 0.9);
  letter-spacing: 0.06em;
}

/* ---- Title (absolute center) ---- */
.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 1;
}

.platform-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #f2f8ff;
  text-shadow: 0 0 24px rgba(160, 200, 255, 0.15);
  white-space: nowrap;
}

/* ---- Metrics (right) ---- */
.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 1;
}

.info-block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  min-width: 110px;
  padding: 6px 16px;
  border-left: 1px solid rgba(128, 156, 226, 0.18);
}

.info-label {
  color: rgba(180, 200, 235, 0.7);
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
  letter-spacing: 0.03em;
}

.info-block strong {
  margin-top: 6px;
  color: #e8f0ff;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.highlight-cyan {
  color: var(--accent-cyan, #53d1ff) !important;
}

.highlight-alert {
  color: var(--accent-cyan, #53d1ff) !important;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  margin-left: 8px;
  border: 1px solid rgba(112, 143, 222, 0.2);
  border-radius: 10px;
  background: rgba(10, 19, 44, 0.4);
  color: rgba(200, 216, 245, 0.7);
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(30, 50, 100, 0.5);
  color: #fff;
  border-color: rgba(112, 143, 222, 0.4);
}

/* ---- Responsive ---- */
@media (max-width: 1440px) {
  .platform-title {
    font-size: 22px;
  }

  .info-block {
    min-width: 95px;
    padding: 6px 12px;
  }
}

@media (max-width: 1280px) {
  .header-shell {
    flex-wrap: wrap;
    height: auto;
    padding: 14px 18px;
    gap: 12px;
    border-radius: 14px;
    border-bottom: 1px solid rgba(89, 122, 233, 0.25);
  }

  .header-center {
    position: static;
    transform: none;
    width: 100%;
  }

  .header-chevron {
    display: none;
  }

  .header-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .info-block {
    border-left: none;
    padding-left: 0;
  }
}
</style>
