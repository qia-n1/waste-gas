<template>
  <view class="records-page">
    <view class="records-hero">
      <view>
        <text class="hero-kicker">DISPOSAL RECORDS</text>
        <text class="page-title">处置记录</text>
        <text class="page-subtitle">查看闭环结果并支持导出。</text>
      </view>
      <button class="primary-btn small" @click="exportRecords">导出</button>
    </view>

    <view class="records-card" v-for="item in records" :key="item.id">
      <text class="record-title">{{ item.result }}</text>
      <text class="record-meta">告警 ID：{{ item.alertId }} · {{ item.status }}</text>
      <text class="record-meta">{{ item.notes }}</text>
      <text class="record-meta">{{ item.createdAt }}</text>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';

export default {
  data() {
    return { records: [] };
  },
  onShow() { this.loadRecords(); },
  methods: {
    async loadRecords() {
      try {
        const res = await request({ url: '/profile/disposals' });
        if (res?.code === 200) this.records = res.data;
      } catch (error) {
        uni.showToast({ title: '记录加载失败', icon: 'none' });
      }
    },
    async exportRecords() {
      try {
        const res = await request({ url: '/alerts/exports/disposals' });
        if (res?.code === 200) uni.showModal({ title: '导出内容', content: res.data.content.slice(0, 200) + '...', showCancel: false });
      } catch (error) {
        uni.showToast({ title: '导出失败', icon: 'none' });
      }
    }
  }
};
</script>

<style>
.records-page { min-height:100vh; padding:24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background:linear-gradient(180deg,#f7f3ff 0%,#fcfbff 52%,#ffffff 100%); }
.records-hero,.records-card { margin-bottom:22rpx; padding:26rpx; border-radius:28rpx; background:#fff; box-shadow:0 16rpx 36rpx rgba(49,30,109,.06); }
.records-hero { display:flex; justify-content:space-between; align-items:flex-end; gap:16rpx; }
.hero-kicker { display:inline-block; font-size:18rpx; color:#7b61ff; letter-spacing:2rpx; font-weight:700; }
.page-title { display:block; margin-top:14rpx; font-size:42rpx; font-weight:800; color:#2b2156; }
.page-subtitle { display:block; margin-top:10rpx; font-size:21rpx; line-height:1.6; color:#8378a1; }
.record-title { display:block; font-size:24rpx; font-weight:700; color:#2d2454; }
.record-meta { display:block; margin-top:10rpx; font-size:20rpx; line-height:1.6; color:#8d82aa; }
.primary-btn { height:88rpx; padding:0 24rpx; border-radius:22rpx; background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; font-size:22rpx; font-weight:700; }
.primary-btn.small::after { border:none; }
</style>
