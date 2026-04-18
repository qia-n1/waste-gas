<template>
  <view class="home-page" :class="{ 'motion-ready': motionReady }">
    <view class="hero-panel motion-fade delay-1">
      <view class="hero-text">
        <text class="hero-title">厂区监测</text>
        <text class="hero-subtitle">地图、预警、巡检与处置</text>
      </view>
      <view class="hero-badge">
        <text class="hero-badge-label">最新时间</text>
        <text class="hero-badge-value">{{ realTimeData.timestamp || '--' }}</text>
      </view>
    </view>

    <view class="workbench-row motion-fade delay-2">
      <view class="wb-card" @click="navigateTo('/pages/alerts/list')">
        <text class="wb-num">{{ animatedWorkbench.pendingDispatch }}</text>
        <text class="wb-label">待接单预警</text>
      </view>
      <view class="wb-card" @click="navigateTo('/pages/alerts/list')">
        <text class="wb-num">{{ animatedWorkbench.inProgress }}</text>
        <text class="wb-label">处理中工单</text>
      </view>
      <view class="wb-card accent" @click="navigateTo('/pages/records/index')">
        <text class="wb-icon">巡检</text>
        <text class="wb-label">日常巡检记录</text>
      </view>
    </view>

    <view class="map-card motion-fade delay-3">
      <view class="section-head">
        <view>
          <text class="section-title">厂区地图</text>
          <text class="section-desc">火电厂平面示意（白紫）· 仅本人负责区可点选查看数据</text>
        </view>
        <view class="map-actions">
          <view class="map-action" @click="zoomOut">-</view>
          <view class="map-action" @click="resetZoom">{{ zoomLabel }}</view>
          <view class="map-action" @click="zoomIn">+</view>
          <view class="map-action" @click="focusMyArea">我的区域</view>
          <view class="map-action wide" @click="focusNearestAlert">告警</view>
        </view>
      </view>
      <view class="map-legend">
        <view class="legend-item"><text class="legend-dot low"></text><text class="legend-text">正常</text></view>
        <view class="legend-item"><text class="legend-dot medium"></text><text class="legend-text">预警</text></view>
        <view class="legend-item"><text class="legend-dot high"></text><text class="legend-text">告警</text></view>
      </view>
      <view class="map-area">
        <view
          class="map-zoom-wrap"
          @touchstart="onMapTouchStart"
          @touchmove="onMapTouchMove"
          @touchend="onMapTouchEnd"
          @touchcancel="onMapTouchEnd"
        >
        <view class="plant-canvas" :style="{ transform: `scale(${mapScale})` }">
          <view class="plant-grid"></view>
          <view class="plant-border"></view>
          <view class="plant-node desulfurization">脱硫塔</view>
          <view class="plant-node chimney">烟囱</view>
          <view class="plant-node cooling-a">冷却塔1</view>
          <view class="plant-node cooling-b">冷却塔2</view>
          <view class="plant-node main-workshop">主厂房</view>
          <view class="plant-node material-corridor">原料廊道</view>
          <view class="plant-node auxiliary-a">辅助楼A</view>
          <view class="plant-node auxiliary-b">辅助楼B</view>
          <view class="plant-node power-zone">配电装置区</view>
          <view class="plant-node painting-shell" @click="openPaintingWorkshop">涂装车间</view>

          <view
            v-for="area in plantOverlays"
            :key="`overlay-${area.id}`"
            class="area-overlay"
            :class="[area.level, { active: selectedArea && selectedArea.id === area.id }]"
            :style="areaOverlayStyle(area)"
            @click="selectArea(area)"
          >
            <text class="overlay-badge" v-if="area.level === 'high'">告警</text>
            <text class="overlay-title">{{ area.name }}</text>
            <text class="overlay-meta">设备 {{ area.deviceCount }} · 告警 {{ area.alertCount }}</text>
            <text class="overlay-hint">点击查看指标</text>
          </view>
        </view>
        </view>
      </view>
      <view v-if="selectedAreaData && metricPointsForSelected.length" class="metric-block">
        <text class="metric-block-title">监测指标 · {{ selectedAreaData.name }}</text>
        <view class="metric-col">
          <view
            v-for="point in metricPointsForSelected"
            :key="point.id"
            class="metric-node"
            :class="[point.level, { active: selectedPoint && selectedPoint.id === point.id }]"
            @click="selectPoint(selectedAreaData, point)"
          >
            <text class="metric-name">{{ formatMetricLabel(point.name) }}</text>
            <text class="metric-value">{{ point.concentration }}</text>
          </view>
        </view>
      </view>
      <view v-else-if="selectedAreaData && !metricPointsForSelected.length" class="metric-empty">
        <text class="metric-empty-text">该区域暂无监测点位数据</text>
      </view>
      <view class="map-footer">
        <view class="stat-chip">负责区域 {{ safeOwnedAreaCount }}</view>
        <view class="stat-chip">在线点位 {{ mapPoints.length }}</view>
        <view class="stat-chip warning">高等级 {{ highAlertCount }}</view>
      </view>
    </view>

    <view v-if="selectedPoint && selectedAreaData" class="detail-card motion-fade delay-4">
      <view class="section-head compact">
        <view>
          <text class="section-title">区域详情</text>
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
        <view class="quick-button" @click="navigateTo('/pages/ai/chat')"><text class="quick-title">智能问答</text><text class="quick-sub">分析建议</text></view>
        <view class="quick-button" @click="navigateTo('/pages/alerts/list')"><text class="quick-title">告警</text><text class="quick-sub">列表与接单</text></view>
        <view class="quick-button" @click="navigateTo('/pages/records/index')"><text class="quick-title">记录</text><text class="quick-sub">巡检与处置</text></view>
      </view>
    </view>

    <view class="overview-card motion-fade delay-4">
      <view class="section-head compact">
        <view>
          <text class="section-title">未来 6 小时 VOCs</text>
          <text class="section-desc">短时预测（mg/m³）</text>
        </view>
      </view>
      <view v-if="prediction6h.length" class="pred-chart">
        <view
          v-for="(seg, i) in predictionLineSegments"
          :key="`pred-seg-${i}`"
          class="pred-seg"
          :style="seg.style"
        ></view>
        <view
          v-for="(pt, i) in predictionLinePoints"
          :key="`pred-pt-${i}`"
          class="pred-point"
          :style="{ left: pt.x + '%', top: pt.y + '%' }"
        >
          <text class="pred-dot"></text>
          <text class="pred-val">{{ pt.predicted }}</text>
          <text class="pred-lab">{{ pt.label }}</text>
        </view>
      </view>
      <view v-if="actualSeries.length" class="actual-strip">
        <text class="strip-title">最近实测</text>
        <scroll-view scroll-x class="strip-scroll" :show-scrollbar="false">
          <view v-for="(a, j) in actualTail" :key="j" class="strip-chip">
            <text class="chip-t">{{ a.time.slice(-5) }}</text>
            <text class="chip-v">{{ a.vocs }}</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <view class="overview-card motion-fade delay-5">
      <view class="section-head compact">
        <view>
          <text class="section-title">快捷入口</text>
          <text class="section-desc">常用功能</text>
        </view>
      </view>
      <view class="quick-buttons top-entries">
        <view class="quick-button" @click="navigateTo('/pages/alerts/list')"><text class="quick-title">告警</text><text class="quick-sub">接单与处理</text></view>
        <view class="quick-button" @click="navigateTo('/pages/ai/chat')"><text class="quick-title">问答</text><text class="quick-sub">现场分析</text></view>
        <view class="quick-button" @click="navigateTo('/pages/records/index')"><text class="quick-title">记录</text><text class="quick-sub">巡检与闭环</text></view>
      </view>
      <view class="quick-buttons">
        <view class="quick-button" @click="navigateTo('/pages/area/index')"><text class="quick-title">区域</text><text class="quick-sub">设备排口</text></view>
        <view class="quick-button" @click="navigateTo('/pages/monitor/realtime')"><text class="quick-title">监控</text><text class="quick-sub">实时趋势</text></view>
        <view class="quick-button" @click="navigateTo('/pages/settings/index')"><text class="quick-title">设置</text><text class="quick-sub">地址与通知</text></view>
      </view>
    </view>

    <view class="overview-card motion-fade delay-5">
      <view class="section-head compact">
        <view>
          <text class="section-title">实时概览</text>
          <text class="section-desc">当前 VOCs、温度、湿度核心指标</text>
        </view>
      </view>
      <view class="metric-grid">
        <view class="metric-box"><text class="metric-label">VOCs</text><text class="metric-value">{{ animatedRealtime.vocs }}</text><text class="metric-unit">mg/m³</text></view>
        <view class="metric-box"><text class="metric-label">温度</text><text class="metric-value">{{ animatedRealtime.temperature }}</text><text class="metric-unit">℃</text></view>
        <view class="metric-box"><text class="metric-label">湿度</text><text class="metric-value">{{ animatedRealtime.humidity }}</text><text class="metric-unit">%</text></view>
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
      mapAreas: [],
      mapPoints: [],
      selectedArea: null,
      selectedPoint: null,
      nearestAlertId: null,
      ownedAreaNames: [],
      prediction6h: [],
      actualSeries: [],
      workbench: { pendingDispatch: 0, inProgress: 0 },
      animatedWorkbench: { pendingDispatch: 0, inProgress: 0 },
      animatedRealtime: { vocs: 0, temperature: 0, humidity: 0 },
      predMax: 1,
      predPlotSize: { w: 1, h: 1 },
      mapScale: 1,
      pinchStartDistance: 0,
      pinchStartScale: 1,
      isPinching: false,
      motionReady: false,
    };
  },
  computed: {
    highAlertCount() {
      return this.mapPoints.filter(item => item.level === 'high').length;
    },
    safeOwnedAreaCount() {
      return Array.isArray(this.ownedAreaNames) ? this.ownedAreaNames.length : 0;
    },
    selectedAreaData() {
      return this.selectedArea || null;
    },
    zoomLabel() {
      return `${Math.round(this.mapScale * 100)}%`;
    },
    pointsByArea() {
      const grouped = {};
      (this.mapPoints || []).forEach((item) => {
        const key = item.areaName || '';
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(item);
      });
      return grouped;
    },
    plantOverlays() {
      return (this.mapAreas || []).filter((a) => a.canView);
    },
    metricPointsForSelected() {
      if (!this.selectedAreaData) return [];
      return this.pointsByArea[this.selectedAreaData.name] || [];
    },
    actualTail() {
      const list = this.actualSeries || [];
      return list.slice(Math.max(0, list.length - 8));
    },
    predictionLinePoints() {
      const list = this.prediction6h || [];
      if (!list.length) return [];
      const max = this.predMax || 1;
      const min = Math.min(...list.map((x) => Number(x.predicted || 0)), max);
      const span = Math.max(1, max - min);
      const n = list.length;
      return list.map((item, idx) => {
        const x = n === 1 ? 50 : Math.round((idx * 100) / (n - 1));
        const y = Math.round((1 - ((Number(item.predicted || 0) - min) / span)) * 72) + 12;
        return { ...item, x, y };
      });
    },
    predictionLineSegments() {
      const points = this.predictionLinePoints;
      if (points.length < 2) return [];
      const result = [];
      const w = Math.max(1, this.predPlotSize.w || 1);
      const h = Math.max(1, this.predPlotSize.h || 1);
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
  onShow() {
    this.motionReady = false;
    this.$nextTick(() => {
      this.motionReady = true;
    });
    this.loadOverview();
  },
  methods: {
    animateNumber(fromValue, toValue, setValue, duration = 480) {
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
        const progress = Math.min(1, (Date.now() - start) / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        const next = from + delta * eased;
        setValue(Number(next.toFixed(1)));
        if (progress >= 1) {
          clearInterval(timer);
          setValue(Number(to.toFixed(1)));
        }
      }, 16);
    },
    animateOverviewNumbers() {
      this.animateNumber(this.animatedWorkbench.pendingDispatch, this.workbench.pendingDispatch, (v) => {
        this.animatedWorkbench.pendingDispatch = Math.max(0, Math.round(v));
      });
      this.animateNumber(this.animatedWorkbench.inProgress, this.workbench.inProgress, (v) => {
        this.animatedWorkbench.inProgress = Math.max(0, Math.round(v));
      });
      this.animateNumber(this.animatedRealtime.vocs, this.realTimeData.vocs, (v) => {
        this.animatedRealtime.vocs = Number(v.toFixed(1));
      });
      this.animateNumber(this.animatedRealtime.temperature, this.realTimeData.temperature, (v) => {
        this.animatedRealtime.temperature = Number(v.toFixed(1));
      });
      this.animateNumber(this.animatedRealtime.humidity, this.realTimeData.humidity, (v) => {
        this.animatedRealtime.humidity = Math.round(v);
      });
    },
    async loadOverview() {
      try {
        const [overview, mapRes] = await Promise.all([
          request({ url: '/dashboard/overview' }),
          request({ url: '/monitor/map' })
        ]);
        if (overview?.code === 200 && overview.data) {
          this.realTimeData = overview.data.realTimeData || this.realTimeData;
          this.prediction6h = overview.data.prediction_6h || [];
          this.actualSeries = overview.data.actual_series || [];
          this.workbench = overview.data.workbench || { pendingDispatch: 0, inProgress: 0 };
          this.animateOverviewNumbers();
          const preds = this.prediction6h.map((x) => x.predicted || 0);
          const acts = this.actualSeries.map((x) => x.vocs || 0);
          this.predMax = Math.max(1, ...preds, ...acts, this.realTimeData.vocs || 0);
          this.$nextTick(() => this.measurePredPlot());
        }
        if (mapRes?.code === 200 && mapRes.data) {
          this.mapAreas = mapRes.data.areas || [];
          this.mapPoints = mapRes.data.points || [];
          this.nearestAlertId = mapRes.data.nearestAlertId;
          this.ownedAreaNames = mapRes.data.ownedAreaNames || [];
          this.selectedPoint = this.mapPoints.find(item => item.id === this.nearestAlertId) || this.mapPoints[0] || null;
          const ownFirst = this.mapAreas.find((item) => item.canView) || null;
          if (this.selectedPoint) {
            const match = this.mapAreas.find((item) => item.name === this.selectedPoint.areaName && item.canView);
            this.selectedArea = match || ownFirst;
            if (!match && ownFirst) {
              const pts = this.pointsByArea[ownFirst.name] || [];
              this.selectedPoint = pts[0] || this.selectedPoint;
            }
          } else {
            this.selectedArea = ownFirst;
          }
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

    selectArea(area) {
      if (!area.canView) {
        uni.showToast({ title: '无权限查看该区域', icon: 'none' });
        return;
      }
      this.selectedArea = area;
      const first = (this.pointsByArea[area.name] || [])[0];
      if (first) this.selectedPoint = first;
    },
    selectPoint(area, point) {
      if (!area.canView) {
        uni.showToast({ title: '无权限查看该区域', icon: 'none' });
        return;
      }
      this.selectedArea = area;
      this.selectedPoint = point;
    },
    focusNearestAlert() {
      const target = this.mapPoints.find(item => item.id === this.nearestAlertId);
      if (target) {
        this.selectedPoint = target;
        this.selectedArea = this.mapAreas.find(item => item.name === target.areaName && item.canView) || null;
        if (!this.selectedArea) {
          uni.showToast({ title: '告警不在您负责区域内', icon: 'none' });
        }
        return;
      }
      uni.showToast({ title: '暂无高等级告警定位', icon: 'none' });
    },
    focusMyArea() {
      const own = this.plantOverlays[0];
      if (own) {
        this.selectArea(own);
        return;
      }
      uni.showToast({ title: '暂无负责区域', icon: 'none' });
    },
    zoomIn() {
      this.mapScale = Math.min(2.2, Number((this.mapScale + 0.2).toFixed(2)));
    },
    zoomOut() {
      this.mapScale = Math.max(0.8, Number((this.mapScale - 0.2).toFixed(2)));
    },
    resetZoom() {
      this.mapScale = 1;
    },
    getTouchDistance(touches) {
      if (!touches || touches.length < 2) return 0;
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    },
    onMapTouchStart(e) {
      const touches = e.touches || [];
      if (touches.length < 2) return;
      const distance = this.getTouchDistance(touches);
      if (!distance) return;
      this.isPinching = true;
      this.pinchStartDistance = distance;
      this.pinchStartScale = this.mapScale;
    },
    onMapTouchMove(e) {
      if (!this.isPinching) return;
      const touches = e.touches || [];
      if (touches.length < 2) return;
      const distance = this.getTouchDistance(touches);
      if (!distance || !this.pinchStartDistance) return;
      const ratio = distance / this.pinchStartDistance;
      const nextScale = this.pinchStartScale * ratio;
      this.mapScale = Math.max(0.8, Math.min(2.2, Number(nextScale.toFixed(2))));
    },
    onMapTouchEnd(e) {
      const touches = (e && e.touches) || [];
      if (touches.length >= 2) return;
      this.isPinching = false;
      this.pinchStartDistance = 0;
      this.pinchStartScale = this.mapScale;
    },
    openPaintingWorkshop() {
      const paintArea = (this.mapAreas || []).find((a) => String(a.name || '').includes('涂装') && a.canView);
      if (!paintArea) {
        uni.showToast({ title: '无权限查看涂装车间', icon: 'none' });
        return;
      }
      this.selectArea(paintArea);
      uni.showToast({ title: '已定位涂装车间', icon: 'none' });
    },
    areaOverlayStyle(area) {
      const name = String(area.name || '');
      if (name.includes('涂装')) {
        return { left: '69%', top: '30%', width: '14%', height: '13%', minHeight: '88rpx' };
      }
      return {
        left: `${Math.max(2, Math.min(88, area.x || 5))}%`,
        top: `${Math.max(6, Math.min(84, area.y || 8))}%`,
        width: `${Math.max(12, Math.min(28, area.w || 16))}%`,
        height: `${Math.max(10, Math.min(22, area.h || 12))}%`,
        minHeight: '88rpx',
      };
    },
    formatMetricLabel(key) {
      const k = String(key || '');
      const map = {
        coating_flow: '涂装风量',
        coating_conc: '涂装浓度',
        coating_temp: '涂装温度',
        coating_pressure: '涂装压力',
      };
      return map[k] || k;
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
    },
    measurePredPlot() {
      const q = uni.createSelectorQuery().in(this);
      q.select('.pred-chart').boundingClientRect((rect) => {
        if (!rect) return;
        this.predPlotSize = { w: rect.width || 1, h: rect.height || 1 };
      }).exec();
    },
  }
};
</script>

<style>
.home-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.hero-panel,.map-card,.detail-card,.overview-card { margin-bottom: 22rpx; border-radius: 30rpx; padding: 26rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.hero-panel { display:flex; justify-content:space-between; align-items:flex-start; gap:16rpx; background: linear-gradient(135deg, #7b61ff 0%, #9178ff 100%); color:#fff; }
.hero-text { flex:1; min-width:0; }
.hero-title { display:block; font-size:40rpx; font-weight:800; line-height:1.2; word-break:break-word; }
.hero-subtitle { display:block; margin-top:10rpx; font-size:22rpx; line-height:1.45; opacity:.92; word-break:break-word; }
.hero-badge { flex-shrink:0; min-width:160rpx; max-width:42%; padding:18rpx; border-radius:22rpx; background:rgba(255,255,255,.16); text-align:right; }
.hero-badge-value { word-break:break-all; }
.hero-badge-label { display:block; font-size:18rpx; opacity:.82; }
.hero-badge-value { display:block; margin-top:8rpx; font-size:22rpx; font-weight:700; }
.section-head { display:flex; justify-content:space-between; align-items:center; gap:12rpx; margin-bottom:18rpx; }
.section-head > view:first-child { flex:1; min-width:0; }
.section-head.compact { margin-bottom:16rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; line-height:1.25; word-break:break-word; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; line-height:1.45; word-break:break-word; }
.map-actions { display:flex; gap:10rpx; }
.map-action { min-width:56rpx; height:56rpx; border-radius:16rpx; background:#f3eeff; display:flex; align-items:center; justify-content:center; color:#7b61ff; font-size:20rpx; font-weight:700; padding:0 10rpx; }
.map-action.wide { min-width:112rpx; padding:0 12rpx; }
.map-legend { display:flex; flex-wrap:wrap; gap:16rpx; margin:-6rpx 0 14rpx 0; }
.legend-item { display:flex; align-items:center; gap:8rpx; }
.legend-dot { width:16rpx; height:16rpx; border-radius:50%; border:2rpx solid #7b1fa2; }
.legend-dot.low { background:#34c759; border-color:#2f9d57; }
.legend-dot.medium { background:#ff9500; border-color:#d48618; }
.legend-dot.high { background:#ff4d67; border-color:#dd5175; }
.legend-text { font-size:18rpx; color:#6f638f; }
.map-area { width:100%; border-radius:24rpx; overflow:auto; background:linear-gradient(180deg,#ffffff 0%,#f7f1ff 100%); box-shadow:inset 0 0 0 1rpx rgba(123,31,162,.08); }
.map-zoom-wrap { width:100%; height:560rpx; overflow:auto; }
.plant-canvas { position:relative; width:100%; min-width:720rpx; height:560rpx; padding:14rpx; transform-origin: top left; transition: transform .16s ease; }
.plant-grid { position:absolute; inset:12rpx; border-radius:12rpx; opacity:0.45; background-image:linear-gradient(rgba(123,31,162,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(123,31,162,.06) 1px, transparent 1px); background-size:36rpx 36rpx; pointer-events:none; z-index:0; }
.plant-border { position:absolute; inset:12rpx; border:3rpx solid #7b1fa2; border-radius:14rpx; z-index:0; }
.plant-node { position:absolute; z-index:1; display:flex; align-items:center; justify-content:center; text-align:center; color:#54107a; font-size:19rpx; font-weight:800; line-height:1.25; padding:6rpx; background:#f5f5f5; border:2rpx solid #7b1fa2; border-radius:10rpx; box-shadow:0 4rpx 12rpx rgba(123,31,162,.08); }
.desulfurization { left:8%; top:12%; width:84rpx; height:84rpx; border-radius:50%; background:linear-gradient(145deg,#bb86fc 0%,#e1bee7 100%); }
.chimney { left:21%; top:8%; width:26rpx; height:180rpx; border-radius:8rpx; background:linear-gradient(180deg,#ffffff 0%,#e8e0f0 45%,#f5f5f5 100%); }
.cooling-a { left:34%; top:8%; width:110rpx; height:170rpx; border-radius:55rpx / 85rpx; }
.cooling-b { left:50%; top:8%; width:110rpx; height:170rpx; border-radius:55rpx / 85rpx; }
.main-workshop { left:25%; top:44%; width:300rpx; height:110rpx; background:linear-gradient(180deg,rgba(187,134,252,.85) 0%,rgba(187,134,252,.55) 100%); font-size:20rpx; }
.material-corridor { left:10%; top:78%; width:520rpx; height:44rpx; background:linear-gradient(90deg,rgba(187,134,252,.5) 0%,rgba(187,134,252,.25) 100%); border-radius:8rpx; }
.auxiliary-a { left:70%; top:50%; width:96rpx; height:78rpx; }
.auxiliary-b { left:82%; top:60%; width:94rpx; height:92rpx; }
.power-zone { left:79%; top:42%; width:124rpx; height:66rpx; background:#faf8ff; }
.painting-shell { left:69%; top:30%; width:14%; height:13%; min-height:72rpx; z-index:1; background:linear-gradient(180deg,#ffcdd2 0%,#f8bbd9 100%); border-width:3rpx; font-size:14rpx; color:#7b1fa2; opacity:0.92; }
.area-overlay { position:absolute; padding:10rpx; border-radius:12rpx; border:3rpx solid #7b1fa2; background:rgba(243,229,245,.96); z-index:4; box-sizing:border-box; display:flex; flex-direction:column; justify-content:center; }
.area-overlay.active { box-shadow:0 12rpx 28rpx rgba(123,31,162,.28); border-color:#5e1380; transform:scale(1.02); }
.area-overlay.low { background:rgba(238,249,241,.96); border-color:#2f9d57; }
.area-overlay.medium { background:rgba(255,246,232,.96); border-color:#d48618; }
.area-overlay.high { background:rgba(255,238,242,.96); border-color:#dd5175; }
.overlay-badge { position:absolute; top:6rpx; right:8rpx; font-size:12rpx; font-weight:800; color:#dd5175; background:#fff; padding:2rpx 8rpx; border-radius:999rpx; border:1rpx solid #ffc9d4; }
.overlay-title { display:block; color:#4c0f71; font-size:20rpx; font-weight:800; line-height:1.25; padding-right:56rpx; }
.overlay-meta { display:block; margin-top:6rpx; color:#5e5478; font-size:16rpx; line-height:1.35; }
.overlay-hint { display:block; margin-top:6rpx; font-size:14rpx; color:#7e7299; }
.metric-block { margin-top:18rpx; }
.metric-block-title { display:block; font-size:24rpx; font-weight:800; color:#5e1380; margin-bottom:12rpx; }
.metric-col { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12rpx; }
.metric-empty { margin-top:18rpx; padding:24rpx; border-radius:16rpx; background:#faf8ff; border:2rpx dashed #dcd2ff; }
.metric-empty-text { font-size:22rpx; color:#8c81a7; text-align:center; display:block; }
.metric-node { padding:14rpx; border-radius:14rpx; background:#fff; border:2rpx solid #e8d5f2; }
.metric-node.active { border-color:#7b1fa2; box-shadow:0 8rpx 20rpx rgba(123,31,162,.12); }
.metric-node.low { background:linear-gradient(180deg,#f1fbf4 0%, #fff 100%); }
.metric-node.medium { background:linear-gradient(180deg,#fff7eb 0%, #fff 100%); }
.metric-node.high { background:linear-gradient(180deg,#fff1f4 0%, #fff 100%); }
.metric-name { display:block; font-size:16rpx; color:#6f638f; word-break:break-word; }
.metric-value { display:block; margin-top:6rpx; font-size:20rpx; font-weight:700; color:#2d2454; }
.map-footer { display:flex; gap:10rpx; margin-top:16rpx; }
.stat-chip { padding:10rpx 16rpx; border-radius:999rpx; background:#efeaff; color:#7b61ff; font-size:18rpx; }
.stat-chip.warning { background:#fff3e2; color:#db8a1b; }
.point-status { padding:10rpx 16rpx; border-radius:999rpx; font-size:18rpx; font-weight:700; }
.point-status.high { background:rgba(221,81,117,.12); color:#dd5175; border:1rpx solid rgba(221,81,117,.2); }
.point-status.medium { background:rgba(212,134,24,.12); color:#d48618; border:1rpx solid rgba(212,134,24,.2); }
.point-status.low { background:rgba(17,163,107,.12); color:#11a36b; border:1rpx solid rgba(17,163,107,.2); }
.point-info-grid,.metric-grid,.quick-buttons { display:grid; gap:14rpx; }
.point-info-grid { grid-template-columns:repeat(3,1fr); }
.metric-grid { grid-template-columns:repeat(3,1fr); }
.quick-buttons { grid-template-columns:repeat(3,1fr); margin-top:18rpx; }
.top-entries { margin-top:0; }
.info-box,.metric-box,.quick-button { padding:18rpx; border-radius:22rpx; background:#faf8ff; min-width:0; }
.quick-button { display:flex; flex-direction:column; align-items:flex-start; }
.quick-title,.quick-sub { max-width:100%; word-break:break-word; }
.info-label,.metric-label { display:block; font-size:18rpx; color:#9489af; }
.info-value,.metric-value { display:block; margin-top:10rpx; font-size:24rpx; font-weight:800; color:#2d2454; }
.metric-unit,.quick-sub { display:block; margin-top:8rpx; font-size:18rpx; color:#9388ae; }
.quick-title { display:block; font-size:22rpx; font-weight:700; color:#2d2454; }
.workbench-row { display:flex; gap:12rpx; margin-bottom:22rpx; }
.wb-card { flex:1; min-width:0; padding:20rpx 10rpx; border-radius:24rpx; background:#fff; box-shadow:0 12rpx 28rpx rgba(49,30,109,.06); text-align:center; }
.wb-card.accent { background:linear-gradient(135deg,#eef2ff 0%,#fff 100%); border:2rpx solid #e8e0ff; }
.wb-num { display:block; font-size:36rpx; font-weight:800; color:#7b61ff; line-height:1.1; }
.wb-icon { display:block; font-size:26rpx; font-weight:800; color:#7b61ff; margin-bottom:6rpx; }
.wb-label { display:block; margin-top:6rpx; font-size:17rpx; color:#8c81a7; line-height:1.3; word-break:break-word; }
.pred-chart { position:relative; margin-top:16rpx; min-height:220rpx; border-radius:16rpx; background:#f8f4ff; }
.pred-seg { position:absolute; height:4rpx; transform-origin:left center; background:linear-gradient(90deg,#7b61ff 0%,#a38eff 100%); border-radius:999rpx; }
.pred-point { position:absolute; transform:translate(-50%,-50%); display:flex; flex-direction:column; align-items:center; }
.pred-dot { width:14rpx; height:14rpx; border-radius:50%; background:#7b61ff; border:3rpx solid #fff; box-shadow:0 0 0 2rpx rgba(123,97,255,.2); }
.pred-val { margin-top:6rpx; font-size:16rpx; font-weight:700; color:#2d2454; line-height:1.1; }
.pred-lab { font-size:14rpx; color:#9a8fb2; margin-top:2rpx; line-height:1.2; text-align:center; word-break:break-all; }
.actual-strip { margin-top:20rpx; padding-top:16rpx; border-top:1rpx solid #f0ecf8; }
.strip-title { font-size:20rpx; color:#7b61ff; font-weight:700; margin-bottom:10rpx; display:block; }
.strip-scroll { white-space:nowrap; width:100%; }
.strip-chip { display:inline-flex; flex-direction:column; align-items:center; padding:12rpx 18rpx; margin-right:10rpx; border-radius:16rpx; background:#faf8ff; }
.chip-t { font-size:16rpx; color:#9a8fb2; }
.chip-v { font-size:20rpx; font-weight:800; color:#2d2454; margin-top:4rpx; }
.motion-fade { opacity: 0; transform: translateY(12rpx); transition: opacity var(--wg-motion-slow) var(--wg-ease-standard), transform var(--wg-motion-slow) var(--wg-ease-standard); }
.home-page.motion-ready .motion-fade { opacity: 1; transform: translateY(0); }
.delay-1 { transition-delay: .02s; }
.delay-2 { transition-delay: .08s; }
.delay-3 { transition-delay: .14s; }
.delay-4 { transition-delay: .2s; }
.delay-5 { transition-delay: .26s; }
</style>
