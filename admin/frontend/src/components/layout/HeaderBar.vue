<script setup lang="ts">
import dayjs from "dayjs";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { HomeFilled, Operation, UserFilled } from "@element-plus/icons-vue";

import type { DashboardMetrics } from "@/types/dashboard";

const props = defineProps<{
  metrics: DashboardMetrics;
  connected: boolean;
  userName: string;
}>();

defineEmits<{
  logout: [];
}>();

const route = useRoute();
const router = useRouter();

const now = ref(dayjs());
const menuVisible = ref(false);
let timer: number | null = null;

const navigationItems = [
  {
    name: "dashboard",
    label: "主页面",
    icon: HomeFilled,
    description: "返回 VOCs 综合看板主页",
  },
  {
    name: "users",
    label: "用户管理",
    icon: UserFilled,
    description: "查看和维护平台用户信息",
  },
] as const;

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

const openMenu = () => {
  menuVisible.value = true;
};

const navigateTo = async (target: (typeof navigationItems)[number]["name"]) => {
  menuVisible.value = false;
  if (route.name !== target) {
    await router.push({ name: target });
  }
};

const isActive = (target: (typeof navigationItems)[number]["name"]) => route.name === target;

const formattedTime = computed(() => now.value.format("YYYY-MM-DD HH:mm"));
</script>

<template>
  <header class="header-bar">
    <div class="header-shell">
      <div class="header-left">
        <button class="menu-trigger" type="button" @click="openMenu">
          <span class="menu-icon-shell">
            <el-icon class="menu-icon"><Operation /></el-icon>
          </span>
          <span class="menu-label">菜单</span>
        </button>
      </div>

      <div class="header-center">
        <h1 class="platform-title">智洁园区 - 废气综合管理平台</h1>
      </div>

      <div class="header-right">
        <div class="info-block">
          <span class="info-label">时间</span>
          <strong>{{ formattedTime }}</strong>
        </div>
        <div class="info-block">
          <span class="info-label">在线设备</span>
          <strong class="highlight-cyan">{{ metrics.onlineDevices }}/{{ metrics.totalDevices }}</strong>
        </div>
        <div class="info-block">
          <span class="info-label">告警次数</span>
          <strong class="highlight-alert">{{ metrics.todayAlerts }}次（今日）</strong>
        </div>
        <button class="logout-btn" type="button" title="退出登录" @click="$emit('logout')">
          <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
            <path
              d="M7 3H4a1 1 0 00-1 1v12a1 1 0 001 1h3M13 14l4-4m0 0l-4-4m4 4H7"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <el-drawer
      v-model="menuVisible"
      direction="ltr"
      size="286px"
      :with-header="false"
      modal-class="admin-menu-overlay"
      class="admin-menu-drawer"
    >
      <div class="drawer-panel">
        <div class="drawer-header">
          <span class="drawer-eyebrow">Navigation</span>
          <h2>系统菜单</h2>
          <p>在不打断当前看板布局的前提下快速切换页面。</p>
        </div>

        <nav class="drawer-nav">
          <button
            v-for="item in navigationItems"
            :key="item.name"
            class="nav-item"
            :class="{ 'nav-item--active': isActive(item.name) }"
            type="button"
            @click="navigateTo(item.name)"
          >
            <span class="nav-item__icon">
              <el-icon>
                <component :is="item.icon" />
              </el-icon>
            </span>
            <span class="nav-item__copy">
              <strong>{{ item.label }}</strong>
              <small>{{ item.description }}</small>
            </span>
          </button>
        </nav>
      </div>
    </el-drawer>
  </header>
</template>

<style scoped>
.header-bar {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: visible;
  z-index: 10;
}

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

.header-shell::before {
  content: "";
  position: absolute;
  top: 0;
  left: 8%;
  right: 8%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(160, 195, 255, 0.4), transparent);
}

.header-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  z-index: 1;
}

.menu-trigger {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: none;
  background: transparent;
  color: rgba(214, 230, 255, 0.92);
  cursor: pointer;
  transition: transform 0.18s ease;
}

.menu-trigger:hover {
  transform: translateY(-1px);
}

.menu-icon-shell {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgba(117, 167, 255, 0.38);
  background: rgba(11, 22, 49, 0.72);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.menu-trigger:hover .menu-icon-shell {
  border-color: rgba(117, 167, 255, 0.62);
  background: rgba(18, 34, 72, 0.88);
  box-shadow:
    0 0 18px rgba(83, 209, 255, 0.16),
    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.menu-icon {
  font-size: 17px;
}

.menu-label {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

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
  color: #ffb0bc !important;
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

:deep(.admin-menu-drawer) {
  background: rgba(9, 17, 34, 0.96);
}

:deep(.admin-menu-drawer .el-drawer__body) {
  padding: 0;
}

.drawer-panel {
  height: 100%;
  padding: 22px 18px;
  background:
    linear-gradient(180deg, rgba(15, 27, 56, 0.98), rgba(8, 15, 31, 0.98)),
    rgba(8, 15, 31, 0.98);
  color: var(--text-primary);
}

.drawer-header {
  padding: 8px 8px 18px;
  border-bottom: 1px solid rgba(109, 141, 222, 0.14);
}

.drawer-eyebrow {
  color: rgba(140, 165, 225, 0.72);
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.drawer-header h2 {
  margin: 10px 0 8px;
  font-size: 26px;
}

.drawer-header p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 13px;
}

.drawer-nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 18px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 12px;
  border: 1px solid rgba(98, 128, 194, 0.16);
  border-radius: 16px;
  background: rgba(13, 24, 49, 0.62);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease,
    transform 0.18s ease;
}

.nav-item:hover {
  background: rgba(21, 39, 78, 0.88);
  border-color: rgba(97, 160, 255, 0.34);
  transform: translateX(2px);
}

.nav-item--active {
  background: linear-gradient(135deg, rgba(48, 87, 174, 0.88), rgba(29, 57, 116, 0.9));
  border-color: rgba(110, 183, 255, 0.4);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.nav-item__icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(8, 18, 39, 0.56);
  color: #b8d7ff;
  font-size: 18px;
}

.nav-item__copy {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item__copy strong {
  font-size: 15px;
}

.nav-item__copy small {
  color: var(--text-secondary);
  font-size: 12px;
}

.nav-item--active .nav-item__copy small {
  color: rgba(225, 238, 255, 0.82);
}

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
