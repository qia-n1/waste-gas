<template>
  <view class="home-page">
    <view class="hero-panel">
      <view>
        <text class="hero-kicker">SMART MAP</text>
        <text class="hero-title">厂区废气源 2D 地图</text>
        <text class="hero-subtitle">支持点位查看、最近告警定位、AI 咨询与快捷处置。</text>
      </view>
      <view class="hero-badge">
        <text class="hero-badge-label">最新时间</text>
        <text class="hero-badge-value">{{ realTimeData.timestamp || '--' }}</text>
      </view>
    </view>

    <view class="map-card">
      <view class="section-head">
        <view>
          <text class="section-title">厂区地图</text>
          <text class="section-desc">绿色正常，橙色预警，红色告警</text>
        </view>
        <view class="map-actions">
          <view class="map-action" @click="zoomOut">-</view>
          <view class="map-action" @click="zoomIn">+</view>
          <view class="map-action wide" @click="focusNearestAlert">最近告警</view>
        </view>
      </view>
      <movable-area class="map-area">
        <movable-view class="map-canvas" direction="all" :scale="true" :scale-min="0.8" :scale-max="2.2" :scale-value="mapScale">
          <view class="map-grid"></view>
          <view v-for="point in mapPoints" :key="point.id" class="map-point" :class="point.level" :style="{ left: point.x + '%', top: point.y + '%' }" @click="selectPoint(point)">
            <text class="map-point-dot"></text>
            <text class="map-point-name">{{ point.name }}</text>
          </view>
        </movable-view>
      </movable-area>
      <view class="map-footer">
        <view class="stat-chip">在线点位 {{ mapPoints.length }}</view>
        <view class="stat-chip warning">高等级 {{ highAlertCount }}</view>
      </view>
    </view>

    <view v-if="selectedPoint" class="detail-card">
      <view class="section-head compact">
        <view>
          <text class="section-title">点位详情</text>
          <text class="section-desc">{{ selectedPoint.areaName }} · {{ selectedPoint.deviceId }}</text>
        </view>
        <text class="point-status" :class="selectedPoint.level">{{ selectedPoint.status }}</text>
      </view>
      <view class="point-info-grid">
        <view class="info-box"><text class="info-label">浓度</text><text class="info-value">{{ selectedPoint.concentration }}</text></view>
        <view class="info-box"><text class="info-label">趋势</text><text class="info-value">{{ trendLabel(selectedPoint.trend) }}</text></view>
        <view class="info-box"><text class="info-label">等级</text><text class="info-value">{{ levelLabel(selectedPoint.level) }}</text></view>
      </view>
      <view class="quick-buttons">
        <view class="quick-button" @click="navigateTo('/pages/ai/chat')"><text class="quick-title">AI 咨询</text><text class="quick-sub">原因分析与 SOP</text></view>
        <view class="quick-button" @click="navigateTo('/pages/alerts/list')"><text class="quick-title">查看告警</text><text class="quick-sub">跳转告警中心</text></view>
        <view class="quick-button" @click="navigateTo('/pages/records/index')"><text class="quick-title">处置记录</text><text class="quick-sub">提交与导出</text></view>
      </view>
    </view>

    <view class="overview-card">
      <view class="section-head compact">
        <view>
          <text class="section-title">实时概览</text>
          <text class="section-desc">当前 VOCs、温度、湿度核心指标</text>
        </view>
      </view>
      <view class="metric-grid">
        <view class="metric-box"><text class="metric-label">VOCs</text><text class="metric-value">{{ realTimeData.vocs }}</text><text class="metric-unit">mg/m³</text></view>
        <view class="metric-box"><text class="metric-label">温度</text><text class="metric-value">{{ realTimeData.temperature }}</text><text class="metric-unit">℃</text></view>
        <view class="metric-box"><text class="metric-label">湿度</text><text class="metric-value">{{ realTimeData.humidity }}</text><text class="metric-unit">%</text></view>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return {
      realTimeData: { vocs: 0, temperature: 0, humidity: 0, timestamp: '' },
      mapPoints: [],
      selectedPoint: null,
      mapScale: 1,
      nearestAlertId: null,
    };
  },
  computed: {
    highAlertCount() {
      return this.mapPoints.filter(item => item.level === 'high').length;
    }
  },
  onShow() {
    this.loadOverview();
  },
  methods: {
    async loadOverview() {
      try {
        const [overview, mapRes] = await Promise.all([
          request({ url: '/dashboard/overview' }),
          request({ url: '/monitor/map' })
        ]);
        if (overview?.code === 200 && overview.data) {
          this.realTimeData = overview.data.realTimeData || this.realTimeData;
        }
        if (mapRes?.code === 200 && mapRes.data) {
          this.mapPoints = mapRes.data.points || [];
          this.nearestAlertId = mapRes.data.nearestAlertId;
          this.selectedPoint = this.mapPoints.find(item => item.id === this.nearestAlertId) || this.mapPoints[0] || null;
        }
      } catch (error) {
        uni.showToast({ title: '首页数据加载失败', icon: 'none' });
      }
    },
    navigateTo(url) {
      const tabPages = ['/pages/index/index', '/pages/monitor/realtime', '/pages/alerts/list', '/pages/profile/index'];
      const path = url.split('?')[0];
      if (tabPages.includes(path)) uni.switchTab({ url: path });
      else uni.navigateTo({ url });
    },

    selectPoint(point) {
      this.selectedPoint = point;
    },
    zoomIn() {
      this.mapScale = Math.min(2.2, this.mapScale + 0.2);
    },
    zoomOut() {
      this.mapScale = Math.max(0.8, this.mapScale - 0.2);
    },
    focusNearestAlert() {
      const target = this.mapPoints.find(item => item.id === this.nearestAlertId);
      if (target) this.selectedPoint = target;
    },
    trendLabel(trend) {
      if (trend === 'up') return '上升';
      if (trend === 'down') return '下降';
      return '平稳';
    },
    levelLabel(level) {
      if (level === 'high') return '红色告警';
      if (level === 'medium') return '橙色预警';
      return '绿色正常';
    }
  }
};
</script>

