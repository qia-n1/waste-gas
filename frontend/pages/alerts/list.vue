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
        :class="alert.level"
        @click="navigateToDetail(alert.id)"
      >
        <view class="alert-icon" :class="alert.level">
          <text class="icon" v-if="alert.level === 'high'">高</text>
          <text class="icon" v-else-if="alert.level === 'medium'">中</text>
          <text class="icon" v-else>低</text>
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
      alerts: [
        {
          id: 1,
          title: "VOCs 浓度超标",
          time: "2026-04-13 10:00",
          description: "VOCs 浓度达到 65.2 mg/m³，超过阈值 50 mg/m³",
          level: "high",
          status: "unresolved"
        },
        {
          id: 2,
          title: "温度异常",
          time: "2026-04-13 09:30",
          description: "温度达到 42.5 ℃，超过阈值 40 ℃",
          level: "high",
          status: "unresolved"
        },
        {
          id: 3,
          title: "湿度异常",
          time: "2026-04-13 09:00",
          description: "湿度达到 85%，超过阈值 80%",
          level: "medium",
          status: "resolved"
        },
        {
          id: 4,
          title: "压力异常",
          time: "2026-04-13 08:30",
          description: "压力达到 106.5 kPa，超过阈值 105 kPa",
          level: "medium",
          status: "resolved"
        },
        {
          id: 5,
          title: "设备离线",
          time: "2026-04-13 08:00",
          description: "设备 DEV-001 离线",
          level: "high",
          status: "resolved"
        }
      ]
    };
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
  min-height: 100vh;
  padding: 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background:
    radial-gradient(860rpx 460rpx at 8% 0%, rgba(123, 97, 255, 0.12) 0%, rgba(123, 97, 255, 0) 60%),
    linear-gradient(180deg, #f8f5ff 0%, #ffffff 48%, #ffffff 100%);
}

.page-header {
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--text-main);
}

.filter-section {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.filter-tabs {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.filter-tabs:last-child {
  margin-bottom: 0;
}

.filter-tab {
  padding: 12rpx 20rpx;
  border: 1rpx solid #E5E7EB;
  border-radius: 20rpx;
  font-size: 20rpx;
  color: var(--text-second);
  white-space: nowrap;
  cursor: pointer;
}

.filter-tab.active {
  background-color: var(--primary);
  color: white;
  border-color: var(--primary);
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
  border-radius: var(--radius);
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.1);
  border-left: 4rpx solid;
  cursor: pointer;
}

.alert-item.high {
  border-left-color: var(--danger);
}

.alert-item.medium {
  border-left-color: var(--warning);
}

.alert-item.low {
  border-left-color: var(--primary-light);
}

.alert-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  flex-shrink: 0;
  font-weight: 700;
  color: #FFFFFF;
  border: 1rpx solid rgba(255, 255, 255, 0.9);
}

.alert-icon.high {
  background: linear-gradient(135deg, #EF4444 0%, #F87171 100%);
}

.alert-icon.medium {
  background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 100%);
}

.alert-icon.low {
  background: linear-gradient(135deg, #7B61FF 0%, #A78BFA 100%);
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 20rpx;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 8rpx;
  display: block;
}

.alert-time {
  font-size: 18rpx;
  color: var(--text-second);
  margin-bottom: 8rpx;
  display: block;
}

.alert-description {
  font-size: 20rpx;
  color: var(--text-second);
  line-height: 1.4;
}

.alert-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 18rpx;
  flex-shrink: 0;
}

.alert-status.unresolved {
  background-color: #FFF6F6;
  color: var(--danger);
}

.alert-status.resolved {
  background-color: var(--primary-ultra-light);
  color: var(--primary);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 20rpx;
  background-color: white;
  border-radius: var(--radius);
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.empty-icon {
  font-size: 64rpx;
  margin-bottom: 16rpx;
}

.empty-text {
  font-size: 20rpx;
  color: var(--text-desc);
}

.load-more {
  text-align: center;
  padding: 20rpx;
  color: var(--text-desc);
  font-size: 20rpx;
}
</style>