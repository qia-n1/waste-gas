<template>
  <view class="alerts-page">
    <view class="page-hero">
      <view class="hero-text">
        <text class="page-title">告警</text>
        <text class="page-subtitle">按状态与等级筛选</text>
      </view>
      <view class="hero-pill">{{ alerts.length }} 条</view>
    </view>

    <view class="filter-panel">
      <view class="filter-group">
        <text class="filter-caption">处理状态</text>
        <view class="filter-tabs">
          <view 
            v-for="status in statusFilters" 
            :key="status.value"
            class="filter-tab"
            :class="{ active: selectedStatus === status.value }"
            @click="changeStatusFilter(status.value)"
          >
            <text>{{ status.label }}</text>
          </view>
        </view>
      </view>
      <view class="filter-group no-gap">
        <text class="filter-caption">告警等级</text>
        <view class="filter-tabs">
          <view 
            v-for="level in levelFilters" 
            :key="level.value"
            class="filter-tab"
            :class="{ active: selectedLevel === level.value }"
            @click="changeLevelFilter(level.value)"
          >
            <text>{{ level.label }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="alerts-container">
      <view 
        v-for="alert in pagedAlerts" 
        :key="alert.id"
        class="alert-card"
        @click="navigateToDetail(alert.id)"
      >
        <view class="alert-top">
          <view class="alert-icon" :class="alert.level">
            <text v-if="alert.level === 'high'">🔥</text>
            <text v-else-if="alert.level === 'medium'">⚠️</text>
            <text v-else>ℹ️</text>
          </view>
          <view class="alert-content">
            <text class="alert-title">{{ alert.title }}</text>
            <text class="alert-time">{{ alert.time }}</text>
          </view>
          <StatusTag class="alert-status" :label="getStatusLabel(alert.status)" :type="statusTagType(alert.status)" />
        </view>
        <text class="alert-description">{{ alert.description }}</text>
        <view class="alert-footer">
          <text class="alert-level" :class="alert.level">{{ getLevelLabel(alert.level) }}</text>
          <view class="footer-actions">
            <text v-if="alert.status === 'unresolved'" class="btn-accept" @click.stop="acceptOrder(alert.id)">接单</text>
            <text class="alert-link">详情 →</text>
          </view>
        </view>
      </view>

      <view v-if="alerts.length === 0" class="empty-card">
        <text class="empty-icon">📭</text>
        <text class="empty-title">暂无告警信息</text>
        <text class="empty-desc">暂无数据，可切换筛选条件</text>
      </view>
      <view v-if="alerts.length" class="pager-row">
        <button class="pager-btn" :disabled="currentPage <= 1" @click="changePage(-1)">上一页</button>
        <text class="pager-text">{{ currentPage }}/{{ totalPages }}</text>
        <button class="pager-btn" :disabled="currentPage >= totalPages" @click="changePage(1)">下一页</button>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';
import StatusTag from '../../components/StatusTag.vue';

export default {
  components: {
    StatusTag,
  },
  data() {
    return {
      statusFilters: [
        { label: '全部', value: 'all' },
        { label: '待接单', value: 'unresolved' },
        { label: '处理中', value: 'accepted' },
        { label: '持续跟踪', value: 'tracking' },
        { label: '已结案', value: 'resolved' }
      ],
      levelFilters: [
        { label: '全部', value: 'all' },
        { label: '紧急', value: 'high' },
        { label: '警告', value: 'medium' },
        { label: '信息', value: 'low' }
      ],
      selectedStatus: 'all',
      selectedLevel: 'all',
      alerts: [],
      currentPage: 1,
      pageSize: 8,
    };
  },
  computed: {
    totalPages() {
      return Math.max(1, Math.ceil(this.alerts.length / this.pageSize));
    },
    pagedAlerts() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.alerts.slice(start, start + this.pageSize);
    },
  },
  watch: {
    selectedStatus() { this.loadAlerts(); },
    selectedLevel() { this.loadAlerts(); }
  },
  onShow() {
    this.loadAlerts();
  },
  methods: {
    changeStatusFilter(value) { this.selectedStatus = value; },
    changeLevelFilter(value) { this.selectedLevel = value; },
    getLevelLabel(level) {
      if (level === 'high') return '紧急';
      if (level === 'medium') return '警告';
      return '信息';
    },
    getStatusLabel(status) {
      if (status === 'unresolved') return '待接单';
      if (status === 'accepted') return '处理中';
      if (status === 'tracking') return '持续跟踪';
      if (status === 'resolved') return '已结案';
      return status || '--';
    },
    statusTagType(status) {
      if (status === 'unresolved') return 'error';
      if (status === 'accepted' || status === 'tracking') return 'warning';
      return 'normal';
    },
    async acceptOrder(id) {
      try {
        await request({ url: `/alerts/${id}/accept`, method: 'POST' });
        uni.showToast({ title: '已接单', icon: 'success' });
        await this.loadAlerts();
      } catch (e) {
        uni.showToast({ title: '接单失败', icon: 'none' });
      }
    },
    async loadAlerts() {
      try {
        const res = await request({ url: `/alerts?status=${this.selectedStatus}&level=${this.selectedLevel}` });
        if (res && res.code === 200 && Array.isArray(res.data)) {
          this.alerts = res.data;
          this.currentPage = 1;
        }
      } catch (error) {
        uni.showToast({ title: '告警加载失败', icon: 'none' });
      }
    },
    changePage(step) {
      const next = this.currentPage + step;
      this.currentPage = Math.min(this.totalPages, Math.max(1, next));
    },
    navigateToDetail(id) {
      uni.navigateTo({ url: `/pages/alerts/detail?id=${id}` });
    }
  }
};
</script>

