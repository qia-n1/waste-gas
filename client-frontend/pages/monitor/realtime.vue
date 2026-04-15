<template>
  <view class="realtime-monitor">
    <!-- 页面标题 -->
    <view class="page-header">
      <text class="page-title">实时监控</text>
      <view class="header-actions">
        <button class="btn-refresh" @click="refreshData">
          <text>🔄</text>
        </button>
        <button class="btn-export" @click="exportData">
          <text>📤</text>
        </button>
      </view>
    </view>

    <!-- 实时数据卡片 -->
    <view class="data-cards">
      <view class="data-card">
        <text class="data-label">VOCs 浓度</text>
        <text class="data-value">{{ realTimeData.vocs }}</text>
        <text class="data-unit">mg/m³</text>
        <text class="data-status" :class="vocsStatusClass">
          {{ vocsStatusText }}
        </text>
      </view>
      <view class="data-card">
        <text class="data-label">温度</text>
        <text class="data-value">{{ realTimeData.temperature }}</text>
        <text class="data-unit">℃</text>
        <text class="data-status" :class="tempStatusClass">
          {{ tempStatusText }}
        </text>
      </view>
      <view class="data-card">
        <text class="data-label">湿度</text>
        <text class="data-value">{{ realTimeData.humidity }}</text>
        <text class="data-unit">%</text>
        <text class="data-status" :class="humidityStatusClass">
          {{ humidityStatusText }}
        </text>
      </view>
      <view class="data-card">
        <text class="data-label">压力</text>
        <text class="data-value">{{ realTimeData.pressure }}</text>
        <text class="data-unit">kPa</text>
        <text class="data-status" :class="pressureStatusClass">
          {{ pressureStatusText }}
        </text>
      </view>
    </view>

    <!-- 数据趋势图表 -->
    <view class="chart-section">
      <text class="section-title">数据趋势</text>
      <view class="chart-container">
        <!-- 这里可以使用 uni-app 的图表组件或第三方库 -->
        <view class="chart-placeholder">
          <text class="chart-placeholder-text">数据趋势图表</text>
          <text class="chart-placeholder-subtext">过去 24 小时</text>
        </view>
      </view>
    </view>

    <!-- 设备状态 -->
    <view class="device-status">
      <text class="section-title">设备状态</text>
      <view class="status-list">
        <view class="status-item">
          <text class="status-label">设备 ID</text>
          <text class="status-value">{{ deviceInfo.deviceId }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">设备名称</text>
          <text class="status-value">{{ deviceInfo.deviceName }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">设备状态</text>
          <text class="status-value normal">{{ deviceInfo.status }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">最后在线</text>
          <text class="status-value">{{ deviceInfo.lastOnline }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">IP 地址</text>
          <text class="status-value">{{ deviceInfo.ipAddress }}</text>
        </view>
        <view class="status-item">
          <text class="status-label">固件版本</text>
          <text class="status-value">{{ deviceInfo.firmwareVersion }}</text>
        </view>
      </view>
    </view>

    <!-- 操作按钮 -->
    <view class="action-buttons">
      <button class="btn-primary" @click="startMonitoring">开始监控</button>
      <button class="btn-secondary" @click="stopMonitoring">停止监控</button>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return {
      realTimeData: {
        vocs: 12.5,
        temperature: 25.3,
        humidity: 45,
        pressure: 101.3
      },
      deviceInfo: {
        deviceId: "DEV-001",
        deviceName: "废气监测设备 1",
        status: "在线",
        lastOnline: "2026-04-13 09:00",
        ipAddress: "192.168.1.100",
        firmwareVersion: "v1.0.0"
      },
      isMonitoring: true
    };
  },
  onShow() {
    this.loadRealtimeData();
  },
  computed: {
    vocsStatusClass() {
      if (this.realTimeData.vocs > 50) return 'error';
      if (this.realTimeData.vocs > 20) return 'warning';
      return 'normal';
    },
    vocsStatusText() {
      if (this.realTimeData.vocs > 50) return '超标';
      if (this.realTimeData.vocs > 20) return '警告';
      return '正常';
    },
    tempStatusClass() {
      if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return 'error';
      if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return 'warning';
      return 'normal';
    },
    tempStatusText() {
      if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return '异常';
      if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return '警告';
      return '正常';
    },
    humidityStatusClass() {
      if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return 'error';
      if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return 'warning';
      return 'normal';
    },
    humidityStatusText() {
      if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return '异常';
      if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return '警告';
      return '正常';
    },
    pressureStatusClass() {
      if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return 'error';
      if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return 'warning';
      return 'normal';
    },
    pressureStatusText() {
      if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return '异常';
      if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return '警告';
      return '正常';
    }
  },
  methods: {
    async loadRealtimeData() {
      try {
        const res = await request({ url: '/monitor/realtime' });
        if (res && res.code === 200 && res.data) {
          if (res.data.real_time_data) {
            this.realTimeData = {
              vocs: res.data.real_time_data.vocs,
              temperature: res.data.real_time_data.temperature,
              humidity: res.data.real_time_data.humidity,
              pressure: res.data.real_time_data.pressure
            };
          }
          if (res.data.device_info) {
            this.deviceInfo = res.data.device_info;
          }
        }
      } catch (error) {
        uni.showToast({ title: '监控数据加载失败', icon: 'none' });
      }
    },
    async refreshData() {
      await this.loadRealtimeData();
      uni.showToast({ title: '数据已刷新', duration: 1000 });
    },
    exportData() {
      // 模拟导出数据
      uni.showToast({ title: '数据已导出', duration: 1000 });
    },
    async startMonitoring() {
      try {
        await request({ url: '/monitor/control/start', method: 'POST' });
        this.isMonitoring = true;
        uni.showToast({ title: '监控已开始', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: '操作失败', icon: 'none' });
      }
    },
    async stopMonitoring() {
      try {
        await request({ url: '/monitor/control/stop', method: 'POST' });
        this.isMonitoring = false;
        uni.showToast({ title: '监控已停止', duration: 1000 });
      } catch (error) {
        uni.showToast({ title: '操作失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.realtime-monitor {
  padding: 20rpx;
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12rpx;
}

.btn-refresh, .btn-export {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: none;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.data-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.data-card {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  text-align: center;
}

.data-label {
  font-size: 16rpx;
  color: #666;
  margin-bottom: 8rpx;
  display: block;
}

.data-value {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 4rpx;
  display: block;
}

.data-unit {
  font-size: 14rpx;
  color: #999;
  margin-bottom: 8rpx;
  display: block;
}

.data-status {
  font-size: 14rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  display: inline-block;
}

.data-status.normal {
  background-color: #e8f5e8;
  color: #4CAF50;
}

.data-status.warning {
  background-color: #fff3cd;
  color: #ff9800;
}

.data-status.error {
  background-color: #f8d7da;
  color: #ff4444;
}

.chart-section {
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

.chart-container {
  height: 300rpx;
  background-color: #f9f9f9;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  text-align: center;
}

.chart-placeholder-text {
  font-size: 20rpx;
  color: #666;
  margin-bottom: 8rpx;
  display: block;
}

.chart-placeholder-subtext {
  font-size: 16rpx;
  color: #999;
  display: block;
}

.device-status {
  background-color: white;
  padding: 20rpx;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
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

.action-buttons {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.btn-primary {
  flex: 1;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 18rpx;
  font-weight: 500;
}

.btn-secondary {
  flex: 1;
  background-color: white;
  color: #4CAF50;
  border: 1rpx solid #4CAF50;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 18rpx;
  font-weight: 500;
}
</style>