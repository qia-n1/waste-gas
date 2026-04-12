<script setup lang="ts">
import type { DashboardMetrics, StatusBanner } from "@/types/dashboard";

import HeaderBar from "@/components/layout/HeaderBar.vue";

defineProps<{
  metrics: DashboardMetrics;
  banner: StatusBanner;
  connected: boolean;
  userName: string;
}>();

defineEmits<{
  logout: [];
}>();
</script>

<template>
  <div class="dashboard-layout">
    <HeaderBar
      :metrics="metrics"
      :connected="connected"
      :user-name="userName"
      @logout="$emit('logout')"
    />

    <div class="dashboard-banner" :class="`dashboard-banner--${banner.severity}`">
      <span class="banner-dot"></span>
      <span>{{ banner.text }}</span>
    </div>

    <main class="dashboard-grid">
      <section class="dashboard-column dashboard-column--left">
        <slot name="left" />
      </section>
      <section class="dashboard-column dashboard-column--center">
        <slot name="center" />
      </section>
      <section class="dashboard-column dashboard-column--right">
        <slot name="right" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.dashboard-layout {
  width: 100%;
  height: 100%;
  padding: 18px;
  display: grid;
  grid-template-rows: 78px 54px minmax(0, 1fr);
  gap: 14px;
}

.dashboard-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid rgba(83, 209, 255, 0.2);
  background: rgba(12, 23, 46, 0.76);
  color: var(--text-primary);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
}

.dashboard-banner--warning {
  border-color: rgba(255, 179, 71, 0.4);
  color: #ffe6c4;
}

.dashboard-banner--critical {
  border-color: rgba(255, 91, 97, 0.45);
  color: #ffe0e2;
  animation: pulse 1.6s infinite;
}

.banner-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
  box-shadow: 0 0 18px rgba(83, 209, 255, 0.6);
}

.dashboard-banner--warning .banner-dot {
  background: linear-gradient(135deg, #ffd27d, var(--accent-amber));
  box-shadow: 0 0 18px rgba(255, 179, 71, 0.55);
}

.dashboard-banner--critical .banner-dot {
  background: linear-gradient(135deg, #ff969b, var(--accent-red));
  box-shadow: 0 0 18px rgba(255, 91, 97, 0.65);
}

.dashboard-grid {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(310px, 360px) minmax(0, 1fr) minmax(320px, 400px);
  gap: 14px;
}

.dashboard-column {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.dashboard-column--center {
  overflow: hidden;
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 rgba(255, 91, 97, 0.2);
  }
  50% {
    box-shadow: 0 0 28px rgba(255, 91, 97, 0.22);
  }
}

@media (max-width: 1600px) {
  .dashboard-grid {
    grid-template-columns: 320px minmax(0, 1fr) 340px;
  }
}

@media (max-width: 1280px) {
  .dashboard-layout {
    height: auto;
    min-height: 100%;
    grid-template-rows: 78px auto auto;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
