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
          <text class="section-desc">缩放至约百分之一百五十显示工艺单元与标点；涂装车间设在喷涂生产厂房内。管辖区域有高亮，点击厂房可看说明与实时汇总</text>
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
          :class="{ 'map-zoom-detail': showMapDetail }"
          :style="mapZoomWrapStyle"
          @touchstart="onMapTouchStart"
          @touchmove="onMapTouchMove"
          @touchend="onMapTouchEnd"
          @touchcancel="onMapTouchEnd"
        >
        <view
          class="plant-canvas plant-campus"
          :class="{ 'zoom-detail': showMapDetail }"
          :style="mapCanvasStyle"
        >
          <view class="campus-bg"></view>
          <view class="campus-grass"></view>
          <view class="campus-road campus-road-n"></view>
          <view class="campus-road campus-road-s"></view>
          <view class="campus-road campus-road-w"></view>
          <view class="campus-road campus-road-e"></view>
          <view class="road-dash road-dash-h"></view>
          <view class="road-dash road-dash-v"></view>

          <view class="cooling-tower ct-a"></view>
          <view class="cooling-tower ct-b"></view>

          <block v-for="zone in mapZoneBubblesResolved" :key="`zone-bubble-${zone.key}`">
            <view
              v-if="shouldShowZoneBubble(zone)"
              class="zone-bubble"
              :style="zoneBubbleStyle(zone)"
              @click.stop="openBuildingFromKey(zone.key)"
            >
              <text class="zone-bubble-title">{{ zone.title }}</text>
              <text class="zone-bubble-sub">工艺单元</text>
            </view>
          </block>

          <view class="hit-stack" @click.stop="openBuildingFromKey('stack')"></view>
          <view class="chimney-column"></view>
          <view class="chimney-smoke s1"></view>
          <view class="chimney-smoke s2"></view>
          <view class="chimney-smoke s3"></view>

          <view
            class="bld bld-coating"
            :class="{ 'bld-owned': isOwnedZoneKey('coating') }"
            @click.stop="openBuildingFromKey('coating')"
          >
            <view class="bld-roof"></view>
            <view class="bld-body">
              <view v-if="showMapDetail" class="bld-structure"><view class="bld-str-line v1"></view><view class="bld-str-line v2"></view><view class="bld-str-line h1"></view></view>
            </view>
          </view>
          <view
            class="bld bld-rotor"
            :class="{ 'bld-owned': isOwnedZoneKey('rotor') }"
            @click.stop="openBuildingFromKey('rotor')"
          >
            <view class="bld-roof"></view>
            <view class="bld-body">
              <view v-if="showMapDetail" class="bld-structure"><view class="bld-str-line v1"></view><view class="bld-str-line h1"></view></view>
            </view>
          </view>
          <view
            class="bld bld-rto"
            :class="{ 'bld-owned': isOwnedZoneKey('rto') }"
            @click.stop="openBuildingFromKey('rto')"
          >
            <view class="bld-roof"></view>
            <view class="bld-body">
              <view v-if="showMapDetail" class="bld-structure bld-structure--dense"><view class="bld-str-line v1"></view><view class="bld-str-line v2"></view><view class="bld-str-line h1"></view><view class="bld-str-line h2"></view></view>
            </view>
          </view>
          <view
            class="bld bld-utility"
            :class="{ 'bld-owned': isOwnedZoneKey('utility') }"
            @click.stop="openBuildingFromKey('utility')"
          >
            <view class="bld-roof"></view>
            <view class="bld-body">
              <view v-if="showMapDetail" class="bld-structure"><view class="bld-str-line v1"></view><view class="bld-str-line h1"></view></view>
            </view>
          </view>
          <view class="bld bld-public" @click.stop="openBuildingFromKey('public')">
            <view class="bld-roof bld-roof--flat"></view>
            <view class="bld-body">
              <view v-if="showMapDetail" class="bld-structure"><view class="bld-str-line h1"></view></view>
            </view>
          </view>

          <block v-for="area in ownedAreasHighlight" :key="'own-' + area.id">
            <view class="area-own-ring" :style="areaOverlayStyle(area)"></view>
          </block>

          <block v-for="area in mapAreas" :key="'outline-' + area.id">
            <view
              v-if="area.canView && selectedArea && selectedArea.id === area.id"
              class="area-sel-outline"
              :class="area.level"
              :style="areaOverlayStyle(area)"
            ></view>
          </block>

          <view
            v-for="area in externalAreas"
            :key="`ext-${area.id}`"
            class="ext-marker"
            :class="area.level"
            :style="externalMarkerStyle(area)"
          >
            <view class="ext-dot"></view>
          </view>

          <view
            v-for="point in mapPointsForCanvas"
            :key="`mpt-${point.id}`"
            class="map-point"
            :class="[point.level, { active: selectedPoint && selectedPoint.id === point.id }]"
            :style="mapPointStyle(point)"
            @click.stop="selectPointByMap(point)"
          >
            <view class="map-point-anchor">
              <view
                v-if="showMapDetail || isAlwaysVisiblePoint(point)"
                class="map-point-cap"
                :class="{ compact: !showMapDetail }"
                :style="mapPointCapStyle(point)"
              >
                <text class="map-point-cap-txt">{{ showMapDetail ? formatPointMapLabel(point) : formatPointMarkerLabel(point) }}</text>
              </view>
              <view class="map-point-dotlayer">
                <view class="map-point-ring"></view>
                <view class="map-point-core"></view>
              </view>
            </view>
          </view>

          <view
            v-for="point in referenceMapPoints"
            :key="`ref-mpt-${point.id}`"
            class="map-point ref-only"
            :class="point.level"
            :style="mapPointStyle(point)"
          >
            <view class="map-point-anchor">
              <view class="map-point-dotlayer">
                <view class="map-point-ring"></view>
                <view class="map-point-core"></view>
              </view>
            </view>
          </view>
        </view>
        </view>
      </view>
      <view v-if="selectedAreaData && metricPointsForSelected.length" class="metric-block">
        <text class="metric-block-title">监测指标，{{ displayZoneTitle(selectedAreaData.name) }}</text>
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

      <view v-if="mapPanel && mapPanel.canView" class="map-building-panel">
        <text class="mbp-kicker">已选厂房与单元</text>
        <text class="mbp-title">{{ mapPanel.title }}</text>
        <text class="mbp-sub">{{ mapPanel.sub }}</text>
        <view class="mbp-stats">
          <text class="mbp-line">设备 {{ mapPanel.deviceCount }}，在线率 {{ mapPanel.onlineRate }}％，告警 {{ mapPanel.alertCount }}</text>
          <text class="mbp-line">区域均值挥发性有机物 {{ mapPanel.avgVocs }} 毫克每立方米，{{ levelLabel(mapPanel.level) }}</text>
          <text class="mbp-line mbp-live">实时数据：首页上方为全厂挥发性有机物与温湿度；选中排口后下方「区域详情」展示该点浓度与趋势。</text>
        </view>
      </view>
    </view>

    <view v-if="selectedPoint && selectedAreaData" class="detail-card motion-fade delay-4">
      <view class="section-head compact">
        <view>
          <text class="section-title">区域详情</text>
          <text class="section-desc">{{ displayZoneTitle(selectedPoint.areaName) }}，设备编号 {{ selectedPoint.deviceId }}</text>
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
          <text class="section-title">未来六小时挥发性有机物</text>
          <text class="section-desc">短时预测（毫克每立方米）</text>
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
          <text class="section-desc">当前挥发性有机物、温度、湿度核心指标</text>
        </view>
      </view>
      <view class="metric-grid">
        <view class="metric-box"><text class="metric-label">挥发性有机物</text><text class="metric-value">{{ animatedRealtime.vocs }}</text><text class="metric-unit">毫克每立方米</text></view>
        <view class="metric-box"><text class="metric-label">温度</text><text class="metric-value">{{ animatedRealtime.temperature }}</text><text class="metric-unit">摄氏度</text></view>
        <view class="metric-box"><text class="metric-label">相对湿度</text><text class="metric-value">{{ animatedRealtime.humidity }}</text><text class="metric-unit">百分比</text></view>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';
