<script setup lang="ts">
import { ref, watch } from "vue";

import type { AlertItem } from "@/types/dashboard";

const props = defineProps<{
  alerts: AlertItem[];
  loading: boolean;
  search: string;
}>();

const emit = defineEmits<{
  search: [value: string];
  select: [alertId: string];
  acknowledge: [alertId: string];
}>();

const localSearch = ref(props.search);

watch(
  () => props.search,
  (value) => {
    localSearch.value = value;
  },
);

watch(localSearch, (value) => {
  emit("search", value);
});

const levelLabel = (level: string) => {
  if (level === "critical") {
    return "红色";
  }
  if (level === "warning") {
    return "橙色";
  }
  return "正常";
};
</script>

<template>
  <section class="panel-card alarm-card">
    <div class="panel-title">实时告警中心</div>
    <el-input v-model="localSearch" placeholder="搜索告警列表" clearable />

    <div class="alarm-table">
      <div class="alarm-head">
        <span>时间</span>
        <span>位置</span>
        <span>等级</span>
        <span>状态</span>
      </div>

      <div v-if="loading" class="empty-row">告警加载中...</div>
      <div v-else-if="alerts.length === 0" class="empty-row">当前没有活跃告警</div>

      <button
        v-for="alert in alerts"
        :key="alert.alert_id"
        class="alarm-row"
        type="button"
        @click="emit('select', alert.alert_id)"
      >
        <span>{{ alert.timestamp.slice(5, 16).replace("T", " ") }}</span>
        <span>{{ alert.location }}</span>
        <span class="badge" :class="`badge-${alert.level}`">{{ levelLabel(alert.level) }}</span>
        <span class="row-actions">
          <span>{{ alert.status }}</span>
          <el-button
            v-if="!alert.acknowledged"
            size="small"
            type="primary"
            @click.stop="emit('acknowledge', alert.alert_id)"
          >
            确认
          </el-button>
        </span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.alarm-card {
  min-height: 0;
  flex: 1 1 0;
  overflow: hidden;
}

.alarm-table {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
  min-height: 0;
  flex: 1 1 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
}

.alarm-head,
.alarm-row {
  display: grid;
  grid-template-columns: 1.4fr 0.9fr 0.7fr 1.2fr;
  gap: 8px;
  align-items: center;
}

.alarm-head {
  color: var(--text-secondary);
  font-size: 12px;
  padding: 0 8px;
}

.alarm-row {
  padding: 12px 10px;
  border: 1px solid rgba(95, 122, 191, 0.16);
  border-radius: 14px;
  background: rgba(7, 15, 31, 0.4);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.row-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.empty-row {
  padding: 18px 0;
  color: var(--text-secondary);
  text-align: center;
}
</style>
