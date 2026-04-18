<template>
  <view class="profile-page">
    <view class="profile-hero">
      <view class="hero-left">
        <view class="user-avatar"><text class="avatar-text">{{ userAvatar }}</text></view>
        <view class="user-details">
          <text class="username">{{ userInfo.username || '未登录用户' }}</text>
          <text class="user-role">{{ userInfo.role || '普通用户' }}</text>
          <text class="user-area">负责区域：{{ areaText }}</text>
        </view>
      </view>
      <view class="hero-actions">
        <button class="btn-edit" @click="editProfile">编辑</button>
        <button class="btn-logout-top" @click="logout">退出</button>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">我的告警与处置</text><text class="section-desc">处置与巡检</text></view></view>
      <view class="summary-grid">
        <view class="summary-box"><text class="summary-label">我的处置</text><text class="summary-value">{{ disposals.length }}</text></view>
        <view class="summary-box"><text class="summary-label">巡检记录</text><text class="summary-value">{{ inspections.length }}</text></view>
      </view>
      <view class="summary-actions">
        <view class="action-pill" @click="navigateTo('/pages/records/index')">处置记录</view>
        <view class="action-pill" @click="navigateTo('/pages/area/index')">我的区域</view>
        <view class="action-pill" @click="navigateTo('/pages/ai/chat')">AI 助手</view>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">工人月度总结</text><text class="section-desc">{{ monthlySummary.month }} 工作概览</text></view></view>
      <view class="summary-grid monthly-grid">
        <view class="summary-box"><text class="summary-label">本月处置</text><text class="summary-value">{{ monthlySummary.disposalCount }}</text></view>
        <view class="summary-box"><text class="summary-label">本月巡检</text><text class="summary-value">{{ monthlySummary.inspectionCount }}</text></view>
        <view class="summary-box"><text class="summary-label">活跃天数</text><text class="summary-value">{{ monthlySummary.activeDays }}</text></view>
        <view class="summary-box"><text class="summary-label">结案处置</text><text class="summary-value">{{ monthlySummary.resolvedCount }}</text></view>
      </view>
      <view class="monthly-note">
        <text class="monthly-label">最近巡检：</text>
        <text class="monthly-value">{{ monthlySummary.lastInspectionAt }}</text>
      </view>
      <view class="monthly-list">
        <text v-for="(item, idx) in monthlySummary.highlights" :key="idx" class="monthly-item">• {{ item }}</text>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">个人信息</text><text class="section-desc">账号资料</text></view></view>
      <view class="info-list">
        <view class="info-item"><text class="info-label">姓名</text><text class="info-value">{{ userInfo.name || '-' }}</text></view>
        <view class="info-item"><text class="info-label">邮箱</text><text class="info-value">{{ userInfo.email || '-' }}</text></view>
        <view class="info-item"><text class="info-label">电话</text><text class="info-value">{{ userInfo.phone || '-' }}</text></view>
        <view class="info-item"><text class="info-label">所属部门</text><text class="info-value">{{ userInfo.department || '-' }}</text></view>
        <view class="info-item"><text class="info-label">入职时间</text><text class="info-value">{{ userInfo.joinDate || '-' }}</text></view>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">我的处置记录</text><text class="section-desc">可导出</text></view><text class="action-link" @click="exportDisposals">导出</text></view>
      <view class="record-list">
        <view v-for="item in pagedDisposals" :key="item.id" class="record-item"><text class="record-title">{{ item.result }}</text><text class="record-meta">{{ item.status }} · {{ item.createdAt }}</text></view>
      </view>
      <view v-if="disposals.length" class="pager-row">
        <button class="pager-btn" :disabled="disposalPage <= 1" @click="changeDisposalPage(-1)">上一页</button>
        <text class="pager-text">{{ disposalPage }}/{{ disposalTotalPages }}</text>
        <button class="pager-btn" :disabled="disposalPage >= disposalTotalPages" @click="changeDisposalPage(1)">下一页</button>
      </view>
    </view>

    <view class="profile-card">
      <view class="section-head"><view><text class="section-title">个人巡检记录</text><text class="section-desc">最近记录</text></view></view>
      <view class="record-list">
        <view v-for="item in pagedInspections" :key="item.id" class="record-item"><text class="record-title">{{ item.areaName }}</text><text class="record-meta">{{ item.summary }}</text><text class="record-meta">{{ item.createdAt }}</text></view>
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
import { clearAuthState, request } from '../../utils/api';

