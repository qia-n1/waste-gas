<script setup lang="ts">
import type { DashboardMetrics } from "@/types/dashboard";

import HeaderBar from "@/components/layout/HeaderBar.vue";

defineProps<{
  metrics: DashboardMetrics;
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
  grid-template-rows: 88px minmax(0, 1fr);
  gap: 14px;
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

@media (max-width: 1600px) {
  .dashboard-grid {
    grid-template-columns: 320px minmax(0, 1fr) 340px;
  }
}

@media (max-width: 1280px) {
  .dashboard-layout {
    height: auto;
    min-height: 100%;
    grid-template-rows: 88px auto;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
