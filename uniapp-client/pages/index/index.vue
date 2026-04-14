<template>
  <view class="home">
    <!-- 顶部欢迎区域 -->
    <view class="welcome-section">
      <text class="welcome-title">废气监测系统</text>
      <text class="welcome-subtitle">实时监控 · 智能预警</text>
    </view>

    <!-- 实时数据概览 -->
    <view class="data-overview">
      <text class="section-title">实时数据</text>
      <view class="data-cards">
        <view class="data-card">
          <text class="data-value">{{ realTimeData.vocs }}</text>
          <text class="data-label">VOCs 浓度</text>
          <text class="data-unit">mg/m³</text>
        </view>
        <view class="data-card">
          <text class="data-value">{{ realTimeData.temperature }}</text>
          <text class="data-label">温度</text>
          <text class="data-unit">℃</text>
        </view>
        <view class="data-card">
          <text class="data-value">{{ realTimeData.humidity }}</text>
          <text class="data-label">湿度</text>
          <text class="data-unit">%</text>
        </view>
      </view>
    </view>

    <!-- 快捷功能入口 -->
    <view class="quick-access">
      <text class="section-title">快捷功能</text>
      <view class="quick-buttons">
        <view class="quick-button" @click="navigateTo('/pages/monitor/realtime')">
          <view class="button-icon">📊</view>
          <text class="button-text">实时监控</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/alerts/list')">
          <view class="button-icon">⚠️</view>
          <text class="button-text">告警中心</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/profile/index')">
          <view class="button-icon">👤</view>
          <text class="button-text">个人中心</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/settings/index')">
          <view class="button-icon">⚙️</view>
          <text class="button-text">设置</text>
        </view>
      </view>
    </view>

    <!-- 最近告警信息 -->
    <view class="recent-alerts">
      <view class="section-header">
        <text class="section-title">最近告警</text>
        <text class="section-more" @click="navigateTo('/pages/alerts/list')">查看全部</text>
      </view>
      <view class="alerts-list">
        <view v-for="(alert, index) in recentAlerts" :key="index" class="alert-item">
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
      </view>
    </view>

    <!-- 系统状态 -->
    <view class="system-status">
      <text class="section-title">系统状态</text>
      <view class="status-items">
        <view class="status-item">
          <text class="status-label">设备在线</text>
          <text class="status-value normal">正常</text>
        </view>
        <view class="status-item">
          <text class="status-label">数据采集</text>
          <text class="status-value normal">正常</text>
        </view>
        <view class="status-item">
          <text class="status-label">网络连接</text>
          <text class="status-value normal">正常</text>
        </view>
        <view class="status-item">
          <text class="status-label">系统版本</text>
          <text class="status-value">v1.0.0</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      realTimeData: {
        vocs: 12.5,
        temperature: 25.3,
        humidity: 45
      },
      recentAlerts: [
        {
          title: "VOCs 浓度超标",
          time: "2026-04-11 10:00",
          level: "high",
          status: "unresolved"
        },
        {
          title: "温度异常",
          time: "2026-04-11 09:30",
          level: "medium",
          status: "resolved"
        },
        {
          title: "湿度异常",
          time: "2026-04-11 09:00",
          level: "low",
          status: "resolved"
        }
      ]
    };
  },
  methods: {
    navigateTo(url) {
      uni.navigateTo({ url: url });
    }
  }
};
</script>

<style>
.home {
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.welcome-section {
  background-color: #4CAF50;
  color: white;
  padding: 40rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.welcome-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
  display: block;
}

.welcome-subtitle {
  font-size: 20rpx;
  opacity: 0.9;
}

.data-overview {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 24rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
  color: #333;
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.data-card {
  background-color: #f9f9f9;
  padding: 20rpx;
  border-radius: 12rpx;
  text-align: center;
}

.data-value {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 4rpx;
  display: block;
}

.data-label {
  font-size: 16rpx;
  color: #666;
  margin-bottom: 4rpx;
  display: block;
}

.data-unit {
  font-size: 14rpx;
  color: #999;
  display: block;
}

.quick-access {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.quick-buttons {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16rpx;
}

.quick-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.button-icon {
  font-size: 48rpx;
  margin-bottom: 8rpx;
}

.button-text {
  font-size: 16rpx;
  color: #333;
}

.recent-alerts {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.section-more {
  font-size: 16rpx;
  color: #4CAF50;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.alert-item {
  display: flex;
  align-items: center;
  padding: 16rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.alert-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
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
  color: #333;
  margin-bottom: 4rpx;
  display: block;
}

.alert-time {
  font-size: 14rpx;
  color: #999;
  display: block;
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

.system-status {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.status-items {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
}

.status-label {
  font-size: 16rpx;
  color: #666;
}

.status-value {
  font-size: 16rpx;
  color: #333;
  font-weight: 500;
}

.status-value.normal {
  color: #4CAF50;
}
</style>