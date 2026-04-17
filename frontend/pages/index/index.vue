<template>
  <view class="home">
    <!-- 顶部欢迎区域 -->
    <view class="welcome-section">
      <text class="welcome-title">废气监测系统</text>
      <text class="welcome-subtitle">实时监控 · 智能预警</text>
    </view>

    <!-- 2D厂区地图 -->
    <view class="factory-map">
      <text class="section-title">厂区地图</text>
      <view class="map-container">
        <view class="map-grid">
          <view v-for="(point, index) in mapPoints" :key="index" 
                class="map-point" 
                :class="point.status"
                @click="showPointDetail(point)">
            <view class="point-dot"></view>
            <text class="point-label">{{ point.name }}</text>
          </view>
        </view>
      </view>
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
          <view class="button-icon text-icon">监</view>
          <text class="button-text">实时监控</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/alerts/list')">
          <view class="button-icon text-icon">警</view>
          <text class="button-text">告警中心</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/ai/chat')">
          <view class="button-icon text-icon">AI</view>
          <text class="button-text">AI 对话</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/profile/index')">
          <view class="button-icon text-icon">我</view>
          <text class="button-text">个人中心</text>
        </view>
        <view class="quick-button" @click="navigateTo('/pages/settings/index')">
          <view class="button-icon text-icon">设</view>
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
            <text v-if="alert.level === 'high'">高</text>
            <text v-else-if="alert.level === 'medium'">中</text>
            <text v-else>低</text>
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

    <!-- 底部统计条 -->
    <view class="bottom-stats">
      <view class="stat-item">
        <text class="stat-value">{{ stats.normal }}</text>
        <text class="stat-label">正常</text>
      </view>
      <view class="stat-item">
        <text class="stat-value warning">{{ stats.warning }}</text>
        <text class="stat-label">预警</text>
      </view>
      <view class="stat-item">
        <text class="stat-value danger">{{ stats.danger }}</text>
        <text class="stat-label">告警</text>
      </view>
    </view>

    <!-- 点位详情弹窗 -->
    <view v-if="showDetail" class="point-detail">
      <view class="detail-content">
        <text class="detail-title">{{ selectedPoint.name }}</text>
        <view class="divider-light"></view>
        <view class="detail-item">
          <text class="detail-label">状态：</text>
          <text class="detail-value" :class="selectedPoint.status">{{ getStatusText(selectedPoint.status) }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">VOCs浓度：</text>
          <text class="detail-value">{{ selectedPoint.vocs }} mg/m³</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">温度：</text>
          <text class="detail-value">{{ selectedPoint.temperature }} ℃</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">湿度：</text>
          <text class="detail-value">{{ selectedPoint.humidity }} %</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">更新时间：</text>
          <text class="detail-value">{{ selectedPoint.updateTime }}</text>
        </view>
        <button class="btn-primary btn-block mt-20" @click="closeDetail">关闭</button>
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
      ],
      mapPoints: [
        {
          name: "A区",
          status: "normal",
          vocs: 10.2,
          temperature: 24.5,
          humidity: 42,
          updateTime: "2026-04-11 10:00"
        },
        {
          name: "B区",
          status: "warning",
          vocs: 25.8,
          temperature: 26.7,
          humidity: 48,
          updateTime: "2026-04-11 10:00"
        },
        {
          name: "C区",
          status: "danger",
          vocs: 45.3,
          temperature: 28.9,
          humidity: 52,
          updateTime: "2026-04-11 10:00"
        },
        {
          name: "D区",
          status: "normal",
          vocs: 8.7,
          temperature: 23.8,
          humidity: 40,
          updateTime: "2026-04-11 10:00"
        },
        {
          name: "E区",
          status: "normal",
          vocs: 9.5,
          temperature: 24.2,
          humidity: 43,
          updateTime: "2026-04-11 10:00"
        },
        {
          name: "F区",
          status: "warning",
          vocs: 22.1,
          temperature: 25.9,
          humidity: 46,
          updateTime: "2026-04-11 10:00"
        }
      ],
      stats: {
        normal: 3,
        warning: 2,
        danger: 1
      },
      showDetail: false,
      selectedPoint: {}
    };
  },
  onLoad() {
    // 简化 onLoad 方法，避免访问 undefined 的 options
  },
  methods: {
    navigateTo(url) {
      // 如果目标是 tabbar 页面，使用 switchTab
      const tabPages = ['/pages/index/index', '/pages/monitor/realtime', '/pages/alerts/list', '/pages/profile/index'];
      const path = url.split('?')[0];
      if (tabPages.includes(path)) {
        uni.switchTab({ url: path });
      } else {
        uni.navigateTo({ url: url });
      }
    },
    showPointDetail(point) {
      this.selectedPoint = point;
      this.showDetail = true;
    },
    closeDetail() {
      this.showDetail = false;
    },
    getStatusText(status) {
      switch(status) {
        case 'normal': return '正常';
        case 'warning': return '预警';
        case 'danger': return '告警';
        default: return '未知';
      }
    }
  }
};
</script>

