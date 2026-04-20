<template>
  <view class="monitor-page" :class="{ 'motion-ready': motionReady }">
    <view class="monitor-hero motion-fade delay-1">
      <view class="hero-text">
        <text class="page-title">实时监控</text>
        <text class="page-subtitle">设备与挥发性有机物等指标</text>
      </view>
      <view class="header-actions">
        <button class="icon-btn" @click="refreshData"><text>刷新</text></button>
        <button class="icon-btn" @click="exportData"><text>导出</text></button>
      </view>
    </view>

    <view class="data-cards motion-fade delay-2">
      <view class="data-card accent-violet">
        <text class="data-label">挥发性有机物浓度</text>
        <text class="data-value">{{ displayData.vocs }}</text>
        <text class="data-unit">毫克每立方米</text>
        <StatusTag class="data-status" :label="vocsStatusText" :type="vocsStatusClass" />
      </view>
      <view class="data-card accent-pink">
        <text class="data-label">温度</text>
        <text class="data-value">{{ displayData.temperature }}</text>
        <text class="data-unit">摄氏度</text>
        <StatusTag class="data-status" :label="tempStatusText" :type="tempStatusClass" />
      </view>
      <view class="data-card accent-sky">
        <text class="data-label">湿度</text>
        <text class="data-value">{{ displayData.humidity }}</text>
        <text class="data-unit">百分比</text>
        <StatusTag class="data-status" :label="humidityStatusText" :type="humidityStatusClass" />
      </view>
      <view class="data-card accent-peach">
        <text class="data-label">压力</text>
        <text class="data-value">{{ displayData.pressure }}</text>
        <text class="data-unit">千帕</text>
        <StatusTag class="data-status" :label="pressureStatusText" :type="pressureStatusClass" />
      </view>
    </view>

    <view class="chart-card motion-fade delay-3">
      <view class="section-head">
        <view>
          <text class="section-title">数据趋势</text>
          <text class="section-desc">最近读数，约二十秒自动同步</text>
        </view>
      </view>
      <view class="chart-container">
        <view class="chart-grid"></view>
        <view v-if="trendSeries.length" class="trend-line-wrap">
          <view
            v-for="(seg, i) in trendLineSegments"
            :key="`seg-${i}`"
            class="trend-seg"
            :style="seg.style"
          ></view>
          <view
            v-for="(pt, i) in trendLinePoints"
            :key="`pt-${i}`"
            class="trend-point"
            :style="{ left: pt.x + '%', top: pt.y + '%' }"
          >
            <text class="trend-dot"></text>
            <text class="trend-lab">{{ pt.short }}</text>
          </view>
        </view>
        <view v-else class="chart-caption">
          <text class="chart-placeholder-text">暂无趋势数据</text>
        </view>
      </view>
    </view>

    <view class="device-card motion-fade delay-4">
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

    <view class="action-buttons motion-fade delay-5">
      <button class="btn-primary" @click="startMonitoring">开始监控</button>
      <button class="btn-secondary" @click="stopMonitoring">停止监控</button>
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
      realTimeData: { vocs: 12.5, temperature: 25.3, humidity: 45, pressure: 101.3 },
      displayData: { vocs: 12.5, temperature: 25.3, humidity: 45, pressure: 101.3 },
      deviceInfo: {
        deviceId: 'DEV-001',
        deviceName: '废气监测设备 1',
        status: '在线',
        lastOnline: '2026-04-13 09:00',
        ipAddress: '192.168.1.100',
        firmwareVersion: 'v1.0.0'
      },
      isMonitoring: true,
      trendSeries: [],
      trendMax: 1,
      trendMin: 0,
      trendPlotSize: { w: 1, h: 1 },
      pollTimer: null,
      pollMs: 20000,
      motionReady: false,
      pageActive: true,
      animTimers: [],
    };
  },
  onShow() {
    this.pageActive = true;
    this.motionReady = false;
    this.$nextTick(() => {
      this.motionReady = true;
    });
    this.loadRealtimeData();
    this.startPoll();
  },
  onHide() {
    this.pageActive = false;
    this.stopPoll();
    this.clearAnimTimers();
  },
  onUnload() {
    this.pageActive = false;
    this.stopPoll();
    this.clearAnimTimers();
  },
  computed: {
    vocsStatusClass() { if (this.realTimeData.vocs > 50) return 'error'; if (this.realTimeData.vocs > 20) return 'warning'; return 'normal'; },
    vocsStatusText() { if (this.realTimeData.vocs > 50) return '超标'; if (this.realTimeData.vocs > 20) return '警告'; return '正常'; },
    tempStatusClass() { if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return 'error'; if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return 'warning'; return 'normal'; },
    tempStatusText() { if (this.realTimeData.temperature > 40 || this.realTimeData.temperature < 0) return '异常'; if (this.realTimeData.temperature > 35 || this.realTimeData.temperature < 5) return '警告'; return '正常'; },
    humidityStatusClass() { if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return 'error'; if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return 'warning'; return 'normal'; },
    humidityStatusText() { if (this.realTimeData.humidity > 90 || this.realTimeData.humidity < 20) return '异常'; if (this.realTimeData.humidity > 80 || this.realTimeData.humidity < 30) return '警告'; return '正常'; },
    pressureStatusClass() { if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return 'error'; if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return 'warning'; return 'normal'; },
    pressureStatusText() { if (this.realTimeData.pressure > 110 || this.realTimeData.pressure < 90) return '异常'; if (this.realTimeData.pressure > 105 || this.realTimeData.pressure < 95) return '警告'; return '正常'; },
    trendLinePoints() {
      const list = this.trendSeries || [];
      if (!list.length) return [];
      const max = this.trendMax;
      const min = this.trendMin;
      const span = Math.max(1, max - min);
      const n = list.length;
      return list.map((item, idx) => {
        const x = n === 1 ? 50 : Math.round((idx * 100) / (n - 1));
        const norm = (Number(item.value || 0) - min) / span;
        const y = Math.round((1 - Math.max(0, Math.min(1, norm))) * 82) + 8;
        return { ...item, x, y };
      });
    },
    trendLineSegments() {
      const points = this.trendLinePoints;
      if (points.length < 2) return [];
      const result = [];
      const w = Math.max(1, this.trendPlotSize.w || 1);
      const h = Math.max(1, this.trendPlotSize.h || 1);
      for (let i = 0; i < points.length - 1; i += 1) {
        const p1 = points[i];
        const p2 = points[i + 1];
        const dxPct = p2.x - p1.x;
        const dyPct = p2.y - p1.y;
        const dxPx = (dxPct / 100) * w;
        const dyPx = (dyPct / 100) * h;
        const widthPct = (Math.sqrt(dxPx * dxPx + dyPx * dyPx) / w) * 100;
        const angle = Math.atan2(dyPx, dxPx) * (180 / Math.PI);
        result.push({
          style: {
            left: `${p1.x}%`,
            top: `${p1.y}%`,
            width: `${widthPct}%`,
            transform: `translateY(-50%) rotate(${angle}deg)`,
          },
        });
      }
      return result;
    },
  },
  methods: {
    clearAnimTimers() {
      (this.animTimers || []).forEach((t) => clearInterval(t));
      this.animTimers = [];
    },
    animateNumber(fromValue, toValue, setValue, duration = 420) {
      const from = Number(fromValue || 0);
      const to = Number(toValue || 0);
      if (!Number.isFinite(to)) {
        setValue(0);
        return;
      }
      const delta = to - from;
      if (Math.abs(delta) < 0.01) {
        setValue(Number(to.toFixed(1)));
        return;
      }
      const start = Date.now();
      const timer = setInterval(() => {
        if (!this.pageActive) {
          clearInterval(timer);
          const off = this.animTimers.indexOf(timer);
          if (off >= 0) this.animTimers.splice(off, 1);
          return;
        }
        const progress = Math.min(1, (Date.now() - start) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        const next = from + delta * eased;
        setValue(Number(next.toFixed(1)));
        if (progress >= 1) {
          clearInterval(timer);
          const idx = this.animTimers.indexOf(timer);
          if (idx >= 0) this.animTimers.splice(idx, 1);
          setValue(Number(to.toFixed(1)));
        }
      }, 16);
      this.animTimers.push(timer);
    },
    animateMetrics() {
      this.clearAnimTimers();
      this.animateNumber(this.displayData.vocs, this.realTimeData.vocs, (v) => {
        this.displayData.vocs = Number(v.toFixed(1));
      });
      this.animateNumber(this.displayData.temperature, this.realTimeData.temperature, (v) => {
        this.displayData.temperature = Number(v.toFixed(1));
      });
      this.animateNumber(this.displayData.humidity, this.realTimeData.humidity, (v) => {
        this.displayData.humidity = Math.round(v);
      });
      this.animateNumber(this.displayData.pressure, this.realTimeData.pressure, (v) => {
        this.displayData.pressure = Number(v.toFixed(1));
      });
    },
    startPoll() {
      this.stopPoll();
      this.pollTimer = setInterval(() => {
        this.loadRealtimeData();
      }, this.pollMs);
    },
    stopPoll() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer);
        this.pollTimer = null;
      }
    },
    async loadRealtimeData() {
      try {
        const res = await request({ url: '/monitor/realtime' });
        if (!this.pageActive) return;
        if (res && res.code === 200 && res.data) {
          if (res.data.real_time_data) {
            this.realTimeData = {
              vocs: res.data.real_time_data.vocs,
              temperature: res.data.real_time_data.temperature,
              humidity: res.data.real_time_data.humidity,
              pressure: res.data.real_time_data.pressure
            };
            if (this.pageActive) this.animateMetrics();
          }
          if (res.data.device_info) this.deviceInfo = res.data.device_info;
          const trend = res.data.trend || [];
          const vals = trend.map((t) => t.vocs || 0);
          this.trendMax = Math.max(1, ...vals);
          this.trendMin = Math.min(...vals, this.trendMax);
          const tail = trend.slice(-12);
          this.trendSeries = tail.map((t) => ({
            short: (t.time || '').slice(-5) || '—',
            value: Number(t.vocs || 0),
          }));
          this.$nextTick(() => {
            if (this.pageActive) this.measureTrendPlot();
          });
        }
      } catch (error) {
        uni.showToast({ title: '监控数据加载失败', icon: 'none' });
      }
    },
    measureTrendPlot() {
      if (!this.pageActive) return;
      const q = uni.createSelectorQuery().in(this);
      q.select('.trend-line-wrap').boundingClientRect((rect) => {
        if (!this.pageActive || !rect) return;
        this.trendPlotSize = { w: rect.width || 1, h: rect.height || 1 };
      }).exec();
    },
    async refreshData() {
      await this.loadRealtimeData();
      uni.showToast({ title: '数据已刷新', duration: 1000 });
    },
    exportData() {
      uni.showModal({
        title: '导出说明',
        content: '实时监控原始记录已在“巡检与处置”页提供导出入口，是否前往？',
        success: (res) => {
          if (!res.confirm) return;
          uni.navigateTo({ url: '/pages/records/index?tab=disposal' });
        },
      });
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
.header-actions { display: flex; gap: 12rpx; flex-shrink: 0; }
.icon-btn {
  width: 84rpx;
  height: 84rpx;
  padding: 0;
  border-radius: 24rpx;
  background: #f4efff;
  color: #7b61ff;
  font-size: 30rpx;
}
.icon-btn:active { transform: scale(0.96); background:#ece3ff; }
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
  display: inline-flex;
  margin-top: 14rpx;
  padding: 0;
}
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
.trend-line-wrap {
  position: absolute;
  left: 24rpx;
  right: 24rpx;
  bottom: 24rpx;
  top: 24rpx;
}
.trend-seg {
  position: absolute;
  height: 4rpx;
  transform-origin: left center;
  background: linear-gradient(90deg, #7b61ff 0%, #a38eff 100%);
  border-radius: 999rpx;
}
.trend-point {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.trend-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #7b61ff;
  border: 3rpx solid #fff;
  box-shadow: 0 0 0 2rpx rgba(123, 97, 255, 0.2);
}
.trend-lab { font-size: 14rpx; color: #9a8fb2; margin-top: 8rpx; }
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
.status-item:active { transform: scale(0.995); background:#f4efff; }
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
  height: 88rpx;
  padding: 0 20rpx;
  border-radius: 22rpx;
  font-size: 28rpx;
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
.motion-fade { opacity: 0; transform: translateY(12rpx); transition: opacity var(--wg-motion-slow) var(--wg-ease-standard), transform var(--wg-motion-slow) var(--wg-ease-standard); }
.monitor-page.motion-ready .motion-fade { opacity: 1; transform: translateY(0); }
.delay-1 { transition-delay: .02s; }
.delay-2 { transition-delay: .08s; }
.delay-3 { transition-delay: .14s; }
.delay-4 { transition-delay: .2s; }
.delay-5 { transition-delay: .26s; }
</style>
