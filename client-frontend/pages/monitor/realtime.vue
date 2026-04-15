<template>
  <view class="monitor-page">
    <view class="monitor-hero">
      <view>
        <text class="hero-kicker">REALTIME MONITOR</text>
        <text class="page-title">实时监控</text>
        <text class="page-subtitle">当前设备运行状态与关键监测指标实时同步。</text>
      </view>
      <view class="header-actions">
        <button class="icon-btn" @click="refreshData"><text>🔄</text></button>
        <button class="icon-btn" @click="exportData"><text>📤</text></button>
      </view>
    </view>

    <view class="data-cards">
      <view class="data-card accent-violet">
        <text class="data-label">VOCs 浓度</text>
        <text class="data-value">{{ realTimeData.vocs }}</text>
        <text class="data-unit">mg/m³</text>
        <text class="data-status" :class="vocsStatusClass">{{ vocsStatusText }}</text>
      </view>
      <view class="data-card accent-pink">
        <text class="data-label">温度</text>
        <text class="data-value">{{ realTimeData.temperature }}</text>
        <text class="data-unit">℃</text>
        <text class="data-status" :class="tempStatusClass">{{ tempStatusText }}</text>
      </view>
      <view class="data-card accent-sky">
        <text class="data-label">湿度</text>
        <text class="data-value">{{ realTimeData.humidity }}</text>
        <text class="data-unit">%</text>
        <text class="data-status" :class="humidityStatusClass">{{ humidityStatusText }}</text>
      </view>
      <view class="data-card accent-peach">
        <text class="data-label">压力</text>
        <text class="data-value">{{ realTimeData.pressure }}</text>
        <text class="data-unit">kPa</text>
        <text class="data-status" :class="pressureStatusClass">{{ pressureStatusText }}</text>
      </view>
    </view>

    <view class="chart-card">
      <view class="section-head">
        <view>
          <text class="section-title">数据趋势</text>
          <text class="section-desc">观察过去 24 小时的监测变化曲线</text>
        </view>
      </view>
      <view class="chart-container">
        <view class="chart-grid"></view>
        <view class="chart-line chart-line-main"></view>
        <view class="chart-line chart-line-sub"></view>
        <view class="chart-caption">
          <text class="chart-placeholder-text">趋势图占位</text>
          <text class="chart-placeholder-subtext">可后续接入真实图表组件</text>
        </view>
      </view>
    </view>

    <view class="device-card">
      <view class="section-head">
        <view>
          <text class="section-title">设备状态</text>
          <text class="section-desc">核心连接信息与运行参数</text>
        </view>
        <view class="device-pill">{{ deviceInfo.status }}</view>
      </view>
      <view class="status-list">
        <view class="status-item"><text class="status-label">设备 ID</text><text class="status-value">{{ deviceInfo.deviceId }}</text></view>
        <view class="status-item"><text class="status-label">设备名称</text><text class="status-value">{{ deviceInfo.deviceName }}</text></view>
        <view class="status-item"><text class="status-label">最后在线</text><text class="status-value">{{ deviceInfo.lastOnline }}</text></view>
        <view class="status-item"><text class="status-label">IP 地址</text><text class="status-value">{{ deviceInfo.ipAddress }}</text></view>
        <view class="status-item"><text class="status-label">固件版本</text><text class="status-value">{{ deviceInfo.firmwareVersion }}</text></view>
      </view>
    </view>

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
      realTimeData: { vocs: 12.5, temperature: 25.3, humidity: 45, pressure: 101.3 },
      deviceInfo: {
        deviceId: 'DEV-001',
        deviceName: '废气监测设备 1',
        status: '在线',
        lastOnline: '2026-04-13 09:00',
        ipAddress: '192.168.1.100',
        firmwareVersion: 'v1.0.0'
      },
      isMonitoring: true
    };
  },
  onShow() { this.loadRealtimeData(); },
  computed: {
    vocsStatusClass() { if (this.realTimeData.vocs > 50) return 'error'; if (this.realTimeData.vocs > 20) return 'warning'; return 'normal'; },
    vocsStatusText() { if (this.realTimeData.vocs > 50) return '超标'; if (this.realTimeData.vocs > 20) return '警告'; return '正常'; },
    tempStatusClass() { if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return 'error'; if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return 'warning'; return 'normal'; },
    tempStatusText() { if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return '异常'; if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return '警告'; return '正常'; },
    humidityStatusClass() { if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return 'error'; if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return 'warning'; return 'normal'; },
    humidityStatusText() { if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return '异常'; if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return '警告'; return '正常'; },
    pressureStatusClass() { if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return 'error'; if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return 'warning'; return 'normal'; },
    pressureStatusText() { if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return '异常'; if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return '警告'; return '正常'; }
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
          if (res.data.device_info) this.deviceInfo = res.data.device_info;
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
.monitor-page {
  min-height: 100vh;
  padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%);
}
.monitor-hero {
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
.header-actions { display: flex; gap: 12rpx; }
.icon-btn {
  width: 84rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: #f4efff;
  color: #7b61ff;
  font-size: 30rpx;
}
.icon-btn::after { border: none; }
.data-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-top: 22rpx;
}
.data-card {
  padding: 24rpx;
  border-radius: 26rpx;
  box-shadow: 0 16rpx 36rpx rgba(49, 30, 109, 0.06);
}
.accent-violet { background: linear-gradient(180deg, #f4efff 0%, #ffffff 100%); }
.accent-pink { background: linear-gradient(180deg, #fff0f7 0%, #ffffff 100%); }
.accent-sky { background: linear-gradient(180deg, #eef7ff 0%, #ffffff 100%); }
.accent-peach { background: linear-gradient(180deg, #fff5ec 0%, #ffffff 100%); }
.data-label {
  display: block;
  font-size: 20rpx;
  color: #7d7198;
}
.data-value {
  display: block;
  margin-top: 18rpx;
  font-size: 47rpx;
  font-weight: 800;
  color: #2d2454;
}
.data-unit {
  display: block;
  margin-top: 8rpx;
  font-size: 18rpx;
  color: #9a8fb2;
}
.data-status {
  display: inline-block;
  margin-top: 14rpx;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  font-weight: 700;
}
.data-status.normal { background: #efeaff; color: #7b61ff; }
.data-status.warning { background: #fff5df; color: #d48618; }
.data-status.error { background: #ffe9ee; color: #dd5175; }
.chart-card,
.device-card {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 16rpx 36rpx rgba(49, 30, 109, 0.06);
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}
.section-title {
  display: block;
  font-size: 31rpx;
  font-weight: 800;
  color: #2d2454;
}
.section-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: #8c81a7;
}
.chart-container {
  position: relative;
  height: 320rpx;
  margin-top: 20rpx;
  overflow: hidden;
  border-radius: 24rpx;
  background: linear-gradient(180deg, #faf7ff 0%, #ffffff 100%);
}
.chart-grid {
  position: absolute;
  inset: 0;
  opacity: 0.35;
  background-image: linear-gradient(rgba(123, 97, 255, 0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(123, 97, 255, 0.08) 1px, transparent 1px);
  background-size: 44rpx 44rpx;
}
.chart-line {
  position: absolute;
  left: 40rpx;
  right: 40rpx;
  height: 6rpx;
  border-radius: 999rpx;
}
.chart-line-main {
  top: 132rpx;
  background: linear-gradient(90deg, #7b61ff 0%, #aa94ff 100%);
  transform: rotate(-8deg);
}
.chart-line-sub {
  top: 176rpx;
  background: linear-gradient(90deg, #88d3ff 0%, #7b61ff 100%);
  transform: rotate(5deg);
}
.chart-caption {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 34rpx;
  text-align: center;
}
.chart-placeholder-text {
  display: block;
  font-size: 24rpx;
  font-weight: 700;
  color: #51476c;
}
.chart-placeholder-subtext {
  display: block;
  margin-top: 8rpx;
  font-size: 18rpx;
  color: #9a8fb2;
}
.device-pill {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: #efeaff;
  color: #7b61ff;
  font-size: 18rpx;
  font-weight: 700;
}
.status-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 20rpx;
}
.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: #faf8ff;
}
.status-label {
  font-size: 20rpx;
  color: #9388ae;
}
.status-value {
  font-size: 21rpx;
  font-weight: 700;
  color: #2d2454;
  text-align: right;
}
.action-buttons {
  display: flex;
  gap: 16rpx;
  margin-top: 22rpx;
}
.btn-primary,
.btn-secondary {
  flex: 1;
  height: 96rpx;
  border-radius: 22rpx;
  font-size: 23rpx;
  font-weight: 700;
}
.btn-primary {
  background: linear-gradient(135deg, #7b61ff 0%, #947dff 100%);
  color: #fff;
  box-shadow: 0 16rpx 30rpx rgba(123, 97, 255, 0.18);
}
.btn-secondary {
  background: #fff;
  color: #7b61ff;
  border: 2rpx solid #e8e0ff;
}
.btn-primary::after,
.btn-secondary::after { border: none; }
</style>