import { displaySensorFieldLabel } from '../../utils/sensorDisplay';
import { displayZoneTitle, formatPointMapLabel, formatPointMarkerLabel } from '../../utils/zoneDisplay';

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
      mapViewportHeight: 360,
      pinchStartDistance: 0,
      pinchStartScale: 1,
      isPinching: false,
      motionReady: false,
      mapPanel: null,
      /** 地图缩放 ≥ 该值时显示排口名称、厂房内构造线（与 zoomLabel 100% 基准对应） */
      mapDetailZoomThreshold: 1.5,
      /** 避免切页后 setInterval 仍回调，触发微信内部 __subPageFrameEndTime__ 空引用 */
      pageActive: true,
      animTimers: [],
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
      return `${Math.round(this.mapScale * 100)}％`;
    },
    showMapDetail() {
      return this.mapScale >= this.mapDetailZoomThreshold;
    },
    mapZoomWrapStyle() {
      const h = Number(this.mapViewportHeight || 360);
      return {
        minHeight: `${h}px`,
        maxHeight: `${Math.round(h * 1.12)}px`,
      };
    },
    mapCanvasStyle() {
      const h = Number(this.mapViewportHeight || 360);
      const detail = this.showMapDetail ? Math.round(h * 1.08) : h;
      return {
        transform: `scale(${this.mapScale})`,
        width: '100%',
        minWidth: '0',
        height: `${detail}px`,
        minHeight: `${detail}px`,
      };
    },
    ownedAreasHighlight() {
      return (this.mapAreas || []).filter((a) => a.canView);
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
    externalAreas() {
      return (this.mapAreas || []).filter((a) => !a.canView);
    },
    mapZoneBubbles() {
      return [
        { key: 'stack', title: '排口烟囱区', left: 11, top: 13 },
        { key: 'coating', title: '喷涂生产厂房', left: 35, top: 42 },
        { key: 'rotor', title: '转轮吸附厂房', left: 49, top: 39 },
        { key: 'rto', title: 'RTO 主处理厂房', left: 64, top: 47 },
        // 右侧两块固定错层，避免互相压住
        { key: 'utility', title: '公辅燃烧区', left: 89, top: 54 },
        { key: 'public', title: '监测附属区', left: 89, top: 69 },
      ];
    },
    primaryMonitorPointId() {
      const points = (this.mapPoints || []).filter((p) => String(p?.areaName || '').trim() === '喷涂生产厂房');
      if (!points.length) return null;
      // 默认态只显示 1 个监测点位：选喷涂车间附近（接近厂房中心）的点
      const target = { x: 34, y: 43 };
      const sorted = points.slice().sort((a, b) => {
        const dax = Number(a?.x ?? 50) - target.x;
        const day = Number(a?.y ?? 50) - target.y;
        const dbx = Number(b?.x ?? 50) - target.x;
        const dby = Number(b?.y ?? 50) - target.y;
        const da = dax * dax + day * day;
        const db = dbx * dbx + dby * dby;
        return da - db;
      });
      return sorted[0]?.id ?? null;
    },
    mapZoneBubblesResolved() {
      const bubbles = (this.mapZoneBubbles || []).map((item) => ({ ...item }));
      if (this.showMapDetail) return bubbles;
      const occupied = [];
      const visiblePointBoxes = (this.mapPoints || [])
        .filter((point) => this.isAlwaysVisiblePoint(point))
        .map((point) => this.pointLabelBox(point));
      const tryOffsets = [
        { dx: 0, dy: 0 },
        { dx: 0, dy: 14 },
        { dx: 0, dy: -10 },
        { dx: 0, dy: 10 },
        { dx: -12, dy: 0 },
        { dx: 12, dy: 0 },
        { dx: -16, dy: 14 },
        { dx: 16, dy: 14 },
        { dx: -12, dy: -8 },
        { dx: 12, dy: -8 },
        { dx: -14, dy: 10 },
        { dx: 14, dy: 10 },
      ];
      const resolved = bubbles.map((zone) => {
        const picked = this.pickBubblePlacement(zone, tryOffsets, visiblePointBoxes, occupied);
        occupied.push(this.zoneBubbleBox(picked.left, picked.top));
        return picked;
      });
      return this.enforceBubbleRowSpacing(resolved);
    },
    visiblePointAreaNames() {
      const names = new Set();
      (this.mapPoints || []).forEach((point) => {
        if (!this.isAlwaysVisiblePoint(point)) return;
        names.add(String(point?.areaName || '').trim());
      });
      return names;
    },
    metricPointsForSelected() {
      if (!this.selectedAreaData) return [];
      return this.pointsByArea[this.selectedAreaData.name] || [];
    },
    mapPointsForCanvas() {
      // 默认视图隐藏点位圆点，减少地图干扰；放大后仍可查看全部点位
      return this.showMapDetail ? (this.mapPoints || []) : [];
    },
    referenceMapPoints() {
      // 参考示意图补充的固定点位（仅地图展示，不影响后端监测数据）
      if (this.showMapDetail) return [];
      return [
        { id: 'ref-monitor-left', x: 12, y: 42, level: 'low' },
        { id: 'ref-coating-main', x: 34, y: 50, level: 'low' },
        { id: 'ref-key-device', x: 52, y: 34, level: 'high' },
        { id: 'ref-rto-mid', x: 63, y: 42, level: 'low' },
        { id: 'ref-outlet-right', x: 86, y: 42, level: 'high' },
        { id: 'ref-outlet-bottom', x: 84, y: 70, level: 'low' },
      ];
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
    this.pageActive = true;
    this.motionReady = false;
    this.updateMapViewport();
    this.$nextTick(() => {
      this.motionReady = true;
    });
    this.loadOverview();
  },
  onHide() {
    this.pageActive = false;
    this.clearAnimTimers();
  },
  onUnload() {
    this.pageActive = false;
    this.clearAnimTimers();
  },
  methods: {
    displayZoneTitle,
    formatPointMapLabel,
    formatPointMarkerLabel,
    clearAnimTimers() {
      (this.animTimers || []).forEach((t) => clearInterval(t));
      this.animTimers = [];
    },
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
    animateOverviewNumbers() {
      this.clearAnimTimers();
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
        if (!this.pageActive) return;
        if (overview?.code === 200 && overview.data) {
          this.realTimeData = overview.data.realTimeData || this.realTimeData;
          this.prediction6h = overview.data.prediction_6h || [];
          this.actualSeries = overview.data.actual_series || [];
          this.workbench = overview.data.workbench || { pendingDispatch: 0, inProgress: 0 };
          if (this.pageActive) this.animateOverviewNumbers();
          const preds = this.prediction6h.map((x) => x.predicted || 0);
          const acts = this.actualSeries.map((x) => x.vocs || 0);
          this.predMax = Math.max(1, ...preds, ...acts, this.realTimeData.vocs || 0);
          this.$nextTick(() => {
            if (this.pageActive) this.measurePredPlot();
          });
        }
        if (mapRes?.code === 200 && mapRes.data) {
          this.mapAreas = mapRes.data.areas || [];
          this.mapPoints = mapRes.data.points || [];
          this.nearestAlertId = mapRes.data.nearestAlertId;
          this.ownedAreaNames = mapRes.data.ownedAreaNames || [];
          this.mapPanel = null;
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
          if (this.selectedArea && this.selectedArea.canView) {
            this.syncMapPanelFromArea(this.selectedArea);
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
      this.syncMapPanelFromArea(area);
    },
    selectPoint(area, point) {
      if (!area.canView) {
        uni.showToast({ title: '无权限查看该区域', icon: 'none' });
        return;
      }
      this.selectedArea = area;
      this.selectedPoint = point;
      this.syncMapPanelFromArea(area);
    },
    focusNearestAlert() {
      const target = this.mapPoints.find(item => item.id === this.nearestAlertId);
      if (target) {
        this.selectedPoint = target;
        this.selectedArea = this.mapAreas.find(item => item.name === target.areaName && item.canView) || null;
        if (!this.selectedArea) {
          uni.showToast({ title: '告警不在您负责区域内', icon: 'none' });
          return;
        }
        this.syncMapPanelFromArea(this.selectedArea);
        return;
      }
      uni.showToast({ title: '暂无高等级告警定位', icon: 'none' });
    },
    focusMyArea() {
      const own = (this.mapAreas || []).find((a) => a.canView);
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
    updateMapViewport() {
      try {
        let w = 375;
        if (typeof uni.getWindowInfo === 'function') {
          const info = uni.getWindowInfo();
          w = Number(info?.windowWidth || w);
        } else if (typeof uni.getWindowInfoSync === 'function') {
          const info = uni.getWindowInfoSync();
          w = Number(info?.windowWidth || w);
        } else if (typeof uni.getSystemInfoSync === 'function') {
          const info = uni.getSystemInfoSync();
          w = Number(info?.windowWidth || w);
        }
        // 兼顾小屏与大屏，保持地图在首屏可完整查看
        const h = Math.max(300, Math.min(460, Math.round(w * 0.72)));
        this.mapViewportHeight = h;
      } catch (e) {
        this.mapViewportHeight = 360;
      }
    },
    isOwnedZoneKey(key) {
      const zoneByKey = {
        coating: '喷涂生产厂房',
        stack: '排口烟囱区',
        rotor: '转轮吸附厂房',
        rto: 'RTO 主处理厂房',
        utility: '公辅燃烧区',
        public: '监测附属区',
      };
      const zn = zoneByKey[key];
      if (!zn) return false;
      const a = (this.mapAreas || []).find((x) => x.name === zn);
      return !!(a && a.canView);
    },
    syncMapPanelFromArea(area) {
      if (!area || !area.canView) return;
      const subByZone = {
        喷涂生产厂房: '涂装车间位于喷涂生产厂房内，您负责的区域',
        排口烟囱区: '排口烟囱工艺单元，您负责的区域',
      };
      this.mapPanel = {
        title: this.displayZoneTitle(area.name),
        sub: subByZone[area.name] || '您负责的区域',
        canView: true,
        deviceCount: area.deviceCount,
        onlineRate: area.onlineRate,
        alertCount: area.alertCount,
        avgVocs: area.avgVocs,
        level: area.level,
      };
    },
    openBuildingFromKey(key) {
      const zoneByKey = {
        coating: '喷涂生产厂房',
        stack: '排口烟囱区',
        rotor: '转轮吸附厂房',
        rto: 'RTO 主处理厂房',
        utility: '公辅燃烧区',
        public: '监测附属区',
      };
      const name = zoneByKey[key];
      const area = (this.mapAreas || []).find((a) => a.name === name);
      if (!area) {
        this.selectedArea = null;
        this.selectedPoint = null;
        this.mapPanel = null;
        uni.showToast({ title: '暂无该区域数据', icon: 'none' });
        return;
      }
      if (!area.canView) {
        this.selectedArea = null;
        this.selectedPoint = null;
        this.mapPanel = null;
        uni.showToast({ title: '非您负责区域', icon: 'none' });
        return;
      }
      this.selectArea(area);
    },
    externalMarkerStyle(area) {
      const x = Number(area.x || 0);
      const y = Number(area.y || 0);
      const w = Number(area.w || 18);
      const h = Number(area.h || 24);
      const cx = x + w / 2;
      const cy = y + h / 2;
      return {
        left: `${Math.max(6, Math.min(94, cx))}%`,
        top: `${Math.max(10, Math.min(90, cy))}%`,
      };
    },
    zoneBubbleStyle(zone) {
      return {
        left: `${Math.max(8, Math.min(92, Number(zone.left || 50)))}%`,
        top: `${Math.max(10, Math.min(84, Number(zone.top || 50)))}%`,
      };
    },
    zoneNameByKey(key) {
      const zoneByKey = {
        coating: '喷涂生产厂房',
        stack: '排口烟囱区',
        rotor: '转轮吸附厂房',
        rto: 'RTO 主处理厂房',
        utility: '公辅燃烧区',
        public: '监测附属区',
      };
      return zoneByKey[key] || '';
    },
    shouldShowZoneBubble(zone) {
      if (this.showMapDetail) return true;
      const areaName = this.zoneNameByKey(zone?.key);
      if (!areaName) return true;
      // 同一区域默认只显示一种信息源：有点位短标签时隐藏区域气泡，降低交错
      return !this.visiblePointAreaNames.has(areaName);
    },
    zoneBubbleBox(left, top) {
      const cx = Number(left || 50);
      const cy = Number(top || 50);
      // 近似区域气泡尺寸（百分比），用于轻量碰撞规避
      const halfW = 9;
      const halfH = 4;
      return { l: cx - halfW, r: cx + halfW, t: cy - halfH, b: cy + halfH };
    },
    enforceBubbleRowSpacing(zones) {
      // 同一行最小水平间距约束：不够则下移一行，避免文字打架
      const minGap = 13;
      const rowBand = 8;
      const rowDrop = 9;
      const placed = [];
      return (zones || []).map((zone) => {
        const out = { ...zone };
        for (let i = 0; i < placed.length; i += 1) {
          const prev = placed[i];
          const sameRow = Math.abs(Number(prev.top) - Number(out.top)) <= rowBand;
          const closeX = Math.abs(Number(prev.left) - Number(out.left)) < minGap;
          if (sameRow && closeX) {
            out.top = Math.min(84, Number(out.top) + rowDrop);
          }
        }
        placed.push(out);
        return out;
      });
    },
    pointLabelBox(point) {
      const x = Number(point?.x ?? 50);
      const y = Number(point?.y ?? 50);
      const areaName = String(point?.areaName || '').trim();
      const below = areaName === '监测附属区';
      if (below) return { l: x - 8, r: x + 8, t: y + 3, b: y + 10 };
      return { l: x - 8, r: x + 8, t: y - 13, b: y - 5 };
    },
    boxesOverlap(a, b) {
      return !(a.r < b.l || a.l > b.r || a.b < b.t || a.t > b.b);
    },
    pickBubblePlacement(zone, offsets, pointBoxes, occupiedBoxes) {
      const baseLeft = Number(zone.left || 50);
      const baseTop = Number(zone.top || 50);
      for (let i = 0; i < offsets.length; i += 1) {
        const off = offsets[i];
        const left = Math.max(8, Math.min(92, baseLeft + off.dx));
        const top = Math.max(10, Math.min(84, baseTop + off.dy));
        const box = this.zoneBubbleBox(left, top);
        const hitPoint = pointBoxes.some((b) => this.boxesOverlap(box, b));
        const hitZone = occupiedBoxes.some((b) => this.boxesOverlap(box, b));
        if (!hitPoint && !hitZone) return { ...zone, left, top };
      }
      return { ...zone, left: baseLeft, top: baseTop };
    },
    isAlwaysVisiblePoint(point) {
      // 默认层级下仅保留一个“监测点位”（喷涂车间附近）；放大后展示全部
      if (this.showMapDetail) return true;
      return this.primaryMonitorPointId != null && point?.id === this.primaryMonitorPointId;
    },
    mapPointCapStyle(point) {
      if (this.showMapDetail) return {};
      const byAreaOffset = {
        排口烟囱区: { dx: 0, dy: -58 },
        喷涂生产厂房: { dx: -12, dy: -62 },
        转轮吸附厂房: { dx: 0, dy: -56 },
        'RTO 主处理厂房': { dx: 10, dy: -56 },
        公辅燃烧区: { dx: 18, dy: -56 },
        监测附属区: { dx: 16, dy: 44 },
      };
      const off = byAreaOffset[String(point?.areaName || '').trim()] || { dx: 0, dy: -56 };
      return {
        transform: `translate3d(calc(-50% + ${off.dx}rpx), ${off.dy}rpx, 0)`,
      };
    },
    mapPointStyle(point) {
      const x = Number(point && point.x != null ? point.x : 50);
      const y = Number(point && point.y != null ? point.y : 50);
      return {
        left: `${Math.max(4, Math.min(96, x))}%`,
        top: `${Math.max(8, Math.min(90, y))}%`,
      };
    },
    selectPointByMap(point) {
      const area = (this.mapAreas || []).find((a) => a.name === point.areaName && a.canView);
      if (!area) {
        uni.showToast({ title: '无权限查看该点位', icon: 'none' });
        return;
      }
      this.selectPoint(area, point);
    },
    areaOverlayStyle(area) {
      return {
        left: `${Math.max(2, Math.min(88, area.x || 5))}%`,
        top: `${Math.max(6, Math.min(84, area.y || 8))}%`,
        width: `${Math.max(12, Math.min(32, area.w || 16))}%`,
        height: `${Math.max(10, Math.min(52, area.h || 12))}%`,
      };
    },
    formatMetricLabel(key) {
      return displaySensorFieldLabel(key);
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
      if (!this.pageActive) return;
      const q = uni.createSelectorQuery().in(this);
      q.select('.pred-chart').boundingClientRect((rect) => {
        if (!this.pageActive || !rect) return;
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
.map-area { width:100%; border-radius:24rpx; overflow:auto; background:linear-gradient(180deg,#172343 0%,#0b1322 100%); box-shadow:inset 0 0 0 1rpx rgba(95,122,191,.22); }
.map-zoom-wrap { width:100%; min-height:560rpx; max-height:720rpx; overflow:auto; -webkit-overflow-scrolling:touch; }
.map-zoom-wrap.map-zoom-detail { padding:28rpx 12rpx 12rpx; box-sizing:border-box; }
.plant-canvas { position:relative; width:100%; min-width:720rpx; min-height:600rpx; height:600rpx; padding:14rpx; transform-origin: top left; transition: transform .16s ease, min-height .2s ease; box-sizing:border-box; overflow:visible; }
.plant-canvas.zoom-detail { min-height:640rpx; height:640rpx; }
.plant-campus { border-radius:16rpx; overflow:visible; }
.plant-campus.zoom-detail .campus-grass { opacity:1; filter:saturate(1.08); }
.campus-bg { position:absolute; inset:12rpx; border-radius:14rpx; background:radial-gradient(ellipse 70% 55% at 40% 22%, rgba(122,166,255,.14), transparent 55%), linear-gradient(180deg, rgba(23,35,67,.92), rgba(8,15,31,.98)); z-index:0; }
.campus-grass { position:absolute; left:9%; right:9%; top:18%; bottom:14%; border-radius:12rpx; background:linear-gradient(180deg,#7a9458 0%,#5f7a48 55%,#4d663c 100%); box-shadow:inset 0 0 0 2rpx rgba(0,0,0,.12); z-index:1; opacity:0.96; }
.campus-road { position:absolute; background:#2a3347; z-index:2; box-shadow:inset 0 0 0 1rpx rgba(255,255,255,.06); }
.campus-road-n { left:5%; right:5%; top:10%; height:2.4%; border-radius:6rpx; }
.campus-road-s { left:5%; right:5%; bottom:10%; height:2.4%; border-radius:6rpx; }
.campus-road-w { left:5%; width:2.2%; top:12%; bottom:12%; border-radius:6rpx; }
.campus-road-e { right:5%; width:2.2%; top:12%; bottom:12%; border-radius:6rpx; }
.road-dash { position:absolute; z-index:3; pointer-events:none; opacity:0.35; }
.road-dash-h { left:12%; right:12%; top:50%; height:0; border-top:4rpx dashed #d7d9df; }
.road-dash-v { top:18%; bottom:14%; left:50%; width:0; border-left:4rpx dashed #d7d9df; }
.cooling-tower { position:absolute; z-index:4; width:10%; height:20%; border-radius:50% 50% 42% 42%; background:linear-gradient(180deg,#f2f4f6 0%,#cfd5de 45%,#e6e8ec 100%); border:2rpx solid rgba(255,255,255,.2); box-shadow:0 6rpx 16rpx rgba(0,0,0,.25); }
.ct-a { left:46%; top:11%; }
.ct-b { left:58%; top:12%; }
.hit-stack { position:absolute; z-index:12; left:3%; top:22%; width:11%; height:28%; border-radius:12rpx; }
.chimney-column { position:absolute; z-index:5; left:6.5%; top:28%; width:2.8%; height:22%; border-radius:8rpx; background:linear-gradient(180deg,#ffffff 0%,#dfe3ea 55%,#cfd5de 100%); border:2rpx solid rgba(0,0,0,.08); pointer-events:none; }
.chimney-smoke { position:absolute; z-index:6; left:6%; width:4.5%; height:4.5%; border-radius:50%; background:rgba(230,236,245,.55); filter:blur(2rpx); animation:wg-smoke 3.2s ease-in-out infinite; pointer-events:none; }
.chimney-smoke.s1 { top:24%; animation-delay:0s; }
.chimney-smoke.s2 { top:20%; animation-delay:.6s; opacity:.75; }
.chimney-smoke.s3 { top:16%; animation-delay:1.1s; opacity:.55; }
@keyframes wg-smoke { 0%,100% { transform:translate(0,0) scale(1); opacity:.55; } 50% { transform:translate(6rpx,-10rpx) scale(1.15); opacity:.85; } }
.bld { position:absolute; z-index:5; border-radius:10rpx; pointer-events:auto; }
.bld-roof { position:absolute; left:-2%; right:-2%; top:0; height:22%; border-radius:8rpx 8rpx 4rpx 4rpx; background:linear-gradient(180deg,#2b84d3 0%,#1f6bb5 100%); box-shadow:0 2rpx 0 rgba(0,0,0,.12); }
.bld-roof--flat { height:16%; background:linear-gradient(180deg,#3a6d9a 0%,#2b84d3 100%); }
.bld-body { position:absolute; left:0; right:0; top:18%; bottom:0; border-radius:0 0 8rpx 8rpx; background:linear-gradient(180deg,#e6e7ea 0%,#d0d4dc 100%); border:2rpx solid rgba(0,0,0,.06); overflow:hidden; }
.bld-structure { position:absolute; inset:10%; pointer-events:none; opacity:0.55; }
.bld-structure--dense { opacity:0.65; }
.bld-str-line { position:absolute; background:rgba(35,117,193,.42); }
.bld-str-line.v1 { left:32%; top:8%; bottom:8%; width:2rpx; }
.bld-str-line.v2 { left:66%; top:8%; bottom:8%; width:2rpx; }
.bld-str-line.h1 { top:38%; left:8%; right:8%; height:2rpx; }
.bld-str-line.h2 { top:68%; left:8%; right:8%; height:2rpx; }
.bld-owned { animation:wg-bld-own 2.4s ease-in-out infinite; }
@keyframes wg-bld-own { 0%,100% { box-shadow:0 0 0 0 rgba(83,209,255,0); } 50% { box-shadow:0 0 22rpx 4rpx rgba(83,209,255,.45); } }
.area-own-ring { position:absolute; z-index:4; border-radius:16rpx; pointer-events:none; box-sizing:border-box; border:2rpx solid rgba(83,209,255,.55); animation:wg-area-ring 2s ease-in-out infinite; }
@keyframes wg-area-ring { 0%,100% { opacity:0.45; transform:scale(1); box-shadow:0 0 0 0 rgba(83,209,255,0); } 50% { opacity:0.95; transform:scale(1.01); box-shadow:0 0 20rpx 6rpx rgba(83,209,255,.35); } }
.bld-coating { left:15%; top:40%; width:19%; height:28%; }
.bld-rotor { left:33%; top:40%; width:17%; height:28%; }
.bld-rto { left:50%; top:36%; width:24%; height:34%; z-index:6; }
.bld-utility { left:76%; top:40%; width:15%; height:28%; }
.bld-public { left:72%; top:68%; width:22%; height:15%; }
.zone-bubble { position:absolute; z-index:24; transform:translate(-50%,-50%); min-width:152rpx; max-width:228rpx; padding:8rpx 12rpx; border-radius:12rpx; background:rgba(5,15,38,.88); border:1rpx solid rgba(112,175,255,.35); box-shadow:0 10rpx 24rpx rgba(0,0,0,.28); text-align:left; }
.zone-bubble-title { display:block; font-size:20rpx; font-weight:700; color:#eef6ff; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.zone-bubble-sub { display:block; margin-top:2rpx; font-size:16rpx; color:rgba(219,233,255,.9); line-height:1.2; }
.map-point { position:absolute; z-index:40; transform:translate(-50%,-50%); pointer-events:auto; overflow:visible; }
.map-point-anchor { position:relative; min-width:88rpx; min-height:88rpx; display:flex; align-items:center; justify-content:center; overflow:visible; z-index:1; }
.map-point-dotlayer { position:relative; width:48rpx; height:48rpx; pointer-events:none; }
.map-point-core { position:absolute; left:50%; top:50%; width:20rpx; height:20rpx; margin-left:-10rpx; margin-top:-10rpx; border-radius:50%; box-shadow:0 0 16rpx currentColor; border:3rpx solid rgba(255,255,255,.9); z-index:2; }
.map-point.low .map-point-core { background:#53d1ff; color:#53d1ff; }
.map-point.medium .map-point-core { background:#ffb347; color:#ffb347; }
.map-point.high .map-point-core { background:#ff5b61; color:#ff5b61; }
.map-point-ring { position:absolute; left:50%; top:50%; width:44rpx; height:44rpx; margin-left:-22rpx; margin-top:-22rpx; border-radius:50%; border:3rpx solid currentColor; opacity:.45; animation:wg-pulse 2s ease-out infinite; z-index:1; }
.map-point.low .map-point-ring { color:#53d1ff; }
.map-point.medium .map-point-ring { color:#ffb347; }
.map-point.high .map-point-ring { color:#ff5b61; }
.map-point.active .map-point-ring { opacity:.75; animation-duration:1.2s; }
.map-point.ref-only { z-index:32; pointer-events:none; }
.map-point.ref-only .map-point-dotlayer { width:42rpx; height:42rpx; }
.map-point.ref-only .map-point-core { width:16rpx; height:16rpx; margin-left:-8rpx; margin-top:-8rpx; }
.map-point.ref-only .map-point-ring { width:38rpx; height:38rpx; margin-left:-19rpx; margin-top:-19rpx; opacity:.35; }
@keyframes wg-pulse { 0% { transform:scale(.6); opacity:.6; } 100% { transform:scale(1.35); opacity:0; } }
.map-point-cap { position:absolute; z-index:41; bottom:100%; left:50%; transform:translate3d(-50%,0,0); margin-bottom:10rpx; max-width:520rpx; min-width:120rpx; padding:10rpx 14rpx; border-radius:12rpx; background:rgba(7,15,31,.92); border:1rpx solid rgba(95,122,191,.55); text-align:center; line-height:1.45; box-sizing:border-box; pointer-events:none; box-shadow:0 10rpx 22rpx rgba(0,0,0,.28); }
.map-point-cap.compact { min-width:88rpx; max-width:190rpx; padding:6rpx 10rpx; border-radius:10rpx; }
.map-point-cap.compact::after { content:''; position:absolute; left:50%; top:100%; width:2rpx; height:14rpx; margin-left:-1rpx; background:rgba(149,183,255,.7); border-radius:2rpx; }
.map-point-cap-txt { display:block; font-size:20rpx; font-weight:700; color:#f0f7ff; white-space:pre-line; word-break:keep-all; word-wrap:break-word; overflow-wrap:break-word; line-height:1.4; }
.map-point-cap.compact .map-point-cap-txt { font-size:18rpx; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.area-sel-outline { position:absolute; z-index:7; border-radius:14rpx; border:3rpx dashed rgba(83,209,255,.9); box-shadow:0 0 0 2rpx rgba(83,209,255,.15); pointer-events:none; box-sizing:border-box; }
.area-sel-outline.low { border-color:rgba(52,199,89,.85); box-shadow:0 0 0 2rpx rgba(52,199,89,.12); }
.area-sel-outline.medium { border-color:rgba(255,179,71,.9); box-shadow:0 0 0 2rpx rgba(255,179,71,.12); }
.area-sel-outline.high { border-color:rgba(255,91,97,.95); box-shadow:0 0 0 2rpx rgba(255,91,97,.15); }
.ext-marker { position:absolute; z-index:11; transform:translate(-50%,-50%); pointer-events:none; }
.ext-dot { width:14rpx; height:14rpx; border-radius:50%; border:3rpx solid rgba(255,255,255,.85); box-shadow:0 0 12rpx currentColor; }
.ext-marker.low .ext-dot { background:#53d1ff; color:#53d1ff; }
.ext-marker.medium .ext-dot { background:#ffb347; color:#ffb347; }
.ext-marker.high .ext-dot { background:#ff5b61; color:#ff5b61; }
.map-building-panel { margin-top:18rpx; padding:22rpx; border-radius:22rpx; background:linear-gradient(180deg,#f4f6ff 0%,#fff 100%); border:2rpx solid #e2e8ff; }
.mbp-kicker { display:block; font-size:18rpx; color:#7b61ff; font-weight:700; margin-bottom:8rpx; }
.mbp-title { display:block; font-size:30rpx; font-weight:800; color:#1f2548; line-height:1.25; }
.mbp-sub { display:block; margin-top:6rpx; font-size:22rpx; color:#6b7a99; }
.mbp-stats { margin-top:14rpx; }
.mbp-muted { margin-top:14rpx; }
.mbp-line { display:block; font-size:22rpx; color:#3d4663; line-height:1.5; margin-top:8rpx; }
.mbp-line.light { font-size:20rpx; color:#8c96b5; }
.mbp-live { margin-top:12rpx; font-size:20rpx; color:#5a6a94; line-height:1.45; }
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