<style>
.alerts-page {
  min-height: 100vh;
  padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%);
}
.page-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20rpx;
  padding: 30rpx;
  border-radius: 30rpx;
  background: linear-gradient(135deg, #ffffff 0%, #f4efff 100%);
  box-shadow: 0 16rpx 40rpx rgba(71, 45, 143, 0.08);
}
.hero-text { flex: 1; min-width: 0; }
.page-title {
  display: block;
  font-size: 42rpx;
  font-weight: 800;
  color: #2b2156;
  line-height: 1.2;
  word-break: break-word;
}
.page-subtitle {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.45;
  color: #8378a1;
  word-break: break-word;
}
.hero-pill {
  flex-shrink: 0;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #efe9ff;
  color: #7b61ff;
  font-size: 21rpx;
  font-weight: 700;
}
.filter-panel {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 16rpx 36rpx rgba(49, 30, 109, 0.06);
}
.filter-group { margin-top: 20rpx; }
.filter-group:first-child { margin-top: 0; }
.filter-group.no-gap { margin-top: 18rpx; }
.filter-caption {
  display: block;
  margin-bottom: 14rpx;
  font-size: 20rpx;
  color: #8d81a9;
}
.filter-tabs {
  display: flex;
  gap: 12rpx;
  overflow-x: auto;
}
.filter-tab {
  padding: 14rpx 22rpx;
  border-radius: 999rpx;
  background: #f6f2ff;
  color: #726889;
  font-size: 21rpx;
  white-space: nowrap;
}
.filter-tab.active {
  background: linear-gradient(135deg, #7b61ff 0%, #957dff 100%);
  color: #fff;
  box-shadow: 0 12rpx 26rpx rgba(123, 97, 255, 0.18);
}
.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 22rpx;
}
.alert-card {
  padding: 24rpx;
  border-radius: 26rpx;
  background: #ffffff;
  box-shadow: 0 16rpx 36rpx rgba(49, 30, 109, 0.06);
  border: 2rpx solid rgba(123, 97, 255, 0.06);
}
.alert-card:active {
  transform: scale(0.995);
  border-color: rgba(123, 97, 255, 0.2);
}
.alert-top {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.alert-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
}
.alert-icon.high { background: #ffe9ee; }
.alert-icon.medium { background: #fff5df; }
.alert-icon.low { background: #e9f4ff; }
.alert-content { flex: 1; min-width: 0; }
.alert-title {
  display: block;
  font-size: 23rpx;
  font-weight: 700;
  color: #2d2454;
  line-height: 1.35;
  word-break: break-word;
}
.alert-time {
  display: block;
  margin-top: 8rpx;
  font-size: 18rpx;
  color: #9a8fb2;
}
.alert-status {
  flex-shrink: 0;
  padding: 0;
  max-width: 38%;
  text-align: center;
  line-height: 1.2;
  word-break: break-word;
}
.footer-actions { display:flex; align-items:center; gap:16rpx; }
.btn-accept {
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:56rpx;
  padding:12rpx 24rpx;
  border-radius:999rpx;
  background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%);
  color:#fff;
  font-size:22rpx;
  font-weight:700;
  line-height:1.2;
}
.alert-description {
  display: block;
  margin-top: 18rpx;
  font-size: 21rpx;
  line-height: 1.55;
  color: #6f6686;
  word-break: break-word;
}
.alert-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 18rpx;
}
.alert-level {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  font-weight: 700;
}
.alert-level.high { background: #ffe9ee; color: #dd5175; }
.alert-level.medium { background: #fff5df; color: #d48618; }
.alert-level.low { background: #e9f4ff; color: #3c86c5; }
.alert-link {
  font-size: 19rpx;
  color: #7b61ff;
  font-weight: 700;
}
.footer-actions { min-height: 56rpx; }
.empty-card {
  padding: 56rpx 30rpx;
  border-radius: 28rpx;
  background: #ffffff;
  text-align: center;
  box-shadow: 0 16rpx 36rpx rgba(49, 30, 109, 0.06);
}
.empty-icon { font-size: 72rpx; }
.empty-title {
  display: block;
  margin-top: 20rpx;
  font-size: 27rpx;
  font-weight: 700;
  color: #2d2454;
}
.empty-desc {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  line-height: 1.6;
  color: #8d82aa;
}
.pager-row { margin-top: 6rpx; display:flex; align-items:center; justify-content:flex-end; gap:12rpx; }
.pager-btn { min-width:112rpx; height:62rpx; padding:0 16rpx; border-radius:16rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.pager-btn::after { border:none; }
.pager-btn[disabled] { opacity:.45; }
.pager-text { font-size:20rpx; color:#8f84ab; min-width:72rpx; text-align:center; }
</style>
