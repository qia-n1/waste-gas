<template>
  <view class="records-page">
    <view class="records-hero">
      <view class="hero-text">
        <text class="page-title">巡检与处置</text>
        <text class="page-subtitle">处置闭环与日常巡检</text>
      </view>
      <view class="hero-side">
        <text class="hero-chip">{{ activeTab === 'disposal' ? disposals.length : inspections.length }} 条</text>
        <button class="primary-btn small" @click="exportRecords">导出处置</button>
      </view>
    </view>

    <view class="tab-row">
      <view class="tab-item" :class="{ active: activeTab === 'disposal' }" @click="activeTab = 'disposal'"><text>处置闭环</text></view>
      <view class="tab-item" :class="{ active: activeTab === 'inspection' }" @click="activeTab = 'inspection'"><text>日常巡检</text></view>
    </view>

    <view v-if="activeTab === 'disposal'" class="tab-panel">
      <view v-if="!disposals.length" class="empty-tip"><text>暂无处置记录</text></view>
      <view class="records-card" v-for="item in pagedDisposals" :key="'d-' + item.id">
        <text class="record-title">{{ item.result }}</text>
        <text class="record-meta">告警编号 {{ item.alertId }}，{{ item.status }}</text>
        <text class="record-meta">{{ item.notes }}</text>
        <text class="record-meta">{{ item.createdAt }}</text>
      </view>
      <view v-if="disposals.length" class="pager-row">
        <button class="pager-btn" :disabled="disposalPage <= 1" @click="changeDisposalPage(-1)">上一页</button>
        <text class="pager-text">{{ disposalPage }}/{{ disposalTotalPages }}</text>
        <button class="pager-btn" :disabled="disposalPage >= disposalTotalPages" @click="changeDisposalPage(1)">下一页</button>
      </view>
    </view>

    <view v-else class="tab-panel">
      <view class="form-card">
        <text class="form-title">新建巡检</text>
        <input v-model.trim="inspectForm.areaName" class="form-input" placeholder="区域名称" />
        <textarea v-model.trim="inspectForm.summary" class="form-textarea" placeholder="巡检摘要" />
        <button class="primary-btn full" @click="submitInspection">提交巡检</button>
      </view>
      <text class="list-title">历史巡检</text>
      <view v-if="!inspections.length" class="empty-tip"><text>暂无巡检记录</text></view>
      <view class="records-card" v-for="item in pagedInspections" :key="'i-' + item.id">
        <text class="record-title">{{ displayZoneTitle(item.areaName) }}</text>
        <text class="record-meta">{{ item.summary }}</text>
        <text class="record-meta">{{ item.createdAt }}</text>
      </view>
      <view v-if="inspections.length" class="pager-row">
        <button class="pager-btn" :disabled="inspectionPage <= 1" @click="changeInspectionPage(-1)">上一页</button>
        <text class="pager-text">{{ inspectionPage }}/{{ inspectionTotalPages }}</text>
        <button class="pager-btn" :disabled="inspectionPage >= inspectionTotalPages" @click="changeInspectionPage(1)">下一页</button>
      </view>
    </view>
  </view>
</template>

<script>
import { request } from '../../utils/api';
import { displayZoneTitle } from '../../utils/zoneDisplay';

export default {
  data() {
    return {
      activeTab: 'disposal',
      disposals: [],
      inspections: [],
      inspectForm: { areaName: '', summary: '' },
      pageSize: 8,
      disposalPage: 1,
      inspectionPage: 1,
    };
  },
  computed: {
    disposalTotalPages() { return Math.max(1, Math.ceil(this.disposals.length / this.pageSize)); },
    inspectionTotalPages() { return Math.max(1, Math.ceil(this.inspections.length / this.pageSize)); },
    pagedDisposals() {
      const start = (this.disposalPage - 1) * this.pageSize;
      return this.disposals.slice(start, start + this.pageSize);
    },
    pagedInspections() {
      const start = (this.inspectionPage - 1) * this.pageSize;
      return this.inspections.slice(start, start + this.pageSize);
    },
  },
  onLoad(query) {
    if (query?.tab === 'inspection') {
      this.activeTab = 'inspection';
    } else if (query?.tab === 'disposal') {
      this.activeTab = 'disposal';
    }
  },
  onShow() {
    this.loadDisposals();
    this.loadInspections();
  },
  methods: {
    displayZoneTitle,
    async loadDisposals() {
      try {
        const res = await request({ url: '/profile/disposals' });
        if (res?.code === 200) this.disposals = res.data || [];
        this.disposalPage = 1;
      } catch (e) {
        uni.showToast({ title: '处置记录加载失败', icon: 'none' });
      }
    },
    async loadInspections() {
      try {
        const res = await request({ url: '/profile/inspections' });
        if (res?.code === 200) this.inspections = res.data || [];
        this.inspectionPage = 1;
      } catch (e) {
        uni.showToast({ title: '巡检记录加载失败', icon: 'none' });
      }
    },
    async submitInspection() {
      if (!this.inspectForm.areaName || !this.inspectForm.summary) {
        return uni.showToast({ title: '请填写区域与摘要', icon: 'none' });
      }
      try {
        await request({
          url: '/profile/inspections',
          method: 'POST',
          data: { area_name: this.inspectForm.areaName, summary: this.inspectForm.summary },
        });
        uni.showToast({ title: '已保存', icon: 'success' });
        this.inspectForm = { areaName: '', summary: '' };
        await this.loadInspections();
        this.activeTab = 'inspection';
      } catch (e) {
        uni.showToast({ title: '提交失败', icon: 'none' });
      }
    },
    async exportRecords() {
      try {
        const res = await request({ url: '/alerts/exports/disposals' });
        if (res?.code === 200) {
          const c = res.data?.content || '';
          uni.showModal({
            title: '导出预览',
            content: c.length > 400 ? c.slice(0, 400) + '…' : c,
            confirmText: '去个人中心',
            cancelText: '关闭',
            success: (modalRes) => {
              if (!modalRes.confirm) return;
              uni.switchTab({ url: '/pages/profile/index' });
            },
          });
        }
      } catch (e) {
        uni.showToast({ title: '导出失败', icon: 'none' });
      }
    },
    changeDisposalPage(step) {
      const next = this.disposalPage + step;
      this.disposalPage = Math.min(this.disposalTotalPages, Math.max(1, next));
    },
    changeInspectionPage(step) {
      const next = this.inspectionPage + step;
      this.inspectionPage = Math.min(this.inspectionTotalPages, Math.max(1, next));
    },
  },
};
</script>