<style>
.home-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.hero-panel,.map-card,.detail-card,.overview-card { margin-bottom: 22rpx; border-radius: 30rpx; padding: 26rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.hero-panel { display:flex; justify-content:space-between; gap:16rpx; background: linear-gradient(135deg, #7b61ff 0%, #9178ff 100%); color:#fff; }
.hero-kicker { display:block; font-size:18rpx; letter-spacing:2rpx; opacity:.85; }
.hero-title { display:block; margin-top:12rpx; font-size:40rpx; font-weight:800; }
.hero-subtitle { display:block; margin-top:10rpx; font-size:21rpx; line-height:1.6; opacity:.92; }
.hero-badge { min-width:180rpx; padding:18rpx; border-radius:22rpx; background:rgba(255,255,255,.16); }
.hero-badge-label { display:block; font-size:18rpx; opacity:.82; }
.hero-badge-value { display:block; margin-top:8rpx; font-size:22rpx; font-weight:700; }
.section-head { display:flex; justify-content:space-between; align-items:center; gap:12rpx; margin-bottom:18rpx; }
.section-head.compact { margin-bottom:16rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; }
.map-actions { display:flex; gap:10rpx; }
.map-action { min-width:56rpx; height:56rpx; border-radius:16rpx; background:#f3eeff; display:flex; align-items:center; justify-content:center; color:#7b61ff; font-size:22rpx; font-weight:700; }
.map-action.wide { min-width:128rpx; padding:0 12rpx; }
.map-area { width:100%; height:420rpx; border-radius:24rpx; overflow:hidden; background:linear-gradient(180deg,#faf7ff 0%,#f1e9ff 100%); }
.map-canvas { width:100%; height:100%; position:relative; }
.map-grid { position:absolute; inset:0; background-image: linear-gradient(rgba(123,97,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(123,97,255,.08) 1px, transparent 1px); background-size:44rpx 44rpx; }
.map-point { position:absolute; transform:translate(-50%,-50%); display:flex; flex-direction:column; align-items:center; }
.map-point-dot { width:26rpx; height:26rpx; border-radius:50%; border:4rpx solid #fff; box-shadow:0 8rpx 16rpx rgba(0,0,0,.12); }
.map-point.low .map-point-dot { background:#34c759; }
.map-point.medium .map-point-dot { background:#ff9500; }
.map-point.high .map-point-dot { background:#ff4d67; }
.map-point-name { margin-top:8rpx; padding:6rpx 12rpx; border-radius:999rpx; background:#fff; font-size:17rpx; color:#5d5478; }
.map-footer { display:flex; gap:10rpx; margin-top:16rpx; }
.stat-chip { padding:10rpx 16rpx; border-radius:999rpx; background:#efeaff; color:#7b61ff; font-size:18rpx; }
.stat-chip.warning { background:#fff3e2; color:#db8a1b; }
.point-status { padding:10rpx 16rpx; border-radius:999rpx; font-size:18rpx; font-weight:700; }
.point-status.high { background:#ffe9ee; color:#dd5175; }
.point-status.medium { background:#fff5df; color:#d48618; }
.point-status.low { background:#ebf9ef; color:#2f9d57; }
.point-info-grid,.metric-grid,.quick-buttons { display:grid; gap:14rpx; }
.point-info-grid { grid-template-columns:repeat(3,1fr); }
.metric-grid { grid-template-columns:repeat(3,1fr); }
.quick-buttons { grid-template-columns:repeat(3,1fr); margin-top:18rpx; }
.info-box,.metric-box,.quick-button { padding:18rpx; border-radius:22rpx; background:#faf8ff; }
.info-label,.metric-label { display:block; font-size:18rpx; color:#9489af; }
.info-value,.metric-value { display:block; margin-top:10rpx; font-size:24rpx; font-weight:800; color:#2d2454; }
.metric-unit,.quick-sub { display:block; margin-top:8rpx; font-size:18rpx; color:#9388ae; }
.quick-title { display:block; font-size:22rpx; font-weight:700; color:#2d2454; }
</style>
