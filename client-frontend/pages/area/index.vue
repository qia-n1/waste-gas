<template>
  <view class="area-page">
    <view class="area-hero">
      <view class="hero-text">
        <text class="page-title">我的区域</text>
        <text class="page-subtitle">设备与浓度概览</text>
      </view>
      <view class="hero-chip">{{ overview.deviceCount }} 台设备</view>
    </view>

    <view class="area-card">
      <view class="summary-grid">
        <view class="summary-box"><text class="summary-label">在线率</text><text class="summary-value">{{ overview.onlineRate }}%</text></view>
        <view class="summary-box"><text class="summary-label">告警数</text><text class="summary-value">{{ overview.alertCount }}</text></view>
      </view>
    </view>

    <view class="area-card">
      <view class="section-head">
        <view>
          <text class="section-title">负责区域</text>
          <text class="section-desc">按权限展示可管理区域</text>
        </view>
      </view>
      <view v-if="!areas.length" class="empty-card">
        <text class="empty-title">暂无负责区域</text>
        <text class="empty-desc">请联系管理员分配区域权限</text>
      </view>
      <view class="list-box" v-for="item in areas" :key="item.name"><text class="list-title">{{ item.name }}</text><text class="list-meta">设备 {{ item.deviceCount }} · 在线率 {{ item.onlineRate }}% · 告警 {{ item.alertCount }}</text></view>
    </view>

    <view class="area-card">
      <view class="section-head">
        <view>
          <text class="section-title">废气源列表</text>
          <text class="section-desc">按区域归集的监测点</text>
        </view>
      </view>
      <view v-if="!sources.length" class="empty-card">
        <text class="empty-title">暂无废气源数据</text>
        <text class="empty-desc">当前筛选下没有可展示数据</text>
      </view>
      <view class="list-box" v-for="item in sources" :key="item.id"><text class="list-title">{{ item.name }}</text><text class="list-meta">{{ item.areaName }} · {{ item.concentration }} mg/m³ · {{ item.status }}</text></view>
    </view>

    <view class="area-card">
      <view class="section-head">
        <view>
          <text class="section-title">设备状态</text>
          <text class="section-desc">连接信息与运行状态</text>
        </view>
      </view>
      <view v-if="!deviceStatus.length" class="empty-card">
        <text class="empty-title">暂无设备状态</text>
        <text class="empty-desc">请确认设备接入或稍后刷新</text>
      </view>
      <view class="list-box" v-for="item in deviceStatus" :key="item.deviceId"><text class="list-title">{{ item.deviceName }}</text><text class="list-meta">{{ item.deviceId }} · {{ item.location }} · {{ item.status }}</text></view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return { overview: { deviceCount: 0, onlineRate: 0, alertCount: 0 }, areas: [], sources: [], deviceStatus: [] };
  },
  onShow() { this.loadAreaData(); },
  methods: {
    async loadAreaData() {
      try {
        const res = await request({ url: '/dashboard/my-area' });
        if (res?.code === 200) {
          this.overview = res.data.overview;
          this.areas = res.data.areas;
          this.sources = res.data.sources;
          this.deviceStatus = res.data.deviceStatus;
        }
      } catch (error) {
        uni.showToast({ title: '区域数据加载失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.area-page { min-height:100vh; padding:24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background:linear-gradient(180deg,#f7f3ff 0%,#fcfbff 52%,#ffffff 100%); }
.area-hero,.area-card { margin-bottom:22rpx; padding:26rpx; border-radius:28rpx; background:#fff; box-shadow:0 16rpx 36rpx rgba(49,30,109,.06); }
.area-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:16rpx; }
.hero-text { flex:1; min-width:0; }
.page-title { display:block; font-size:42rpx; font-weight:800; color:#2b2156; line-height:1.2; word-break:break-word; }
.page-subtitle { display:block; margin-top:10rpx; font-size:22rpx; line-height:1.45; color:#8378a1; word-break:break-word; }
.hero-chip { flex-shrink:0; padding:12rpx 18rpx; border-radius:999rpx; background:#efe9ff; color:#7b61ff; font-size:21rpx; font-weight:700; }
.summary-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:14rpx; }
.summary-box,.list-box { padding:20rpx; border-radius:22rpx; background:#faf8ff; }
.summary-label,.list-meta { display:block; font-size:19rpx; color:#9388ae; }
.summary-value,.list-title,.section-title { display:block; margin-top:10rpx; font-size:24rpx; font-weight:700; color:#2d2454; }
.section-title { margin-top:0; margin-bottom:16rpx; font-size:31rpx; }
.section-head { margin-bottom: 8rpx; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; line-height:1.45; color:#8c81a7; }
.list-box { margin-top:14rpx; }
.list-box:active { transform: scale(0.995); background:#f4efff; }
.list-meta { line-height:1.45; word-break:break-word; }
.empty-card { padding:32rpx 24rpx; border-radius:22rpx; background:#faf8ff; text-align:center; margin-top:14rpx; }
.empty-title { display:block; font-size:23rpx; color:#2d2454; font-weight:700; }
.empty-desc { display:block; margin-top:10rpx; font-size:20rpx; color:#9388ae; line-height:1.55; }
</style>