<style>
.records-page { min-height:100vh; padding:24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background:linear-gradient(180deg,#f7f3ff 0%,#fcfbff 52%,#ffffff 100%); }
.records-hero,.records-card,.form-card { margin-bottom:22rpx; padding:26rpx; border-radius:28rpx; background:#fff; box-shadow:0 16rpx 36rpx rgba(49,30,109,.06); }
.records-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:16rpx; }
.hero-text { flex:1; min-width:0; }
.hero-side { display:flex; flex-direction:column; align-items:flex-end; gap:10rpx; flex-shrink:0; }
.hero-chip { padding:10rpx 16rpx; border-radius:999rpx; background:#efe9ff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.page-title { display:block; font-size:42rpx; font-weight:800; color:#2b2156; line-height:1.2; word-break:break-word; }
.page-subtitle { display:block; margin-top:10rpx; font-size:22rpx; line-height:1.45; color:#8378a1; word-break:break-word; }
.primary-btn.small { flex-shrink:0; }
.tab-row { display:flex; gap:12rpx; margin-bottom:18rpx; }
.tab-item { flex:1; text-align:center; padding:20rpx; border-radius:22rpx; background:#fff; color:#8d82aa; font-size:22rpx; font-weight:700; box-shadow:0 8rpx 20rpx rgba(49,30,109,.05); }
.tab-item.active { background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; }
.tab-item:active { transform: scale(0.995); }
.tab-panel { min-height:200rpx; }
.record-title { display:block; font-size:24rpx; font-weight:700; color:#2d2454; line-height:1.3; word-break:break-word; }
.record-meta { display:block; margin-top:10rpx; font-size:20rpx; line-height:1.45; color:#8d82aa; word-break:break-word; }
.primary-btn { height:88rpx; padding:0 24rpx; border-radius:22rpx; background:linear-gradient(135deg,#7b61ff 0%,#947dff 100%); color:#fff; font-size:28rpx; font-weight:700; }
.primary-btn.small::after,.primary-btn.full::after { border:none; }
.primary-btn.full { width:100%; margin-top:16rpx; }
.records-card { border:2rpx solid rgba(123,97,255,.06); }
.form-card { display:flex; flex-direction:column; gap:0; }
.form-title { font-size:28rpx; font-weight:800; color:#2d2454; margin-bottom:16rpx; display:block; }
.form-input {
  width:100%;
  margin-top:12rpx;
  height:88rpx;
  line-height:88rpx;
  padding:0 20rpx;
  border-radius:20rpx;
  background:#faf8ff;
  font-size:22rpx;
  box-sizing:border-box;
  vertical-align:middle;
}
.form-textarea {
  width:100%;
  margin-top:12rpx;
  min-height:160rpx;
  padding:20rpx;
  border-radius:20rpx;
  background:#faf8ff;
  font-size:22rpx;
  line-height:1.45;
  box-sizing:border-box;
}
.list-title { display:block; margin:8rpx 0 14rpx; font-size:24rpx; font-weight:800; color:#2d2454; }
.empty-tip { padding:36rpx 24rpx; text-align:center; font-size:21rpx; color:#9a8fb2; line-height:1.6; border-radius:22rpx; background:#faf8ff; }
.pager-row { margin-top:2rpx; margin-bottom:12rpx; display:flex; align-items:center; justify-content:flex-end; gap:12rpx; }
.pager-btn { min-width:112rpx; height:62rpx; padding:0 16rpx; border-radius:16rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.pager-btn::after { border:none; }
.pager-btn[disabled] { opacity:.45; }
.pager-text { font-size:20rpx; color:#8f84ab; min-width:72rpx; text-align:center; }
</style>