<style>
.home {
  min-height: 100vh;
  padding: 24rpx;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
  background:
    radial-gradient(900rpx 500rpx at 5% 0%, rgba(123, 97, 255, 0.14) 0%, rgba(123, 97, 255, 0) 62%),
    radial-gradient(780rpx 420rpx at 100% 24%, rgba(167, 139, 250, 0.16) 0%, rgba(167, 139, 250, 0) 58%),
    linear-gradient(180deg, #f7f4ff 0%, #ffffff 52%, #ffffff 100%);
}

.welcome-section {
  background: linear-gradient(180deg, var(--primary), var(--primary-light));
  color: white;
  padding: 40rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: 0 6rpx 22rpx rgba(123, 97, 255, 0.15);
}

.welcome-title {
  font-size: 34rpx;
  font-weight: 800;
  margin-bottom: 8rpx;
  display: block;
}

.welcome-subtitle {
  font-size: 18rpx;
  opacity: 0.95;
}

.factory-map {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.map-container {
  background-color: #f9fafb;
  border-radius: var(--radius);
  padding: 30rpx;
  min-height: 300rpx;
}

.map-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30rpx;
  justify-items: center;
}

.map-point {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.point-dot {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  margin-bottom: 8rpx;
  position: relative;
}

.point-dot::after {
  content: '';
  position: absolute;
  top: -8rpx;
  left: -8rpx;
  right: -8rpx;
  bottom: -8rpx;
  border-radius: 50%;
  opacity: 0.3;
}

.map-point.normal .point-dot {
  background-color: var(--primary-light);
}

.map-point.normal .point-dot::after {
  background-color: var(--primary-light);
}

.map-point.warning .point-dot {
  background-color: var(--warning);
}

.map-point.warning .point-dot::after {
  background-color: var(--warning);
}

.map-point.danger .point-dot {
  background-color: var(--danger);
}

.map-point.danger .point-dot::after {
  background-color: var(--danger);
}

.point-label {
  font-size: 16rpx;
  color: var(--text-main);
  margin-top: 8rpx;
}

.data-overview {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 16rpx;
  color: var(--text-main);
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.data-card {
  background-color: var(--primary-ultra-light);
  padding: 20rpx;
  border-radius: var(--radius);
  text-align: center;
}

.data-value {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 4rpx;
  display: block;
}

.data-label {
  font-size: 18rpx;
  color: var(--text-second);
  margin-bottom: 4rpx;
  display: block;
}

.data-unit {
  font-size: 16rpx;
  color: var(--text-desc);
  display: block;
}

.quick-access {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.quick-buttons {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16rpx;
}

.quick-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16rpx 12rpx;
  background-color: var(--primary-ultra-light);
  border-radius: var(--radius);
  cursor: pointer;
}

.button-icon {
  font-size: 26rpx;
  margin-bottom: 8rpx;
}

.text-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, #7B61FF 0%, #A78BFA 100%);
  color: #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 10rpx 24rpx rgba(123, 97, 255, 0.2);
}

.button-text {
  font-size: 18rpx;
  color: var(--text-main);
  text-align: center;
}

.recent-alerts {
  background-color: white;
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  box-shadow: var(--shadow-2);
  border: 1rpx solid rgba(123, 97, 255, 0.12);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.section-more {
  font-size: 18rpx;
  color: var(--primary);
  cursor: pointer;
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
  background-color: var(--primary-ultra-light);
  border-radius: var(--radius);
  border-left: 4rpx solid;
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
  margin-right: 16rpx;
  font-size: 20rpx;
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
  color: var(--text-main);
  margin-bottom: 4rpx;
  display: block;
}

.alert-time {
  font-size: 16rpx;
  color: var(--text-desc);
  display: block;
}

.alert-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 16rpx;
}

.alert-status.unresolved {
  background-color: #FFF6F6;
  color: var(--danger);
}

.alert-status.resolved {
  background-color: var(--primary-ultra-light);
  color: var(--primary);
}

.bottom-stats {
  background-color: var(--primary-ultra-light);
  padding: 20rpx;
  border-radius: var(--radius);
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 4rpx;
}

.stat-value.warning {
  color: var(--warning);
}

.stat-value.danger {
  color: var(--danger);
}

.stat-label {
  font-size: 16rpx;
  color: var(--text-second);
}

.point-detail {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.detail-content {
  background-color: white;
  border-radius: var(--radius);
  padding: 30rpx;
  width: 80%;
  max-width: 500rpx;
  max-height: 80vh;
  overflow: auto;
}

.detail-title {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--primary);
  text-align: center;
  margin-bottom: 20rpx;
  display: block;
}

.detail-item {
  display: flex;
  margin-bottom: 16rpx;
  align-items: center;
}

.detail-label {
  font-size: 18rpx;
  color: var(--text-second);
  width: 120rpx;
}

.detail-value {
  font-size: 18rpx;
  color: var(--text-main);
  flex: 1;
}

.detail-value.normal {
  color: var(--primary);
}

.detail-value.warning {
  color: var(--warning);
}

.detail-value.danger {
  color: var(--danger);
}
</style>