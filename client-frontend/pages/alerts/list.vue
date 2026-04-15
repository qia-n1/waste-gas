<template>
  <view class="alerts-list">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">告警中心</text>
    </view>

    <!-- 筛选条件 -->
    <view class="filter-section">
      <view class="filter-tabs">
        <view 
          v-for="status in statusFilters" 
          :key="status.value"
          class="filter-tab"
          :class="{ active: selectedStatus === status.value }"
          @click="selectedStatus = status.value"
        >
          <text>{{ status.label }}</text>
        </view>
      </view>
      <view class="filter-tabs">
        <view 
          v-for="level in levelFilters" 
          :key="level.value"
          class="filter-tab"
          :class="{ active: selectedLevel === level.value }"
          @click="selectedLevel = level.value"
        >
          <text>{{ level.label }}</text>
        </view>
      </view>
    </view>

    <!-- 告警列表 -->
    <view class="alerts-container">
      <view 
        v-for="(alert, index) in filteredAlerts" 
        :key="alert.id"
        class="alert-item"
        @click="navigateToDetail(alert.id)"
      >
        <view class="alert-icon" :class="alert.level">
          <text v-if="alert.level === 'high'">🔥</text>
          <text v-else-if="alert.level === 'medium'">⚠️</text>
          <text v-else>ℹ️</text>
        </view>
        <view class="alert-content">
          <text class="alert-title">{{ alert.title }}</text>
          <text class="alert-time">{{ alert.time }}</text>
          <text class="alert-description">{{ alert.description }}</text>
        </view>
        <view class="alert-status" :class="alert.status">
          <text v-if="alert.status === 'unresolved'">未处理</text>
          <text v-else>已处理</text>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="filteredAlerts.length === 0" class="empty">
        <text class="empty-icon">📭</text>
        <text class="empty-text">暂无告警信息</text>
      </view>
    </view>

    <!-- 加载更多 -->
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
    selectedStatus() {
      this.loadAlerts();
    },
    selectedLevel() {
      this.loadAlerts();
    }
  },
  onShow() {
    this.loadAlerts();
  },
  computed: {
    filteredAlerts() {
      let filtered = this.alerts;
      
      if (this.selectedStatus !== 'all') {
        filtered = filtered.filter(alert => alert.status === this.selectedStatus);
      }
      
      if (this.selectedLevel !== 'all') {
        filtered = filtered.filter(alert => alert.level === this.selectedLevel);
      }
      
      return filtered;
    }
  },
  methods: {
    async loadAlerts() {
      try {
        const res = await request({
          url: `/alerts?status=${this.selectedStatus}&level=${this.selectedLevel}`
        });
        if (res && res.code === 200 && Array.isArray(res.data)) {
          this.alerts = res.data;
        }
      } catch (error) {
        uni.showToast({ title: '告警加载失败', icon: 'none' });
      }
    },
    navigateToDetail(id) {
      uni.navigateTo({
        url: `/pages/alerts/detail?id=${id}`
      });
    }
  }
};
</script>

<style>
.alerts-list {
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.filter-section {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.filter-tabs {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
  overflow-x: auto;
}

.filter-tabs:last-child {
  margin-bottom: 0;
}

.filter-tab {
  padding: 12rpx 20rpx;
  border: 1rpx solid #ddd;
  border-radius: 20rpx;
  font-size: 16rpx;
  color: #666;
  white-space: nowrap;
}

.filter-tab.active {
  background-color: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.alert-item {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.alert-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.alert-icon.high {
  background-color: #ffeeee;
}

.alert-icon.medium {
  background-color: #fff3cd;
}

.alert-icon.low {
  background-color: #e3f2fd;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 18rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 8rpx;
  display: block;
}

.alert-time {
  font-size: 14rpx;
  color: #999;
  margin-bottom: 8rpx;
  display: block;
}

.alert-description {
  font-size: 16rpx;
  color: #666;
  line-height: 1.4;
}

.alert-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 14rpx;
}

.alert-status.unresolved {
  background-color: #ffeeee;
  color: #ff4444;
}

.alert-status.resolved {
  background-color: #e8f5e8;
  color: #4CAF50;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 20rpx;
  background-color: white;
  border-radius: 16rpx;
  text-align: center;
}

.empty-icon {
  font-size: 64rpx;
  margin-bottom: 16rpx;
}

.empty-text {
  font-size: 18rpx;
  color: #999;
}

.load-more {
  text-align: center;
  padding: 20rpx;
  color: #999;
  font-size: 16rpx;
}
</style>