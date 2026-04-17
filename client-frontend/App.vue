<template>
  <div class="app-shell" :class="{ 'with-tabbar': showTabbar }">
    <router-view />

    <nav v-if="showTabbar" class="app-tabbar">
      <button
        v-for="item in tabItems"
        :key="item.path"
        type="button"
        class="tab-item"
        :class="{ active: isActive(item.path) }"
        @click="go(item.path)"
      >
        <span class="tab-text">{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

export default {
  name: 'App',
  setup() {
    const route = useRoute();
    const router = useRouter();

    const tabItems = [
      { path: '/pages/index/index', label: '首页' },
      { path: '/pages/monitor/realtime', label: '监控' },
      { path: '/pages/alerts/list', label: '告警' },
      { path: '/pages/profile/index', label: '我的' },
    ];

    const hidePaths = new Set(['/auth/login']);

    const showTabbar = computed(() => {
      if (hidePaths.has(route.path)) {
        return false;
      }
      return Boolean(localStorage.getItem('authToken'));
    });

    const go = (path) => {
      if (route.path === path) {
        return;
      }
      router.replace(path);
    };

    const isActive = (path) => route.path === path;

    return {
      tabItems,
      showTabbar,
      go,
      isActive,
    };
  }
};
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
}

.app-shell.with-tabbar {
  padding-bottom: calc(64px + env(safe-area-inset-bottom));
}

.app-tabbar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  height: calc(64px + env(safe-area-inset-bottom));
  padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  background: rgba(255, 255, 255, 0.95);
  border-top: 1px solid #ececf3;
  backdrop-filter: blur(10px);
}

.tab-item {
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #8a8fa5;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-item.active {
  color: #4f46e5;
  background: #eef2ff;
}

.tab-text {
  line-height: 1;
}
</style>