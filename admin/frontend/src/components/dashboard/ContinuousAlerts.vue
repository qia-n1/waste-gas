<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import type { ContinuousAlert } from "@/types/dashboard";

const props = defineProps<{
  items: ContinuousAlert[];
}>();

const now = ref(Date.now());
const startedAt = Date.now();
let timer: number | null = null;

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = Date.now();
  }, 1000);
});

onBeforeUnmount(() => {
  if (timer !== null) {
    window.clearInterval(timer);
  }
});

const sortedItems = computed(() =>
  [...props.items].sort((left, right) => right.elapsed_seconds - left.elapsed_seconds),
);

const formatDuration = (seconds: number) => {
  const total = Math.max(seconds, 0);
  const hours = `${Math.floor(total / 3600)}`.padStart(2, "0");
  const minutes = `${Math.floor((total % 3600) / 60)}`.padStart(2, "0");
  const remainingSeconds = `${total % 60}`.padStart(2, "0");
  return `${hours}:${minutes}:${remainingSeconds}`;
};

const levelDot = (level: string) => (level === "critical" ? "dot-critical" : "dot-warning");
</script>

<template>
  <section class="panel-card">
    <div class="panel-title">异常持续关注区</div>
    <div v-if="sortedItems.length === 0" class="empty-text">当前没有持续异常事件</div>
    <div v-else class="alert-list">
      <div v-for="item in sortedItems" :key="item.id" class="alert-item">
        <div class="alert-copy">
          <span class="dot" :class="levelDot(item.level)"></span>
          <div>
            <strong>{{ item.location }}</strong>
            <p>{{ item.message }}</p>
          </div>
        </div>
        <span class="duration">
          {{ formatDuration(item.elapsed_seconds + Math.floor((now - startedAt) / 1000)) }}
        </span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel-card {
  min-height: 0;
  flex: 0 0 auto;
  max-height: 220px;
  overflow: hidden;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  flex: 1 1 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

.alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(7, 15, 31, 0.42);
  border: 1px solid rgba(95, 122, 191, 0.16);
}

.alert-copy {
  display: flex;
  align-items: center;
  gap: 12px;
}

.alert-copy p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.duration {
  color: #ffd3b1;
  font-size: 20px;
  font-weight: 700;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-critical {
  background: var(--accent-red);
  box-shadow: 0 0 14px rgba(255, 91, 97, 0.6);
}

.dot-warning {
  background: var(--accent-amber);
  box-shadow: 0 0 14px rgba(255, 179, 71, 0.55);
}

.empty-text {
  color: var(--text-secondary);
}
</style>
