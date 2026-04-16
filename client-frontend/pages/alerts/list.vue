<template>
  <view class="alerts-page">
    <view class="page-hero">
      <view>
        <text class="hero-kicker">ALERT CENTER</text>
        <text class="page-title">告警中心</text>
        <text class="page-subtitle">按状态与等级快速筛选，优先处理关键异常。</text>
      </view>
      <view class="hero-pill">{{ filteredAlerts.length }} 条</view>
    </view>

    <view class="filter-panel">
      <text class="panel-title">筛选条件</text>
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
        v-for="alert in filteredAlerts" 
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
          <view class="alert-status" :class="alert.status">
            <text v-if="alert.status === 'unresolved'">未处理</text>
            <text v-else>已处理</text>
          </view>
        </view>
        <text class="alert-description">{{ alert.description }}</text>
        <view class="alert-footer">
          <text class="alert-level" :class="alert.level">{{ getLevelLabel(alert.level) }}</text>
          <text class="alert-link">查看详情 →</text>
        </view>
      </view>

      <view v-if="filteredAlerts.length === 0" class="empty-card">
        <text class="empty-icon">📭</text>
        <text class="empty-title">暂无告警信息</text>
        <text class="empty-desc">当前筛选条件下没有匹配结果，可以尝试切换筛选标签。</text>
      </view>
    </view>

    <view v-if="filteredAlerts.length > 0" class="load-more">
      <text class="load-more-text">上拉加载更多</text>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return {
      statusFilters: [
        { label: '全部', value: 'all' },
        { label: '未处理', value: 'unresolved' },
        { label: '已处理', value: 'resolved' }
      ],
      levelFilters: [
        { label: '全部', value: 'all' },
        { label: '紧急', value: 'high' },
        { label: '警告', value: 'medium' },
        { label: '信息', value: 'low' }
      ],
      selectedStatus: 'all',
      selectedLevel: 'all',
      alerts: []
    };
  },
  watch: {
    selectedStatus() { this.loadAlerts(); },
    selectedLevel() { this.loadAlerts(); }
  },
  onShow() {
    this.loadAlerts();
  },
  computed: {
    filteredAlerts() {
      let filtered = this.alerts;
      if (this.selectedStatus !== 'all') filtered = filtered.filter(alert => alert.status === this.selectedStatus);
      if (this.selectedLevel !== 'all') filtered = filtered.filter(alert => alert.level === this.selectedLevel);
      return filtered;
    }
  },
  methods: {
    changeStatusFilter(value) { this.selectedStatus = value; },
    changeLevelFilter(value) { this.selectedLevel = value; },
    getLevelLabel(level) {
      if (level === 'high') return '紧急';
      if (level === 'medium') return '警告';
      return '信息';
    },
    async loadAlerts() {
      try {
        const res = await request({ url: `/alerts?status=${this.selectedStatus}&level=${this.selectedLevel}` });
        if (res && res.code === 200 && Array.isArray(res.data)) this.alerts = res.data;
      } catch (error) {
        uni.showToast({ title: '告警加载失败', icon: 'none' });
      }
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
  align-items: flex-end;
  gap: 20rpx;
  padding: 30rpx;
  border-radius: 30rpx;
  background: linear-gradient(135deg, #ffffff 0%, #f4efff 100%);
  box-shadow: 0 16rpx 40rpx rgba(71, 45, 143, 0.08);
}
.hero-kicker {
  display: inline-block;
  font-size: 18rpx;
  color: #7b61ff;
  letter-spacing: 2rpx;
  font-weight: 700;
}
.page-title {
  display: block;
  margin-top: 14rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: #2b2156;
}
.page-subtitle {
  display: block;
  margin-top: 10rpx;
  font-size: 21rpx;
  line-height: 1.6;
  color: #8378a1;
}
.hero-pill {
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
.panel-title {
  display: block;
  font-size: 27rpx;
  font-weight: 800;
  color: #2d2454;
}
.filter-group { margin-top: 20rpx; }
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
.alert-content { flex: 1; }
.alert-title {
  display: block;
  font-size: 23rpx;
  font-weight: 700;
  color: #2d2454;
}
.alert-time {
  display: block;
  margin-top: 8rpx;
  font-size: 18rpx;
  color: #9a8fb2;
}
.alert-status {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  font-weight: 700;
}
.alert-status.unresolved { background: #ffe9ee; color: #dd5175; }
.alert-status.resolved { background: #efeaff; color: #7b61ff; }
.alert-description {
  display: block;
  margin-top: 18rpx;
  font-size: 21rpx;
  line-height: 1.7;
  color: #6f6686;
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
.load-more {
  margin-top: 18rpx;
  text-align: center;
  padding: 20rpx;
}
.load-more-text {
  font-size: 20rpx;
  color: #998fb1;
}
</style>