export default {
  data() {
    return {
      userInfo: { username: '', role: '', name: '', email: '', phone: '', department: '', joinDate: '', areas: [] },
      disposals: [],
      inspections: [],
      loading: false,
      monthlySummary: {
        month: '--',
        disposalCount: 0,
        inspectionCount: 0,
        activeDays: 0,
        resolvedCount: 0,
        lastInspectionAt: '暂无',
        highlights: [],
      },
      pageSize: 6,
      disposalPage: 1,
      inspectionPage: 1,
    };
  },
  computed: {
    userAvatar() { return this.userInfo.username ? this.userInfo.username.charAt(0).toUpperCase() : 'U'; },
    areaText() { return Array.isArray(this.userInfo.areas) && this.userInfo.areas.length ? this.userInfo.areas.join('、') : '未分配'; },
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
  onShow() { this.loadProfile(); },
  methods: {
    async loadProfile() {
      this.loading = true;
      try {
        const [profileRes, disposalRes, inspectionRes, monthlyRes] = await Promise.all([
          request({ url: '/profile/me' }),
          request({ url: '/profile/disposals' }),
          request({ url: '/profile/inspections' }),
          request({ url: '/profile/monthly-summary' }),
        ]);
        if (profileRes?.code === 200) this.userInfo = profileRes.data;
        if (disposalRes?.code === 200) this.disposals = disposalRes.data || [];
        if (inspectionRes?.code === 200) this.inspections = inspectionRes.data || [];
        if (monthlyRes?.code === 200 && monthlyRes.data) this.monthlySummary = monthlyRes.data;
        this.disposalPage = 1;
        this.inspectionPage = 1;
      } catch (error) {
        if (String(error?.message || '').includes('Unauthorized')) return;
        uni.showToast({ title: '用户信息加载失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    editProfile() { uni.navigateTo({ url: '/pages/profile/edit' }); },
    async exportDisposals() {
      try {
        const res = await request({ url: '/alerts/exports/disposals' });
        if (res?.code === 200) {
          uni.showModal({
            title: '导出内容',
            content: res.data.content.slice(0, 200) + '...',
            confirmText: '去记录页',
            cancelText: '关闭',
            success: (modalRes) => {
              if (!modalRes.confirm) return;
              uni.navigateTo({ url: '/pages/records/index?tab=disposal' });
            },
          });
        }
      } catch (error) {
        uni.showToast({ title: '导出失败', icon: 'none' });
      }
    },
    navigateTo(url) {
      const tabPages = ['/pages/index/index', '/pages/monitor/realtime', '/pages/alerts/list', '/pages/profile/index'];
      const path = url.split('?')[0];
      if (tabPages.includes(path)) {
        uni.switchTab({ url: path });
        return;
      }
      uni.navigateTo({ url });
    },
    changeDisposalPage(step) {
      const next = this.disposalPage + step;
      this.disposalPage = Math.min(this.disposalTotalPages, Math.max(1, next));
    },
    changeInspectionPage(step) {
      const next = this.inspectionPage + step;
      this.inspectionPage = Math.min(this.inspectionTotalPages, Math.max(1, next));
    },
    logout() {
      uni.showModal({ title: '退出登录', content: '确定要退出登录吗？', success: (res) => {
        if (res.confirm) {
          clearAuthState();
          uni.showToast({ title: '已退出登录', duration: 1000 });
          uni.reLaunch({ url: '/pages/auth/login' });
        }
      }});
    }
  }
};
</script>

<style>
.profile-page { min-height: 100vh; padding: 24rpx 24rpx calc(36rpx + env(safe-area-inset-bottom)); background: linear-gradient(180deg, #f7f3ff 0%, #fcfbff 52%, #ffffff 100%); }
.profile-hero,.profile-card { margin-bottom: 22rpx; padding: 26rpx; border-radius: 28rpx; background: #fff; box-shadow: 0 16rpx 36rpx rgba(49,30,109,.06); }
.profile-hero { display:flex; justify-content:space-between; align-items:center; gap:18rpx; background:linear-gradient(135deg,#7b61ff 0%,#8d74ff 50%,#b39cff 100%); }
.hero-left { display:flex; align-items:center; gap:18rpx; flex:1; min-width:0; }
.hero-actions { display:flex; flex-direction:column; gap:10rpx; flex-shrink:0; }
.user-details { flex:1; min-width:0; }
.user-avatar { width:112rpx; height:112rpx; border-radius:34rpx; background:rgba(255,255,255,.18); display:flex; align-items:center; justify-content:center; font-size:42rpx; font-weight:800; }
.avatar-text,.username,.user-role,.user-area,.btn-edit { color:#fff; }
.username { display:block; font-size:31rpx; font-weight:800; line-height:1.25; word-break:break-word; }
.user-role,.user-area { display:block; margin-top:8rpx; font-size:20rpx; opacity:.92; line-height:1.4; word-break:break-word; }
.btn-edit { flex-shrink:0; min-height:72rpx; padding:0 26rpx; border-radius:22rpx; background:rgba(255,255,255,.18); font-size:24rpx; font-weight:700; }
.btn-edit::after { border:none; }
.btn-logout-top { min-height:64rpx; padding:0 22rpx; border-radius:18rpx; background:rgba(255,255,255,.2); color:#fff; font-size:20rpx; font-weight:700; }
.btn-logout-top::after { border:none; }
.section-head { display:flex; justify-content:space-between; align-items:center; gap:12rpx; margin-bottom:18rpx; }
.section-title { display:block; font-size:31rpx; font-weight:800; color:#2d2454; }
.section-desc { display:block; margin-top:8rpx; font-size:20rpx; color:#8c81a7; }
.action-link { color:#7b61ff; font-size:20rpx; font-weight:700; }
.summary-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:14rpx; }
.monthly-grid { margin-bottom: 10rpx; }
.summary-box,.info-item,.record-item { padding:20rpx; border-radius:22rpx; background:#faf8ff; }
.summary-actions { display:flex; gap:12rpx; margin-top:14rpx; }
.action-pill { flex:1; text-align:center; padding:16rpx 12rpx; border-radius:18rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.action-pill:active { transform: scale(0.98); background:#e4dbff; }
.summary-label,.info-label,.record-meta { display:block; font-size:18rpx; color:#9388ae; }
.summary-value,.info-value,.record-title { display:block; margin-top:10rpx; font-size:23rpx; color:#2d2454; font-weight:700; }
.info-list,.record-list { display:flex; flex-direction:column; gap:14rpx; }
.info-item { display:flex; justify-content:space-between; align-items:center; gap:16rpx; }
.info-value { text-align:right; }
.record-title { margin-top:0; }
.record-meta { margin-top:8rpx; line-height:1.6; }
.monthly-note { margin-top: 8rpx; padding: 16rpx 18rpx; border-radius: 18rpx; background: #faf8ff; }
.monthly-label { font-size: 18rpx; color: #8f84ab; }
.monthly-value { font-size: 20rpx; color: #2d2454; font-weight: 700; }
.monthly-list { margin-top: 12rpx; display:flex; flex-direction:column; gap:8rpx; }
.monthly-item { font-size: 19rpx; color: #6f6686; line-height: 1.5; }
.pager-row { margin-top:14rpx; display:flex; align-items:center; justify-content:flex-end; gap:12rpx; }
.pager-btn { min-width:112rpx; height:62rpx; padding:0 16rpx; border-radius:16rpx; background:#efeaff; color:#7b61ff; font-size:20rpx; font-weight:700; }
.pager-btn::after { border:none; }
.pager-btn[disabled] { opacity:.45; }
.pager-text { font-size:20rpx; color:#8f84ab; min-width:72rpx; text-align:center; }
</style>
