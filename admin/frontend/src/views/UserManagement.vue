<script setup lang="ts">
import { reactive } from "vue";
import { useRouter } from "vue-router";

import HeaderBar from "@/components/layout/HeaderBar.vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const router = useRouter();

const metrics = reactive({
  currentVocs: 0,
  peakForecast: 0,
  alertLevel: "normal",
  onlineDevices: 0,
  totalDevices: 0,
  todayAlerts: 0,
  systemPhase: "用户管理",
  uptime: "--",
  confidence: 0,
  dataCompleteness: 0,
  latencyMs: 0,
  predictionType: "manual",
});

const handleLogout = async () => {
  authStore.logout();
  await router.push("/login");
};
</script>

<template>
  <div class="user-page">
    <HeaderBar
      :metrics="metrics"
      :connected="true"
      :user-name="authStore.user?.name ?? '管理员'"
      @logout="handleLogout"
    />

    <main class="user-page__content">
      <section class="panel-card user-panel">
        <div class="panel-title">用户管理</div>
        <div class="user-panel__hero">
          <h2>用户管理页面占位</h2>
          <p>当前版本已接入菜单导航。这里预留给用户列表、角色配置、搜索筛选和账号状态管理。</p>
        </div>

        <div class="placeholder-grid">
          <div class="placeholder-card">
            <span>模块 A</span>
            <strong>用户列表</strong>
            <p>支持分页、检索、状态筛选。</p>
          </div>
          <div class="placeholder-card">
            <span>模块 B</span>
            <strong>角色权限</strong>
            <p>预留角色和权限映射区域。</p>
          </div>
          <div class="placeholder-card">
            <span>模块 C</span>
            <strong>账号操作</strong>
            <p>预留新增、禁用、重置密码等操作。</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.user-page {
  width: 100%;
  height: 100%;
  padding: 18px;
  display: grid;
  grid-template-rows: 88px minmax(0, 1fr);
  gap: 14px;
}

.user-page__content {
  min-height: 0;
}

.user-panel {
  padding: 22px;
}

.user-panel__hero {
  margin-bottom: 22px;
}

.user-panel__hero h2 {
  margin: 0 0 10px;
  font-size: 32px;
}

.user-panel__hero p {
  max-width: 720px;
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.placeholder-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(93, 129, 209, 0.16);
  background: rgba(8, 16, 33, 0.54);
}

.placeholder-card span {
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.placeholder-card strong {
  display: block;
  margin: 8px 0 10px;
  font-size: 22px;
}

.placeholder-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

@media (max-width: 1200px) {
  .placeholder-grid {
    grid-template-columns: 1fr;
  }
}
</style>
